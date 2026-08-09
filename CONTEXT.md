# Dotfiles

Personal configuration for Linux, Windows, and Termux. It does two separable
jobs: installing software onto a machine, and placing configuration files into
the home directory.

## Language

### The two jobs

**Provision**:
Installing software and applying system-level settings on a machine. Ansible on
Linux, Chocolatey on Windows, `pkg` on Termux.
_Avoid_: install, bootstrap, setup

**Stow**:
Placing this repo's configuration into the home directory as symlinks, so the
repo remains the single copy. The inverse is **unstow**.
_Avoid_: deploy, install, sync, link

### Units

"Package" is never used bare — it means three different things here, so it
always carries a qualifier.

**Stow package**:
A top-level directory in this repo whose tree is mirrored into `$HOME` by
stowing — `git/`, `nvim/`, `zsh/`. A unit of configuration, never a unit of
software.
_Avoid_: package, module, bundle, dotfile group

**System package**:
Software installed by the operating system's package manager — apt, Chocolatey,
`pkg`.
_Avoid_: package, dependency

**Language package**:
Software installed by a language ecosystem's package manager — Python, npm,
Rust.
_Avoid_: package, library, dependency

### Placement

**Link**:
An explicit single source-to-destination symlink that is not derived from a
package tree, such as the Dropbox-to-files link. Stowing places symlinks too,
but those come from packages and are not called links.
_Avoid_: symlink, alias, shortcut

**Dead link**:
A symlink in the home directory pointing into this repo at a path that no longer
exists, left behind when a package's contents change. Removed by `clean-stow`,
which is distinct from `clean`.
_Avoid_: broken link, orphan, stale symlink

**Shared skills hub**:
The directory where agent skills from several repos are collected so more than
one repo can contribute to it. Because it has multiple contributors, it holds
per-entry symlinks rather than one directory symlink.
_Avoid_: skills directory, skills folder

### Environments

**Baseline**:
System-level state applied to every Linux machine regardless of what is
installed on it, such as masking units this setup does not want running.
_Avoid_: defaults, base config

**Headless host**:
A machine with no desktop session — chiefly CI runners. Desktop-only units and
packages are absent there, so anything assuming a desktop must not fail the
provisioning run.
_Avoid_: server, CI box, bare machine
