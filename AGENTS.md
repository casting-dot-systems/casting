# Repository Guidelines

## Project Structure & Module Organization
- `apps/` holds deployable services and interfaces (`cast/cli`, `cast/tui`, `identity-server`, etc.); each sub-app keeps its own entrypoints and adapters.
- `libs/` contains reusable domain packages (e.g., `cast/core`, `discord/framework`, `members`) that expose typed APIs consumed by apps.
- `llmgine/` centralizes LLM integrations and prompt tooling shared across products.
- `docs/` and `archive/` track design references and experiments; `orgs/` stores organization-specific wiring and is excluded from the default workspace.

## Build, Test, and Development Commands
- `uv run poe fmt` → format codebase with Ruff across Python packages.
- `uv run poe lint` → run Ruff linting with autofix to catch import/order issues early.
- `uv run poe check` → execute Pyright type checks (Python 3.13 target).
- `uv run poe test:all` → run the aggregate pytest suite (`apps/cast` and `libs/cast` targets).
- Use `uv run poe test:cli` or `uv run poe test:tui` for focused suites; pass extra pytest options after `--`.

## Coding Style & Naming Conventions
- Python code uses Ruff’s defaults plus a 120-char line limit; prefer explicit imports and keep module paths stable for `ruff.isort`.
- Indent with 4 spaces; favor dataclasses and `typing` annotations so Pyright stays green.
- Package, module, and directory names stay lowercase with underscores; public classes use `PascalCase`, functions and variables use `snake_case`.
- Run `uv run poe fmt` before committing; CI reruns the same jobs (`ci:*` tasks) so match them locally.

## Testing Guidelines
- Tests live beside source modules (`tests/` folders or `test_*.py` files) and rely on pytest/pytest-asyncio.
- Name async-heavy tests with descriptive suffixes (e.g., `test_sync_client_handles_timeout`); mark live Discord scenarios with `@pytest.mark.live` as needed.
- Aim to cover new service endpoints and adapters with both unit and integration tests; replicate fixture patterns already present in `libs/cast/core/tests` when adding new ones.

## Commit & Pull Request Guidelines
- Follow the existing history: prefix messages with a concise tag (`feat:`, `mini:`, `checkpoint:`) plus a short scope summary.
- Keep commits focused on one concern; include refactors and generated assets separately.
- PRs should describe intent, list major modules touched, and link any related issues or runbooks; add CLI/TUI screenshots if behavior changes.
- Confirm `poe fmt`, `lint`, `check`, and relevant `test:*` tasks succeed before requesting review, and note any skipped suites.

## Security & Configuration Tips
- Store secrets in local `.env` files ignored by git; never commit API tokens from Discord, Chromadb, or identity providers.
- When wiring new providers, reuse helpers in `libs/discord/framework` and `llmgine/` so credential handling stays centralized.
