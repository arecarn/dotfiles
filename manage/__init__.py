"""The logic behind this repo's tasks, separated from the command surface.

`tasks.py` is the CLI: invoke owns argument parsing, `inv --list` discovery, and
the task graph that composes provisioning with stowing. Everything it calls that
is worth testing on its own lives here, so a rule can be exercised without
running a task.

The three modules mirror the jobs CONTEXT.md names:

- `instructions` -- assemble each agent harness's instruction file from the
  shared fragments.
- `plugins` -- read the plugin manifest and answer what to run for a tool, which
  MCP servers to register, and which pi packages are declared.
- `skills_hub` -- own where the shared skills hub lives and how it reaches each
  tool's skills discovery path.

Import the submodules rather than these names when you want the whole surface;
the re-exports below are the entry points tasks.py actually calls.
"""

from manage import instructions, plugins, skills_hub
from manage.instructions import generate as generate_instructions
from manage.plugins import load as load_plugin_manifest
from manage.skills_hub import pre_create as pre_create_skills_hub
from manage.skills_hub import stow_out as stow_skills_out

__all__ = [
    "instructions",
    "plugins",
    "skills_hub",
    "generate_instructions",
    "load_plugin_manifest",
    "pre_create_skills_hub",
    "stow_skills_out",
]
