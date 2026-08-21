"""Tests for the manifest rules documented in the plugins.yaml header comment.

Every fixture is built inline. Nothing here reads ~/.config/ai-skills/plugins.yaml:
CI stows after it tests, so a test reading the stowed manifest passes only on a
machine that happens to be stowed.
"""

# Test names document each case, and these helpers are private to the module.
# `== []` is deliberate: these assert an empty list, not merely a falsey value.
# pylint: disable=missing-function-docstring,protected-access
# pylint: disable=use-implicit-booleaness-not-comparison

from manage.agents import plugins


def _manifest(tmp_path, base, local=None):
    (tmp_path / plugins.BASE_NAME).write_text(base)
    if local is not None:
        (tmp_path / plugins.LOCAL_NAME).write_text(local)
    return plugins.Manifest.from_dir(tmp_path)


# --- derived update commands -------------------------------------------------


def test_marketplace_name_is_the_part_after_the_at_sign():
    cmds = plugins._default_update_cmds(
        {"repo": "obra/superpowers", "plugin": "superpowers@superpowers-dev"}, "claude"
    )
    assert cmds[0] == "claude plugin marketplace update superpowers-dev"


def test_marketplace_name_falls_back_to_the_last_path_segment_of_the_repo():
    cmds = plugins._default_update_cmds(
        {"repo": "someone/their-marketplace", "plugin": "a-plugin"}, "claude"
    )
    assert cmds[0] == "claude plugin marketplace update their-marketplace"


def test_the_plugin_spec_is_passed_through_unchanged():
    cmds = plugins._default_update_cmds(
        {"repo": "obra/superpowers", "plugin": "superpowers@superpowers-dev"}, "claude"
    )
    assert cmds[1] == "claude plugin update superpowers@superpowers-dev"


def test_a_marketplace_name_needing_quoting_is_quoted():
    cmds = plugins._default_update_cmds(
        {"repo": "someone/repo", "plugin": "plugin@two words"}, "claude"
    )
    assert cmds[0] == "claude plugin marketplace update 'two words'"


def test_pi_derives_its_command_from_the_package_source():
    assert plugins._default_update_cmds({"pi_package": "npm:pi-subagents"}, "pi") == [
        "pi update npm:pi-subagents"
    ]


def test_pi_needs_no_repo_or_plugin():
    assert plugins._default_update_cmds({"pi_package": "npm:x"}, "pi")


def test_an_entry_without_the_fields_a_tool_needs_gets_no_command():
    assert plugins._default_update_cmds({"pi_package": "npm:x"}, "claude") == []
    assert plugins._default_update_cmds({"repo": "a/b", "plugin": "c"}, "pi") == []


def test_an_unknown_tool_gets_no_command():
    assert plugins._default_update_cmds({"repo": "a/b", "plugin": "c"}, "nope") == []


# --- derived install commands ------------------------------------------------


def test_claude_install_adds_the_marketplace_then_installs_the_plugin():
    assert plugins._default_install_cmds(
        {"repo": "obra/superpowers", "plugin": "superpowers@superpowers-dev"}, "claude"
    ) == [
        "claude plugin marketplace add obra/superpowers",
        "claude plugin install superpowers@superpowers-dev",
    ]


def test_opencode_install_derives_from_the_repo_alone():
    assert plugins._default_install_cmds({"repo": "a/b", "plugin": "c"}, "opencode") == [
        "npx --yes skills add a/b --agent opencode --global --yes"
    ]


def test_pi_has_no_derived_install_because_packages_are_reconciled_in_bulk():
    assert plugins._default_install_cmds({"pi_package": "npm:x"}, "pi") == []


def test_an_install_default_needs_both_repo_and_plugin():
    assert plugins._default_install_cmds({"repo": "a/b"}, "claude") == []


# --- precedence --------------------------------------------------------------


def test_an_explicit_command_wins_over_the_derived_default():
    entry = {
        "repo": "a/b",
        "plugin": "c",
        "install": {"claude": "claude plugin install c@official"},
    }
    assert plugins.entry_commands(entry, "claude", "install") == [
        "claude plugin install c@official"
    ]


def test_an_explicit_command_may_be_a_list():
    entry = {"install": {"claude": ["one", "two"]}}
    assert plugins.entry_commands(entry, "claude", "install") == ["one", "two"]


def test_an_explicit_command_for_another_tool_is_ignored():
    entry = {"repo": "a/b", "plugin": "c", "install": {"opencode": "custom"}}
    assert plugins.entry_commands(entry, "claude", "install") == [
        "claude plugin marketplace add a/b",
        "claude plugin install c",
    ]


def test_update_falls_back_to_rerunning_install_when_nothing_else_applies():
    entry = {"install": {"claude": "claude plugin install x@official"}}
    assert plugins.entry_commands(entry, "claude", "update") == [
        "claude plugin install x@official"
    ]


def test_an_explicit_update_wins_over_the_install_fallback():
    entry = {
        "install": {"claude": "install-cmd"},
        "update": {"claude": "update-cmd"},
    }
    assert plugins.entry_commands(entry, "claude", "update") == ["update-cmd"]


def test_a_derived_update_wins_over_the_install_fallback():
    entry = {"repo": "a/b", "plugin": "c", "install": {"claude": "install-cmd"}}
    assert plugins.entry_commands(entry, "claude", "update")[0].startswith(
        "claude plugin marketplace update"
    )


def test_install_never_falls_back_to_anything():
    assert plugins.entry_commands({"update": {"claude": "u"}}, "claude", "install") == []


def test_an_entry_that_only_declares_an_mcp_server_yields_no_commands():
    entry = {"mcp": {"type": "http", "url": "https://example.test/"}}
    assert plugins.entry_commands(entry, "claude", "install") == []
    assert plugins.entry_commands(entry, "claude", "update") == []


# --- loading and merging -----------------------------------------------------


def test_a_local_entry_wins_over_a_base_entry_of_the_same_name(tmp_path):
    manifest = _manifest(
        tmp_path,
        base="thing:\n  repo: base/repo\n  plugin: p\n",
        local="thing:\n  repo: local/repo\n  plugin: p\n",
    )
    assert manifest.entries["thing"]["repo"] == "local/repo"


def test_a_local_entry_is_added_alongside_the_base_entries(tmp_path):
    manifest = _manifest(
        tmp_path,
        base="a:\n  repo: x/a\n  plugin: a\n",
        local="b:\n  repo: x/b\n  plugin: b\n",
    )
    assert set(manifest.entries) == {"a", "b"}


def test_an_absent_local_manifest_is_not_an_error(tmp_path):
    manifest = _manifest(tmp_path, base="a:\n  repo: x/a\n  plugin: a\n")
    assert set(manifest.entries) == {"a"}


def test_an_absent_base_manifest_is_not_an_error(tmp_path):
    assert plugins.Manifest.from_dir(tmp_path).entries == {}


def test_an_empty_manifest_file_is_not_an_error(tmp_path):
    assert _manifest(tmp_path, base="# just a comment\n").entries == {}


def test_commands_are_collected_across_entries_in_manifest_order(tmp_path):
    manifest = _manifest(
        tmp_path,
        base=(
            "first:\n  install:\n    claude: one\n"
            "second:\n  install:\n    claude: two\n"
        ),
    )
    assert manifest.commands("claude", "install") == ["one", "two"]


# --- the other two questions the manifest answers ----------------------------


def test_mcp_servers_are_keyed_by_entry_name(tmp_path):
    manifest = _manifest(
        tmp_path,
        base=(
            "ticktick:\n  mcp:\n    type: http\n    url: https://example.test/\n"
            "notaserver:\n  repo: a/b\n  plugin: c\n"
        ),
    )
    assert manifest.mcp_servers() == {
        "ticktick": {"type": "http", "url": "https://example.test/"}
    }


def test_pi_packages_are_listed_in_manifest_order(tmp_path):
    manifest = _manifest(
        tmp_path,
        base=(
            "a:\n  pi_package: npm:a\n"
            "b:\n  repo: x/y\n  plugin: z\n"
            "c:\n  pi_package: git:github.com/x/c\n"
        ),
    )
    assert manifest.pi_packages() == ["npm:a", "git:github.com/x/c"]


def test_a_local_manifest_can_add_a_pi_package(tmp_path):
    manifest = _manifest(
        tmp_path,
        base="a:\n  pi_package: npm:a\n",
        local="work:\n  pi_package: git:example.test/work\n",
    )
    assert manifest.pi_packages() == ["npm:a", "git:example.test/work"]


def test_the_real_manifest_is_read_only_once(monkeypatch, tmp_path):
    plugins.load.cache_clear()
    monkeypatch.setattr(plugins, "AGENTS_DIR", tmp_path)
    (tmp_path / plugins.BASE_NAME).write_text("a:\n  repo: x/a\n  plugin: a\n")

    calls = []
    real_from_dir = plugins.Manifest.from_dir

    def counting_from_dir(agents_dir):
        calls.append(agents_dir)
        return real_from_dir(agents_dir)

    monkeypatch.setattr(plugins.Manifest, "from_dir", counting_from_dir)
    try:
        assert plugins.load() is plugins.load()
        assert len(calls) == 1
    finally:
        plugins.load.cache_clear()
