from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

discord = pytest.importorskip("discord")

from llmgine.bus.bus import MessageBus
from llmgine.llm import SessionID

from casting.discord.framework.models import (
    ActionRow,
    ButtonComponent,
    EmbedField,
    EmbedFooter,
    EmbedInfo,
    OutboundMessage,
)
from casting.discord.framework.testing import (
    LiveDiscordTestError,
    LiveDiscordTestHarness,
    load_live_test_config,
)
from casting.discord.framework.protocol import SendMessageCommand


pytestmark = pytest.mark.live


try:
    LIVE_CONFIG = load_live_test_config()
except LiveDiscordTestError as exc:  # pragma: no cover - environment dependent
    pytest.fail(f"Live Discord tests require configuration: {exc}")


@pytest.fixture(scope="session")
def live_config():
    return LIVE_CONFIG


@pytest.fixture(scope="session")
async def live_harness(live_config):
    async with LiveDiscordTestHarness(live_config) as harness:
        yield harness


@pytest.mark.asyncio
async def test_send_and_cleanup_channel_message(live_harness, live_config):
    content = f"[framework-test] {datetime.utcnow().isoformat()}"
    result = await live_harness.send_message(OutboundMessage(content=content))
    assert result.message.content == content

    await live_harness.cleanup_messages([result])


@pytest.mark.asyncio
async def test_fetch_recent_messages_includes_latest(live_harness, live_config):
    content = f"[framework-fetch-test] {datetime.utcnow().isoformat()}"
    result = await live_harness.send_message(OutboundMessage(content=content))

    history = await live_harness.fetch_recent_messages(limit=20)
    assert any(message.content == content for message in history)

    await live_harness.cleanup_messages([result])


@pytest.mark.asyncio
async def test_send_dm_when_configured(live_harness, live_config):
    if not live_config.dm_targets:
        pytest.fail("Configure DISCORD_TEST_DM_TARGETS to exercise DM messaging")

    alias = next(iter(live_config.dm_targets))
    content = f"[framework-dm-test] {datetime.utcnow().isoformat()}"
    result = await live_harness.send_dm(OutboundMessage(content=content), user_alias=alias)

    assert result.message.content == content

    await live_harness.cleanup_messages([result])


@pytest.mark.asyncio
async def test_send_message_with_embed_and_button(live_harness):
    title = "Framework Embed"
    button_id = f"live-btn-{uuid4()}"
    content = f"[framework-embed] {datetime.utcnow().isoformat()}"

    embed = EmbedInfo(
        title=title,
        description="Live harness integration test",
        footer=EmbedFooter(text="integration"),
        fields=[EmbedField(name="Key", value="Value", inline=True)],
    )
    components = [ActionRow(components=[ButtonComponent(label="Acknowledge", custom_id=button_id, style="success")])]

    result = await live_harness.send_message(
        OutboundMessage(content=content, embeds=[embed], components=components)
    )

    assert any(e.title == title for e in result.message.embeds)

    await live_harness.cleanup_messages([result])


@pytest.mark.asyncio
async def test_runtime_send_via_message_bus(live_harness, live_config):
    bus = MessageBus()
    await bus.reset()
    runtime = live_harness.create_runtime(bus)

    await bus.start()
    content = f"[framework-runtime] {datetime.utcnow().isoformat()}"
    command = SendMessageCommand(
        channel_id=live_config.resolve_channel(),
        message=OutboundMessage(content=content),
        session_id=SessionID("live-test"),
    )
    command_result = await bus.execute(command)
    await bus.stop()

    assert command_result.success is True
    assert command_result.result and command_result.result.content == content

    if command_result.result and command_result.result.id:
        await live_harness.api.delete_message(
            live_config.resolve_channel(),
            command_result.result.id,
        )
