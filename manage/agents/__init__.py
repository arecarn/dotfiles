"""Managing the agent tools: their instruction files, plugins, and shared skills.

They read and write the `agents` stow package, the directories it stows into,
and the config files the harnesses themselves own -- which is what makes them
one namespace rather than a handful of loose modules:

- `instructions` -- assemble each harness's instruction file from the shared
  fragments in `agents/.config/ai-instructions/`.
- `plugins` -- read the plugin manifest at `agents/.config/ai-skills/plugins.yaml`
  and answer what to run for a tool, which MCP servers to register, and which pi
  packages are declared.
- `skills_hub` -- own where the shared skills hub lives and how it reaches each
  tool's skills discovery path.
- `mcp` -- register the manifest's MCP servers with every harness.
- `settings` -- write this repo's declarations into each harness's own settings
  file, which the harness also writes its own state into.
"""

from manage.agents import instructions, mcp, plugins, settings, skills_hub

__all__ = ["instructions", "mcp", "plugins", "settings", "skills_hub"]
