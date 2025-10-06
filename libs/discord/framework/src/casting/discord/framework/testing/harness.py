from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable
from contextlib import suppress
from typing import TypeVar

import discord

from ..api import DiscordAgentAPI, SendResult
from ..models import MessageInfo, OutboundMessage
from ..runtime import DiscordAgentRuntime
from .config import LiveDiscordTestConfig, LiveDiscordTestError
from llmgine.bus.bus import MessageBus


def _default_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    intents.dm_messages = True
    intents.guild_messages = True
    return intents


T = TypeVar("T")


class LiveDiscordTestHarness:
    """Utility for running live integration tests against Discord."""

    def __init__(
        self,
        config: LiveDiscordTestConfig,
        *,
        intents: discord.Intents | None = None,
    ) -> None:
        self.config = config
        self._intents = intents or _default_intents()
        self.client = discord.Client(intents=self._intents)
        self.api = DiscordAgentAPI(self.client)
        self._ready = asyncio.Event()
        self._start_task: asyncio.Task[None] | None = None

        @self.client.event
        async def on_ready() -> None:  # type: ignore[misc]
            self._ready.set()

    async def __aenter__(self) -> "LiveDiscordTestHarness":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def start(self) -> None:
        if self._start_task is not None:
            return
        loop = asyncio.get_running_loop()
        self._start_task = loop.create_task(self._run_client())
        try:
            await self._wait_until_ready(timeout=self.config.ready_timeout)
        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        if self.client.is_closed():
            await self._await_start_task()
            return
        await self.client.close()
        await self._await_start_task()

    async def _run_client(self) -> None:
        try:
            await self.client.start(self.config.bot_token)
        except Exception:
            self._ready.set()
            raise
        finally:
            self._ready.set()

    async def _await_start_task(self) -> None:
        if self._start_task is None:
            return
        task = self._start_task
        self._start_task = None
        with suppress(asyncio.CancelledError):
            await task

    async def _wait_until_ready(self, *, timeout: float) -> None:
        if self._ready.is_set():
            return
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while not self._ready.is_set():
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise asyncio.TimeoutError("Discord client failed to become ready before timeout")
            await asyncio.sleep(min(0.5, remaining))

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    async def send_message(
        self,
        message: OutboundMessage,
        *,
        channel_alias: str | None = None,
        channel_id: str | None = None,
    ) -> SendResult:
        target_channel = self.config.resolve_channel(alias=channel_alias, channel_id=channel_id)
        return await self._run_on_client_loop(self.api.send_message(target_channel, message))

    async def send_dm(
        self,
        message: OutboundMessage,
        *,
        user_alias: str | None = None,
        user_id: str | None = None,
    ) -> SendResult:
        target_user = self.config.resolve_dm_target(alias=user_alias, user_id=user_id)

        async def runner() -> SendResult:
            user = await self.client.fetch_user(int(target_user))
            dm_channel = user.dm_channel or await user.create_dm()
            return await self.api.send_message(str(dm_channel.id), message)

        return await self._run_on_client_loop(runner())

    async def fetch_recent_messages(
        self,
        *,
        channel_alias: str | None = None,
        channel_id: str | None = None,
        limit: int = 10,
    ) -> list[MessageInfo]:
        target_channel = self.config.resolve_channel(alias=channel_alias, channel_id=channel_id)
        return await self._run_on_client_loop(self.api.fetch_channel_history(target_channel, limit=limit))

    async def cleanup_messages(self, messages: Iterable[SendResult | discord.Message]) -> None:
        items = list(messages)

        async def runner() -> None:
            for item in items:
                message = item.raw if isinstance(item, SendResult) else item
                with suppress(Exception):
                    # await message.delete()
                    print("Skipping")

        await self._run_on_client_loop(runner())

    # ------------------------------------------------------------------
    # Runtime helpers
    # ------------------------------------------------------------------

    def create_runtime(self, bus: MessageBus, *, action_handler=None) -> DiscordAgentRuntime:
        if bus is None:
            raise LiveDiscordTestError("A message bus instance is required to build a runtime")
        runtime = DiscordAgentRuntime(bus=bus, api=self.api, action_handler=action_handler)
        runtime.register()
        return runtime

    async def _run_on_client_loop(self, coro: Awaitable[T]) -> T:
        client_loop = self.client.loop
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if client_loop is current_loop:
            return await coro

        if not client_loop.is_running():
            raise LiveDiscordTestError(
                "Discord client loop is not running; ensure live harness is started on an active event loop"
            )

        future = asyncio.run_coroutine_threadsafe(coro, client_loop)
        try:
            return await asyncio.wrap_future(future)
        except Exception:
            future.cancel()
            raise
