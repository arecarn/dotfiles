"""Argument parsing and JSON output for the `agent-knowledge` command.

The command itself is a launcher in the `scripts` stow package, so a harness
hook can invoke it by absolute path. Everything with behaviour lives
here instead, where `inv lint` and the test suite reach it.

There is no separate `reload`: the resolver holds no state, so `resolve` *is* the
recompute. An adapter that caches a catalog reloads by calling `resolve` again.

Exit codes are for the caller's control flow, not shell convention:

- 0  a usable answer, including "no bundles apply" and "configuration is broken"
- 1  the request was valid but refused (see the `error` code in the payload)
- 2  the invocation itself was wrong

A malformed config file must NOT fail the harness that called us, so it exits 0
with a diagnostic. stdout carries exactly one JSON object; stderr is for our own
failures only.
"""

import argparse
import json
import os
import pathlib
import sys

from manage.knowledge import resolver

# Overridable so a test, or a harness with its own config location, does not have
# to depend on the caller's real XDG environment.
CONFIG_DIR_ENV = "AGENT_KNOWLEDGE_CONFIG_DIR"


def resolve_config_dir(explicit):
    """The config directory: the flag, then the env var, then the XDG default."""
    if explicit:
        return pathlib.Path(explicit)
    from_env = os.environ.get(CONFIG_DIR_ENV)
    if from_env:
        return pathlib.Path(from_env)
    xdg = os.environ.get("XDG_CONFIG_HOME") or (pathlib.Path.home() / ".config")
    return pathlib.Path(xdg) / "ai-knowledge"


def _diagnostics(diagnostics):
    return [
        {
            "code": d.code,
            "bundle_id": d.bundle_id,
            "message": d.message,
        }
        for d in diagnostics
    ]


def _resolve(config_dir, cwd, with_project=True):
    result = resolver.resolve(config_dir=config_dir, cwd=cwd, with_project=with_project)
    return 0, {
        "operation": "resolve",
        "catalog": result.catalog,
        "bundles": [
            {"id": b.id, "name": b.name, "description": b.description}
            for b in result.bundles
        ],
        "diagnostics": _diagnostics(result.diagnostics),
    }


def _read(config_dir, cwd, args):
    result = resolver.read(
        config_dir=config_dir,
        cwd=cwd,
        bundle_id=args.bundle,
        target=args.target,
        source=args.source,
    )
    payload = {
        "operation": "read",
        "bundle_id": result.bundle_id,
        "path": result.path,
        "content": result.content,
        "fragment": result.fragment,
        "error": result.error,
    }
    # Refusals are a normal outcome of an agent following a link, so they are
    # reported in the payload; the exit code is what lets a wrapper branch.
    return (1 if result.error else 0), payload


def _status(config_dir, cwd):
    payload = resolver.status(config_dir=config_dir, cwd=cwd)
    payload["operation"] = "status"
    return 0, payload


def _check(config_dir, cwd, path):
    """Structural problems in the bundles that apply here, or in one directory.

    Local-only, like `status`: problems name bundle paths, so an adapter must
    keep this out of model context. Exits non-zero when anything is wrong, so a
    `dotfiles_local` checkout can run it from its own CI without parsing JSON.
    """
    from manage.knowledge import bundles  # pylint: disable=import-outside-toplevel

    if path:
        roots = [pathlib.Path(path)]
    else:
        payload = resolver.status(config_dir=config_dir, cwd=cwd)
        roots = [
            pathlib.Path(bundle["path"])
            for bundle in payload["bundles"]
            if bundle["active"]
        ]

    problems = bundles.check_roots(roots)
    return (1 if problems else 0), {
        "operation": "check",
        "checked": [str(root) for root in roots],
        "problems": problems,
    }


def main(argv=None):
    """Run one operation and print its JSON payload."""
    parser = argparse.ArgumentParser(prog="agent-knowledge", description=__doc__)
    parser.add_argument(
        "operation",
        choices=("resolve", "read", "status", "check"),
        help=(
            "resolve the catalog, read one document, report local status, or "
            "check bundle structure"
        ),
    )
    parser.add_argument("--config-dir", help="override the config directory")
    parser.add_argument(
        "--no-project",
        action="store_true",
        help="withhold the discovered project bundle (resolve)",
    )
    parser.add_argument("--cwd", help="directory to resolve for (default: current)")
    parser.add_argument("--bundle", help="bundle id (read)")
    parser.add_argument(
        "--path", help="bundle directory to check instead of the active ones (check)"
    )
    parser.add_argument("--target", help="link target to read (read)")
    parser.add_argument(
        "--source",
        default="index.md",
        help="document the link came from, for relative targets (read)",
    )
    args = parser.parse_args(argv)

    directory = resolve_config_dir(args.config_dir)
    cwd = pathlib.Path(args.cwd) if args.cwd else pathlib.Path.cwd()

    if args.operation == "read":
        if not args.bundle or not args.target:
            parser.error("read requires --bundle and --target")
        code, payload = _read(directory, cwd, args)
    elif args.operation == "status":
        code, payload = _status(directory, cwd)
    elif args.operation == "check":
        code, payload = _check(directory, cwd, args.path)
    else:
        code, payload = _resolve(directory, cwd, not args.no_project)

    payload["protocol_version"] = 1
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return code
