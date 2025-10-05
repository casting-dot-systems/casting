from __future__ import annotations

from typing import Any, Optional, Sequence

import discord

from ..models import ActionRow, AttachmentInfo, AuthorInfo, ButtonComponent, ChannelInfo, ChannelType, ChatContext
from ..models import ComponentEmoji, EmojiInfo, EmbedAuthor, EmbedField, EmbedFooter, EmbedInfo, GuildInfo
from ..models import InteractionContext, InteractionOption, InteractionResolvedData, InteractionType, MessageInfo
from ..models import MessageReference, MessageType, ReactionInfo, SelectMenuComponent, SelectOption, TextInputComponent


def to_author_info(user: discord.abc.User) -> AuthorInfo:
    display = getattr(user, "display_name", None) or getattr(user, "global_name", None) or user.name
    username = getattr(user, "name", None) or getattr(user, "username", None)
    avatar_url = None
    avatar = getattr(user, "avatar", None)
    if avatar is not None and hasattr(avatar, "url"):
        avatar_url = avatar.url
    return AuthorInfo(
        id=str(user.id),
        display_name=str(display),
        username=str(username) if username else None,
        global_name=getattr(user, "global_name", None),
        bot=getattr(user, "bot", False),
        avatar_url=avatar_url,
    )


def to_channel_info(channel: discord.abc.GuildChannel | discord.DMChannel | discord.Thread) -> ChannelInfo:
    if isinstance(channel, discord.Thread):
        return ChannelInfo(
            id=str(channel.id),
            name=channel.name,
            type=ChannelType.THREAD,
            parent_id=str(channel.parent_id) if channel.parent_id else None,
            is_nsfw=getattr(channel, "is_nsfw", False),
        )
    if isinstance(channel, discord.DMChannel):
        recipient = getattr(channel, "recipient", None)
        name = f"DM with {recipient.display_name}" if recipient else "DM"
        return ChannelInfo(id=str(channel.id), name=name, type=ChannelType.DM)
    name = getattr(channel, "name", "unknown")
    channel_type = getattr(channel, "type", None)
    mapped_type = ChannelType.TEXT
    if channel_type is not None:
        try:
            mapped_type = ChannelType(channel_type.name.lower())  # type: ignore[arg-type]
        except (ValueError, AttributeError):
            mapped_type = ChannelType.TEXT
    topic = getattr(channel, "topic", None)
    parent_id = getattr(channel, "category_id", None)
    nsfw = getattr(channel, "is_nsfw", False)
    return ChannelInfo(
        id=str(getattr(channel, "id", "unknown")),
        name=str(name),
        type=mapped_type,
        topic=topic,
        parent_id=str(parent_id) if parent_id else None,
        is_nsfw=bool(nsfw),
    )


def to_guild_info(guild: Optional[discord.Guild]) -> GuildInfo:
    if guild is None:
        return GuildInfo(id=None, name=None)
    icon = None
    if guild.icon:
        icon = guild.icon.url
    return GuildInfo(id=str(guild.id), name=guild.name, icon_url=icon)


def _to_component_emoji(emoji: discord.PartialEmoji | str | None) -> Optional[ComponentEmoji]:
    if emoji is None:
        return None
    if isinstance(emoji, str):
        return ComponentEmoji(name=emoji)
    return ComponentEmoji(name=emoji.name or "", id=str(emoji.id) if emoji.id else None, animated=emoji.animated)


def _to_button(component: Any) -> ButtonComponent:
    return ButtonComponent(
        label=component.label,
        style=component.style.name.lower() if hasattr(component.style, "name") else str(component.style),
        custom_id=component.custom_id,
        url=component.url,
        disabled=component.disabled,
        emoji=_to_component_emoji(component.emoji),
    )


def _to_select_menu(component: Any) -> SelectMenuComponent:
    options = [
        SelectOption(
            label=opt.label,
            value=opt.value,
            description=opt.description,
            emoji=_to_component_emoji(opt.emoji),
            default=opt.default,
        )
        for opt in component.options
    ]
    custom_id = getattr(component, "custom_id", "") or ""
    return SelectMenuComponent(
        custom_id=custom_id,
        options=options,
        placeholder=component.placeholder,
        min_values=component.min_values,
        max_values=component.max_values,
        disabled=component.disabled,
    )


def _to_text_input(component: Any) -> TextInputComponent:
    return TextInputComponent(
        custom_id=component.custom_id,
        label=component.label,
        style=component.style.name.lower() if hasattr(component.style, "name") else str(component.style),
        placeholder=component.placeholder,
        default=component.default,
        required=component.required,
        min_length=component.min_length,
        max_length=component.max_length,
    )


def _to_action_rows(components: Sequence[discord.Component]) -> list[ActionRow]:
    rows: list[ActionRow] = []
    for comp in components:
        if comp.type == discord.ComponentType.action_row:
            children: list[object] = []
            for child in comp.children:
                if child.type == discord.ComponentType.button:
                    children.append(_to_button(child))
                elif child.type in {
                    discord.ComponentType.string_select,
                    discord.ComponentType.user_select,
                    discord.ComponentType.role_select,
                    discord.ComponentType.channel_select,
                    discord.ComponentType.mentionable_select,
                }:
                    children.append(_to_select_menu(child))
                elif child.type == discord.ComponentType.text_input:
                    children.append(_to_text_input(child))
            rows.append(ActionRow(components=children))
    return rows


def _to_embed(embed: discord.Embed) -> EmbedInfo:
    footer = None
    if embed.footer:
        footer = EmbedFooter(text=embed.footer.text, icon_url=embed.footer.icon_url)
    author = None
    if embed.author:
        author = EmbedAuthor(name=embed.author.name, url=embed.author.url, icon_url=embed.author.icon_url)
    fields = [EmbedField(name=f.name, value=f.value, inline=f.inline) for f in embed.fields]
    return EmbedInfo(
        title=embed.title,
        description=embed.description,
        url=embed.url,
        colour=embed.colour.value if embed.colour else None,
        timestamp=embed.timestamp,
        footer=footer,
        author=author,
        fields=fields,
        image_url=embed.image.url if embed.image else None,
        thumbnail_url=embed.thumbnail.url if embed.thumbnail else None,
    )


def _to_reaction(reaction: discord.Reaction) -> ReactionInfo:
    emoji = reaction.emoji
    if isinstance(emoji, discord.PartialEmoji):
        emoji_info = EmojiInfo(name=emoji.name or "", id=str(emoji.id) if emoji.id else None, animated=emoji.animated)
    elif isinstance(emoji, str):
        emoji_info = EmojiInfo(name=emoji)
    else:
        emoji_info = EmojiInfo(name=str(emoji))
    return ReactionInfo(emoji=emoji_info, count=reaction.count or 0)


def _to_message_type(msg: discord.Message) -> MessageType:
    try:
        msg_type = MessageType(msg.type.name.lower())
    except (ValueError, AttributeError):
        msg_type = MessageType.UNKNOWN
    if msg.reference:
        msg_type = MessageType.REPLY
    return msg_type


def to_message_info(msg: discord.Message) -> MessageInfo:
    reference = None
    if msg.reference:
        reference = MessageReference(
            message_id=str(msg.reference.message_id) if msg.reference.message_id else None,
            channel_id=str(msg.reference.channel_id) if msg.reference.channel_id else None,
            guild_id=str(msg.reference.guild_id) if msg.reference.guild_id else None,
            fail_if_not_exists=getattr(msg.reference, "fail_if_not_exists", True),
        )

    embeds = [_to_embed(e) for e in msg.embeds]
    components = _to_action_rows(msg.components)
    reactions = [_to_reaction(r) for r in msg.reactions]

    return MessageInfo(
        author=to_author_info(msg.author),
        content=msg.content,
        id=str(msg.id),
        mentions=[to_author_info(u) for u in msg.mentions],
        attachments=[AttachmentInfo(filename=a.filename, url=a.url, content_type=a.content_type, size=a.size) for a in msg.attachments],
        embeds=embeds,
        components=components,
        reactions=reactions,
        type=_to_message_type(msg),
        created_at=msg.created_at,
        edited_at=msg.edited_at,
        reference=reference,
    )


def to_attachment_info(att: discord.Attachment) -> AttachmentInfo:
    return AttachmentInfo(filename=att.filename, url=att.url, content_type=att.content_type, size=att.size)


def to_interaction_context(interaction: discord.Interaction) -> InteractionContext:
    user = to_author_info(interaction.user)
    channel = to_channel_info(interaction.channel)
    guild = to_guild_info(interaction.guild)

    resolved = InteractionResolvedData()
    if interaction.data and "resolved" in interaction.data:
        resolved_payload = interaction.data["resolved"]
        for user_id, payload in resolved_payload.get("users", {}).items():
            resolved.users[str(user_id)] = AuthorInfo(
                id=str(user_id),
                display_name=payload.get("global_name") or payload.get("username") or payload.get("display_name", ""),
                username=payload.get("username"),
                global_name=payload.get("global_name"),
                bot=payload.get("bot", False),
                avatar_url=None,
            )
        for channel_id, payload in resolved_payload.get("channels", {}).items():
            raw_type = payload.get("type", "text")
            try:
                channel_type = ChannelType(raw_type if isinstance(raw_type, str) else ChannelType(raw_type).value)
            except (ValueError, TypeError):
                channel_type = ChannelType.TEXT
            resolved.channels[str(channel_id)] = ChannelInfo(
                id=str(channel_id),
                name=payload.get("name", ""),
                type=channel_type,
                topic=payload.get("topic"),
            )
        for message_id, payload in resolved_payload.get("messages", {}).items():
            content = payload.get("content", "")
            author_payload = payload.get("author") or {}
            resolved.messages[str(message_id)] = MessageInfo(
                author=AuthorInfo(
                    id=str(author_payload.get("id", "")),
                    display_name=author_payload.get("global_name") or author_payload.get("username") or "Unknown",
                    username=author_payload.get("username"),
                    global_name=author_payload.get("global_name"),
                    bot=author_payload.get("bot", False),
                ),
                content=content,
                id=str(message_id),
            )

    options: list[InteractionOption] = []
    if interaction.data:
        for opt in interaction.data.get("options", []):
            options.append(
                InteractionOption(
                    name=str(opt.get("name", "")),
                    value=opt.get("value"),
                    focused=bool(opt.get("focused", False)),
                )
            )

    return InteractionContext(
        id=str(interaction.id),
        token=interaction.token,
        application_id=str(interaction.application_id),
        type=InteractionType(interaction.type.value),
        user=user,
        channel=channel,
        guild=guild,
        command_name=interaction.command.name if interaction.command else None,
        custom_id=getattr(interaction.data, "custom_id", None) if interaction.data else None,
        message=to_message_info(interaction.message) if interaction.message else None,
        options=options,
        resolved=resolved,
    )


def build_chat_context(
    *,
    message: discord.Message,
    recent: list[discord.Message],
    replied: Optional[discord.Message],
    interaction: Optional[discord.Interaction] = None,
) -> ChatContext:
    mentions = [to_author_info(u) for u in message.mentions]
    attachments = [to_attachment_info(a) for a in message.attachments]
    recent_infos = [to_message_info(m) for m in recent]
    reply_info = to_message_info(replied) if replied else None

    return ChatContext(
        content=message.content,
        author=to_author_info(message.author),
        channel=to_channel_info(message.channel),
        guild=to_guild_info(message.guild),
        mentions=mentions,
        attachments=attachments,
        reply_to=reply_info,
        recent_messages=recent_infos,
        interaction=to_interaction_context(interaction) if interaction else None,
    )


def build_chat_context_from_message(context: ChatContext) -> str:
    result = ""
    result += f"Message to Respond To: {context.content}\n"
    result += f"Author: {context.author.display_name}\n"
    result += f"Channel: {context.channel.name}\n"
    if context.reply_to:
        result += f"Reply to: {context.reply_to.content}\n"
    if context.recent_messages:
        result += "Recent messages:\n"
        for msg in context.recent_messages[-5:]:
            result += f"  - {msg.author.display_name}: {msg.content[:120]}\n"
    if context.attachments:
        result += "Attachments:\n"
        for att in context.attachments:
            result += f"  - {att.filename}: {att.url}\n"
    if context.interaction:
        result += f"Interaction: {context.interaction.type.name} -> {context.interaction.command_name or context.interaction.custom_id}\n"
    return result