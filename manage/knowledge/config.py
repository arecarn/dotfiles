"""Compose the agent-knowledge configuration from its two files.

`config.yaml` is public and `config_local.yaml` is the optional private sibling
a dotfiles_local repo supplies -- the same arrangement as plugins.yaml and
plugins_local.yaml.

Neither file declares a bundle: a directory beside them is one, so a work
bundle's name and path never have to be written down anywhere. What is composed
here is the sections that tune the defaults, currently just `scopes`. New
sections go in the same way; the version is what a breaking change costs.

Composition is **add-only**. A local entry cannot redefine a public one, so a
duplicate is a fatal error rather than a silent override: a private file must
not be able to widen a scope a public one narrowed. Every other error is fatal
too, because a partially-loaded configuration could disclose private knowledge
somewhere it was meant to be kept out of.
"""

import dataclasses
import os
import pathlib
import re

# A harness hook runs under whatever `python3` it finds, not this repo's venv, so
# either YAML library is accepted and neither is required. Without one there is
# no knowledge rather than a broken session -- `_read` raises ConfigError, which
# the resolver already reports as a diagnostic.
try:  # pragma: no cover - exercised by whichever library is installed
    from ruamel.yaml import YAML as _YamlLoader
    from ruamel.yaml.error import YAMLError as _YamlError

    def _parse(text):
        return _YamlLoader(typ="safe").load(text)

except ImportError:  # pragma: no cover - same
    try:
        import yaml as _pyyaml

        _YamlError = _pyyaml.YAMLError

        def _parse(text):
            return _pyyaml.safe_load(text)

    except ImportError:

        class _YamlError(Exception):
            """Stands in for a parser error when no YAML library is installed."""

        def _parse(_text):
            raise _YamlError(
                "no YAML library available (install ruamel.yaml or PyYAML)"
            )

BASE_NAME = "config.yaml"
LOCAL_NAME = "config_local.yaml"

SCHEMA_VERSION = 1

# Reserved for the bundle discovered at the worktree root, so diagnostics and
# ordering can name it without colliding with a configured id.
PROJECT_ID = "project"

# Reserved for the bundle discovered at USER_DIR_NAME beside these files.
USER_ID = "user"

MAX_CONFIG_BYTES = 256 * 1024
MAX_BUNDLES = 256

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

_TOP_LEVEL_KEYS = frozenset({"version", "scopes"})
_SCOPE_KEYS = frozenset({"id", "activate"})


class ConfigError(Exception):
    """A configuration file is unusable, so no configured bundle is trusted."""


@dataclasses.dataclass(frozen=True, kw_only=True)
class Bundle:
    """One configured bundle: its identity, its root, and when it applies.

    `path` and `roots` are absolute but deliberately not resolved: activation
    canonicalises them at match time, when the filesystem is consulted.
    """

    id: str
    name: str
    description: str
    path: pathlib.Path
    always: bool
    roots: list


@dataclasses.dataclass(frozen=True, kw_only=True)
class Scope:
    """Where one discovered bundle applies, when the default is not wanted.

    The default is everywhere. A rule exists to narrow that, which is why
    `roots` empty and `always` true mean the same thing the default does.
    """

    always: bool
    roots: list


@dataclasses.dataclass(frozen=True, kw_only=True)
class Configuration:
    """Everything the config file says, by section.

    Bundles are not declared here -- a directory beside this file is a bundle,
    and a repository's `agents-knowledge/` is its own -- so a machine with no
    config file at all still has working knowledge. `scopes` only narrows: it
    says where an already-discovered bundle applies. Sections are added here as
    the file grows; a version bump is what a breaking change costs.
    """

    scopes: dict


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
        data = _parse(path.read_text(encoding="utf-8"))
    except (_YamlError, UnicodeDecodeError) as error:
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
    if expanded == "~" or expanded.startswith(("~/", "~\\")):
        # HOME is the cross-harness override; Windows normally has only
        # USERPROFILE, which Path.home() resolves when no override is present.
        home = os.environ.get("HOME") or str(pathlib.Path.home())
        expanded = home + expanded[1:]
    path = pathlib.Path(expanded)
    return path if path.is_absolute() else config_dir / path


def _scope(entry, config_dir, where):
    """Validate one scope rule, returning its bundle id and where it applies."""
    if not isinstance(entry, dict):
        raise ConfigError(f"{where}: each scope must be a mapping")
    unknown = set(entry) - _SCOPE_KEYS
    if unknown:
        raise ConfigError(f"{where}: unknown key {sorted(unknown)[0]!r}")

    bundle_id = entry.get("id")
    if not isinstance(bundle_id, str) or not _ID_PATTERN.match(bundle_id):
        raise ConfigError(f"{where}: bundle id must match {_ID_PATTERN.pattern}")
    if bundle_id == PROJECT_ID:
        raise ConfigError(f"{where}: bundle id {bundle_id!r} is reserved")

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

    return bundle_id, Scope(
        always=bool(always),
        roots=[
            _expand(root, config_dir, f"{where}: {bundle_id} root")
            for root in raw_roots
        ],
    )


@dataclasses.dataclass
class _Accumulator:
    """Composition state across the two files.

    A named holder rather than a tuple: adding a tracked value here should not
    require editing an unpack line at every call site to match.
    """

    scopes: dict = dataclasses.field(default_factory=dict)


def _merge(data, path, config_dir, acc):
    """Fold one parsed file into the accumulating configuration."""
    unknown = set(data) - _TOP_LEVEL_KEYS
    if unknown:
        key = sorted(unknown)[0]
        if key == "project_roots":
            # Named rather than reported as merely unknown: a file carrying it
            # was written against the allowlist that used to gate project
            # discovery, and silence would look like the setting still applied.
            raise ConfigError(
                f"{path}: project_roots is no longer configured -- a project's "
                "agents-knowledge/ is discovered wherever the repository "
                "commits one, so remove the key"
            )
        raise ConfigError(f"{path}: unknown key {key!r}")
    if data and data.get("version") != SCHEMA_VERSION:
        raise ConfigError(f"{path}: version must be {SCHEMA_VERSION}")

    raw_scopes = data.get("scopes") or []
    if not isinstance(raw_scopes, list):
        raise ConfigError(f"{path}: scopes must be a list")

    for entry in raw_scopes:
        bundle_id, scope = _scope(entry, config_dir, str(path))
        # A duplicate is fatal rather than last-wins: two rules for one bundle
        # leave its scope ambiguous, and a private file must not be able to
        # widen what a public one narrowed.
        if bundle_id in acc.scopes:
            raise ConfigError(f"{path}: duplicate scope for bundle {bundle_id!r}")
        acc.scopes[bundle_id] = scope
        if len(acc.scopes) > MAX_BUNDLES:
            raise ConfigError(f"{path}: more than {MAX_BUNDLES} scopes declared")


def load(config_dir):
    """The composed configuration for a config directory.

    Both files may be absent; a machine with no dotfiles_local, or no knowledge
    configured at all, is the normal case and yields an empty configuration.
    """
    config_dir = pathlib.Path(config_dir)
    acc = _Accumulator()
    for name in (BASE_NAME, LOCAL_NAME):
        path = config_dir / name
        data = _read(path)
        if data is not None:
            _merge(data, path, config_dir, acc)
    return Configuration(scopes=acc.scopes)
