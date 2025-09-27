# Environment Variable Management in Casting Systems Monorepo

This document explains how to manage environment variables across different workspace members in the monorepo.

## Strategy: Local `.env` Files per Workspace Member

Each workspace member (app/lib) can have its own `.env` file for environment-specific configuration.

### Directory Structure
```
casting-systems/
├── apps/
│   ├── cast/
│   │   ├── discord/
│   │   │   ├── .env              # Discord bot env vars
│   │   │   ├── .env.example      # Template for Discord env vars
│   │   │   └── src/
│   │   ├── server/
│   │   │   ├── .env              # Server env vars
│   │   │   ├── .env.example      # Template for server env vars
│   │   │   └── src/
│   │   └── cli/
│   │       ├── .env              # CLI env vars (if needed)
│   │       └── src/
├── llmgine/
│   ├── .env                      # LLM engine env vars
│   ├── .env.example              # Template for LLM engine env vars
│   └── src/
└── .env                          # Global/shared env vars (optional)
```

## Implementation Patterns

### 1. Python Applications with python-dotenv

For Python apps, use `python-dotenv` to load environment variables:

```python
# apps/cast/discord/src/casting/apps/cast/discord/bot.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the Discord app directory
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# Or use find_dotenv to search up the directory tree
# load_dotenv(find_dotenv())

def get_discord_config():
    return {
        'token': os.getenv('DISCORD_TOKEN'),
        'prefix': os.getenv('DISCORD_COMMAND_PREFIX', '!'),
        'allowed_channels': os.getenv('DISCORD_ALLOWED_CHANNELS', '').split(','),
        'allowed_roles': os.getenv('DISCORD_ALLOWED_ROLES', '').split(',')
    }
```

### 2. Multiple Environment Support

You can support different environments (dev, staging, prod):

```python
# apps/cast/server/src/casting/apps/cast/server/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    env = os.getenv('ENVIRONMENT', 'development')
    
    # Load base .env
    base_env = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(base_env)
    
    # Load environment-specific .env
    env_file = Path(__file__).parent.parent.parent.parent / f'.env.{env}'
    if env_file.exists():
        load_dotenv(env_file, override=True)
```

### 3. Workspace Member Configuration Class

Create a configuration class for each workspace member:

```python
# apps/cast/server/src/casting/apps/cast/server/config.py
from pydantic import BaseSettings
from pathlib import Path

class ServerConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    database_url: str = "sqlite:///./cast_server.db"
    secret_key: str
    access_token_expire_minutes: int = 30
    allowed_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    
    class Config:
        env_file = Path(__file__).parent.parent.parent.parent / '.env'
        env_file_encoding = 'utf-8'

# Usage
config = ServerConfig()
```

### 4. Global + Local Environment Variables

You can have both global and local environment variables:

```python
# shared/env_loader.py
import os
from pathlib import Path
from dotenv import load_dotenv

def load_workspace_env(workspace_path: Path):
    """Load environment variables for a specific workspace member."""
    
    # 1. Load global .env from repo root
    repo_root = Path(__file__).parent.parent  # Adjust path as needed
    global_env = repo_root / '.env'
    if global_env.exists():
        load_dotenv(global_env)
    
    # 2. Load workspace-specific .env
    local_env = workspace_path / '.env'
    if local_env.exists():
        load_dotenv(local_env, override=True)  # Local overrides global
    
    # 3. Load environment-specific .env
    env = os.getenv('ENVIRONMENT', 'development')
    env_specific = workspace_path / f'.env.{env}'
    if env_specific.exists():
        load_dotenv(env_specific, override=True)
```

## Best Practices

### 1. Always Use .env.example Files
Create `.env.example` files with dummy values as templates:

```bash
# apps/cast/discord/.env.example
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_COMMAND_PREFIX=!
DISCORD_ALLOWED_CHANNELS=channel1,channel2,channel3
DISCORD_ALLOWED_ROLES=admin,moderator
API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
```

### 2. Update .gitignore
Make sure your `.gitignore` excludes `.env` files but includes `.env.example`:

```gitignore
# Environment variables
.env
.env.*
!.env.example
!.env.*.example
```

### 3. Use Environment Variable Validation
Validate required environment variables at startup:

```python
def validate_required_env_vars():
    required = ['DISCORD_TOKEN', 'API_BASE_URL']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
```

### 4. Development Scripts
Create development scripts that can set up environments:

```bash
#!/bin/bash
# scripts/setup-dev-env.sh

# Copy example files if .env doesn't exist
for dir in apps/cast/discord apps/cast/server llmgine; do
    if [ -f "$dir/.env.example" ] && [ ! -f "$dir/.env" ]; then
        cp "$dir/.env.example" "$dir/.env"
        echo "Created $dir/.env from example"
    fi
done
```

## Running Commands with Specific Environments

### Using uv with environment files:
```bash
# Run Discord bot with its environment
cd apps/cast/discord && uv run python -m casting.apps.cast.discord.bot

# Run server with its environment  
cd apps/cast/server && uv run python -m casting.apps.cast.server.main

# Or use environment variables directly
ENVIRONMENT=production uv run python -m casting.apps.cast.server.main
```

### Using VS Code with workspace-specific environments:
Each workspace member can have its own VS Code launch configuration:

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Discord Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/apps/cast/discord/src/casting/apps/cast/discord/bot.py",
            "envFile": "${workspaceFolder}/apps/cast/discord/.env",
            "cwd": "${workspaceFolder}/apps/cast/discord"
        },
        {
            "name": "Cast Server", 
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/apps/cast/server/src/casting/apps/cast/server/main.py",
            "envFile": "${workspaceFolder}/apps/cast/server/.env",
            "cwd": "${workspaceFolder}/apps/cast/server"
        }
    ]
}
```

This approach gives you maximum flexibility while keeping environment variables organized and scoped to their respective workspace members.
