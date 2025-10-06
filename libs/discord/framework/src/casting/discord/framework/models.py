from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional, Sequence


class ChannelType(str, Enum):
    """Subset of Discord channel types relevant to agents."""

    TEXT = "text"
    THREAD = "thread"
    DM = "dm"
    VOICE = "voice"
    CATEGORY = "category"
    STAGE = "stage"
    FORUM = "forum"


class InteractionType(IntEnum):
    """Interaction types supported by Discord."""

    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class MessageType(str, Enum):
    DEFAULT = "default"
    REPLY = "reply"
    SYSTEM = "system"
    THREAD_STARTER = "thread_starter"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class AuthorInfo:
    """Lightweight representation of a Discord user or member."""

    id: str
    display_name: str
    username: Optional[str] = None
    global_name: Optional[str] = None
    bot: bool = False
    avatar_url: Optional[str] = None


@dataclass(slots=True)
class AttachmentInfo:
    filename: str
    url: str
    content_type: Optional[str] = None
    size: Optional[int] = None


@dataclass(slots=True)
class EmojiInfo:
    name: str
    id: Optional[str] = None
    animated: bool = False


@dataclass(slots=True)
class ReactionInfo:
    emoji: EmojiInfo
    count: int
    user_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EmbedField:
    name: str
    value: str
    inline: bool = False


@dataclass(slots=True)
class EmbedFooter:
    text: str
    icon_url: Optional[str] = None


@dataclass(slots=True)
class EmbedAuthor:
    name: str
    url: Optional[str] = None
    icon_url: Optional[str] = None


@dataclass(slots=True)
class EmbedInfo:
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    colour: Optional[int] = None
    timestamp: Optional[datetime] = None
    footer: Optional[EmbedFooter] = None
    author: Optional[EmbedAuthor] = None
    fields: list[EmbedField] = field(default_factory=list)
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass(slots=True)
class ComponentEmoji:
    name: str
    id: Optional[str] = None
    animated: bool = False


@dataclass(slots=True)
class ButtonComponent:
    label: Optional[str] = None
    style: str = "primary"
    custom_id: Optional[str] = None
    url: Optional[str] = None
    disabled: bool = False
    emoji: Optional[ComponentEmoji] = None


@dataclass(slots=True)
class SelectOption:
    label: str
    value: str
    description: Optional[str] = None
    emoji: Optional[ComponentEmoji] = None
    default: bool = False


@dataclass(slots=True)
class SelectMenuComponent:
    custom_id: str
    options: list[SelectOption]
    placeholder: Optional[str] = None
    min_values: int = 1
    max_values: int = 1
    disabled: bool = False


@dataclass(slots=True)
class TextInputComponent:
    custom_id: str
    label: str
    style: str = "short"  # short | paragraph
    placeholder: Optional[str] = None
    default: Optional[str] = None
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass(slots=True)
class ActionRow:
    components: list[object] = field(default_factory=list)


ComponentType = object


@dataclass(slots=True)
class MessageReference:
    message_id: Optional[str] = None
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    fail_if_not_exists: bool = True


@dataclass(slots=True)
class MessageInfo:
    author: AuthorInfo
    content: str
    id: Optional[str] = None
    mentions: list[AuthorInfo] = field(default_factory=list)
    attachments: list[AttachmentInfo] = field(default_factory=list)
    embeds: list[EmbedInfo] = field(default_factory=list)
    components: list[ActionRow] = field(default_factory=list)
    reactions: list[ReactionInfo] = field(default_factory=list)
    type: MessageType = MessageType.DEFAULT
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    reference: Optional[MessageReference] = None


@dataclass(slots=True)
class OutboundMessage:
    """Data required to send or edit a Discord message."""

    content: Optional[str] = None
    embeds: list[EmbedInfo] = field(default_factory=list)
    components: list[ActionRow] = field(default_factory=list)
    tts: bool = False
    suppress_embeds: bool = False
    allowed_mentions: Optional[dict[str, Sequence[str]]] = None
    files: list[str] = field(default_factory=list)
    reference: Optional[MessageReference] = None


@dataclass(slots=True)
class ChannelInfo:
    id: str
    name: str
    type: ChannelType
    topic: Optional[str] = None
    parent_id: Optional[str] = None
    is_nsfw: bool = False


@dataclass(slots=True)
class GuildInfo:
    id: Optional[str]
    name: Optional[str]
    icon_url: Optional[str] = None


@dataclass(slots=True)
class InteractionResolvedData:
    users: dict[str, AuthorInfo] = field(default_factory=dict)
    messages: dict[str, MessageInfo] = field(default_factory=dict)
    channels: dict[str, ChannelInfo] = field(default_factory=dict)


@dataclass(slots=True)
class InteractionOption:
    name: str
    value: Optional[str] = None
    focused: bool = False


@dataclass(slots=True)
class InteractionContext:
    id: str
    token: str
    application_id: str
    type: InteractionType
    user: AuthorInfo
    channel: ChannelInfo
    guild: GuildInfo
    command_name: Optional[str] = None
    custom_id: Optional[str] = None
    message: Optional[MessageInfo] = None
    options: list[InteractionOption] = field(default_factory=list)
    resolved: InteractionResolvedData = field(default_factory=InteractionResolvedData)


@dataclass(slots=True)
class ToolCallInfo:
    id: str
    name: str
    arguments: dict[str, object]
    issued_at: datetime


@dataclass(slots=True)
class ChatContext:
    """Transport-agnostic context a chatbot can use."""

    content: str
    author: AuthorInfo
    channel: ChannelInfo
    guild: GuildInfo
    mentions: list[AuthorInfo] = field(default_factory=list)
    attachments: list[AttachmentInfo] = field(default_factory=list)
    reply_to: Optional[MessageInfo] = None
    recent_messages: list[MessageInfo] = field(default_factory=list)  # chronological
    interaction: Optional[InteractionContext] = None


@dataclass(slots=True)
class AgentActionRequest:
    """Represents an action the agent would like the adapter to perform."""

    description: str
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class AgentActionResult:
    success: bool
    data: Optional[object] = None
    error: Optional[str] = None
