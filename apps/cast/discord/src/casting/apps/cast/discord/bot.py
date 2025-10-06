import discord
from discord.ext import commands
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from casting.apps.cast.discord.utils.api_client import APIClient
from casting.apps.cast.discord.utils.helpers import get_discord_config, is_authorized
from casting.apps.cast.discord.commands.git_commands import GitCommands
from casting.apps.cast.discord.commands.markdown_commands import MarkdownCommands


class CastingBot(commands.Bot):
    def __init__(self):
        self.config = get_discord_config()
        self.api_client = APIClient()

        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=self.config["prefix"],
            intents=intents,
            description="Casting API Discord Bot - Git and Markdown Operations",
        )

    async def setup_hook(self):
        """Setup the bot when it starts"""
        await self.add_cog(GitCommands(self))
        await self.add_cog(MarkdownCommands(self))
        print(f"Bot setup complete. Prefix: {self.config['prefix']}")

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"{self.user} has connected to Discord!")
        print(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"for {self.config['prefix']}help")
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ **Command not found.** Use `{self.config['prefix']}help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ **Missing required argument:** {error.param}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ **Command on cooldown.** Try again in {error.retry_after:.2f} seconds.")
        else:
            await ctx.send(f"❌ **An error occurred:** {str(error)}")
            print(f"Command error: {error}")

    def check_authorization(self, ctx):
        """Check if user is authorized to use commands"""
        return is_authorized(ctx, self.config)

    async def close(self):
        """Clean up when bot shuts down"""
        await self.api_client.close()
        await super().close()


def run_bot():
    """Run the Discord bot"""
    config = get_discord_config()

    if not config["token"] or config["token"] == "your_discord_bot_token_here":
        print("❌ Discord bot token not configured. Please set DISCORD_TOKEN in .env file.")
        return

    bot = CastingBot()

    try:
        bot.run(config["token"])
    except discord.LoginFailure:
        print("❌ Invalid Discord bot token. Please check your DISCORD_TOKEN in .env file.")
    except Exception as e:
        print(f"❌ Failed to run bot: {e}")


if __name__ == "__main__":
    run_bot()
