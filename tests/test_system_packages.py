"""Tests for the system package data shared by all three platforms.

The lists live in `ansible/group_vars/all.yml`; Ansible reads them on Linux and
`manage.provision` reads the same file for Windows and Termux.
"""

# Test names document each case, and these helpers are private to the module.
# pylint: disable=missing-function-docstring

from ruamel.yaml import YAML

from manage import provision


def _data():
    return YAML(typ="safe").load(provision.PACKAGE_DATA.read_text(encoding="utf-8"))


def test_a_headless_windows_run_installs_only_the_non_desktop_packages():
    headless = provision.windows_system_packages(desktop=False)
    desktop_only = _data()["windows_desktop_only_system_packages"]

    assert headless == list(_data()["windows_system_packages"])
    assert not set(headless) & set(desktop_only)


def test_a_desktop_windows_run_adds_the_desktop_only_packages():
    packages = provision.windows_system_packages(desktop=True)

    for package in _data()["windows_desktop_only_system_packages"]:
        assert package in packages


def test_the_common_list_is_not_mutated_by_adding_the_desktop_only_packages():
    """The failure this guards: the desktop run aliasing the stored list.

    Extending an alias grows the data for every later caller, so a headless run
    in the same process would install the desktop-only packages anyway.
    """
    provision.windows_system_packages(desktop=True)

    assert provision.windows_system_packages(desktop=False) == list(
        _data()["windows_system_packages"]
    )


def test_each_call_returns_a_list_the_caller_may_own():
    first = provision.windows_system_packages(desktop=False)
    first.append("not-a-real-package")

    assert "not-a-real-package" not in provision.windows_system_packages(desktop=False)


def test_the_termux_bootstrap_packages_come_from_the_data_file():
    assert provision.termux_bootstrap_system_packages() == list(
        _data()["termux_bootstrap_system_packages"]
    )


def test_no_gui_naming_remains_in_the_package_data():
    assert not [key for key in _data() if "gui" in key]
