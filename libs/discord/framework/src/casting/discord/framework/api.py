from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import discord

from .discord_adapter.context import (
    to_author_info,
    to_channel_info,
    to_guild_info,
    to_message_info,
)
from .models import (
    ActionRow,
    AttachmentInfo,
    ButtonComponent,
    ChannelInfo,
    ChatContext,
    ComponentEmoji,
    EmbedInfo,
    GuildInfo,
    MessageInfo,
    MessageReference,
    OutboundMessage,
    SelectMenuComponent,
    SelectOption,
)


@dataclass(slots=True)
class SendResult:
    message: MessageInfo
    raw: discord.Message


class DiscordAgentAPI:
    """High-level wrapper around discord.py exposing ergonomic primitives for agents."""

    def __init__(self, client: discord.Client | discord.AutoShardedClient | discord.ext.commands.Bot) -> None:  # type: ignore[name-defined]
        self._client = client
        self._interaction_cache: dict[str, discord.Interaction] = {}

    # ------------------------------------------------------------------
    # Interaction lifecycle helpers
    # ------------------------------------------------------------------

    def cache_interaction(self, interaction: discord.Interaction) -> None:
        self._interaction_cache[interaction.token] = interaction

    def release_interaction(self, token: str) -> None:
        self._interaction_cache.pop(token, None)

    def get_interaction(self, token: str) -> discord.Interaction | None:
        return self._interaction_cache.get(token)

    # ------------------------------------------------------------------
    # Message operations
    # ------------------------------------------------------------------

    async def send_message(self, channel_id: str, message: OutboundMessage) -> SendResult:
        channel = await self._resolve_messageable(channel_id)
        kwargs = self._build_message_kwargs(message)
        files = kwargs.pop("files", None)
        with ExitStack() as stack:
            if files:
                managed_files = [stack.enter_context(f) for f in files]
                kwargs["files"] = managed_files
            sent = await channel.send(**kwargs)
        return SendResult(message=to_message_info(sent), raw=sent)

    async def edit_message(self, channel_id: str, message_id: str, message: OutboundMessage) -> MessageInfo:
        channel = await self._resolve_messageable(channel_id)
        discord_message = await channel.fetch_message(int(message_id))
        kwargs = self._build_message_kwargs(message)
        files = kwargs.pop("files", None)
        with ExitStack() as stack:
            if files:
                managed_files = [stack.enter_context(f) for f in files]
                kwargs["attachments"] = managed_files
            updated = await discord_message.edit(**kwargs)
        return to_message_info(updated)

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        channel = await self._resolve_messageable(channel_id)
        message = await channel.fetch_message(int(message_id))
        await message.delete()

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        message = await self._fetch_message(channel_id, message_id)
        await message.add_reaction(emoji)

    async def remove_reaction(self, channel_id: str, message_id: str, emoji: str, user_id: str | None = None) -> None:
        message = await self._fetch_message(channel_id, message_id)
        if user_id is None:
            await message.remove_reaction(emoji, self._client.user)  # type: ignore[arg-type]
        else:
            user = await self._client.fetch_user(int(user_id))
            await message.remove_reaction(emoji, user)

    async def fetch_channel_history(
        self,
        channel_id: str,
        *,
        limit: int = 50,
        before: str | None = None,
        after: str | None = None,
    ) -> list[MessageInfo]:
        channel = await self._resolve_messageable(channel_id)
        history = channel.history(limit=limit, before=self._id_to_object(before), after=self._id_to_object(after))
        messages: list[MessageInfo] = []
        async for message in history:
            messages.append(to_message_info(message))
        return messages

    async def fetch_thread_messages(
        self,
        thread_id: str,
        *,
        limit: int = 50,
        before: str | None = None,
        after: str | None = None,
    ) -> list[MessageInfo]:
        channel = await self._resolve_thread(thread_id)
        history = channel.history(limit=limit, before=self._id_to_object(before), after=self._id_to_object(after))
        messages: list[MessageInfo] = []
        async for message in history:
            messages.append(to_message_info(message))
        return messages

    async def create_thread(
        self,
        channel_id: str,
        name: str,
        *,
        message_id: str | None = None,
        auto_archive_minutes: int | None = None,
    ) -> ChannelInfo:
        channel = await self._resolve_messageable(channel_id)
        if message_id is not None:
            base_message = await channel.fetch_message(int(message_id))
            thread = await base_message.create_thread(name=name, auto_archive_duration=auto_archive_minutes)
        else:
            thread = await channel.create_thread(name=name, auto_archive_duration=auto_archive_minutes)
        return to_channel_info(thread)

    async def respond_to_interaction(
        self,
        token: str,
        message: OutboundMessage,
        *,
        ephemeral: bool = False,
        followup: bool = False,
    ) -> MessageInfo:
        interaction = self._require_interaction(token)
        kwargs = self._build_message_kwargs(message)
        files = kwargs.pop("files", None)
        with ExitStack() as stack:
            if files:
                managed_files = [stack.enter_context(f) for f in files]
                kwargs["files"] = managed_files
            if not interaction.response.is_done() and not followup:
                await interaction.response.send_message(ephemeral=ephemeral, **kwargs)
            else:
                await interaction.followup.send(ephemeral=ephemeral, **kwargs)
        final_message = await interaction.original_response()
        return to_message_info(final_message)

    async def defer_interaction(self, token: str, *, ephemeral: bool = False) -> None:
        interaction = self._require_interaction(token)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=ephemeral)

    async def edit_interaction_response(self, token: str, message: OutboundMessage) -> MessageInfo:
        interaction = self._require_interaction(token)
        original = await interaction.original_response()
        kwargs = self._build_message_kwargs(message)
        files = kwargs.pop("files", None)
        with ExitStack() as stack:
            if files:
                managed_files = [stack.enter_context(f) for f in files]
                kwargs["attachments"] = managed_files
            updated = await original.edit(**kwargs)
        return to_message_info(updated)

    async def create_chat_context(
        self,
        message: discord.Message,
        *,
        history_limit: int = 10,
    ) -> ChatContext:
        replied_message = None
        if message.reference and message.reference.message_id:
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
            except discord.NotFound:  # pragma: no cover - network state dependent
                replied_message = None
        recent: list[discord.Message] = []
        async for past in message.channel.history(limit=history_limit, before=message):
            recent.append(past)
        recent.reverse()
        return ChatContext(
            content=message.content,
            author=to_author_info(message.author),
            channel=to_channel_info(message.channel),
            guild=to_guild_info(message.guild),
            mentions=[to_author_info(u) for u in message.mentions],
            attachments=[_attachment_from_discord(a) for a in message.attachments],
            reply_to=to_message_info(replied_message) if replied_message else None,
            recent_messages=[to_message_info(m) for m in recent],
        )

    # ------------------------------------------------------------------
    # Entity helpers
    # ------------------------------------------------------------------

    async def get_channel_info(self, channel_id: str) -> ChannelInfo:
        channel = await self._resolve_channel(channel_id)
        return to_channel_info(channel)

    async def get_guild_info(self, guild_id: str) -> GuildInfo:
        guild = await self._client.fetch_guild(int(guild_id))
        return to_guild_info(guild)

    async def get_message(self, channel_id: str, message_id: str) -> MessageInfo:
        message = await self._fetch_message(channel_id, message_id)
        return to_message_info(message)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    def _require_interaction(self, token: str) -> discord.Interaction:
        interaction = self.get_interaction(token)
        if interaction is None:
            raise KeyError(f"Unknown interaction token: {token}")
        return interaction

    async def _resolve_messageable(self, channel_id: str) -> discord.abc.MessageableChannel:
        channel = await self._resolve_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            raise TypeError(f"Channel {channel_id} is not messageable")
        return channel

    async def _resolve_thread(self, thread_id: str) -> discord.Thread:
        existing = self._client.get_channel(int(thread_id))
        if isinstance(existing, discord.Thread):
            return existing
        channel = await self._client.fetch_channel(int(thread_id))
        if not isinstance(channel, discord.Thread):
            raise TypeError(f"Channel {thread_id} is not a thread")
        return channel

    async def _resolve_channel(self, channel_id: str) -> discord.abc.GuildChannel | discord.DMChannel | discord.Thread:
        existing = self._client.get_channel(int(channel_id))
        if existing is not None:
            return existing  # type: ignore[return-value]
        channel = await self._client.fetch_channel(int(channel_id))
        return channel  # type: ignore[return-value]

    async def _fetch_message(self, channel_id: str, message_id: str) -> discord.Message:
        channel = await self._resolve_messageable(channel_id)
        return await channel.fetch_message(int(message_id))

    @staticmethod
    def _id_to_object(value: str | None) -> discord.Object | None:
        if value is None:
            return None
        return discord.Object(id=int(value))

    def _build_message_kwargs(self, message: OutboundMessage) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if message.content is not None:
            kwargs["content"] = message.content
        if message.embeds:
            kwargs["embeds"] = [self._build_embed(embed) for embed in message.embeds]
        if message.components:
            kwargs["view"] = self._build_view(message.components)
        if message.tts:
            kwargs["tts"] = True
        if message.reference:
            kwargs["reference"] = self._build_reference(message.reference)
        if message.allowed_mentions is not None:
            kwargs["allowed_mentions"] = discord.AllowedMentions(**message.allowed_mentions)
        if message.suppress_embeds:
            kwargs["suppress_embeds"] = True
        if message.files:
            kwargs["files"] = [self._open_file(path) for path in message.files]
        return kwargs

    @staticmethod
    def _build_reference(reference: MessageReference) -> discord.MessageReference:
        return discord.MessageReference(
            message_id=int(reference.message_id) if reference.message_id else None,
            channel_id=int(reference.channel_id) if reference.channel_id else None,
            guild_id=int(reference.guild_id) if reference.guild_id else None,
            fail_if_not_exists=reference.fail_if_not_exists,
        )

    def _build_embed(self, embed: EmbedInfo) -> discord.Embed:
        discord_embed = discord.Embed(
            title=getattr(embed, "title", None),
            description=getattr(embed, "description", None),
            url=getattr(embed, "url", None),
            colour=getattr(embed, "colour", None),
            timestamp=getattr(embed, "timestamp", None),
        )
        if getattr(embed, "footer", None):
            footer = embed.footer
            discord_embed.set_footer(text=footer.text, icon_url=footer.icon_url)
        if getattr(embed, "author", None):
            author = embed.author
            discord_embed.set_author(name=author.name, url=author.url, icon_url=author.icon_url)
        for field in getattr(embed, "fields", []):
            discord_embed.add_field(name=field.name, value=field.value, inline=field.inline)
        if getattr(embed, "image_url", None):
            discord_embed.set_image(url=embed.image_url)
        if getattr(embed, "thumbnail_url", None):
            discord_embed.set_thumbnail(url=embed.thumbnail_url)
        return discord_embed

    def _build_view(self, rows: Sequence[ActionRow]) -> discord.ui.View:
        view = discord.ui.View(timeout=None)
        for row_index, row in enumerate(rows):
            for component in row.components:
                item = self._component_to_ui(component)
                if item is not None:
                    item.row = row_index
                    view.add_item(item)
        return view

    def _component_to_ui(self, component: object) -> discord.ui.Item | None:
        if isinstance(component, ButtonComponent):
            style = getattr(discord.ButtonStyle, component.style.upper(), discord.ButtonStyle.primary)
            emoji = self._emoji_to_partial(component.emoji)
            return discord.ui.Button(
                label=component.label,
                style=style,
                custom_id=component.custom_id,
                url=component.url,
                disabled=component.disabled,
                emoji=emoji,
            )
        if isinstance(component, SelectMenuComponent):
            options = [self._select_option_to_ui(opt) for opt in component.options]
            return discord.ui.Select(
                custom_id=component.custom_id,
                placeholder=component.placeholder,
                min_values=component.min_values,
                max_values=component.max_values,
                options=options,
                disabled=component.disabled,
            )
        return None

    def _emoji_to_partial(self, emoji: ComponentEmoji | None) -> discord.PartialEmoji | None:
        if emoji is None:
            return None
        return discord.PartialEmoji(name=emoji.name, id=int(emoji.id) if emoji.id else None, animated=emoji.animated)

    def _select_option_to_ui(self, option: SelectOption) -> discord.SelectOption:
        return discord.SelectOption(
            label=option.label,
            value=option.value,
            description=option.description,
            emoji=self._emoji_to_partial(option.emoji),
            default=option.default,
        )

    @staticmethod
    def _open_file(path: str):
        file_path = Path(path)
        file_path = file_path.expanduser()
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        file = file_path.open("rb")
        return discord.File(file, filename=file_path.name)


def _attachment_from_discord(attachment: discord.Attachment) -> Any:
    return AttachmentInfo(
        filename=attachment.filename,
        url=attachment.url,
        content_type=attachment.content_type,
        size=attachment.size,
    )
