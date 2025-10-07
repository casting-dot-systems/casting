from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict

from casting.discord.framework import (
    ChatContext,
    DiscordAgentAPI,
    DiscordAgentRuntime,
    OutboundMessage,
    PromptRequestCommand,
    StatusEvent,
)
from casting.discord.framework.discord_adapter.context import build_chat_context_from_message
from casting.discord.framework.discord_adapter.session_manager import SessionManager, SessionStatus
from casting.discord.framework.models import MessageReference
from llmgine.bus.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.messages.commands import CommandResult

from .tool_chat_engine import (
    DarcyToolChatEngine,
    DarcyToolChatEngineCommand,
    DarcyToolChatEngineStatusEvent,
)


class DarcyEngineBridge:
    """Glue code that connects the Discord adapter to the Darcy tool chat engine."""

    def __init__(
        self,
        sessions: SessionManager,
        *,
        engine_factory: Callable[[str], DarcyToolChatEngine] | None = None,
        build_command: Callable[[ChatContext, str], Any] | None = None,
        prompt_request_cls: type = PromptRequestCommand,
        status_event_cls: type = StatusEvent,
    ) -> None:
        self._sessions = sessions
        self._engine_factory = engine_factory or (lambda sid: DarcyToolChatEngine(session_id=sid))
        self._build_command = build_command or self._default_build_command
        self._prompt_cls = prompt_request_cls
        self._status_evt_cls = status_event_cls
        self._engines: Dict[str, DarcyToolChatEngine] = {}
        self._bus = MessageBus()
        self._api = DiscordAgentAPI(self._sessions.bot)
        self._runtime = DiscordAgentRuntime(bus=self._bus, api=self._api)
        self._registered_sessions: set[str] = set()
        self._bus_started = False

    def _default_build_command(self, ctx: ChatContext, sid: str) -> Any:
        ctx_str = build_chat_context_from_message(ctx)
        return DarcyToolChatEngineCommand(session_id=SessionID(sid), prompt=ctx_str)

    def register_handlers(self, session_id: str) -> None:
        bus = self._bus
        sid_key = SessionID(session_id)

        engine = self._engine_factory(session_id)
        self._engines[session_id] = engine

        if session_id not in self._registered_sessions:
            self._runtime.register(session_id=sid_key)
            self._registered_sessions.add(session_id)

        if hasattr(bus, "register_command_handler"):
            bus.register_command_handler(
                DarcyToolChatEngineCommand,
                engine.handle_command,
                session_id=sid_key,
            )  # type: ignore[attr-defined]

        if not self._bus_started:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(bus.start())
                self._bus_started = True
            except RuntimeError:
                pass

        if hasattr(bus, "register_command_handler"):

            async def _prompt_handler(cmd: Any) -> Any:
                if getattr(cmd, "session_id", None) not in (session_id, sid_key):
                    return type("R", (), {"success": False, "result": None, "error": "wrong session"})()
                prompt = getattr(cmd, "prompt", "")
                kind = getattr(cmd, "kind", "yes_no")
                timeout = getattr(cmd, "timeout_sec", 60)
                value = await self._sessions.request_input(session_id, prompt, kind, timeout)
                return type("R", (), {"success": True, "result": value, "error": None})()

            bus.register_command_handler(self._prompt_cls, _prompt_handler, session_id=sid_key)  # type: ignore[attr-defined]

        if hasattr(bus, "register_event_handler"):

            async def _status_handler(evt: Any) -> None:
                if getattr(evt, "session_id", None) not in (session_id, sid_key):
                    return
                status_text = getattr(evt, "status", "")
                await self._sessions.update_status(
                    session_id,
                    SessionStatus.PROCESSING,
                    status_text or None,
                )

            bus.register_event_handler(self._status_evt_cls, _status_handler, session_id=sid_key)  # type: ignore[attr-defined]
            bus.register_event_handler(
                DarcyToolChatEngineStatusEvent,
                _status_handler,
                session_id=sid_key,
            )  # type: ignore[attr-defined]

    async def run_engine(
        self, context: ChatContext, session_id: str, *, max_length: int | None = None
    ) -> CommandResult:
        bus = self._bus
        cmd = self._build_command(context, session_id)
        sid_key = SessionID(session_id)
        session_ctx = getattr(bus, "session", None)

        async def _execute_command() -> CommandResult:
            print(f"Executing command: {cmd}")
            return await bus.execute(cmd)  # type: ignore[arg-type]

        if callable(session_ctx):
            async with session_ctx(session_id):  # type: ignore[misc]
                engine_result = await _execute_command()
        else:
            engine_result = await _execute_command()

        session = self._sessions.active.get(session_id)
        if session is None:
            return engine_result

        channel_id = getattr(session.channel, "id", None)
        if channel_id is None:
            return engine_result

        origin_message = session.data.get("origin_message")
        reference = None
        if origin_message is not None:
            reference = MessageReference(
                message_id=str(getattr(origin_message, "id", "")),
                channel_id=str(getattr(origin_message.channel, "id", "")),
                guild_id=str(getattr(getattr(origin_message, "guild", None), "id", "")) or None,
            )

        if engine_result.success:
            payload = engine_result.result
            if payload is None:
                content = "✅ Done."
            else:
                content = str(payload)
            if max_length is not None:
                content = content[:max_length]
            outbound = OutboundMessage(content=content, reference=reference)
            try:
                await self._api.send_message(str(channel_id), outbound)
            except Exception as exc:  # pragma: no cover - network state
                return CommandResult(
                    success=False,
                    error=str(exc) or "Failed to send response",
                    result=engine_result.result,
                    session_id=sid_key,
                    metadata={"delivery_failed": True},
                )
        else:
            error_text = engine_result.error or "Unknown error"
            content = f"❌ Error: {error_text}"
            if max_length is not None:
                content = content[:max_length]
            outbound = OutboundMessage(content=content, reference=reference)
            try:
                await self._api.send_message(str(channel_id), outbound)
            except Exception:
                pass

        if hasattr(bus, "unregister_session_handlers"):
            bus.unregister_session_handlers(sid_key)  # type: ignore[attr-defined]
        self._registered_sessions.discard(session_id)
        self._engines.pop(session_id, None)
        return engine_result
