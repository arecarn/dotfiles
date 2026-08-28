"""Tests for the review watcher: what it fetches, and what counts as relevant.

Every provider test substitutes the command runner, so nothing here reaches a
network or a real `glab`/`gh`.
"""

# Test names document each case, and the skill ships beside its script rather
# than as an installed package, so the import needs the path insert above it.
# pylint: disable=missing-function-docstring,wrong-import-position

from __future__ import annotations

import io
import subprocess
import sys
import urllib.parse
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

import watch_review


def _requested_endpoint(command: list[str]) -> str:
    """The API endpoint out of a provider CLI invocation.

    Relies on watch_review.api_command putting the endpoint last, which is
    what keeps `--hostname <host>` in front of it from being read as one.
    """
    return command[-1]


def event(
    event_id: str,
    *,
    author: str = "reviewer",
    body: str = "Please change this",
    reply_to_user: bool = False,
    human: bool = True,
) -> watch_review.Event:
    return watch_review.Event(
        id=event_id,
        author=author,
        body=body,
        url=f"https://example.test/comments/{event_id}",
        created_at=f"2026-08-27T00:00:{event_id[-1]}Z",
        reply_to_user=reply_to_user,
        human=human,
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://git.example.test/group/subgroup/project/-/merge_requests/42",
            ("gitlab", "git.example.test", "group/subgroup/project", 42),
        ),
        (
            "https://github.com/owner/repo/pull/17",
            ("github", "github.com", "owner/repo", 17),
        ),
    ],
)
def test_parse_review_url(url: str, expected: tuple[str, str, str, int]) -> None:
    target = watch_review.parse_review_url(url)
    assert (target.provider, target.host, target.project, target.number) == expected


def test_review_author_sees_all_other_human_feedback() -> None:
    candidate = event("note-1")
    assert watch_review.is_relevant(candidate, current_user="author", review_author="author")


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("Could you check this, @rcarney?", True),
        ("This is for @rcarney-other", False),
        ("Email rcarn@example.test", False),
        # An address ending in the username is not a mention of them: both
        # platforms read @name as a mention only at a word boundary.
        ("Ask bob@rcarney.example.test", False),
        ("(@rcarney) and mid-sentence @rcarney.", True),
    ],
)
def test_non_author_sees_only_exact_mentions(body: str, expected: bool) -> None:
    candidate = event("note-1", body=body)
    assert (
        watch_review.is_relevant(
            candidate, current_user="rcarney", review_author="someone-else"
        )
        is expected
    )


def test_non_author_sees_reply_to_own_comment() -> None:
    candidate = event("note-1", reply_to_user=True)
    assert watch_review.is_relevant(
        candidate, current_user="rcarney", review_author="someone-else"
    )


@pytest.mark.parametrize(
    "candidate",
    [event("note-1", author="rcarney"), event("note-2", human=False)],
)
def test_self_and_non_human_events_are_filtered(candidate: watch_review.Event) -> None:
    assert not watch_review.is_relevant(
        candidate, current_user="rcarney", review_author="rcarney"
    )


def test_poll_suppresses_baseline_and_is_silent_when_unchanged() -> None:
    snapshots = iter([[event("note-1")], [event("note-1")]])
    output = io.StringIO()

    watch_review.watch_snapshots(
        lambda: next(snapshots),
        current_user="author",
        review_author="author",
        interval=0,
        output=output,
        sleep=lambda _seconds: None,
        max_polls=1,
    )

    assert output.getvalue() == ""


def test_poll_emits_one_batch_for_new_relevant_events() -> None:
    snapshots = iter(
        [
            [event("note-1")],
            [event("note-1"), event("note-3", author="alice"), event("note-2", author="bob")],
        ]
    )
    output = io.StringIO()

    watch_review.watch_snapshots(
        lambda: next(snapshots),
        current_user="author",
        review_author="author",
        interval=0,
        output=output,
        sleep=lambda _seconds: None,
        max_polls=1,
    )

    rendered = output.getvalue()
    assert rendered.count("Review feedback (2)") == 1
    assert "- bob: Please change this\n  https://example.test/comments/note-2" in rendered
    assert "- alice: Please change this\n  https://example.test/comments/note-3" in rendered


def _requested_page(command: list[str]) -> int:
    """The page number the watcher asked for, parsed as a query rather than a substring.

    Splitting the endpoint on "page=" would match "per_page=" first.
    """
    query = urllib.parse.urlsplit(_requested_endpoint(command)).query
    return int(urllib.parse.parse_qs(query)["page"][0])


def _gitlab_note(note_id: int, author: str) -> dict[str, object]:
    # No web_url: the real discussions endpoint does not return one on MR notes.
    return {
        "id": note_id,
        "author": {"username": author},
        "body": "A note",
        "system": False,
        "created_at": f"2026-08-27T00:00:{note_id:02d}Z",
    }


def _gitlab_replies_to_user(notes: list[dict[str, object]]) -> list[bool]:
    target = watch_review.ReviewTarget("gitlab", "git.example", "group/project", 9)
    provider = watch_review.GitLabProvider(
        target, runner=lambda _command: [{"id": "thread-1", "notes": notes}]
    )
    return [item.reply_to_user for item in provider.events("rcarney")]


def test_gitlab_reply_detection_follows_position_within_the_thread() -> None:
    # GitLab MR notes carry no parent pointer, so position within the
    # discussion is the only relationship the API offers: a note after the
    # user's own continues a thread the user is in, one before it does not.
    assert _gitlab_replies_to_user(
        [
            _gitlab_note(10, "alice"),
            _gitlab_note(11, "rcarney"),
            _gitlab_note(12, "bob"),
        ]
    ) == [False, False, True]


def test_gitlab_thread_without_the_user_has_no_replies_to_them() -> None:
    assert _gitlab_replies_to_user(
        [_gitlab_note(10, "alice"), _gitlab_note(11, "bob")]
    ) == [False, False]


def test_transient_provider_failure_retries_without_resetting_the_baseline() -> None:
    snapshots: list[object] = [
        [event("note-1")],
        subprocess.CalledProcessError(1, ["glab", "api"]),
        [event("note-1"), event("note-2", author="alice")],
    ]

    def fetch() -> list[watch_review.Event]:
        item = snapshots.pop(0)
        if isinstance(item, Exception):
            raise item
        assert isinstance(item, list)
        return item

    slept: list[float] = []
    output = io.StringIO()

    watch_review.watch_snapshots(
        watch_review.retrying(fetch, interval=7, sleep=slept.append),
        current_user="author",
        review_author="author",
        interval=0,
        output=output,
        sleep=lambda _seconds: None,
        max_polls=1,
    )

    rendered = output.getvalue()
    assert slept == [7]
    assert "Review feedback (1)" in rendered
    assert "- alice:" in rendered
    # The baseline outlived the outage, so the pre-existing note stays silent.
    assert "note-1" not in rendered


def test_gitlab_normalizes_paginated_discussions_and_reply_relationships() -> None:
    calls: list[list[str]] = []

    def runner(command: list[str]) -> object:
        calls.append(command)
        if _requested_page(command) == 1:
            return [
                {
                    "id": "thread-1",
                    "notes": [
                        {
                            "id": 10,
                            "author": {"username": "rcarney"},
                            "body": "My question",
                            "system": False,
                            "created_at": "2026-08-27T00:00:00Z",
                        },
                        {
                            "id": 11,
                            "author": {"username": "alice"},
                            "body": "The answer",
                            "system": False,
                            "created_at": "2026-08-27T00:00:01Z",
                        },
                    ],
                }
            ]
        return []

    target = watch_review.ReviewTarget("gitlab", "git.example", "group/project", 9)
    events = watch_review.GitLabProvider(target, runner=runner, page_size=1).events(
        "rcarney"
    )

    assert [item.id for item in events] == ["gitlab-note:10", "gitlab-note:11"]
    assert events[1].reply_to_user
    assert len(calls) == 2
    assert all(command[:2] == ["glab", "api"] for command in calls)
    assert events[1].url == (
        "https://git.example/group/project/-/merge_requests/9#note_11"
    )


def test_as_reviewer_surfaces_feedback_that_neither_mentions_nor_replies() -> None:
    # A principal reviewer owns threads they never posted in, so the default
    # mention-or-reply filter would hide the work the checklist assigns them.
    unrelated = event("note-1", author="alice", body="A thread rcarney never joined")
    common = {"current_user": "rcarney", "review_author": "igaron"}

    assert not watch_review.is_relevant(unrelated, **common)
    assert watch_review.is_relevant(unrelated, **common, as_reviewer=True)


def test_as_reviewer_still_excludes_the_users_own_notes_and_bots() -> None:
    common = {"current_user": "rcarney", "review_author": "igaron", "as_reviewer": True}

    own = event("note-1", author="rcarney")
    bot = event("note-2", author="glsvc.bernie", human=False)
    assert not watch_review.is_relevant(own, **common)
    assert not watch_review.is_relevant(bot, **common)


def test_head_event_reports_each_commit_once() -> None:
    # The push matters to a reviewer because every checked box must be
    # re-evaluated after a change, but only when the head actually moves.
    heads = ["aaaaaaaaaaaa1111", "aaaaaaaaaaaa1111", "bbbbbbbbbbbb2222"]

    def fetch() -> list[watch_review.Event]:
        return [watch_review.head_event(heads.pop(0))]

    output = io.StringIO()
    watch_review.watch_snapshots(
        fetch,
        current_user="rcarney",
        review_author="igaron",
        interval=0,
        output=output,
        sleep=lambda _seconds: None,
        max_polls=2,
        as_reviewer=True,
    )

    rendered = output.getvalue()
    # The first poll repeats the baseline head, so only the second is news.
    assert rendered.count("Review feedback") == 1
    assert "head is now bbbbbbbbbbbb" in rendered
    assert "aaaaaaaaaaaa" not in rendered


def test_gitlab_head_sha_reads_the_merge_request_sha() -> None:
    target = watch_review.ReviewTarget("gitlab", "git.example", "group/project", 9)
    provider = watch_review.GitLabProvider(
        target, runner=lambda _command: {"sha": "cafebabe"}
    )
    assert provider.head_sha() == "cafebabe"


def test_github_head_sha_reads_the_nested_head_sha() -> None:
    target = watch_review.ReviewTarget("github", "github.example", "owner/repo", 7)
    provider = watch_review.GitHubProvider(
        target, runner=lambda _command: {"head": {"sha": "deadbeef"}}
    )
    assert provider.head_sha() == "deadbeef"


def test_batch_omits_the_url_line_when_an_event_has_none() -> None:
    # A harness that delivers each line as an event and drops blank ones would
    # otherwise swallow a bare "  " line, so no line beats an empty one.
    rendered = watch_review.format_batch(
        [
            watch_review.Event(
                id="note-1",
                author="alice",
                body="Please change this",
                url="",
                created_at="2026-08-27T00:00:01Z",
            )
        ]
    )

    assert rendered == "Review feedback (1)\n- alice: Please change this\n"


def test_github_normalizes_all_feedback_types_and_review_comment_replies() -> None:
    responses = {
        "/repos/owner/repo/issues/7/comments?per_page=100&page=1": [
            {
                "id": 1,
                "user": {"login": "alice", "type": "User"},
                "body": "Conversation",
                "created_at": "2026-08-27T00:00:01Z",
                "html_url": "https://github.example/i/1",
            }
        ],
        "/repos/owner/repo/pulls/7/comments?per_page=100&page=1": [
            {
                "id": 2,
                "user": {"login": "rcarney", "type": "User"},
                "body": "Why?",
                "created_at": "2026-08-27T00:00:02Z",
                "html_url": "https://github.example/r/2",
            },
            {
                "id": 3,
                "in_reply_to_id": 2,
                "user": {"login": "bob", "type": "User"},
                "body": "Because",
                "created_at": "2026-08-27T00:00:03Z",
                "html_url": "https://github.example/r/3",
            },
        ],
        "/repos/owner/repo/pulls/7/reviews?per_page=100&page=1": [
            {
                "id": 4,
                "user": {"login": "carol", "type": "User"},
                "body": "Review summary",
                "submitted_at": "2026-08-27T00:00:04Z",
                "html_url": "https://github.example/v/4",
            },
            {
                "id": 5,
                "user": {"login": "dan", "type": "User"},
                "body": "",
                "submitted_at": "2026-08-27T00:00:05Z",
                "html_url": "https://github.example/v/5",
            },
        ],
    }
    calls: list[list[str]] = []

    def runner(command: list[str]) -> object:
        calls.append(command)
        return responses[_requested_endpoint(command)]

    target = watch_review.ReviewTarget("github", "github.example", "owner/repo", 7)
    events = watch_review.GitHubProvider(target, runner=runner).events("rcarney")

    assert [item.id for item in events] == [
        "github-issue-comment:1",
        "github-review-comment:2",
        "github-review-comment:3",
        "github-review:4",
    ]
    assert events[2].reply_to_user
    assert all(command[:2] == ["gh", "api"] for command in calls)
