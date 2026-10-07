# Design and implementation decisions

This document explains the choices behind Tyche Job Hunt: the problems they
address, the alternatives considered, and the tradeoffs accepted. Decisions
are added as the project develops and revisited when its needs change.

## How decisions are recorded

Each entry covers:

- **Context:** What problem or requirement prompted the decision?
- **Decision:** What approach was chosen, and why?
- **Alternatives:** What other approaches were considered?
- **Tradeoffs:** What benefits and limitations does the choice bring?
- **Revisit when:** What changes would justify reconsidering it?

## Decisions

### 001: Use uv for dependency and environment management

**Context:** I needed a way to install dependencies
and run the app, tests, and formatting tools in a consistent environment.
The thought was to make it easy for someone cloning the repository for the first time and running it.

**Decision:** given my prior use of uv, with dependencies declared in `pyproject.toml` and
resolved versions recorded in `uv.lock`. `uv sync` prepares the project
environment, and `uv run` executes commands within it without requiring manual
activation. The README and Makefile use this workflow consistently.
See the [uv project guide](https://docs.astral.sh/uv/guides/projects/).

**Alternatives:** thought about using pipenv instead with a `Pipfile` and `Pipfile.lock`. For this project, and for simplicity's sake uv's workflow around `pyproject.toml` was preferred over maintaining Pipenv-specific dependency declarations.

**Tradeoffs:** uv keeps setup and everyday commands in one tool, while
`pyproject.toml` holds the project's metadata and dependency declarations.
Contributors need to install uv to follow the documented workflow, and
`uv.lock` is specific to uv. By default, `uv run` can update the lockfile when
dependency declarations change; checks that must preserve the recorded
resolution can use `--locked` to reject an outdated lockfile instead.
See [locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

**Revisit when:** A deployment environment or team tooling requirement makes
the uv workflow difficult to support. Changing tools should solve a concrete
compatibility or maintenance problem.
