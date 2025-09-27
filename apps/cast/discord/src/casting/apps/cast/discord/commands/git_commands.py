import discord
from discord.ext import commands
from casting.apps.cast.discord.utils.helpers import format_response, format_code_block, format_git_log, format_git_status, format_branch_list

class GitCommands(commands.Cog):
    """Git operation commands for Discord bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="git-status", help="Show git repository status")
    async def git_status(self, ctx):
        """Show git repository status"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_status()

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'git' in error_msg.lower() and 'not found' in error_msg.lower():
                await ctx.send("🔧❌ **Git is not installed or not in PATH**\n\n💡 **Tip:** Install git and ensure it's available in your system PATH.")
            else:
                await ctx.send(f"❌ **Git status failed:** {error_msg}")
            return

        status_msg = format_git_status(response)
        embed = discord.Embed(
            title="📋 Git Status",
            description=status_msg,
            color=discord.Color.green() if response.get('clean', False) else discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="git-add", help="Stage all changes for commit")
    async def git_add(self, ctx):
        """Stage all changes (git add .)"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_add()

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'permission denied' in error_msg.lower():
                await ctx.send("🔒❌ **Permission denied**\n\n💡 **Tip:** Check file permissions in the repository.")
            else:
                await ctx.send(f"❌ **Git add failed:** {error_msg}")
            return

        await ctx.send("✅ **All changes staged successfully**")

    @commands.command(name="git-commit", help="Create a commit with staged changes")
    async def git_commit(self, ctx, *, message: str):
        """Commit staged changes with a message"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_commit(
                message=message,
                author_name=str(ctx.author),
                author_email=f"{ctx.author.id}@discord.user"
            )

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'nothing to commit' in response.get('message', '').lower():
                await ctx.send("ℹ️ **Nothing to commit, working tree clean**\n\n💡 **Tip:** Use `/git-status` to see if there are changes to stage.")
            elif 'not configured' in error_msg.lower():
                await ctx.send("⚙️❌ **Git user not configured**\n\n💡 **Tip:** Configure git with your name and email first.")
            else:
                await ctx.send(f"❌ **Commit failed:** {error_msg}")
            return

        # Handle the "nothing to commit" success case
        if 'nothing to commit' in response.get('message', '').lower():
            await ctx.send("ℹ️ **Nothing to commit, working tree clean**")
            return

        result_msg = "✅ **Commit created successfully**"
        if response.get('output'):
            result_msg += f"\n{format_code_block(response['output'])}"

        await ctx.send(result_msg)

    @commands.command(name="git-push", help="Push commits to remote repository")
    async def git_push(self, ctx, remote: str = 'origin', branch: str = None, set_upstream: str = 'false'):
        """Push commits to remote repository"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        set_upstream_bool = set_upstream.lower() in ['true', '1', 'yes']

        async with ctx.typing():
            response = await self.bot.api_client.git_push(remote=remote, branch=branch, set_upstream=set_upstream_bool)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            suggestion = response.get('suggestion', '')

            if 'no upstream branch' in error_msg.lower():
                await ctx.send(f"🔗❌ **No upstream branch set**\n\n💡 **Tip:** Try `/git-push {remote} {branch or 'current'} true` to set upstream.")
            elif 'push rejected' in error_msg.lower():
                await ctx.send("🚫❌ **Push rejected by remote repository**\n\n💡 **Tip:** Check permissions or branch protection rules.")
            elif 'failed to push' in error_msg.lower():
                await ctx.send("🔗❌ **Failed to push - repository may not exist or no access**\n\n💡 **Tip:** Verify remote repository URL and access permissions.")
            elif 'not a git repository' in response.get('detailed_error', '').lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            else:
                await ctx.send(f"❌ **Git push failed:** {error_msg}")

            if suggestion:
                await ctx.send(f"💡 **Suggestion:** {suggestion}")
            return

        result_msg = "✅ **Push completed successfully**"
        if response.get('output'):
            result_msg += f"\n{format_code_block(response['output'])}"

        await ctx.send(result_msg)

    @commands.command(name="git-pull", help="Pull changes from remote repository")
    async def git_pull(self, ctx, remote: str = 'origin', branch: str = None):
        """Pull changes from remote repository"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_pull(remote=remote, branch=branch)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            detailed_error = response.get('detailed_error', '')

            if 'merge conflicts' in error_msg.lower():
                await ctx.send(f"⚠️ **Merge conflicts detected during pull**\n\n💡 **Suggestion:** {response.get('suggestion', 'Resolve conflicts manually')}\n\n🔍 **Use `/git-status` to see conflicted files**")
            elif 'divergent branches' in error_msg.lower():
                await ctx.send(f"🌳❌ **Local and remote branches have diverged**\n\n💡 **Suggestion:** {response.get('suggestion', 'Consider rebasing or merging manually')}")
            elif 'no such remote' in error_msg.lower():
                await ctx.send(f"🔗❌ **Remote '{remote}' does not exist**\n\n💡 **Tip:** Use `/git-remote` to add the remote first.")
            elif 'not a git repository' in detailed_error.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            else:
                await ctx.send(f"❌ **Git pull failed:** {error_msg}")
            return

        result_msg = "✅ **Pull completed successfully**"
        if response.get('output'):
            result_msg += f"\n{format_code_block(response['output'])}"

        await ctx.send(result_msg)

    @commands.command(name="git-log", help="Show commit history")
    async def git_log(self, ctx, limit: int = 10):
        """Show commit history"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        if limit > 20:
            limit = 20  # Limit for Discord message length

        async with ctx.typing():
            response = await self.bot.api_client.git_log(limit=limit)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'does not have any commits yet' in error_msg.lower() or 'your current branch' in error_msg.lower():
                await ctx.send("📜❌ **No commits found**\n\n💡 **Tip:** Make your first commit with `/git-add` and `/git-commit`.")
            else:
                await ctx.send(f"❌ **Git log failed:** {error_msg}")
            return

        commits = response.get('commits', [])
        if not commits:
            await ctx.send("📜 **No commits found in repository**")
            return

        log_msg = format_git_log(commits)
        embed = discord.Embed(
            title="📜 Git Log",
            description=log_msg,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Showing last {limit} commits")
        await ctx.send(embed=embed)

    @commands.command(name="git-merge", help="Merge a branch into current branch")
    async def git_merge(self, ctx, branch_name: str, allow_conflicts: str = 'true'):
        """Merge a branch with interactive conflict resolution"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        allow_conflicts_bool = allow_conflicts.lower() in ['true', '1', 'yes']

        async with ctx.typing():
            response = await self.bot.api_client.git_merge(branch_name, allow_conflicts_bool)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'branch' in error_msg.lower() and 'not found' in error_msg.lower():
                await ctx.send(f"🌳❌ **Branch `{branch_name}` not found**\n\n💡 **Tip:** Use `/git-branches` to see available branches.")
            else:
                await ctx.send(f"❌ **Git merge failed:** {error_msg}")
            return

        # Handle merge conflicts interactively
        if response.get('conflicts', False):
            await self._handle_merge_conflicts(ctx, branch_name)
            return

        # Successful merge
        result_msg = f"✅ **Successfully merged `{branch_name}` into current branch**"
        if 'output' in response:
            result_msg += f"\n{format_code_block(response['output'])}"

        await ctx.send(result_msg)

    async def _handle_merge_conflicts(self, ctx, branch_name: str):
        """Handle merge conflicts interactively"""
        conflict_embed = discord.Embed(
            title="⚠️ Merge Conflicts Detected",
            description=f"There are conflicts when merging `{branch_name}`. How would you like to proceed?",
            color=discord.Color.orange()
        )
        conflict_embed.add_field(
            name="🔄 Auto-Commit Conflicts",
            value="Stage and commit all conflicts as-is",
            inline=False
        )
        conflict_embed.add_field(
            name="🔧 Resolve Conflicts",
            value="Show conflict details and choose resolution",
            inline=False
        )
        conflict_embed.add_field(
            name="❌ Cancel Merge",
            value="Abort the merge operation",
            inline=False
        )

        view = discord.ui.View(timeout=60)

        async def auto_commit_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Only the command user can make this choice.", ephemeral=True)
                return

            await interaction.response.defer()

            # Stage and commit conflicts
            async with ctx.typing():
                add_response = await self.bot.api_client.git_add()
                if add_response.get('success', True):
                    commit_response = await self.bot.api_client.git_commit(
                        f"Merge {branch_name} with conflicts",
                        str(ctx.author),
                        f"{ctx.author.id}@discord.user"
                    )
                    if commit_response.get('success', True):
                        await interaction.followup.send("✅ **Conflicts staged and committed successfully**")
                    else:
                        await interaction.followup.send(f"❌ **Commit failed:** {commit_response.get('message', 'Unknown error')}")
                else:
                    await interaction.followup.send(f"❌ **Staging failed:** {add_response.get('message', 'Unknown error')}")
            view.stop()

        async def resolve_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Only the command user can make this choice.", ephemeral=True)
                return

            await interaction.response.defer()
            await self._show_conflict_resolution(ctx, interaction)
            view.stop()

        async def cancel_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Only the command user can make this choice.", ephemeral=True)
                return

            await interaction.response.defer()

            # Abort merge
            async with ctx.typing():
                abort_response = await self.bot.api_client.git_checkout("--", ".")  # Reset to clean state

            await interaction.followup.send("❌ **Merge cancelled**")
            view.stop()

        auto_button = discord.ui.Button(label="Auto-Commit", style=discord.ButtonStyle.primary, emoji="🔄")
        resolve_button = discord.ui.Button(label="Resolve", style=discord.ButtonStyle.secondary, emoji="🔧")
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")

        auto_button.callback = auto_commit_callback
        resolve_button.callback = resolve_callback
        cancel_button.callback = cancel_callback

        view.add_item(auto_button)
        view.add_item(resolve_button)
        view.add_item(cancel_button)

        await ctx.send(embed=conflict_embed, view=view)

        await view.wait()
        if view.is_finished() and not any(item.disabled for item in view.children):
            await ctx.send("⏰ **Conflict resolution timeout - merge remains in conflicted state**")

    async def _show_conflict_resolution(self, ctx, interaction):
        """Show detailed conflict information and resolution options"""
        async with ctx.typing():
            conflicts_response = await self.bot.api_client.git_get_conflicts()

        if not conflicts_response.get('success', True):
            await interaction.followup.send(f"❌ **Failed to get conflict details:** {conflicts_response.get('error', 'Unknown error')}")
            return

        if not conflicts_response.get('has_conflicts', False):
            await interaction.followup.send("✅ **No conflicts found - merge may have been resolved**")
            return

        conflicts = conflicts_response.get('files', [])
        if not conflicts:
            await interaction.followup.send("ℹ️ **No conflicted files to resolve**")
            return

        # Show first conflict (limit to first file for Discord message length)
        first_conflict = conflicts[0]
        conflict_file = first_conflict.get('file', 'unknown')

        conflict_embed = discord.Embed(
            title=f"🔧 Conflict Resolution: {conflict_file}",
            description="Choose how to resolve this conflict:",
            color=discord.Color.red()
        )

        # Get the actual conflict markers content
        async with ctx.typing():
            diff_response = await self.bot.api_client.git_diff()

        if diff_response.get('success', True):
            diff_content = diff_response.get('diff', '')
            truncated_diff = diff_content[:1500] + "..." if len(diff_content) > 1500 else diff_content
            conflict_embed.add_field(
                name="📄 Conflict Content",
                value=f"```diff\n{truncated_diff}\n```",
                inline=False
            )

        conflict_embed.add_field(
            name="Available Actions",
            value="🔄 **Accept All** - Keep all changes\n🏠 **Keep Current** - Keep your version\n📥 **Keep Incoming** - Accept incoming changes",
            inline=False
        )

        view = discord.ui.View(timeout=120)

        async def accept_all_callback(btn_interaction):
            if btn_interaction.user != ctx.author:
                await btn_interaction.response.send_message("❌ Only the command user can resolve conflicts.", ephemeral=True)
                return

            await btn_interaction.response.defer()
            async with ctx.typing():
                add_response = await self.bot.api_client.git_add()
                if add_response.get('success', True):
                    await btn_interaction.followup.send("✅ **All conflicts accepted and staged**")
                else:
                    await btn_interaction.followup.send(f"❌ **Failed to stage:** {add_response.get('message', 'Unknown error')}")
            view.stop()

        accept_button = discord.ui.Button(label="Accept All", style=discord.ButtonStyle.success, emoji="🔄")
        accept_button.callback = accept_all_callback
        view.add_item(accept_button)

        await interaction.followup.send(embed=conflict_embed, view=view)

    @commands.command(name="git-branch-create", help="Create a new branch")
    async def git_create_branch(self, ctx, branch_name: str):
        """Create a new branch"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_create_branch(branch_name)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'already exists' in error_msg.lower():
                await ctx.send(f"🌳❌ **Branch `{branch_name}` already exists**\n\n💡 **Tip:** Use `/git-checkout {branch_name}` to switch to it.")
            elif 'invalid' in error_msg.lower() or 'bad' in error_msg.lower():
                await ctx.send(f"❌ **Invalid branch name `{branch_name}`**\n\n💡 **Tip:** Branch names cannot contain spaces or special characters.")
            else:
                await ctx.send(f"❌ **Failed to create branch:** {error_msg}")
            return

        await ctx.send(f"✅ **Branch `{branch_name}` created successfully**")

    @commands.command(name="git-branches", help="List all branches")
    async def git_list_branches(self, ctx):
        """List all branches"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_list_branches()

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            else:
                await ctx.send(f"❌ **Failed to list branches:** {error_msg}")
            return

        branches = response.get('branches', [])
        if not branches:
            await ctx.send("🌳 **No branches found**")
            return

        branch_msg = format_branch_list(response)
        embed = discord.Embed(
            title="🌳 Git Branches",
            description=branch_msg,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="git-checkout", help="Switch to a different branch")
    async def git_checkout(self, ctx, branch_name: str):
        """Switch to a branch"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        async with ctx.typing():
            response = await self.bot.api_client.git_checkout(branch_name)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            elif 'did not match any file' in error_msg.lower() or 'unknown revision' in error_msg.lower():
                await ctx.send(f"🌳❌ **Branch `{branch_name}` does not exist**\n\n💡 **Tip:** Use `/git-branches` to see available branches or `/git-branch-create {branch_name}` to create it.")
            elif 'uncommitted changes' in error_msg.lower() or 'would be overwritten' in error_msg.lower():
                await ctx.send("📝❌ **Uncommitted changes detected**\n\n💡 **Tip:** Use `/git-add` and `/git-commit` to save changes first.")
            else:
                await ctx.send(f"❌ **Checkout failed:** {error_msg}")
            return

        result_msg = f"✅ **Switched to branch `{branch_name}`**"
        if response.get('output'):
            result_msg += f"\n{format_code_block(response['output'])}"

        await ctx.send(result_msg)

    @commands.command(name="git-diff", help="Show changes in files")
    async def git_diff(self, ctx, staged: str = 'false'):
        """Show changes (staged or unstaged)"""
        if not self.bot.check_authorization(ctx):
            await ctx.send("❌ **You don't have permission to use this command.**")
            return

        staged_bool = staged.lower() in ['true', '1', 'yes']

        async with ctx.typing():
            response = await self.bot.api_client.git_diff(staged=staged_bool)

        if not response.get('success', True):
            error_msg = response.get('error', 'Unknown error')
            if 'not a git repository' in error_msg.lower():
                await ctx.send("📁❌ **Not a git repository**\n\n💡 **Tip:** Navigate to a git repository or run `git init` to initialize one.")
            else:
                await ctx.send(f"❌ **Git diff failed:** {error_msg}")
            return

        diff_text = response.get('diff', '')
        if not diff_text:
            await ctx.send(f"ℹ️ **No {'staged' if staged_bool else 'unstaged'} changes found**")
            return

        # Truncate diff if too long for Discord
        if len(diff_text) > 1900:
            diff_text = diff_text[:1900] + "\n... (truncated)"

        embed = discord.Embed(
            title=f"🔄 Git Diff ({'Staged' if staged_bool else 'Unstaged'})",
            description=format_code_block(diff_text, 'diff'),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)