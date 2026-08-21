"""Interpret the plugin manifest: what to run for a tool, and what to register.

The manifest at `~/.config/ai-skills/plugins.yaml` (merged with the private
`plugins_local.yaml` a dotfiles_local repo supplies) is a small language whose
defaulting rules are documented in that file's header comment. This module is
where those rules live in code, so the two can be checked against each other.

Everything here is pure apart from `load()`: a manifest goes in, command
strings come out. Running them is the task file's job.
"""

import functools
import pathlib
import shlex

from ruamel.yaml import YAML

AGENTS_DIR = pathlib.Path.home() / ".config" / "ai-skills"
BASE_NAME = "plugins.yaml"
LOCAL_NAME = "plugins_local.yaml"

_YAML = YAML()


def _as_commands(value):
    """Normalise a manifest command value -- a string or a list -- to a list."""
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def _default_install_cmds(entry, tool):
    """Install commands derived from an entry's `repo` and `plugin` fields.

    Returns [] when the entry lacks those fields or the tool has no derivable
    default. pi is deliberately absent: its packages are reconciled in bulk from
    the settings file `pi_packages()` feeds, not installed one command at a time
    (see ADR-0002).
    """
    if "repo" not in entry or "plugin" not in entry:
        return []
    repo = entry["repo"]
    plugin = entry["plugin"]
    if tool == "claude":
        return [
            f"claude plugin marketplace add {shlex.quote(repo)}",
            f"claude plugin install {shlex.quote(plugin)}",
        ]
    if tool == "opencode":
        return [
            f"npx --yes skills add {shlex.quote(repo)} --agent opencode --global --yes"
        ]
    return []


def _default_update_cmds(entry, tool):
    """Update commands derived from an entry's declared fields.

    Returns [] when the entry declares nothing the tool can act on.
    """
    if tool == "pi":
        source = entry.get("pi_package")
        return [f"pi update {shlex.quote(source)}"] if source else []
    if "repo" not in entry or "plugin" not in entry:
        return []
    repo = entry["repo"]
    plugin = entry["plugin"]
    # The marketplace name is the part after @ in the plugin spec
    # ("foo@bar" -> "bar"), falling back to the repo's last path segment.
    marketplace = plugin.split("@")[-1] if "@" in plugin else repo.split("/")[-1]
    if tool == "claude":
        return [
            f"claude plugin marketplace update {shlex.quote(marketplace)}",
            f"claude plugin update {shlex.quote(plugin)}",
        ]
    if tool == "opencode":
        return ["npx --yes skills update --global"]
    return []


_DEFAULTS = {"install": _default_install_cmds, "update": _default_update_cmds}


def entry_commands(entry, tool, action):
    """The commands to run for one manifest entry, for a tool and an action.

    `action` is "install" or "update". The precedence is the one the
    plugins.yaml header states: an explicit `install:`/`update:` key for the
    tool wins; otherwise the default is derived from the entry's fields;
    otherwise -- for update only -- the install commands are re-run. Returns []
    when the entry says nothing about this tool.
    """
    explicit = entry.get(action, {}).get(tool)
    if explicit is not None:
        return _as_commands(explicit)

    default = _DEFAULTS[action](entry, tool) if action in _DEFAULTS else []
    if default:
        return default

    if action == "update":
        return _as_commands(entry.get("install", {}).get(tool))
    return []


class Manifest:
    """A loaded plugin manifest, base and local already merged.

    Construct via `from_dir` (or `load()` for the real one). `entries` maps an
    entry name to its raw mapping; the methods below are the only intended
    readers of that shape.
    """

    def __init__(self, entries):
        self.entries = entries

    @classmethod
    def from_dir(cls, agents_dir):
        """Load and merge `plugins.yaml` and `plugins_local.yaml` from a directory.

        Either file may be absent. A local entry replaces a base entry of the
        same name outright; there is no per-key merge.
        """
        agents_dir = pathlib.Path(agents_dir)
        merged = {}
        for name in (BASE_NAME, LOCAL_NAME):
            path = agents_dir / name
            if path.exists():
                merged.update(_YAML.load(path) or {})
        return cls(merged)

    def commands(self, tool, action):
        """Every command to run for a tool and action, in manifest order."""
        cmds = []
        for entry in self.entries.values():
            cmds.extend(entry_commands(entry, tool, action))
        return cmds

    def mcp_servers(self):
        """MCP server definitions keyed by server name."""
        return {
            name: entry["mcp"]
            for name, entry in self.entries.items()
            if "mcp" in entry
        }

    def pi_packages(self):
        """Source specs of every declared pi package, in manifest order."""
        return [
            entry["pi_package"]
            for entry in self.entries.values()
            if "pi_package" in entry
        ]


@functools.lru_cache(maxsize=None)
def load():
    """The real manifest, read from disk at most once per process."""
    return Manifest.from_dir(AGENTS_DIR)
