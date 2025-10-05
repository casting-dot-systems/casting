from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from llmgine.bus.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.messages.commands import CommandResult

from .models import MessageReference, OutboundMessage
from .protocol import (
    AddReactionCommand,
    CreateThreadCommand,
    FetchChannelHistoryCommand,
    RemoveReactionCommand,
    RespondToInteractionCommand,
    SendMessageCommand,
)


class DiscordToolset:
    """Convenience methods to register Discord operations as llmgine tools."""

    def __init__(self, bus: MessageBus, *, session_id: SessionID | None = None) -> None:
        self._bus = bus
        self._session_id = session_id

    async def send_message(self, channel_id: str, content: str) -> dict[str, Any]:
        payload = OutboundMessage(content=content)
        cmd = SendMessageCommand(channel_id=channel_id, message=payload, session_id=self._session_id)
        result = await self._execute(cmd)
        return _to_plain(result)

    async def reply_to_message(self, channel_id: str, message_id: str, content: str) -> dict[str, Any]:
        reference = MessageReference(message_id=message_id, channel_id=channel_id)
        payload = OutboundMessage(content=content, reference=reference)
        cmd = SendMessageCommand(channel_id=channel_id, message=payload, session_id=self._session_id)
        result = await self._execute(cmd)
        return _to_plain(result)

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> dict[str, Any]:
        cmd = AddReactionCommand(
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
            session_id=self._session_id,
        )
        result = await self._execute(cmd)
        return {"success": result}

    async def remove_reaction(self, channel_id: str, message_id: str, emoji: str, user_id: str | None = None) -> dict[str, Any]:
        cmd = RemoveReactionCommand(
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
            user_id=user_id,
            session_id=self._session_id,
        )
        result = await self._execute(cmd)
        return {"success": result}

    async def fetch_channel_history(self, channel_id: str, limit: int = 20) -> list[dict[str, Any]]:
        cmd = FetchChannelHistoryCommand(channel_id=channel_id, limit=limit, session_id=self._session_id)
        messages = await self._execute(cmd)
        return _to_plain(messages)

    async def create_thread(
        self,
        channel_id: str,
        name: str,
        *,
        message_id: str | None = None,
        auto_archive_minutes: int | None = None,
    ) -> dict[str, Any]:
        cmd = CreateThreadCommand(
            channel_id=channel_id,
            name=name,
            message_id=message_id,
            auto_archive_minutes=auto_archive_minutes,
            session_id=self._session_id,
        )
        thread = await self._execute(cmd)
        return _to_plain(thread)

    async def respond_to_interaction(
        self,
        token: str,
        content: str,
        *,
        ephemeral: bool = False,
        followup: bool = False,
    ) -> dict[str, Any]:
        payload = OutboundMessage(content=content)
        cmd = RespondToInteractionCommand(
            token=token,
            message=payload,
            ephemeral=ephemeral,
            followup=followup,
            session_id=self._session_id,
        )
        message = await self._execute(cmd)
        return _to_plain(message)

    async def _execute(self, cmd: Any) -> Any:
        result: CommandResult = await self._bus.execute(cmd)
        if not result.success:
            raise RuntimeError(result.error or "Discord command failed")
        return result.result


def _to_plain(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(val) for key, val in value.items()}
    if is_dataclass(value):
        return _to_plain(asdict(value))
    if hasattr(value, "value") and not isinstance(value, str):
        return getattr(value, "value")
    return value
