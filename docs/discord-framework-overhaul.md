# Discord Framework Overhaul

## Summary

- Expanded `casting.discord.framework.models` to cover authors, messages, embeds, components, reactions, interactions, tool calls, and agent action semantics.
- Refactored adapter serializers to produce the richer dataclasses and provide interaction extraction utilities.
- Introduced `DiscordAgentAPI` with helpers for messaging, reactions, history, threads, interactions, and context synthesis.
- Added `DiscordAgentRuntime` to bridge llmgine message bus commands to the API, emitting structured events and error telemetry.
- Added `DiscordToolset` to expose high-level Discord operations as llmgine-compatible async tools.
- Extended protocol command/event definitions for messaging, reactions, history, thread management, and interaction flows.
- Authored async unit tests covering API behaviour and runtime handling.
