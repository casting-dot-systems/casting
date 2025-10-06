# Development Environment Files

Each app or library can ship a single `.env` file at its root for development and local testing.

```
<app>/
└── .env    # tracked, non-secret defaults for dev/test runs
```

Call `bootstrap_env(app_dir=..., filename=".env")` near startup to apply it:

```python
import os
from casting.platform.config import bootstrap_env, find_app_dir, SettingsBase

APP_DIR = find_app_dir(__file__)
bootstrap_env(app_dir=APP_DIR)

class Settings(SettingsBase):
    api_url: str = "http://localhost:8000"
```

* Values already present in `os.environ` always win.
* When `APP_ENV` is `prod`, `production`, or `staging`, the loader skips the `.env` file so production deployments stay untouched. (Override with `disable_in_prod=False` if needed.)
* Use a different filename by passing `filename=".env.example"`.

Keep per-developer secrets in git-ignored files (`.env.local`, `.env.secrets`, etc.) or through shell tools; the loader intentionally ignores them. For production, inject configuration via your orchestrator (Docker/Kubernetes environment variables, secret managers, etc.).

`find_app_dir` walks up from the current module until it finds a directory with an `.env`
file (or, failing that, a `pyproject.toml`), so you rarely need to hard-code parent
counts to locate your app root.
