### Local and Private Instructions

Private and work-specific instructions live outside this repo, at
`~/.config/ai-instructions/local.md`, placed there by a `dotfiles_local` repo.

Read that file at the start of a session if it exists. It is absent on machines
that have no `dotfiles_local`, which is not an error — carry on without it.

That file is also where a pointer to a **private knowledge bundle** belongs: a
work bundle's path and name are not publishable, and the generated instruction
files that carry this section are. See the `set-up-agent-knowledge` skill.
