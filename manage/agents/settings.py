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
_PI_LOCAL_SETTINGS = pathlib.PurePath(
    ".config/ai-skills/pi-settings.local.json"
)


def _home(home):
    return pathlib.Path.home() if home is None else pathlib.Path(home)


def setup_claude(home=None):
    """Merge this repo's Claude Code preferences into ~/.claude/settings.json.

    The file is created when absent rather than skipped. Claude Code writes it
    on first run, so skipping meant provisioning a fresh machine applied none of
    these settings and said nothing about it -- and a fresh machine is exactly
    when they are wanted. Claude Code merges its own defaults into whatever it
    finds, so a file holding only these keys is not a problem for it.

    Relies on ~/.claude being a real directory, which manage.stow guarantees by
    pre-creating it: unstowed, it folds into a symlink into this repo and the
    file written here would land in the working tree.
    """
    path = _home(home) / _CLAUDE_SETTINGS
    settings = json.loads(path.read_text()) if path.exists() else {}
    settings["voiceEnabled"] = True
    # Selects claude-code/.claude/output-styles/concise.md, generated from the
    # prose-style fragment. Deleting the key here would leave Claude's own
    # brevity instructions in force, which the fragment is meant to replace.
    settings["outputStyle"] = "Concise"
    settings.setdefault("permissions", {})
    settings["permissions"]["defaultMode"] = "bypassPermissions"
    settings["skipDangerousModePermissionPrompt"] = True

    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"{'Updated' if existed else 'Created'} {path}")


def setup_pi(home=None, local_settings_path=None):
    """Merge declared packages and optional private preferences into pi settings.

    `packages` belongs to the manifest, so dropping a declaration there drops
    the package here. Keys in `pi-settings.local.json` are private declarations
    layered over Pi's existing settings. Every other key is Pi's own and is
    preserved.

    An absent file is created rather than skipped: this file is what
    `pi update --extensions` reconciles against, so skipping it on a fresh
    machine would mean no package is ever installed.
    """
    packages = plugins.load().pi_packages()
    if not packages:
        return

    home_path = _home(home)
    path = home_path / _PI_SETTINGS
    local_path = (
        pathlib.Path(local_settings_path)
        if local_settings_path is not None
        else home_path / _PI_LOCAL_SETTINGS
    )

    # Migrate either the former public dead link or dotfiles_local's active
    # shadow to a real runtime file. Read first so Pi-owned state survives.
    settings = json.loads(path.read_text()) if path.exists() else {}
    if path.is_symlink():
        path.unlink()

    if local_path.exists():
        settings.update(json.loads(local_path.read_text(encoding="utf-8")))
    settings["packages"] = packages
    settings["enableSkillCommands"] = True
    settings["quietStartup"] = True

    content = json.dumps(settings, indent=2) + "\n"
    if path.exists() and path.read_text() == content:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Updated generated Pi settings at {path}")
