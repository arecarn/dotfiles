"""Tests for the default plugin commands derived from the manifest.

Every fixture is built inline. Nothing here reads ~/.config/ai-skills/plugins.yaml:
CI stows after it tests, so a test reading the stowed manifest passes only on a
machine that happens to be stowed.
"""

# Test names document each case, and these helpers are private to the module.
# pylint: disable=missing-function-docstring,protected-access

import tasks


def test_marketplace_name_is_the_part_after_the_at_sign():
    cmds = tasks._default_update_cmds(
        {"repo": "obra/superpowers", "plugin": "superpowers@superpowers-dev"}, "claude"
    )
    assert cmds[0] == "claude plugin marketplace update superpowers-dev"


def test_marketplace_name_falls_back_to_the_last_path_segment_of_the_repo():
    cmds = tasks._default_update_cmds(
        {"repo": "someone/their-marketplace", "plugin": "a-plugin"}, "claude"
    )
    assert cmds[0] == "claude plugin marketplace update their-marketplace"


def test_the_plugin_spec_is_passed_through_unchanged():
    cmds = tasks._default_update_cmds(
        {"repo": "obra/superpowers", "plugin": "superpowers@superpowers-dev"}, "claude"
    )
    assert cmds[1] == "claude plugin update superpowers@superpowers-dev"


def test_a_marketplace_name_needing_quoting_is_quoted():
    cmds = tasks._default_update_cmds(
        {"repo": "someone/repo", "plugin": "plugin@two words"}, "claude"
    )
    assert cmds[0] == "claude plugin marketplace update 'two words'"


def test_pi_derives_its_command_from_the_package_source():
    assert (
        tasks._default_update_cmds({"pi_package": "npm:pi-subagents"}, "pi")
        == "pi update npm:pi-subagents"
    )


def test_pi_needs_no_repo_or_plugin():
    assert tasks._default_update_cmds({"pi_package": "npm:x"}, "pi") is not None


def test_an_entry_without_the_fields_a_tool_needs_gets_no_command():
    assert tasks._default_update_cmds({"pi_package": "npm:x"}, "claude") is None
    assert tasks._default_update_cmds({"repo": "a/b", "plugin": "c"}, "pi") is None


def test_an_unknown_tool_gets_no_command():
    assert tasks._default_update_cmds({"repo": "a/b", "plugin": "c"}, "nope") is None
