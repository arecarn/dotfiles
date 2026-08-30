"""Tests for composing the agent-knowledge configuration file.

The file declares no bundles -- a directory beside it is one, and discovery is
covered in test_knowledge_activation. What is composed here is `scopes`, the
optional narrowing rules. The public file and its optional `_local` sibling are
the same shape and merge add-only, exactly as plugins.yaml does.
"""

# The two files are the same shape, so the helpers stay module-private.
# pylint: disable=missing-function-docstring
# Asserting == {} documents "no rules" better than a falsiness check.
# pylint: disable=use-implicit-booleaness-not-comparison
# The parser seam is module-private on purpose; a test may reach it.
# pylint: disable=protected-access


import pytest

from manage.knowledge import config


def _write(directory, name, text):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


PERSONAL = """\
version: 1
scopes:
  - id: personal
    activate:
      always: true
"""

WORK = """\
version: 1
scopes:
  - id: work
    activate:
      roots:
        - ~/work
"""


def test_an_absent_config_directory_yields_an_empty_configuration(tmp_path):
    assert config.load(tmp_path / "missing").scopes == {}


def test_an_absent_local_file_is_not_an_error(tmp_path):
    _write(tmp_path, "config.yaml", PERSONAL)

    assert list(config.load(tmp_path).scopes) == ["personal"]


def test_an_empty_file_is_valid(tmp_path):
    _write(tmp_path, "config.yaml", "# nothing configured\n")

    assert config.load(tmp_path).scopes == {}


def test_a_local_only_configuration_loads(tmp_path):
    _write(tmp_path, "config_local.yaml", WORK)

    assert list(config.load(tmp_path).scopes) == ["work"]


def test_rules_from_both_files_are_merged(tmp_path):
    _write(tmp_path, "config.yaml", PERSONAL)
    _write(tmp_path, "config_local.yaml", WORK)

    assert sorted(config.load(tmp_path).scopes) == ["personal", "work"]


def test_a_duplicate_scope_across_files_is_fatal(tmp_path):
    """Add-only: a private file must not be able to widen what a public one
    narrowed, so a second rule for one bundle is an error, not an override."""
    _write(tmp_path, "config.yaml", WORK)
    _write(tmp_path, "config_local.yaml", WORK)

    with pytest.raises(config.ConfigError, match="duplicate scope"):
        config.load(tmp_path)


def test_the_reserved_project_id_cannot_be_scoped(tmp_path):
    """The project bundle is discovered from the worktree, so a rule naming it
    would describe something this file does not control."""
    _write(tmp_path, "config.yaml", PERSONAL.replace("personal", "project"))

    with pytest.raises(config.ConfigError, match="reserved"):
        config.load(tmp_path)


def test_an_unsupported_version_is_rejected(tmp_path):
    _write(tmp_path, "config.yaml", PERSONAL.replace("version: 1", "version: 2"))

    with pytest.raises(config.ConfigError, match="version must be 1"):
        config.load(tmp_path)


def test_an_unknown_top_level_key_is_rejected(tmp_path):
    _write(tmp_path, "config.yaml", "version: 1\nbundles: []\n")

    with pytest.raises(config.ConfigError, match="unknown key 'bundles'"):
        config.load(tmp_path)


def test_an_unknown_scope_key_is_rejected(tmp_path):
    _write(tmp_path, "config.yaml", PERSONAL.replace(
        "    activate:", "    path: /kb\n    activate:"
    ))

    with pytest.raises(config.ConfigError, match="unknown key 'path'"):
        config.load(tmp_path)


def test_a_leftover_project_roots_key_says_it_is_gone(tmp_path):
    """A file written against the old allowlist must not load as if the setting
    still applied, and "unknown key" would not tell its author what changed."""
    _write(tmp_path, "config.yaml", "version: 1\nproject_roots:\n  - ~/projects\n")

    with pytest.raises(config.ConfigError, match="project_roots is no longer"):
        config.load(tmp_path)


def test_scopes_must_be_a_list(tmp_path):
    _write(tmp_path, "config.yaml", "version: 1\nscopes: work\n")

    with pytest.raises(config.ConfigError, match="scopes must be a list"):
        config.load(tmp_path)


def test_malformed_yaml_is_reported_as_a_config_error(tmp_path):
    _write(tmp_path, "config.yaml", "version: 1\nscopes: [unclosed\n")

    with pytest.raises(config.ConfigError):
        config.load(tmp_path)


def test_a_scope_must_choose_exactly_one_activation_mode(tmp_path):
    """"always plus roots" and "neither" both leave the scope ambiguous, so
    neither is guessed at."""
    both = PERSONAL.replace(
        "      always: true", "      always: true\n      roots:\n        - ~/work"
    )
    _write(tmp_path, "config.yaml", both)

    with pytest.raises(config.ConfigError, match="exactly one"):
        config.load(tmp_path)


def test_always_false_is_rejected_rather_than_treated_as_inactive(tmp_path):
    """`always: false` reads as "off", which this file cannot express: a bundle
    is removed by removing its directory."""
    _write(tmp_path, "config.yaml", PERSONAL.replace("always: true", "always: false"))

    with pytest.raises(config.ConfigError, match="always must be true"):
        config.load(tmp_path)


def test_an_empty_roots_list_is_rejected(tmp_path):
    _write(tmp_path, "config.yaml", WORK.replace("        - ~/work\n", ""))

    with pytest.raises(config.ConfigError, match="exactly one"):
        config.load(tmp_path)


def test_an_id_outside_the_allowed_syntax_is_rejected(tmp_path):
    _write(tmp_path, "config.yaml", PERSONAL.replace("id: personal", "id: Personal"))

    with pytest.raises(config.ConfigError, match="bundle id must match"):
        config.load(tmp_path)


def test_an_oversized_config_file_is_rejected(tmp_path):
    """Capped before parsing, so a huge file is refused rather than parsed."""
    _write(
        tmp_path,
        "config.yaml",
        PERSONAL + "# padding\n" * config.MAX_CONFIG_BYTES,
    )

    with pytest.raises(config.ConfigError, match="too large"):
        config.load(tmp_path)


def test_tilde_and_environment_variables_expand_in_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("WORK_ROOT", str(tmp_path / "elsewhere"))
    _write(tmp_path, "config.yaml", WORK)
    _write(
        tmp_path,
        "config_local.yaml",
        WORK.replace("id: work", "id: other").replace("~/work", "${WORK_ROOT}"),
    )

    scopes = config.load(tmp_path).scopes

    assert scopes["work"].roots == [tmp_path / "home" / "work"]
    assert scopes["other"].roots == [tmp_path / "elsewhere"]


def test_tilde_uses_the_platform_home_when_home_is_unset(tmp_path, monkeypatch):
    """WindowsPath.home() follows USERPROFILE instead of HOME, so a stowed path
    keeps one meaning across harnesses."""
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.setattr(config.pathlib.Path, "home", lambda: tmp_path / "platform-home")
    _write(tmp_path, "config.yaml", WORK)

    roots = config.load(tmp_path).scopes["work"].roots

    assert roots == [tmp_path / "platform-home" / "work"]


def test_an_unset_environment_variable_is_an_error(tmp_path):
    """Silently expanding to "" would point a root at the filesystem root."""
    _write(tmp_path, "config.yaml", WORK.replace("~/work", "${NOT_SET_ANYWHERE}"))

    with pytest.raises(config.ConfigError, match="NOT_SET_ANYWHERE"):
        config.load(tmp_path)


def test_a_relative_root_resolves_against_the_visible_config_directory(tmp_path):
    """The config files are stow symlinks, so resolution must not follow them
    into a repository checkout -- see the spec's stowed-symlink decision."""
    visible = tmp_path / "config"
    visible.mkdir()
    checkout = tmp_path / "repo"
    checkout.mkdir()
    real = checkout / "config.yaml"
    real.write_text(WORK.replace("~/work", "trees"), encoding="utf-8")
    (visible / "config.yaml").symlink_to(real)

    assert config.load(visible).scopes["work"].roots == [visible / "trees"]


# --- the file this repo ships -------------------------------------------------


def test_the_committed_public_config_configures_nothing():
    """The stowed config.yaml is a documented empty starting point, and stays
    that way: knowledge works without it, because bundles are discovered rather
    than declared and everything applies everywhere until a rule narrows it."""
    assert config.load("agents/.config/ai-knowledge").scopes == {}


def test_a_missing_yaml_library_is_a_config_error_not_a_crash(tmp_path, monkeypatch):
    """A hook running under a bare python3 must degrade to "no knowledge", not
    take the session down."""
    _write(tmp_path, "config.yaml", PERSONAL)
    monkeypatch.setattr(
        config, "_parse", lambda _text: (_ for _ in ()).throw(config._YamlError("none"))
    )

    with pytest.raises(config.ConfigError):
        config.load(tmp_path)
