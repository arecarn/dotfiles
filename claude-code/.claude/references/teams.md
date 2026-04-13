### Teams

When spawning team agents, always use the same model as the leader to ensure consistent quality and capabilities.

Use the `model` parameter on the Agent tool with values from `~/.claude/settings.json`:
- `model: "opus"` → `ANTHROPIC_DEFAULT_OPUS_MODEL`
- `model: "sonnet"` → `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `model: "haiku"` → `ANTHROPIC_DEFAULT_HAIKU_MODEL`

The current default model is set via `"model"` key in settings.json.
