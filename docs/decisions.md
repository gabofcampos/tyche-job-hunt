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

### 002: static type checking: astral's ty over mypy

**Context:** The project's type annotations should help catch mistakes during
development, such as passing incompatible arguments or using optional values
without checking for `None`. Static checking complements the tests and does
not replace runtime input validation.

**Decision:** I chose Astral's ty. The project already uses uv, so running
another tool from the same ecosystem fits the existing workflow. Fast feedback
was another reason to try it, although I have not benchmarked ty against mypy
on this project. I had already worked with mypy and wanted practical experience
with a different checker. See the [ty documentation](https://docs.astral.sh/ty/)
and its [uv installation workflow](https://docs.astral.sh/ty/installation/).

**Alternatives:** mypy was the familiar option and could also provide static
type checking. This choice reflects the project's needs and my learning goals,
rather than a claim that mypy would be unsuitable.

**Tradeoffs:** Using ty means learning its diagnostics and configuration instead
of relying on my existing mypy experience. The initial check surfaced optional
widget keys, session-state keys that were not necessarily strings, badge colors
whose types were inferred too broadly, and test overrides that assigned a
callable where a class was expected. These were addressed with guards, literal
type annotations, and scoped mocks. Different checkers can report different
issues; a passing check is still only one part of verification.

**Revisit when:** A reproducible limitation prevents useful checking of the
project's code or dependencies, or a team requires a shared checker. In that
case, compare the tools against the actual code and diagnostics before switching.

### 003: Defer introducing Pydantic

**Context:** I considered introducing Pydantic for runtime validation of fields
such as URLs, dates, and required text. The current app collects data through
forms, represents jobs and companies with standard-library dataclasses, and
uses explicit checks for required fields and HTTP(S) URLs. It does not currently
accept JSON or CSV imports or expose an API.

**Decision:** Keep the dataclasses and explicit validation for now. The current
rules are small enough to express directly, so adding a dependency and changing
the model layer would bring limited benefit at this stage. Display formatting,
such as presenting dates, can remain in ordinary presentation functions.

**Alternatives:** Introduce Pydantic models or validated dataclasses now, with
field constraints and custom validators. Another incremental option is to
extract validation from the forms into shared functions as rules grow, without
changing the data models.

**Tradeoffs:** This keeps the implementation small and the validation behavior
explicit. Standard dataclasses do not enforce their annotations at runtime,
so input checks remain our responsibility. Some validation still lives in the
forms, which could lead to duplication if new input paths are added. Static
type checking does not remove the need to validate incoming data.

**Revisit when:** JSON or CSV imports, an API, or multiple input paths need the
same validation rules; or field and cross-field checks become difficult to
maintain. At that point, evaluate Pydantic at the input boundaries, including
how it handles conversion, errors, and the existing rules, before deciding
whether the internal dataclasses also need to change.
