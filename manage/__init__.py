"""The logic behind this repo's tasks, separated from the command surface.

`tasks.py` is the CLI: invoke owns argument parsing, `inv --list` discovery, and
the task graph that composes provisioning with stowing. Everything it calls that
is worth testing on its own lives here, so a rule can be exercised without
running a task.

- `repo` -- facts about this checkout and the machine, defined once.
- `stow` -- mirroring this repo's stow packages into the home directory.
- `agents` -- the agent tools: instruction files, plugins, shared skills.
- `knowledge` -- which OKF knowledge bundles apply, and reading them.

`agents` is a namespace because its generic names do not survive contact with
this repo -- "plugins" is equally what lazy manages in nvim, and "instructions"
says nothing about whose. Import the namespace, not the module, so the call site
stays unambiguous:

    from manage import agents

    agents.plugins.load()

Deliberately no imports here. `manage.knowledge` is reached from a harness hook
running under whatever `python3` it finds, so importing `agents` eagerly would
make every hook depend on this repo's own dependencies -- and fail the session
when they are missing. Import the namespace you need at the call site.
"""
