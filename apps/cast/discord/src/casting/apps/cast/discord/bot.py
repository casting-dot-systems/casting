import asyncio
import discord
from discord.ext import commands

from casting.apps.discord_bot.config import DiscordBotSettings
from casting.platform.config import bootstrap_env, find_app_dir

from casting.apps.cast.discord.utils.api_client import APIClient
from casting.apps.cast.discord.utils.helpers import get_discord_config, is_authorized
from casting.apps.cast.discord.commands.git_commands import GitCommands
from casting.apps.cast.discord.commands.markdown_commands import MarkdownCommands

APP_DIR = find_app_dir(__file__)
bootstrap_env(app_dir=APP_DIR)


class CastingBot(commands.Bot):
    def __init__(self, settings: DiscordBotSettings | None = None):
        self.settings = settings or get_discord_config()
        self.api_client = APIClient(self.settings)

        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=self.settings.command_prefix,
            intents=intents,
            description="Casting API Discord Bot - Git and Markdown Operations",
        )

    async def setup_hook(self):
        """Setup the bot when it starts"""
        await self.add_cog(GitCommands(self))
        await self.add_cog(MarkdownCommands(self))
        print(f"Bot setup complete. Prefix: {self.settings.command_prefix}")

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"{self.user} has connected to Discord!")
        print(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for {self.settings.command_prefix}help",
        )
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                f"❌ **Command not found.** Use `{self.settings.command_prefix}help` to see available commands."
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ **Missing required argument:** {error.param}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ **Command on cooldown.** Try again in {error.retry_after:.2f} seconds.")
        else:
            await ctx.send(f"❌ **An error occurred:** {str(error)}")
            print(f"Command error: {error}")

    def check_authorization(self, ctx):
        """Check if user is authorized to use commands"""
        return is_authorized(ctx, self.settings)

    async def close(self):
        """Clean up when bot shuts down"""
        await self.api_client.close()
        await super().close()


def run_bot():
    """Run the Discord bot"""
    settings = get_discord_config()

    try:
        token = settings.require_token()
    except ValueError as exc:
        print(f"❌ {exc}")
        return

    bot = CastingBot(settings=settings)

    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Invalid Discord bot token. Please check your DISCORD_TOKEN in .env file.")
    except Exception as exc:
        print(f"❌ Failed to run bot: {exc}")


if __name__ == "__main__":
    run_bot()
