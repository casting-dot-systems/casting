import discord
import asyncio
from discord.ext import commands
from casting.apps.cast.discord.utils.helpers import format_response, format_code_block, truncate_text


class MarkdownCommands(commands.Cog):
    """Markdown file operation commands for Discord bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="md-create", help="Create a new markdown file")
    async def create_markdown(self, ctx, filename: str, *, content: str = ""):
        """Create a new markdown file or append to existing file"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        # Remove .md extension if provided (will be added by API)
        if filename.endswith(".md"):
            filename = filename[:-3]

        async with ctx.typing():
            response = await self.bot.api_client.create_markdown(filename, content)

        result_msg = format_response(response)
        if response.get("success", True):
            # Check if file already existed
            if response.get("file_existed", False):
                result_msg += f"\n📄 **File `{response.get('filename')}` already existed - content has been appended**"
            else:
                result_msg += f"\n📎 **File created:** `{response.get('filename', filename + '.md')}`"

            if content:
                action_text = "appended" if response.get("file_existed", False) else "added"
                result_msg += f"\n📝 **Content {action_text}:**\n{format_code_block(truncate_text(content, 500), 'md')}"

        await ctx.send(result_msg)

    @commands.command(name="md-read", help="Read content from a markdown file")
    async def read_markdown(self, ctx, filename: str):
        """Read content from a markdown file"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        # Remove .md extension if provided
        if filename.endswith(".md"):
            filename = filename[:-3]

        async with ctx.typing():
            response = await self.bot.api_client.read_markdown(filename)

        if not response.get("success", True):
            if response.get("error") == "file_not_found":
                await ctx.send(
                    f"📄❌ **File `{response.get('filename', filename + '.md')}` does not exist**\n\n💡 **Tip:** Use `/md-list` to see available files or `/md-create {filename}` to create it."
                )
            else:
                await ctx.send(format_response(response))
            return

        content = response.get("content", "")
        filename_display = response.get("filename", filename)

        if not content:
            await ctx.send(f"📝 **File `{filename_display}` exists but is empty**")
            return

        embed = discord.Embed(
            title=f"📝 {filename_display}", description=format_code_block(content, "md"), color=discord.Color.blue()
        )
        embed.set_footer(text=f"File size: {len(content)} characters")
        await ctx.send(embed=embed)

    @commands.command(name="md-update", help="Update content in a markdown file")
    async def update_markdown(self, ctx, filename: str, *, content: str):
        """Update content in a markdown file (creates if doesn't exist)"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        # Remove .md extension if provided
        if filename.endswith(".md"):
            filename = filename[:-3]

        async with ctx.typing():
            response = await self.bot.api_client.update_markdown(filename, content)

        result_msg = format_response(response)
        if response.get("success", True):
            # Check if file had to be created instead of updated
            if not response.get("file_existed", True):
                result_msg += f"\n⚠️ **Warning:** File `{response.get('filename')}` did not exist and was created"
                result_msg += f"\n📎 **File created:** `{response.get('filename')}`"
            else:
                result_msg += f"\n📝 **File updated:** `{response.get('filename')}`"

            result_msg += f"\n📄 **Content preview:**\n{format_code_block(truncate_text(content, 500), 'md')}"

        await ctx.send(result_msg)

    @commands.command(name="md-delete", help="Delete a markdown file")
    async def delete_markdown(self, ctx, filename: str):
        """Delete a markdown file"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        # Remove .md extension if provided
        if filename.endswith(".md"):
            filename = filename[:-3]

        # Simple confirmation message
        confirm_msg = await ctx.send(
            f"⚠️ **Are you sure you want to delete `{filename}.md`?**\n\nReact with ✅ to confirm or ❌ to cancel. (30s timeout)"
        )

        # Add reactions
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "✅":
                async with ctx.typing():
                    response = await self.bot.api_client.delete_markdown(filename)

                if not response.get("success", True):
                    if response.get("error") == "file_not_found":
                        await ctx.send(
                            f"📄❌ **File `{response.get('filename', filename + '.md')}` does not exist**\n\n💡 **Tip:** Use `/md-list` to see available files."
                        )
                    else:
                        await ctx.send(format_response(response))
                else:
                    await ctx.send(f"✅ **File `{response.get('filename')}` deleted successfully**")
            else:
                await ctx.send("❌ **Deletion cancelled**")

        except asyncio.TimeoutError:
            await ctx.send("⏰ **Confirmation timeout - deletion cancelled**")

    @commands.command(name="md-list", help="List all markdown files")
    async def list_markdown(self, ctx):
        """List all markdown files"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.list_markdown()

        if not response.get("success", True):
            await ctx.send(format_response(response))
            return

        files = response.get("files", [])
        if not files:
            await ctx.send("📝 **No markdown files found**")
            return

        file_list = "\n".join([f"• `{file}`" for file in files[:20]])  # Limit to 20 files
        if len(files) > 20:
            file_list += f"\n*... and {len(files) - 20} more files*"

        embed = discord.Embed(title="📝 Markdown Files", description=file_list, color=discord.Color.green())
        embed.set_footer(text=f"Total: {len(files)} files")
        await ctx.send(embed=embed)

    @commands.command(name="md-append", help="Append content to an existing markdown file")
    async def append_markdown(self, ctx, filename: str, *, content: str):
        """Append content to an existing markdown file"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        # Remove .md extension if provided
        if filename.endswith(".md"):
            filename = filename[:-3]

        async with ctx.typing():
            # First read the existing content
            read_response = await self.bot.api_client.read_markdown(filename)

            if not read_response.get("success", True):
                if read_response.get("error") == "file_not_found":
                    await ctx.send(
                        f"📄❌ **File `{read_response.get('filename', filename + '.md')}` does not exist**\n\n💡 **Tip:** Use `/md-create {filename}` to create it first, or use `/md-list` to see available files."
                    )
                else:
                    await ctx.send(f"❌ **Cannot append to file:** {read_response.get('message', 'Unknown error')}")
                return

            existing_content = read_response.get("content", "")
            new_content = existing_content + "\n" + content if existing_content else content

            # Update with combined content
            update_response = await self.bot.api_client.update_markdown(filename, new_content)

        result_msg = format_response(update_response)
        if update_response.get("success", True):
            result_msg += f"\n📝 **Appended content:**\n{format_code_block(truncate_text(content, 500), 'md')}"

        await ctx.send(result_msg)
