"""Writing this repo's declarations into each harness's own settings file.

Distinct from stowing: these files belong to the harness, which writes its own
preferences and runtime state into them. Only the keys named here are ours, and
everything else in the file survives untouched. That mixed ownership is why the
files are edited in place rather than stowed from the repo -- and why keeping
the declarations in the manifest is what lets a dotfiles_local repo add a
private one without it landing in this public repo.
"""

import json
import pathlib

from manage.agents import plugins

_CLAUDE_SETTINGS = pathlib.PurePath(".claude/settings.json")
_PI_SETTINGS = pathlib.PurePath(".pi/agent/settings.json")


def _home(home):
    return pathlib.Path.home() if home is None else pathlib.Path(home)


def setup_claude(home=None):
    """Merge this repo's Claude Code preferences into ~/.claude/settings.json.

    An absent file is left absent: Claude Code creates it on first run, and a
    stub written before that would be a config file it never asked for.
    """
    path = _home(home) / _CLAUDE_SETTINGS
    if not path.exists():
        return

    settings = json.loads(path.read_text())
    settings["voiceEnabled"] = True
    # Selects claude-code/.claude/output-styles/concise.md, generated from the
    # prose-style fragment. Deleting the key here would leave Claude's own
    # brevity instructions in force, which the fragment is meant to replace.
    settings["outputStyle"] = "Concise"
    settings.setdefault("permissions", {})
    settings["permissions"]["defaultMode"] = "bypassPermissions"
    settings["skipDangerousModePermissionPrompt"] = True
    path.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"Updated {path}")


def setup_pi(home=None):
    """Declare the manifest's pi packages in pi's own settings file.

    `packages` belongs to the manifest, so dropping a declaration there drops
    the package here. Every other key is pi's own -- theme, provider and model
    defaults, changelog state -- and is preserved.

    Unlike the MCP config Claude Code owns, an absent file is created rather
    than left alone: this file is what `pi update --extensions` reconciles
    against, so skipping it on a machine that has never run pi would mean no
    package is ever installed.
    """
    packages = plugins.load().pi_packages()
    if not packages:
        return

    path = _home(home) / _PI_SETTINGS
    # A machine that stowed the settings.json this repo used to commit still has
    # a symlink to a path the repo no longer has. Writing through it would
    # recreate the file inside the working tree, which is what moving the
    # declaration here removes. inv clean-stow prunes the dead link eventually;
    # this must not depend on that having run first.
    if path.is_symlink():
        path.unlink()

    settings = json.loads(path.read_text()) if path.exists() else {}
    settings["packages"] = packages
    settings["enableSkillCommands"] = True
    settings["quietStartup"] = True

    content = json.dumps(settings, indent=2) + "\n"
    if path.exists() and path.read_text() == content:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Declared {len(packages)} pi packages in {path}")
