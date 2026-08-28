#!/usr/bin/env python3
"""Watch a GitLab merge request or GitHub pull request for relevant feedback."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass
from typing import Callable, TextIO, TypeVar

Json = object
Runner = Callable[[list[str]], Json]

# A harness runs this script with a bare `python3`, not through this repo's
# environment, so it stays clear of syntax newer than it has to be: hence a
# TypeVar rather than PEP 695 generics, which would require 3.12.
T = TypeVar("T")


@dataclass(frozen=True)
class ReviewTarget:
    """A review URL reduced to the fields needed by provider APIs."""

    provider: str
    host: str
    project: str
    number: int


@dataclass(frozen=True)
class Event:
    """Provider-neutral review feedback."""

    id: str
    author: str
    body: str
    url: str
    created_at: str
    reply_to_user: bool = False
    human: bool = True


def parse_review_url(url: str) -> ReviewTarget:
    """Parse a GitLab MR or GitHub PR URL."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip("/")
    gitlab = re.fullmatch(r"(.+)/-/merge_requests/(\d+)(?:/.*)?", path)
    if gitlab:
        return ReviewTarget("gitlab", parsed.netloc, gitlab.group(1), int(gitlab.group(2)))
    github = re.fullmatch(r"([^/]+/[^/]+)/pull/(\d+)(?:/.*)?", path)
    if github:
        return ReviewTarget("github", parsed.netloc, github.group(1), int(github.group(2)))
    raise ValueError(f"not a GitLab MR or GitHub PR URL: {url}")


def run_json(command: list[str]) -> Json:
    """Run an authenticated provider CLI command and decode its JSON output."""
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def _list(value: Json) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("provider API returned a non-list response")
    return [item for item in value if isinstance(item, dict)]


def _dict(value: Json) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("provider API returned a non-object response")
    return value


def _nested(item: dict[str, object], key: str) -> dict[str, object]:
    nested = item.get(key)
    return nested if isinstance(nested, dict) else {}


def _nested_text(item: dict[str, object], key: str, nested_key: str) -> str:
    return str(_nested(item, key).get(nested_key, ""))


# A provider CLI that is briefly unreachable, rate-limited, or mid-deploy fails
# in one of these ways. None of them means the review is gone, so all of them
# wait and retry rather than ending the watch.
TRANSIENT_ERRORS = (
    OSError,
    subprocess.SubprocessError,
    json.JSONDecodeError,
    ValueError,
)


def retrying(
    fetch: Callable[[], T],
    *,
    interval: float,
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[], T]:
    """Wrap a fetch so a transient provider failure waits and retries.

    Retry belongs inside the fetch, not around the poll loop: restarting the
    loop would rebuild its baseline from a fresh snapshot and silently swallow
    every comment that arrived during the outage.
    """

    def attempt() -> T:
        while True:
            try:
                return fetch()
            except TRANSIENT_ERRORS:
                sleep(interval)

    return attempt


class GitLabProvider:
    """Read merge-request metadata and discussions through glab."""

    def __init__(
        self, target: ReviewTarget, *, runner: Runner = run_json, page_size: int = 100
    ) -> None:
        self.target = target
        self.runner = runner
        self.page_size = page_size
        project = urllib.parse.quote(target.project, safe="")
        self.base = f"projects/{project}/merge_requests/{target.number}"
        self.web_base = (
            f"https://{target.host}/{target.project}"
            f"/-/merge_requests/{target.number}"
        )

    def note_url(self, note_id: object) -> str:
        """The browser link to one note.

        Built rather than read: the discussions endpoint returns no `web_url` on
        MR notes, so trusting the field yields a linkless batch, which is half of
        what makes feedback actionable. GitHub's `html_url` is real, hence the
        asymmetry between the two providers here.
        """
        return f"{self.web_base}#note_{note_id}"

    def _get(self, endpoint: str) -> Json:
        return self.runner(["glab", "api", "--hostname", self.target.host, endpoint])

    def current_user(self) -> str:
        """The username `glab` is authenticated as."""
        return str(_dict(self._get("user")).get("username", ""))

    def review_author(self) -> str:
        """The username that opened the merge request."""
        return _nested_text(_dict(self._get(self.base)), "author", "username")

    def head_sha(self) -> str:
        """The commit the merge request currently points at."""
        return str(_dict(self._get(self.base)).get("sha", ""))

    def review_state(self) -> str:
        """Return the provider-neutral merge-request lifecycle state."""
        state = str(_dict(self._get(self.base)).get("state", ""))
        if state == "merged":
            return "merged"
        if state == "closed":
            return "closed"
        return "open"

    def events(self, current_user: str) -> list[Event]:
        """Every merge-request note, flagged for whether it replies to the user.

        GitLab MR notes carry no parent pointer, so position within a discussion
        is the only reply relationship the API offers: a note after one of the
        user's own continues a thread the user is in, a note before it does not.
        Standalone comments are each their own discussion (`individual_note`),
        so this cannot leak across unrelated threads.
        """
        discussions: list[dict[str, object]] = []
        page = 1
        while True:
            batch = _list(
                self._get(
                    f"{self.base}/discussions?per_page={self.page_size}&page={page}"
                )
            )
            discussions.extend(batch)
            if len(batch) < self.page_size:
                break
            page += 1

        events: list[Event] = []
        for discussion in discussions:
            notes = _list(discussion.get("notes", []))
            own_note_seen = False
            for note in notes:
                author = _nested_text(note, "author", "username")
                body = str(note.get("body", ""))
                system = bool(note.get("system", False))
                bot = bool(_nested(note, "author").get("bot", False))
                events.append(
                    Event(
                        id=f"gitlab-note:{note.get('id')}",
                        author=author,
                        body=body,
                        url=self.note_url(note.get("id")),
                        created_at=str(note.get("created_at", "")),
                        reply_to_user=own_note_seen and author != current_user,
                        human=not system and not bot,
                    )
                )
                own_note_seen = own_note_seen or author == current_user
        return events


class GitHubProvider:
    """Read pull-request metadata and feedback through gh."""

    def __init__(
        self, target: ReviewTarget, *, runner: Runner = run_json, page_size: int = 100
    ) -> None:
        self.target = target
        self.runner = runner
        self.page_size = page_size
        self.base = f"/repos/{target.project}"

    def _get(self, endpoint: str) -> Json:
        return self.runner(["gh", "api", "--hostname", self.target.host, endpoint])

    def current_user(self) -> str:
        """The login `gh` is authenticated as."""
        return str(_dict(self._get("/user")).get("login", ""))

    def review_author(self) -> str:
        """The login that opened the pull request."""
        pull = _dict(self._get(f"{self.base}/pulls/{self.target.number}"))
        return _nested_text(pull, "user", "login")

    def head_sha(self) -> str:
        """The commit the pull request currently points at."""
        pull = _dict(self._get(f"{self.base}/pulls/{self.target.number}"))
        return str(_nested(pull, "head").get("sha", ""))

    def review_state(self) -> str:
        """Return the provider-neutral pull-request lifecycle state."""
        pull = _dict(self._get(f"{self.base}/pulls/{self.target.number}"))
        if pull.get("merged_at") is not None:
            return "merged"
        if pull.get("state") == "closed":
            return "closed"
        return "open"

    def _pages(self, endpoint: str) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        page = 1
        while True:
            batch = _list(
                self._get(f"{endpoint}?per_page={self.page_size}&page={page}")
            )
            result.extend(batch)
            if len(batch) < self.page_size:
                return result
            page += 1

    @staticmethod
    def _human(item: dict[str, object]) -> bool:
        return _nested_text(item, "user", "type") == "User"

    def events(self, current_user: str) -> list[Event]:
        """Conversation comments, review comments, and reviews that have a body.

        Review comments carry `in_reply_to_id`, so a reply to the user is an
        exact relationship here rather than the positional guess GitLab needs.
        Reviews with an empty body are approvals and state changes with nothing
        to read, so they are dropped.
        """
        issue_comments = self._pages(
            f"{self.base}/issues/{self.target.number}/comments"
        )
        review_comments = self._pages(
            f"{self.base}/pulls/{self.target.number}/comments"
        )
        reviews = self._pages(f"{self.base}/pulls/{self.target.number}/reviews")
        own_review_comment_ids = {
            item.get("id")
            for item in review_comments
            if _nested_text(item, "user", "login") == current_user
        }
        events = [
            self._event(item, "github-issue-comment", "created_at")
            for item in issue_comments
        ]
        events.extend(
            self._event(
                item,
                "github-review-comment",
                "created_at",
                reply_to_user=item.get("in_reply_to_id") in own_review_comment_ids,
            )
            for item in review_comments
        )
        events.extend(
            self._event(item, "github-review", "submitted_at")
            for item in reviews
            if str(item.get("body", "")).strip()
        )
        return events

    def _event(
        self,
        item: dict[str, object],
        kind: str,
        timestamp_key: str,
        *,
        reply_to_user: bool = False,
    ) -> Event:
        return Event(
            id=f"{kind}:{item.get('id')}",
            author=_nested_text(item, "user", "login"),
            body=str(item.get("body", "")),
            url=str(item.get("html_url", "")),
            created_at=str(item.get(timestamp_key, "")),
            reply_to_user=reply_to_user,
            human=self._human(item),
        )


def is_relevant(
    event: Event, *, current_user: str, review_author: str, as_reviewer: bool = False
) -> bool:
    """Return whether feedback is actionable context for the current user.

    ``as_reviewer`` widens relevance to every other person's feedback, the same
    breadth the author gets. A principal reviewer owns threads they never posted
    in, because the review checklist makes them responsible for resolving them,
    so the default mention-or-reply filter hides exactly the work they must do.
    """
    if not event.human or event.author.casefold() == current_user.casefold():
        return False
    if as_reviewer or review_author.casefold() == current_user.casefold():
        return True
    # Both platforms read @name as a mention only at a word boundary, so the
    # guards on each side are what keep an email address whose domain or local
    # part contains the username from counting as one.
    mention = re.compile(
        rf"(?<![A-Za-z0-9])@{re.escape(current_user)}(?![A-Za-z0-9-])", re.IGNORECASE
    )
    return event.reply_to_user or bool(mention.search(event.body))


def head_event(sha: str) -> Event:
    """The current head commit as an Event, so a push reports like feedback.

    The author is not a person, so ``human`` stays true to keep it reportable
    while the id carries the sha: a new commit is a new id, and an unchanged
    head repeats an id already seen.
    """
    return Event(
        id=f"head:{sha}",
        author="(new commit)",
        body=f"head is now {sha[:12]}",
        url="",
        created_at="",
    )


def format_batch(events: list[Event]) -> str:
    """Render one compact notification for events discovered in one poll."""
    lines = [f"Review feedback ({len(events)})"]
    for item in sorted(events, key=lambda event: (event.created_at, event.id)):
        body = " ".join(item.body.split())
        lines.append(f"- {item.author}: {body}")
        # A harness may deliver each line as its own event and drop blank ones,
        # so an absent url must not become a whitespace-only line that vanishes.
        if item.url:
            lines.append(f"  {item.url}")
    return "\n".join(lines) + "\n"


# The injected output, sleep, and max_polls are what make one poll testable
# without a clock or a real stream; bundling them into a config object would be
# more machinery than the seam is worth.
def watch_snapshots(  # pylint: disable=too-many-arguments,too-many-locals
    fetch: Callable[[], list[Event]],
    *,
    current_user: str,
    review_author: str,
    interval: float,
    output: TextIO = sys.stdout,
    sleep: Callable[[float], None] = time.sleep,
    max_polls: int | None = None,
    as_reviewer: bool = False,
    fetch_state: Callable[[], str] | None = None,
    review_url: str = "",
) -> None:
    """Print new feedback until the review is merged or closed."""

    def report_terminal(state: str) -> bool:
        labels = {
            "merged": "Review merged",
            "closed": "Review closed without merge",
        }
        label = labels.get(state)
        if label is None:
            return False
        output.write(f"{label}\n{review_url}\n")
        output.flush()
        return True

    if fetch_state is not None and report_terminal(fetch_state()):
        return
    seen = {item.id for item in fetch()}
    polls = 0
    while max_polls is None or polls < max_polls:
        sleep(interval)
        if fetch_state is not None and report_terminal(fetch_state()):
            return
        snapshot = fetch()
        new_events = [item for item in snapshot if item.id not in seen]
        seen.update(item.id for item in snapshot)
        relevant = [
            item
            for item in new_events
            if is_relevant(
                item,
                current_user=current_user,
                review_author=review_author,
                as_reviewer=as_reviewer,
            )
        ]
        if relevant:
            output.write(format_batch(relevant))
            output.flush()
        polls += 1


def provider_for(target: ReviewTarget) -> GitLabProvider | GitHubProvider:
    """Build the matching provider adapter."""
    if target.provider == "gitlab":
        return GitLabProvider(target)
    return GitHubProvider(target)


def main(argv: list[str] | None = None) -> int:
    """Run the watcher until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_url")
    parser.add_argument("--interval", type=float, default=120)
    parser.add_argument(
        "--as-reviewer",
        action="store_true",
        help=(
            "report every other person's feedback and each new head commit, for "
            "a principal reviewer who owns threads they did not post in"
        ),
    )
    args = parser.parse_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    try:
        provider = provider_for(parse_review_url(args.review_url))
    except ValueError as error:
        parser.error(str(error))

    def identity() -> tuple[str, str]:
        current_user = provider.current_user()
        review_author = provider.review_author()
        if not current_user or not review_author:
            raise ValueError("provider returned an empty user identity")
        return current_user, review_author

    current_user, review_author = retrying(identity, interval=args.interval)()

    def fetch() -> list[Event]:
        events = provider.events(current_user)
        if not args.as_reviewer:
            return events
        # A push is review-relevant in its own right: the checklist requires
        # re-evaluating every checked box after a change, and forbids rewriting
        # history once review starts. Carried as an Event so one `seen` set
        # reports each commit once instead of on every poll.
        return events + [head_event(provider.head_sha())]

    watch_snapshots(
        retrying(fetch, interval=args.interval),
        current_user=current_user,
        review_author=review_author,
        interval=args.interval,
        as_reviewer=args.as_reviewer,
        fetch_state=retrying(provider.review_state, interval=args.interval),
        review_url=args.review_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
