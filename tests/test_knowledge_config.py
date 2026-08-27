"""Tests for composing the agent-knowledge bundle configuration.

The public file and the optional `_local` sibling are the same shape and are
merged add-only, exactly as plugins.yaml and plugins_local.yaml are.
"""

# The two files are the same shape, so the helpers stay module-private.
# pylint: disable=missing-function-docstring
# Asserting == [] documents "no bundles" better than a falsiness check.
# pylint: disable=use-implicit-booleaness-not-comparison

import pytest

from manage.knowledge import config


def _write(directory, name, text):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


PERSONAL = """\
version: 1
project_roots:
  - ~/projects
bundles:
  - id: personal
    name: Personal knowledge
    description: General references
    path: ~/knowledge/personal
    activate:
      always: true
"""

WORK = """\
version: 1
project_roots:
  - ~/work
bundles:
  - id: work
    name: Work knowledge
    description: Work references
    path: ~/knowledge/work
    activate:
      roots:
        - ~/work
"""


# --- absent and empty files ---------------------------------------------------


def test_an_absent_config_directory_yields_an_empty_configuration(tmp_path):
    loaded = config.load(tmp_path / "missing")

    assert loaded.bundles == []
    assert loaded.project_roots == []


def test_an_absent_local_file_is_not_an_error(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL)

    assert [b.id for b in config.load(tmp_path).bundles] == ["personal"]


def test_an_empty_file_is_valid(tmp_path):
    _write(tmp_path, "bundles.yaml", "# nothing declared\n")

    loaded = config.load(tmp_path)

    assert (loaded.bundles, loaded.project_roots) == ([], [])


def test_a_local_only_configuration_loads(tmp_path):
    _write(tmp_path, "bundles_local.yaml", WORK)

    assert [b.id for b in config.load(tmp_path).bundles] == ["work"]


# --- add-only composition -----------------------------------------------------


def test_public_bundles_precede_local_bundles(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL)
    _write(tmp_path, "bundles_local.yaml", WORK)

    assert [b.id for b in config.load(tmp_path).bundles] == ["personal", "work"]


def test_project_roots_from_both_files_are_appended(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL)
    _write(tmp_path, "bundles_local.yaml", WORK)

    roots = config.load(tmp_path).project_roots

    assert [p.name for p in roots] == ["projects", "work"]


def test_duplicate_project_roots_are_collapsed(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL)
    _write(tmp_path, "bundles_local.yaml", PERSONAL.replace("personal", "other"))

    assert len(config.load(tmp_path).project_roots) == 1


def test_a_duplicate_bundle_id_across_files_is_fatal(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL)
    _write(tmp_path, "bundles_local.yaml", PERSONAL)

    with pytest.raises(config.ConfigError, match="duplicate bundle id 'personal'"):
        config.load(tmp_path)


def test_the_reserved_project_id_cannot_be_declared(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL.replace("id: personal", "id: project"))

    with pytest.raises(config.ConfigError, match="reserved"):
        config.load(tmp_path)


# --- schema errors ------------------------------------------------------------


def test_an_unsupported_version_is_rejected(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL.replace("version: 1", "version: 2"))

    with pytest.raises(config.ConfigError, match="version"):
        config.load(tmp_path)


def test_an_unknown_top_level_key_is_rejected(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL + "extra: true\n")

    with pytest.raises(config.ConfigError, match="unknown key 'extra'"):
        config.load(tmp_path)


def test_an_unknown_bundle_key_is_rejected(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL + "    color: red\n")

    with pytest.raises(config.ConfigError, match="unknown key 'color'"):
        config.load(tmp_path)


def test_malformed_yaml_is_reported_as_a_config_error(tmp_path):
    _write(tmp_path, "bundles.yaml", "version: 1\nbundles: [oops\n")

    with pytest.raises(config.ConfigError):
        config.load(tmp_path)


def test_a_bundle_must_choose_exactly_one_activation_mode(tmp_path):
    both = PERSONAL.replace(
        "      always: true\n",
        "      always: true\n      roots:\n        - ~/elsewhere\n",
    )
    _write(tmp_path, "bundles.yaml", both)

    with pytest.raises(config.ConfigError, match="exactly one"):
        config.load(tmp_path)


def test_always_false_is_rejected_rather_than_treated_as_inactive(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL.replace("always: true", "always: false"))

    with pytest.raises(config.ConfigError, match="always"):
        config.load(tmp_path)


def test_an_empty_roots_list_is_rejected(tmp_path):
    empty = WORK.replace("      roots:\n        - ~/work\n", "      roots: []\n")
    _write(tmp_path, "bundles_local.yaml", empty)

    with pytest.raises(config.ConfigError, match="exactly one"):
        config.load(tmp_path)


def test_an_id_outside_the_allowed_syntax_is_rejected(tmp_path):
    _write(tmp_path, "bundles.yaml", PERSONAL.replace("id: personal", "id: Personal_1"))

    with pytest.raises(config.ConfigError, match="bundle id"):
        config.load(tmp_path)


def test_an_oversized_config_file_is_rejected(tmp_path):
    padding = "# " + "x" * config.MAX_CONFIG_BYTES + "\n"
    _write(tmp_path, "bundles.yaml", PERSONAL + padding)

    with pytest.raises(config.ConfigError, match="too large"):
        config.load(tmp_path)


# --- path expansion -----------------------------------------------------------


def test_home_and_environment_variables_expand_in_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    _write(
        tmp_path,
        "bundles.yaml",
        PERSONAL.replace("path: ~/knowledge/personal", "path: ${KB_ROOT}/personal"),
    )

    bundle = config.load(tmp_path).bundles[0]

    assert bundle.path == tmp_path / "kb" / "personal"
    assert config.load(tmp_path).project_roots[0] == tmp_path / "home" / "projects"


def test_an_unset_environment_variable_is_an_error(tmp_path):
    _write(
        tmp_path,
        "bundles.yaml",
        PERSONAL.replace("path: ~/knowledge/personal", "path: ${NOT_SET_ANYWHERE}/kb"),
    )

    with pytest.raises(config.ConfigError, match="NOT_SET_ANYWHERE"):
        config.load(tmp_path)


def test_a_relative_path_resolves_against_the_visible_config_directory(tmp_path):
    """The config files are stow symlinks, so resolution must not follow them
    into a repository checkout -- see the spec's stowed-symlink decision."""
    visible = tmp_path / "config"
    visible.mkdir()
    checkout = tmp_path / "repo"
    checkout.mkdir()
    real = checkout / "bundles.yaml"
    real.write_text(PERSONAL.replace("path: ~/knowledge/personal", "path: kb"), "utf-8")
    (visible / "bundles.yaml").symlink_to(real)

    assert config.load(visible).bundles[0].path == visible / "kb"


# --- the file this repo ships -------------------------------------------------


def test_the_committed_public_config_loads_and_declares_nothing():
    """The stowed bundles.yaml is a documented empty starting point: a public
    repo cannot name anyone's bundles, and an example entry would activate on a
    path that does not exist."""
    loaded = config.load("agents/.config/ai-knowledge")

    assert (loaded.bundles, loaded.project_roots) == ([], [])
