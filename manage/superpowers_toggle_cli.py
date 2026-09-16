"""Argument parsing for the `superpowers-toggle` command.

The command itself is a launcher in the `agents` stow package, so a harness's
shell tool or hook can invoke it by absolute path. Behaviour lives here, where
`inv lint` and the test suite reach it, matching manage.knowledge.cli's split.
"""

import argparse
import json
import sys

from manage import superpowers_toggle


def main(argv=None):
    """Run one operation and print its JSON payload. Exit code is always 0.

    Always 0: this is a preference flip, never a failed request, so a harness
    invoking it as a hook or command must not treat any outcome as an error.
    """
    parser = argparse.ArgumentParser(
        prog="superpowers-toggle", description=__doc__
    )
    parser.add_argument(
        "operation",
        choices=("on", "off", "toggle", "status"),
        help="enable, disable, flip, or report the bootstrap injection state",
    )
    parser.add_argument("--state-dir", help="override the state directory")
    args = parser.parse_args(argv)

    directory = superpowers_toggle.state_dir(args.state_dir)

    if args.operation == "status":
        enabled = superpowers_toggle.is_enabled(directory)
    elif args.operation == "on":
        superpowers_toggle.set_enabled(True, directory)
        enabled = True
    elif args.operation == "off":
        superpowers_toggle.set_enabled(False, directory)
        enabled = False
    else:  # toggle
        enabled = not superpowers_toggle.is_enabled(directory)
        superpowers_toggle.set_enabled(enabled, directory)

    json.dump({"enabled": enabled}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
