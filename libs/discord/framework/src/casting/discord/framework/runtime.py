from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from llmgine.bus.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.messages.commands import CommandResult

from .api import DiscordAgentAPI
from .models import AgentActionRequest, AgentActionResult
from .protocol import (
    ActionResultEvent,
    AddReactionCommand,
    AgentActionCommand,
    CreateThreadCommand,
    DeferInteractionCommand,
    DeleteMessageCommand,
    DiscordAPIErrorEvent,
    EditInteractionResponseCommand,
    EditMessageCommand,
    FetchChannelHistoryCommand,
    FetchThreadMessagesCommand,
    MessageSentEvent,
    MessagesFetchedEvent,
    RemoveReactionCommand,
    RespondToInteractionCommand,
    SendMessageCommand,
)


ActionHandler = Callable[[AgentActionRequest], Awaitable[AgentActionResult]]


class DiscordAgentRuntime:
    """Registers message bus handlers that bridge engine commands to discord.py."""

    def __init__(
        self,
        bus: MessageBus,
        api: DiscordAgentAPI,
        *,
        action_handler: ActionHandler | None = None,
    ) -> None:
        self._bus = bus
        self._api = api
        self._action_handler = action_handler

    def set_action_handler(self, handler: ActionHandler) -> None:
        self._action_handler = handler

    def register(self, *, session_id: Any | None = None) -> None:
        if session_id is None:
            session_id = SessionID("BUS")

        self._bus.register_command_handler(SendMessageCommand, self._handle_send, session_id=session_id)
        self._bus.register_command_handler(EditMessageCommand, self._handle_edit, session_id=session_id)
        self._bus.register_command_handler(DeleteMessageCommand, self._handle_delete, session_id=session_id)
        self._bus.register_command_handler(AddReactionCommand, self._handle_add_reaction, session_id=session_id)
        self._bus.register_command_handler(RemoveReactionCommand, self._handle_remove_reaction, session_id=session_id)
        self._bus.register_command_handler(
            FetchChannelHistoryCommand, self._handle_fetch_history, session_id=session_id
        )
        self._bus.register_command_handler(FetchThreadMessagesCommand, self._handle_fetch_thread, session_id=session_id)
        self._bus.register_command_handler(CreateThreadCommand, self._handle_create_thread, session_id=session_id)
        self._bus.register_command_handler(
            RespondToInteractionCommand, self._handle_respond_to_interaction, session_id=session_id
        )
        self._bus.register_command_handler(
            DeferInteractionCommand, self._handle_defer_interaction, session_id=session_id
        )
        self._bus.register_command_handler(
            EditInteractionResponseCommand, self._handle_edit_interaction, session_id=session_id
        )
        self._bus.register_command_handler(AgentActionCommand, self._handle_agent_action, session_id=session_id)

    async def _handle_send(self, cmd: SendMessageCommand) -> CommandResult:
        try:
            result = await self._api.send_message(cmd.channel_id, cmd.message)
            await self._bus.publish(
                MessageSentEvent(message=result.message, channel_id=cmd.channel_id, session_id=cmd.session_id)
            )
            return CommandResult(success=True, result=result.message)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("send_message", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_edit(self, cmd: EditMessageCommand) -> CommandResult:
        try:
            updated = await self._api.edit_message(cmd.channel_id, cmd.message_id, cmd.message)
            return CommandResult(success=True, result=updated)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("edit_message", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_delete(self, cmd: DeleteMessageCommand) -> CommandResult:
        try:
            await self._api.delete_message(cmd.channel_id, cmd.message_id)
            return CommandResult(success=True, result=True)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("delete_message", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_add_reaction(self, cmd: AddReactionCommand) -> CommandResult:
        try:
            await self._api.add_reaction(cmd.channel_id, cmd.message_id, cmd.emoji)
            return CommandResult(success=True, result=True)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("add_reaction", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_remove_reaction(self, cmd: RemoveReactionCommand) -> CommandResult:
        try:
            await self._api.remove_reaction(cmd.channel_id, cmd.message_id, cmd.emoji, user_id=cmd.user_id)
            return CommandResult(success=True, result=True)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("remove_reaction", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_fetch_history(self, cmd: FetchChannelHistoryCommand) -> CommandResult:
        try:
            messages = await self._api.fetch_channel_history(
                cmd.channel_id, limit=cmd.limit, before=cmd.before, after=cmd.after
            )
            await self._bus.publish(
                MessagesFetchedEvent(
                    channel_id=cmd.channel_id,
                    messages=messages,
                    fetched_at=datetime.utcnow(),
                    session_id=cmd.session_id,
                )
            )
            return CommandResult(success=True, result=messages)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("fetch_channel_history", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_fetch_thread(self, cmd: FetchThreadMessagesCommand) -> CommandResult:
        try:
            messages = await self._api.fetch_thread_messages(
                cmd.thread_id, limit=cmd.limit, before=cmd.before, after=cmd.after
            )
            await self._bus.publish(
                MessagesFetchedEvent(
                    channel_id=cmd.thread_id,
                    messages=messages,
                    fetched_at=datetime.utcnow(),
                    session_id=cmd.session_id,
                )
            )
            return CommandResult(success=True, result=messages)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("fetch_thread_messages", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_create_thread(self, cmd: CreateThreadCommand) -> CommandResult:
        try:
            thread = await self._api.create_thread(
                cmd.channel_id,
                cmd.name,
                message_id=cmd.message_id,
                auto_archive_minutes=cmd.auto_archive_minutes,
            )
            return CommandResult(success=True, result=thread)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("create_thread", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_respond_to_interaction(self, cmd: RespondToInteractionCommand) -> CommandResult:
        try:
            message = await self._api.respond_to_interaction(
                cmd.token, cmd.message, ephemeral=cmd.ephemeral, followup=cmd.followup
            )
            return CommandResult(success=True, result=message)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("respond_to_interaction", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_defer_interaction(self, cmd: DeferInteractionCommand) -> CommandResult:
        try:
            await self._api.defer_interaction(cmd.token, ephemeral=cmd.ephemeral)
            return CommandResult(success=True, result=True)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("defer_interaction", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_edit_interaction(self, cmd: EditInteractionResponseCommand) -> CommandResult:
        try:
            message = await self._api.edit_interaction_response(cmd.token, cmd.message)
            return CommandResult(success=True, result=message)
        except Exception as exc:  # pragma: no cover - network state
            await self._emit_error("edit_interaction_response", exc, session_id=cmd.session_id)
            return CommandResult(success=False, error=str(exc))

    async def _handle_agent_action(self, cmd: AgentActionCommand) -> CommandResult:
        if self._action_handler is None:
            result = AgentActionResult(success=False, error="No agent action handler registered")
        else:
            try:
                result = await self._action_handler(cmd.request)
            except Exception as exc:  # pragma: no cover - user handler
                await self._emit_error("agent_action", exc, session_id=cmd.session_id)
                result = AgentActionResult(success=False, error=str(exc))

        await self._bus.publish(ActionResultEvent(request=cmd.request, result=result, session_id=cmd.session_id))
        return CommandResult(success=result.success, result=result.data, error=result.error)

    async def _emit_error(self, operation: str, exc: Exception, *, session_id: Any | None) -> None:
        await self._bus.publish(DiscordAPIErrorEvent(operation=operation, detail=str(exc), session_id=session_id))
