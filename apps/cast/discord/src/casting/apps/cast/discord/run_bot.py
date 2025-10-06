#!/usr/bin/env python3
"""
Discord Bot Runner

This script runs the Discord bot for the Casting API project.
Make sure to set your DISCORD_TOKEN in the .env file before running.
"""

from casting.apps.cast.discord.bot import run_bot


def main():
    print("🤖 Starting Casting API Discord Bot...")
    print("Make sure your FastAPI server is running on the configured API_URL")
    print("Press Ctrl+C to stop the bot\n")

    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot crashed: {e}")
        import sys

        sys.exit(1)


if __name__ == "__main__":
    main()
