from typing import List

import discord

from casting.apps.discord_bot.config import DiscordBotSettings


def get_discord_config() -> DiscordBotSettings:
    """Return Discord bot settings backed by environment variables."""

    return DiscordBotSettings()


def is_authorized(ctx, settings: DiscordBotSettings) -> bool:
    """Check if a user is authorized to use bot commands."""

    if not settings.allowed_channels and not settings.allowed_roles:
        return True

    if settings.allowed_channels and str(ctx.channel.id) not in settings.allowed_channels:
        return False

    if settings.allowed_roles:
        user_roles = [role.name for role in ctx.author.roles]
        if not any(role in settings.allowed_roles for role in user_roles):
            return False

    return True


def format_response(response: dict, success_emoji: str = "✅", error_emoji: str = "❌") -> str:
    """Format API response for Discord."""

    if not response.get("success", True):
        return f"{error_emoji} **Error:** {response.get('error', 'Unknown error')}"

    if "message" in response:
        return f"{success_emoji} {response['message']}"

    return f"{success_emoji} Operation completed successfully"


def truncate_text(text: str, max_length: int = 1900) -> str:
    """Truncate text for Discord message limits."""

    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_code_block(text: str, language: str = "") -> str:
    """Format text as Discord code block."""

    return f"```{language}\n{truncate_text(text)}\n```"


def format_git_log(commits: List[str]) -> str:
    """Format git log for Discord display."""

    if not commits:
        return "No commits found"

    formatted = "**Recent Commits:**\n"
    for commit in commits[:10]:  # Limit to 10 commits
        formatted += f"• `{commit}`\n"

    return formatted


def format_git_status(status_data: dict) -> str:
    """Format git status for Discord display."""

    if status_data.get("clean", False):
        return "✅ **Working tree clean**"

    short_status = status_data.get("short_status", [])
    if not short_status:
        return "ℹ️ **No changes detected**"

    formatted = "**Git Status:**\n"
    for item in short_status[:15]:  # Limit items
        formatted += f"• `{item}`\n"

    if len(short_status) > 15:
        formatted += f"*... and {len(short_status) - 15} more files*\n"

    return formatted


def format_branch_list(branches_data: dict) -> str:
    """Format branch list for Discord display."""

    branches = branches_data.get("branches", [])
    current = branches_data.get("current_branch")

    if not branches:
        return "No branches found"

    formatted = "**Branches:**\n"
    for branch in branches:
        name = branch["name"]
        if branch.get("current", False) or name == current:
            formatted += f"• `{name}` **(current)**\n"
        else:
            formatted += f"• `{name}`\n"

    return formatted
