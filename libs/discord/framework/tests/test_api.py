from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

discord = pytest.importorskip("discord")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import casting.discord.framework.api as api_module
from casting.discord.framework.api import DiscordAgentAPI
from casting.discord.framework.models import (
    ActionRow,
    ButtonComponent,
    EmbedField,
    EmbedFooter,
    EmbedInfo,
    OutboundMessage,
)


@pytest.mark.asyncio
async def test_send_message_builds_components(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_channel = AsyncMock()
    fake_message = MagicMock()
    fake_channel.send.return_value = fake_message

    monkeypatch.setattr(api_module, "to_message_info", lambda _: {"ok": True})

    client = MagicMock()
    api = DiscordAgentAPI(client)
    monkeypatch.setattr(api, "_resolve_messageable", AsyncMock(return_value=fake_channel))

    embed = EmbedInfo(
        title="Greetings",
        description="Payload",
        fields=[EmbedField(name="Field", value="Value", inline=True)],
        footer=EmbedFooter(text="Footer"),
    )
    button = ButtonComponent(label="Click", custom_id="btn1")
    outbound = OutboundMessage(content="hello", embeds=[embed], components=[ActionRow(components=[button])])

    result = await api.send_message("123", outbound)

    assert result.message == {"ok": True}
    fake_channel.send.assert_awaited()
    kwargs = fake_channel.send.await_args.kwargs
    assert kwargs["content"] == "hello"
    assert len(kwargs["embeds"]) == 1
    view = kwargs["view"]
    assert isinstance(view, discord.ui.View)
    items = list(view.children)
    assert items and isinstance(items[0], discord.ui.Button)


@pytest.mark.asyncio
async def test_respond_to_interaction_initial_response(monkeypatch: pytest.MonkeyPatch) -> None:
    api = DiscordAgentAPI(MagicMock())
    monkeypatch.setattr(api_module, "to_message_info", lambda _: {"response": True})

    response = SimpleNamespace(
        is_done=lambda: False,
        send_message=AsyncMock(),
        defer=AsyncMock(),
    )
    interaction = MagicMock()
    interaction.token = "tok"
    interaction.response = response
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())

    api.cache_interaction(interaction)

    outbound = OutboundMessage(content="pong")
    result = await api.respond_to_interaction("tok", outbound)

    response.send_message.assert_awaited()
    interaction.followup.send.assert_not_called()
    assert result == {"response": True}


@pytest.mark.asyncio
async def test_respond_to_interaction_followup(monkeypatch: pytest.MonkeyPatch) -> None:
    api = DiscordAgentAPI(MagicMock())
    monkeypatch.setattr(api_module, "to_message_info", lambda _: {"response": True})

    response = SimpleNamespace(
        is_done=lambda: True,
        send_message=AsyncMock(),
        defer=AsyncMock(),
    )
    interaction = MagicMock()
    interaction.token = "tok"
    interaction.response = response
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())

    api.cache_interaction(interaction)

    outbound = OutboundMessage(content="followup")
    await api.respond_to_interaction("tok", outbound, followup=True)

    interaction.followup.send.assert_awaited()
