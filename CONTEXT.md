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
Mirroring a source tree into a destination as symlinks, so the source remains
the single copy. The inverse is **unstow**. Two trees are stowed here: this
repo's stow packages into the home directory, and the shared skills hub into
each skills discovery path.
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

**Package repository**:
A source the operating system's package manager installs from — EPEL, Debian
contrib, a PPA. Always qualified; a bare "repo" is a git repository.
_Avoid_: repo, repository, source

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

**Shared skill**:
An agent skill authored in one of these repos and stowed out to every agent
tool, so one copy serves all of them.
_Avoid_: skill, custom skill, local skill

**Plugin skill**:
An agent skill installed by the tool itself from a marketplace, listed in a
manifest rather than authored here. Never stowed, never edited in place.
_Avoid_: skill, marketplace skill, installed skill

**Shared skills hub**:
The directory where shared skills from several repos are collected so more than
one repo can contribute to them. Because it has multiple contributors, it holds
per-entry symlinks rather than one directory symlink.
_Avoid_: skills directory, skills folder

**Skills discovery path**:
The directory a given agent tool reads its skills from. Each tool has its own,
and the hub is stowed into all of them.
_Avoid_: skills directory, tool config

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

**Desktop-only**:
Provisioning work that is pointless on a headless host, whether or not it would
succeed there — installing a browser, a font, a launcher entry, or masking a
unit that only a desktop starts. Also the Ansible tag naming exactly that set,
which provisioning skips on a headless host.
_Avoid_: gui, graphical, interactive
