### Build & CI Structure

- Projects have a task runner (Make by default) and CI configuration.
- CI calls only task-runner targets, so every pipeline step reproduces locally.
- Docker gives a reproducible environment: targets run in the container
  locally and directly inside CI's own container.
- Use the standard target names (`help`, `lint`, `lint-check`, `format`,
  `format-check`).

Setting up or changing a Makefile, Dockerfile or CI file: read the personal
knowledge entry `docker-makefile.md` first.
