# Discord Framework Overview

## Purpose

`libs/discord/framework` packages a production-ready adapter that connects Discord guilds and users to the `llmgine` orchestration stack. It wraps `discord.py` with typed models, a message bus runtime, and live-testing utilities so agents built in `llmgine` can exchange commands, events, and contextual data with Discord channels in real time.

## Core Modules

- **`models.py`** – Defines lightweight dataclasses (`MessageInfo`, `OutboundMessage`, `InteractionContext`, etc.) that translate raw Discord payloads into transport-agnostic shapes consumed by `llmgine` tooling. These objects are used throughout the bus protocol and API surface so the rest of the system never handles `discord.py` objects directly.
- **`api.py`** – Wraps a `discord.Client` (or compatible bot) to expose high-level async helpers such as `send_message`, `edit_message`, `create_thread`, and `respond_to_interaction`. Each helper converts framework models into `discord.py` calls and returns framework models so downstream code stays decoupled from `discord.py` internals.
- **`protocol.py`** – Declares the command and event dataclasses that flow across the message bus (e.g. `SendMessageCommand`, `MessageSentEvent`, `ActionResultEvent`). Every dataclass is keyword-only to keep command construction explicit and stable.
- **`runtime.py`** – Hosts `DiscordAgentRuntime`, the bridge between the message bus and the Discord API. It registers handlers for all protocol commands, interacts with the API wrapper, publishes corresponding events, and forwards agent action requests to optional callbacks.
- **`testing/`** – Contains the layered dotenv loader, live test harness, and CLI runner that power interactive verification against the real Discord API.

## Interaction with `llmgine`

The framework is designed around `llmgine`'s message bus primitives:

1. **Message Bus Registration** – `DiscordAgentRuntime.register()` accepts a `MessageBus` instance from `llmgine.bus.bus`. By default it scopes handlers to `SessionID("BUS")` so agent code issues commands in that namespace without additional routing.
2. **Command Handling** – When an agent working inside `llmgine` submits commands such as `SendMessageCommand` or `FetchChannelHistoryCommand`, the bus invokes the corresponding runtime handler. The handler uses `DiscordAgentAPI` to call Discord, wraps the response in framework models, and returns a `CommandResult` from `llmgine.messages.commands`.
3. **Event Emission** – After fulfilling a command, the runtime publishes events back onto the bus (e.g. `MessageSentEvent`, `MessagesFetchedEvent`, `DiscordAPIErrorEvent`). Agent orchestration layers subscribe to these events to update state or trigger follow-up actions.
4. **Agent Actions** – `AgentActionCommand` allows `llmgine` agents to request non-standard actions. The runtime forwards these requests to a user-provided async handler and publishes an `ActionResultEvent` that contains the handler’s outcome.

This design keeps the Discord-facing code isolated within the framework while `llmgine` continues to orchestrate agent behavior, tool selection, and higher-level workflows.

## Testing Strategy

### Layered Environment Configuration

- **`testing/env_manager.py`** introduces `DotenvManager`, which merges environment values from the workspace root, package-level `.env` files, and an optional custom dotenv path. The merge order ensures `.env.local` and live environment variables override defaults while preventing duplicate loads.
- `find_workspace_root()` discovers the repository root by walking up to the first directory containing `.git`, allowing tests and CLI tooling to resolve shared `.env` files without hard-coding paths.

### Live Configuration Loading

- **`testing/config.py`** provides `load_live_test_config()`, which consumes the layered dotenv context and validates required keys such as `DISCORD_TEST_BOT_TOKEN`. It supports optional mappings for `DISCORD_TEST_CHANNELS` and `DISCORD_TEST_DM_TARGETS`, parsed from comma-separated or JSON payloads. Configuration errors raise `LiveDiscordTestError` so pytest and CLI commands can surface actionable messages.

### Live Discord Harness

- **`testing/harness.py`** implements `LiveDiscordTestHarness`, an async context manager that spins up a dedicated `discord.Client` on its own event loop. To cooperate with pytest's strict asyncio mode, all Discord API calls are delegated back to the client loop via `_run_on_client_loop()` using `asyncio.run_coroutine_threadsafe`.
- The harness exposes high-level helpers (`send_message`, `send_dm`, `fetch_recent_messages`, `cleanup_messages`, `create_runtime`) so tests and manual scripts can exercise the framework without re-implementing Discord plumbing.

### Pytest Suite

- **`tests/test_env_manager.py`** covers the dotenv layering logic, required layer enforcement, workspace discovery, and the live configuration loader.
- **`tests/test_live_harness.py`** is marked with `@pytest.mark.live` and `loop_scope="session"` to ensure all live operations share the harness’ event loop. The suite verifies channel messaging, history fetching, DM flows, interactive embeds/buttons, and end-to-end message bus execution. Tests skip automatically if the requisite `DISCORD_TEST_*` variables are missing, preventing unintentional live calls during CI.

Run subsets with:

```bash
uv run --package casting-discord-framework pytest libs/discord/framework/tests/test_env_manager.py
uv run --package casting-discord-framework pytest libs/discord/framework/tests/test_live_harness.py -m live
```

### CLI Verification Tooling

- **`testing/runner.py`** powers the `discord-live-test` entry point registered in `pyproject.toml`. The CLI shares the same config loader and harness, offering:
  - `verify` – sends a timestamped message, verifies it appears in recent history, and optionally cleans it up.
  - `send-message` – sends to a configured channel alias or explicit ID and can delete the message afterward.
  - `send-dm` – sends and optionally deletes a direct message to a configured alias or user ID.
- All commands accept `--dotenv` to point at a custom configuration layer if the default workspace/package `.env` files are insufficient.

### Required Environment Keys

To run the live suite or CLI, provide the following in workspace or package `.env` files (or export them in the shell):

- `DISCORD_TEST_BOT_TOKEN` – bot token with permissions to access the target guild/channels.
- `DISCORD_TEST_GUILD_ID` – optional default guild scope.
- `DISCORD_TEST_DEFAULT_CHANNEL` – fallback channel ID used when no alias is specified.
- `DISCORD_TEST_CHANNELS` – optional alias mapping (`alias=channel_id` comma list or JSON object).
- `DISCORD_TEST_DM_TARGETS` – optional DM alias mapping.
- `DISCORD_TEST_READY_TIMEOUT` – optional float specifying the client readiness timeout (default `20`).
- `DISCORD_TEST_DOTENV` – optional path to an additional dotenv file consumed at load time.

## Recommended Workflow

1. Populate workspace/package `.env` files with `DISCORD_TEST_*` credentials (see `.env.example`).
2. Run unit coverage with `uv run --package casting-discord-framework pytest libs/discord/framework/tests/test_env_manager.py` to confirm environment layering works.
3. Execute live integration tests via `uv run --package casting-discord-framework pytest libs/discord/framework/tests/test_live_harness.py -m live` when you have Discord access.
4. Use `uv run discord-live-test verify` (or the other subcommands) for manual checks before deploying new handlers or when validating credentials in CI environments.

With these components, the Discord framework delivers a clear contract between Discord, `llmgine`, and the surrounding Cast systems while offering reproducible tooling for configuration and live validation.
