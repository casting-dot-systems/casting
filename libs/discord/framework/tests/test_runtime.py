from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

discord = pytest.importorskip("discord")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from casting.discord.framework.api import SendResult
from casting.discord.framework.models import AuthorInfo, MessageInfo, OutboundMessage
from casting.discord.framework.protocol import SendMessageCommand
from casting.discord.framework.runtime import DiscordAgentRuntime


class FakeBus:
    def __init__(self) -> None:
        self.events: list[object] = []

    def register_command_handler(
        self, *_args, **_kwargs
    ) -> None:  # pragma: no cover - registration not used in unit tests
        return None

    async def publish(self, event: object) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_runtime_handle_send_success() -> None:
    bus = FakeBus()
    api = MagicMock()
    message = MessageInfo(author=AuthorInfo(id="1", display_name="Agent"), content="ok", id="55")
    api.send_message = AsyncMock(return_value=SendResult(message=message, raw=MagicMock()))

    runtime = DiscordAgentRuntime(bus=bus, api=api)

    cmd = SendMessageCommand(channel_id="123", message=OutboundMessage(content="hi"))
    result = await runtime._handle_send(cmd)

    assert result.success is True
    assert result.result == message
    assert bus.events, "Expected MessageSentEvent to be published"
