from __future__ import annotations

from dataclasses import dataclass
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence

from llmgine.llm import SessionID
from llmgine.messages import Command, Event

from .models import (
    AgentActionRequest,
    AgentActionResult,
    ChatContext,
    InteractionContext,
    MessageInfo,
    OutboundMessage,
)


@dataclass(slots=True)
class ProcessMessageCommand(Command):
    """Engine entrypoint: the adapter sends this to your engine via MessageBus().execute()."""
    context: ChatContext | None = None


@dataclass(slots=True)
class StatusEvent(Event):
    """Engine → adapter: publish progress/status for UI."""
    status: str = ""


@dataclass(slots=True)
class PromptRequestCommand(Command):
    """Engine → adapter: request confirmation or extra input from the user."""
    prompt: str = ""
    kind: Literal["yes_no", "text"] = "yes_no"
    timeout_sec: int = 60


@dataclass(slots=True)
class SendMessageCommand(Command):
    """Engine → adapter: send a message to a Discord channel."""

    channel_id: str
    message: OutboundMessage
    session_id: SessionID | None = None


@dataclass(slots=True)
class EditMessageCommand(Command):
    channel_id: str
    message_id: str
    message: OutboundMessage
    session_id: SessionID | None = None


@dataclass(slots=True)
class DeleteMessageCommand(Command):
    channel_id: str
    message_id: str
    session_id: SessionID | None = None


@dataclass(slots=True)
class AddReactionCommand(Command):
    channel_id: str
    message_id: str
    emoji: str
    session_id: SessionID | None = None


@dataclass(slots=True)
class RemoveReactionCommand(Command):
    channel_id: str
    message_id: str
    emoji: str
    user_id: str | None = None
    session_id: SessionID | None = None


@dataclass(slots=True)
class FetchChannelHistoryCommand(Command):
    channel_id: str
    limit: int = 50
    before: str | None = None
    after: str | None = None
    session_id: SessionID | None = None


@dataclass(slots=True)
class FetchThreadMessagesCommand(Command):
    thread_id: str
    limit: int = 50
    before: str | None = None
    after: str | None = None
    session_id: SessionID | None = None


@dataclass(slots=True)
class CreateThreadCommand(Command):
    channel_id: str
    name: str
    message_id: str | None = None
    auto_archive_minutes: int | None = None
    session_id: SessionID | None = None


@dataclass(slots=True)
class AgentActionCommand(Command):
    """Engine → adapter request to execute a higher level action (e.g. modal)."""

    request: AgentActionRequest
    session_id: SessionID | None = None


@dataclass(slots=True)
class InteractionEvent(Event):
    """Adapter → engine: surface new Discord interactions to the engine."""

    interaction: InteractionContext
    session_id: SessionID | None = None


@dataclass(slots=True)
class MessagesFetchedEvent(Event):
    channel_id: str
    messages: Sequence[MessageInfo]
    fetched_at: datetime
    session_id: SessionID | None = None


@dataclass(slots=True)
class MessageSentEvent(Event):
    message: MessageInfo
    channel_id: str
    session_id: SessionID | None = None


@dataclass(slots=True)
class ActionResultEvent(Event):
    request: AgentActionRequest
    result: AgentActionResult
    session_id: SessionID | None = None


@dataclass(slots=True)
class DiscordAPIErrorEvent(Event):
    operation: str
    detail: str
    session_id: SessionID | None = None


@dataclass(slots=True)
class RespondToInteractionCommand(Command):
    token: str
    message: OutboundMessage
    ephemeral: bool = False
    followup: bool = False
    session_id: SessionID | None = None


@dataclass(slots=True)
class DeferInteractionCommand(Command):
    token: str
    ephemeral: bool = False
    session_id: SessionID | None = None


@dataclass(slots=True)
class EditInteractionResponseCommand(Command):
    token: str
    message: OutboundMessage
    session_id: SessionID | None = None