"""The logic behind this repo's tasks, separated from the command surface.

`tasks.py` is the CLI: invoke owns argument parsing, `inv --list` discovery, and
the task graph that composes provisioning with stowing. Everything it calls that
is worth testing on its own lives here, so a rule can be exercised without
running a task.

Subpackages are named for the job they serve, because the generic names do not
survive contact with this repo -- "plugins" is equally the name for what lazy
manages in nvim, and "instructions" says nothing about whose. Import the
namespace, not the module, so the call site stays unambiguous:

    from manage import agents

    agents.plugins.load()
"""

from manage import agents

__all__ = ["agents"]
