# Working with the Casting Monorepo via `uv`

This guide is a conceptual overview of how our Python monorepo is wired together with [`uv`](https://github.com/astral-sh/uv). It is written for teammates who are new to `uv`, to Python packaging, or to monorepos in general. Instead of documenting every current package (which can change over time), the goal is to explain the ideas that make the tooling predictable so you can confidently explore the codebase.

---

## 1. Monorepo + workspace fundamentals

### 1.1 Why we use a monorepo

* A single Git repository hosts multiple applications and shared libraries.
* Teams can evolve shared code and downstream consumers together, keeping interfaces in lockstep.
* Tooling such as code formatters, linters, and type-checkers only need to be configured once at the root.

The trade-off is that dependency management becomes more complex: we need one coherent environment that satisfies the needs of every active package.

### 1.2 Enter `uv`

`uv` is an all-in-one Python tool that replaces `pip`, `virtualenv`, and `python` launchers with a single high-performance binary. The features that matter most for us are:

| Concept | What `uv` provides |
| --- | --- |
| **Package management** | Resolves dependencies and writes a deterministic `uv.lock`. |
| **Environment management** | Creates an isolated `.venv/` per workspace with the right Python interpreter. |
| **Project execution** | Runs any command with `uv run` so you never manually activate virtual environments. |
| **Build backend** | Packages our libraries for distribution (via `uv build`). |

### 1.3 `uv` workspaces in a monorepo

In `uv`, a *workspace* is a set of projects that share one lockfile and one environment. Any project that opts into the workspace is installed in editable mode inside the root `.venv/`, so changes propagate instantly across the repository.

Key properties of the workspace model:

1. **Single source of truth** – `pyproject.toml` and `uv.lock` at the repo root describe the entire dependency graph.
2. **Local-first development** – Workspace members are installed editably so you can test modifications without publishing packages.
3. **Scoped inclusion** – The workspace is defined by glob patterns (`members`) and opt-outs (`exclude`). Only matched projects participate, allowing archival code to stay dormant.

When a new package is added to the repo, we decide whether it should be part of the workspace. If yes, we update the workspace configuration so that `uv` discovers its `pyproject.toml` and links the package into the shared environment.

---

## 2. Understanding the repository layout

### 2.1 Namespaces and `src/` layout

Our Python packages follow the modern "`src/` layout" convention:

```
libs/
  example-package/
    pyproject.toml
    src/
      company_namespace/
        example_package/
          __init__.py
```

* The package metadata (`pyproject.toml`) lives alongside the code under `src/`.
* The top-level `company_namespace/` directory is a **namespace package**. Multiple packages can contribute modules beneath the same namespace (for example `company_namespace.analytics`, `company_namespace.identity`, etc.).
* Namespace packages avoid collisions because each `pyproject.toml` specifies which portion of the namespace it owns. Python merges them at import time.

Applications follow the same pattern but may expose a runnable entry point (for example a `main.py` or a console script) rather than only library modules.

#### Why the `src/` layout matters

* Imports are always resolved from the installed package, not the repo root. This makes tests behave the same locally and in CI.
* Type checkers and linters understand the namespace structure because each package declares its `packages` or `tool.uv.sources` entry.
* When you run `uv run --package <name> ...`, `uv` executes commands against the installed package, ensuring the namespace wiring is identical to production.

### 2.2 Discovering workspace members

Instead of memorizing current package names, inspect the workspace definition when you need to know what is included:

```toml
[tool.uv.workspace]
members = [
  "apps/**",
  "libs/**",
  # ...additional patterns...
]
exclude = [
  "archive/**",
  # ...paths intentionally kept out of the workspace...
]
```

Any directory that matches a `members` glob and contains a `pyproject.toml` becomes a candidate. If a path also matches an `exclude` pattern, it is skipped. This approach keeps the workspace flexible: we can reorganize folders or add new packages without changing every downstream document.

To see the resolved list locally, run:

```bash
uv tree --editable
```

The command prints each installed editable package, grouped by namespace, so you can confirm what is active in your environment.

---

## 3. Getting set up

### 3.1 Install `uv`

`uv` is distributed as a single binary. On macOS and Linux you can install it with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows users can download the `.exe` from the [release page](https://github.com/astral-sh/uv/releases).

### 3.2 Install the required Python version

The workspace specifies a default interpreter (check `[project]` or `[tool.uv]` for `python = "3.x"`). Install it once:

```bash
uv python install 3.13
```

`uv` stores interpreters under `~/.uv/python`, leaving your system Python untouched.

### 3.3 Clone the repository

Make sure any private submodules or sibling repos mentioned in the README are present before you sync the workspace. Missing packages lead to resolution errors because the workspace expects to find their `pyproject.toml` files.

---

## 4. Syncing and running code

### 4.1 Create or update the workspace environment

From the repository root:

```bash
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock`, installs every workspace member in editable mode, and creates `.venv/`. It also installs any default dependency groups (for example `dev`) defined at the root.

Optional dependency groups can be included on demand:

```bash
uv sync --group data
uv sync --all-groups
```

### 4.2 Run commands without activating the venv

`uv run` launches any program inside the workspace environment. Prefer the package-targeted form so you are insulated from directory changes:

```bash
# Run a package's default entry point (console script)
uv run --package company-analytics python -m pytest

# Execute a task defined in pyproject.toml using poe the poet
uv run --package company-identity poe test
```

Why `--package`? It selects the `pyproject.toml` that should define the working directory, dependency groups, and settings. This is more robust than `--project` (which relies on path structure) when packages are moved.

You can still run repo-wide tooling by omitting `--package` and executing commands from the root:

```bash
uv run poe lint
uv run python -m pytest
```

### 4.3 Running applications

Applications usually expose a console script or module entry point in their `pyproject.toml`. Use `uv run --package <name>` to invoke them:

```bash
uv run --package messaging-bot python -m company_namespace.messaging_bot.main
uv run --package auth-service uvicorn company_namespace.auth.service:app
```

Because packages are installed editably, any changes you make under their `src/` directories are picked up immediately.

---

## 5. Managing dependencies across the workspace

### 5.1 How dependency resolution works

`uv` builds a single dependency graph for the entire workspace. Each package contributes its own `[project]` requirements, and the root `pyproject.toml` can define shared `dependency-groups` such as `dev` or `data`. When you run `uv sync`, the solver combines all of these into `uv.lock`, guaranteeing that every member resolves against the same versions.

Two important pieces tie the graph together:

* **Default groups** – `[tool.uv] default-groups = ["dev"]` ensures shared tooling is present in every environment. Optional groups (for example `cast-query`) can be installed on demand via `uv sync --group cast-query`.
* **Workspace sources** – `[tool.uv.sources]` maps package names (like `llmgine` or `cast-query`) to `{ workspace = true }`. When any package declares `llmgine` as a dependency, `uv` satisfies it from the editable workspace copy instead of fetching from PyPI. This keeps cross-package imports in sync with local code changes.

### 5.2 Adding or updating requirements

From within a package directory (or by specifying `--package`):

```bash
uv add httpx>=0.27
```

This updates the package’s `pyproject.toml` and refreshes the shared `uv.lock`. Always commit both files together so teammates reproduce the same environment.

To remove a dependency, use `uv remove <name>`.

Need an optional dependency? Add it to a named group:

```bash
uv add --group analytics polars
```

Team members can then opt in with `uv sync --group analytics` without bloating the default environment.

### 5.3 Depending on other workspace packages

Because members share a lockfile, you can depend on another local package by using its published name in your `pyproject.toml`:

```toml
[project]
dependencies = [
  "cast-query",
  "httpx>=0.27",
]
```

After saving, run `uv sync` (or `uv sync --package <name>`) to re-resolve. Thanks to the workspace source mapping, `uv` installs the editable version of `cast-query`, so `import company_namespace.cast.query` immediately reflects your edits.

### 5.4 Rebuilding the lockfile

If the lockfile drifts or you need to refresh transitive versions:

```bash
uv lock --rebuild
```

Follow up with `uv sync` to apply the changes to your environment.

---

## 6. Creating new workspace members

Use `uv init` to scaffold packages and applications so they conform to the workspace expectations:

```bash
uv init libs/cast/new-sync-engine
```

This command creates a new directory with a `pyproject.toml`, `src/` layout, and basic configuration. Adjust the generated metadata to match our namespace convention—for example, set `packages = [{ include = "company_namespace.cast.new_sync_engine" }]`.

When you introduce a new member:

1. **Choose the location** – place libraries under `libs/` and applications under `apps/`. If you need a new subtree, add a corresponding glob to `[tool.uv.workspace].members` so `uv` discovers the project.
2. **Preserve namespace layout** – keep code under `src/company_namespace/...` so imports interoperate with existing packages.
3. **Declare dependencies** – use `uv add` (optionally with `--group`) to record requirements. Add other workspace packages by name; `tool.uv.sources` ensures they resolve locally.
4. **Expose sources if necessary** – if the new package should also satisfy workspace dependencies (for example another member depends on it), add an entry under `[tool.uv.sources]` pointing to `{ workspace = true }`.
5. **Sync the environment** – run `uv sync` so the new project appears in `.venv/` and is ready for imports via `uv run --package`.

After these steps, teammates can run commands against the project with:

```bash
uv run --package new-sync-engine poe test
```

Because the package participates in the workspace, its modules can be imported anywhere using the shared namespace (for example `from company_namespace.cast.new_sync_engine import tasks`).

---

## 7. Troubleshooting

* **Package not found** – verify the package directory exists and matches a workspace `members` pattern. If you moved a folder, update the workspace configuration.
* **Import errors within a namespace** – double-check the package’s `pyproject.toml` exposes the intended namespace modules (for example via `packages = [{ include = "company_namespace.analytics" }]`). Missing entries cause Python to skip parts of the namespace.
* **Unexpected dependency versions** – make sure you ran `uv sync` after switching branches. If necessary, refresh with `uv lock --rebuild`.
* **Environment drift** – delete `.venv/` and run `uv sync` to recreate it from the lockfile.

---

## 8. Quick reference

| Task | Command |
| --- | --- |
| Install/update workspace | `uv sync` |
| Install optional dependencies | `uv sync --group <name>` |
| Run repo-wide tooling | `uv run <command>` |
| Run package-specific tooling | `uv run --package <name> <command>` |
| Add or remove dependencies | `uv add <pkg>`, `uv remove <pkg>` |
| Rebuild lockfile | `uv lock --rebuild` |
| Inspect editable installs | `uv tree --editable` |

Keep this document alongside `docs/environment-setup.md` as the conceptual overview for working productively with the Casting monorepo and its `uv` workspace.

