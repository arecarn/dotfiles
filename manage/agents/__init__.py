"""Managing the agent tools: their instruction files, plugins, and shared skills.

These three read and write the `agents` stow package and the directories it
stows into, which is what makes them one namespace rather than three loose
modules:

- `instructions` -- assemble each harness's instruction file from the shared
  fragments in `agents/.config/ai-instructions/`.
- `plugins` -- read the plugin manifest at `agents/.config/ai-skills/plugins.yaml`
  and answer what to run for a tool, which MCP servers to register, and which pi
  packages are declared.
- `skills_hub` -- own where the shared skills hub lives and how it reaches each
  tool's skills discovery path.
"""

from manage.agents import instructions, plugins, skills_hub

__all__ = ["instructions", "plugins", "skills_hub"]
