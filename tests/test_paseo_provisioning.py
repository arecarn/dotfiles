"""Paseo provisioning's ordering and boot-service contract."""

from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
YAML_SAFE = YAML(typ="safe")


def _tasks():
    return YAML_SAFE.load((ROOT / "ansible/tasks/paseo.yml").read_text())


def test_paseo_is_installed_before_its_daemon_is_configured():
    """A fresh install must supply the CLI before configuring its daemon."""
    packages = YAML_SAFE.load((ROOT / "ansible/group_vars/all.yml").read_text())
    site = (ROOT / "ansible/site.yml").read_text()
    assert "@getpaseo/cli" in packages["npm_global_packages"]
    assert site.index("tasks/npm-packages.yml") < site.index("tasks/paseo.yml")


def test_listener_is_set_before_service_starts_and_only_when_needed():
    """Avoid exposing the daemon or restarting it on unchanged runs."""
    tasks = _tasks()
    names = [task["name"] for task in tasks]
    assert names.index("Read Paseo listener") < names.index(
        "Set Paseo loopback listener"
    )
    assert names.index("Set Paseo loopback listener") < names.index(
        "Start Paseo user service"
    )
    listener = next(
        task for task in tasks if task["name"] == "Set Paseo loopback listener"
    )
    assert "127.0.0.1:6767" in listener["ansible.builtin.command"]["cmd"]
    assert "paseo_listener.stdout" in str(listener["when"])
    assert "paseo_listener_change" == listener["register"]


def test_user_service_has_local_agent_path_and_supervised_foreground_process():
    """The boot service must find user tools without publishing credentials."""
    tasks = _tasks()
    unit = next(task for task in tasks if task["name"] == "Install Paseo user service")
    content = unit["ansible.builtin.copy"]["content"]
    assert "ExecStart={{ user_home }}/.local/bin/paseo daemon run" in content
    assert "Environment=PATH={{ user_home }}/.local/bin:" in content
    assert "Restart=on-failure" in content
    # Credentials stay in a private local file, never in the public unit.
    assert "EnvironmentFile=-{{ user_home }}/.config/paseo/provider.env" in content
    assert "LITELLM_TOKEN=" not in content
    assert "ANTHROPIC_AUTH_TOKEN=" not in content
    assert unit["become"] is False
    assert unit["register"] == "paseo_unit_change"


def test_live_service_operations_are_skipped_in_ci_and_enable_boot_start():
    """CI lacks a user bus, but real hosts must enable boot startup."""
    tasks = _tasks()
    linger = next(
        task for task in tasks if task["name"] == "Enable Paseo user lingering"
    )
    service = next(task for task in tasks if task["name"] == "Start Paseo user service")
    assert "desktop-only" in linger["tags"]
    assert "desktop-only" in service["tags"]
    assert linger["become"] is False
    assert service["become"] is False
    assert service["ansible.builtin.systemd_service"]["scope"] == "user"
    assert service["ansible.builtin.systemd_service"]["enabled"] is True
    assert "paseo_unit_change.changed" in str(
        service["ansible.builtin.systemd_service"]["state"]
    )
    assert "paseo_listener_change.changed" in str(
        service["ansible.builtin.systemd_service"]["state"]
    )
