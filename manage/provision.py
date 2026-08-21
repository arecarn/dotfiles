"""System package lists, read from the one file that defines them.

`ansible/group_vars/all.yml` answers "what gets installed on a machine" for all
three platforms. Ansible reads it directly on Linux; Windows and Termux have no
playbook run, so the lists they need are read from the same file here and handed
to Chocolatey and `pkg` by the task layer.

Every accessor returns a fresh list, so a caller extending one cannot reach back
into the loaded data or into another caller's result.
"""

import functools

from ruamel.yaml import YAML

from manage.repo import ROOT

PACKAGE_DATA = ROOT / "ansible" / "group_vars" / "all.yml"

_YAML = YAML(typ="safe")


@functools.cache
def _load() -> dict:
    return _YAML.load(PACKAGE_DATA.read_text(encoding="utf-8"))


def windows_system_packages(*, desktop: bool) -> list[str]:
    """Chocolatey packages for a Windows machine.

    `desktop=False` is the headless host case (CI): the desktop-only packages
    are left out. The returned list is a copy -- appending to it must not grow
    the stored list for the next caller.
    """
    data = _load()
    packages = list(data["windows_system_packages"])
    if desktop:
        packages += data["windows_desktop_only_system_packages"]
    return packages


def termux_bootstrap_system_packages() -> list[str]:
    """`pkg` packages Termux needs before Ansible and uv can run."""
    return list(_load()["termux_bootstrap_system_packages"])
