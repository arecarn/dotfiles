"""Compose the agent-knowledge bundle configuration from its two files.

`bundles.yaml` is public and `bundles_local.yaml` is the optional private
sibling a dotfiles_local repo supplies -- the same arrangement as plugins.yaml
and plugins_local.yaml, for the same reason: work bundle names and paths must
never land in the public repo.

Composition is **add-only**. A local entry cannot redefine a public one, so a
duplicate id is a fatal error rather than a silent override; a private file must
not be able to change what a public bundle means. Every other error is fatal
too, because a partially-loaded configuration could activate the wrong private
knowledge.
"""

import os
import pathlib
import re

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

BASE_NAME = "bundles.yaml"
LOCAL_NAME = "bundles_local.yaml"

SCHEMA_VERSION = 1

# Reserved for the bundle discovered at the worktree root, so diagnostics and
# ordering can name it without colliding with a configured id.
PROJECT_ID = "project"

MAX_CONFIG_BYTES = 256 * 1024
MAX_BUNDLES = 256

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

_TOP_LEVEL_KEYS = frozenset({"version", "project_roots", "bundles"})
_BUNDLE_KEYS = frozenset({"id", "name", "description", "path", "activate"})

_YAML = YAML(typ="safe")


class ConfigError(Exception):
    """A configuration file is unusable, so no configured bundle is trusted."""


class Bundle:
    """One configured bundle: its identity, its root, and when it applies.

    `path` and `roots` are absolute but deliberately not resolved: activation
    canonicalises them at match time, when the filesystem is consulted.
    """

    def __init__(self, id, name, description, path, always, roots):
        self.id = id
        self.name = name
        self.description = description
        self.path = path
        self.always = always
        self.roots = roots

    def __repr__(self):
        return f"Bundle(id={self.id!r}, path={str(self.path)!r})"


class Configuration:
    """The composed configuration: bundles in source order, plus project roots.

    `project_roots` gates project auto-discovery. An empty list disables it
    entirely -- entering an unrelated checkout must not expose whatever
    `agents-knowledge/` it happens to contain.
    """

    def __init__(self, bundles, project_roots):
        self.bundles = bundles
        self.project_roots = project_roots


def _read(path):
    """Parse one config file, or return None when it is absent.

    The size cap is applied before parsing: an oversized file is rejected rather
    than handed to the YAML parser.
    """
    if not path.exists():
        return None
    if path.stat().st_size > MAX_CONFIG_BYTES:
        raise ConfigError(f"{path}: too large (limit {MAX_CONFIG_BYTES} bytes)")
    try:
        data = _YAML.load(path.read_text(encoding="utf-8"))
    except (YAMLError, UnicodeDecodeError) as error:
        raise ConfigError(f"{path}: {error}") from error
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return data


def _expand(value, config_dir, where):
    """Expand ~ and ${VAR} in a path value, then anchor it to `config_dir`.

    Relative paths resolve against the *visible* config directory rather than a
    symlink's target: both files are stowed symlinks, so following them would
    bind bundle paths to whichever checkout provided the file.
    """
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{where}: path must be a non-empty string")

    def substitute(match):
        name = match.group(1)
        try:
            return os.environ[name]
        except KeyError:
            raise ConfigError(f"{where}: ${{{name}}} is not set") from None

    expanded = _ENV_PATTERN.sub(substitute, value)
    if "$" in expanded:
        raise ConfigError(f"{where}: only ${{VAR}} references are supported")
    path = pathlib.Path(expanded).expanduser()
    return path if path.is_absolute() else config_dir / path


def _bundle(entry, config_dir, where):
    """Validate one bundle mapping and expand its paths."""
    if not isinstance(entry, dict):
        raise ConfigError(f"{where}: each bundle must be a mapping")
    unknown = set(entry) - _BUNDLE_KEYS
    if unknown:
        raise ConfigError(f"{where}: unknown key {sorted(unknown)[0]!r}")

    bundle_id = entry.get("id")
    if not isinstance(bundle_id, str) or not _ID_PATTERN.match(bundle_id):
        raise ConfigError(f"{where}: bundle id must match {_ID_PATTERN.pattern}")
    if bundle_id == PROJECT_ID:
        raise ConfigError(f"{where}: bundle id {PROJECT_ID!r} is reserved")

    activate = entry.get("activate")
    if not isinstance(activate, dict):
        raise ConfigError(f"{where}: {bundle_id} needs an activate mapping")
    unknown = set(activate) - {"always", "roots"}
    if unknown:
        raise ConfigError(f"{where}: unknown key {sorted(unknown)[0]!r}")

    always = activate.get("always")
    if always is not None and always is not True:
        raise ConfigError(f"{where}: {bundle_id} always must be true when present")
    raw_roots = activate.get("roots") or []
    if not isinstance(raw_roots, list):
        raise ConfigError(f"{where}: {bundle_id} roots must be a list")
    # One mode only: "always plus roots" and "neither" both leave the intended
    # scope ambiguous, so neither is guessed at.
    if bool(always) == bool(raw_roots):
        raise ConfigError(f"{where}: {bundle_id} needs exactly one of always, roots")

    return Bundle(
        id=bundle_id,
        name=entry.get("name") or bundle_id,
        description=entry.get("description") or "",
        path=_expand(entry.get("path"), config_dir, f"{where}: {bundle_id} path"),
        always=bool(always),
        roots=[
            _expand(root, config_dir, f"{where}: {bundle_id} root")
            for root in raw_roots
        ],
    )


def _merge(data, path, config_dir, bundles, roots, seen_ids, seen_roots):
    """Fold one parsed file into the accumulating configuration."""
    unknown = set(data) - _TOP_LEVEL_KEYS
    if unknown:
        raise ConfigError(f"{path}: unknown key {sorted(unknown)[0]!r}")
    if data and data.get("version") != SCHEMA_VERSION:
        raise ConfigError(f"{path}: version must be {SCHEMA_VERSION}")

    for root in data.get("project_roots") or []:
        expanded = _expand(root, config_dir, f"{path}: project_roots")
        # Equivalent roots collapse to the first declaration, so a local file
        # repeating a public root does not change matching or ordering.
        key = os.path.normcase(str(expanded))
        if key not in seen_roots:
            seen_roots.add(key)
            roots.append(expanded)

    for entry in data.get("bundles") or []:
        bundle = _bundle(entry, config_dir, str(path))
        if bundle.id in seen_ids:
            raise ConfigError(f"{path}: duplicate bundle id {bundle.id!r}")
        seen_ids.add(bundle.id)
        bundles.append(bundle)
        if len(bundles) > MAX_BUNDLES:
            raise ConfigError(f"{path}: more than {MAX_BUNDLES} bundles declared")


def load(config_dir):
    """The composed configuration for a config directory.

    Both files may be absent; a machine with no dotfiles_local, or no knowledge
    configured at all, is the normal case and yields an empty configuration.
    """
    config_dir = pathlib.Path(config_dir)
    bundles, roots = [], []
    seen_ids, seen_roots = set(), set()
    for name in (BASE_NAME, LOCAL_NAME):
        path = config_dir / name
        data = _read(path)
        if data is not None:
            _merge(data, path, config_dir, bundles, roots, seen_ids, seen_roots)
    return Configuration(bundles, roots)
