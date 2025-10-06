# casting-config

Tiny helper to load an app-local `.env` file while developing Casting services.

## Behaviour

```python
from casting.platform.config import bootstrap_env, find_app_dir

APP_DIR = find_app_dir(__file__)
bootstrap_env(app_dir=APP_DIR)
```

`bootstrap_env` looks for `<app>/.env`, loads it if present, and applies any keys that aren’t already set in `os.environ`. When `APP_ENV` is `prod`, `production`, or `staging` the loader skips everything so production deployments rely solely on real runtime configuration. You can choose a different filename with `bootstrap_env(..., filename=".env.example")`, or disable the production guard via `disable_in_prod=False`.

## Settings models

You can continue to derive settings from `SettingsBase` once the env file has been applied:

```python
from pydantic import Field
from casting.platform.config import SettingsBase

class Settings(SettingsBase):
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
```

`SettingsBase` only provides sane defaults (e.g. nested delimiter) and does not load files by itself—always call `bootstrap_env` first.

## Tests & tooling

If your module layout is unusual, `find_app_dir(__file__)` walks upward until it finds
an `.env` file or a `pyproject.toml`, so you rarely need to hard-code parent counts.

The package deliberately leaves secrets alone. Developers can keep private overrides in `.env.local` or shell profiles; the loader never touches them. CI can load the same `.env` as local runs to mimic development behaviour, while production stays controlled by container/runtime variables.
