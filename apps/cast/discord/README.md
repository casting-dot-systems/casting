# 🤖 Casting API Discord Bot

A powerful Discord bot that provides seamless integration with the Casting API, enabling git operations and markdown file management directly from Discord channels.

## ✨ Features

### 🔀 Git Operations
- **Status & Staging**: Check repository status and stage changes
- **Commits & History**: Create commits and view commit history
- **Branching**: Create, list, and switch between branches
- **Remote Operations**: Push, pull, and manage remotes
- **Merge Management**: Merge branches with automatic conflict handling
- **Diff Viewing**: Compare staged and unstaged changes

### 📝 Markdown Operations
- **File Management**: Create, read, update, and delete markdown files
- **Content Operations**: Append content to existing files
- **File Listing**: Browse all available markdown files
- **Rich Previews**: View content with syntax highlighting

### 🛡️ Security Features
- **Permission Control**: Channel and role-based access restrictions
- **Confirmation Dialogs**: Safe delete operations with user confirmation
- **Authorization Checks**: Comprehensive permission validation
- **Safe Operations**: Protected destructive commands

## 🚀 Quick Setup

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Navigate to "Bot" section
4. Create a bot and copy the token
5. Enable necessary intents (Message Content Intent)

### 2. Configure Environment

Add to your `.env` file:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_COMMAND_PREFIX=/
DISCORD_ALLOWED_CHANNELS=           # Optional: 123456789,987654321
DISCORD_ALLOWED_ROLES=              # Optional: Admin,Developer
```

### 3. Bot Permissions

When inviting the bot, ensure these permissions:
- ✅ Send Messages
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Use External Emojis
- ✅ Embed Links

### 4. Invite Bot to Server

1. In Discord Developer Portal → OAuth2 → URL Generator
2. Select scopes: `bot`
3. Select required permissions
4. Use generated URL to invite bot

### 5. Start the Bot

```bash
# Make sure FastAPI server is running first
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start the Discord bot
uv run python -m apps.discord_bot.bot
```

## 📖 Command Reference

### 📝 Markdown Commands

| Command | Parameters | Description | Example |
|---------|------------|-------------|---------|
| `/md-create` | `<filename> [content]` | Create new markdown file | `/md-create notes Hello world!` |
| `/md-read` | `<filename>` | Display markdown file content | `/md-read notes` |
| `/md-update` | `<filename> <content>` | Replace file content entirely | `/md-update notes New content here` |
| `/md-append` | `<filename> <content>` | Add content to end of file | `/md-append notes More text here` |
| `/md-delete` | `<filename>` | Delete file (with confirmation) | `/md-delete notes` |
| `/md-list` | _none_ | Show all markdown files | `/md-list` |

### 🔀 Git Commands

| Command | Parameters | Description | Example |
|---------|------------|-------------|---------|
| `/git-status` | _none_ | Show repository status | `/git-status` |
| `/git-add` | _none_ | Stage all changes | `/git-add` |
| `/git-commit` | `<message>` | Create commit with message | `/git-commit "Fix critical bug"` |
| `/git-push` | `[remote] [branch] [set_upstream]` | Push to remote repository | `/git-push origin main true` |
| `/git-pull` | `[remote] [branch]` | Pull from remote repository | `/git-pull origin main` |
| `/git-log` | `[limit]` | Show commit history | `/git-log 10` |
| `/git-merge` | `<branch> [allow_conflicts]` | Merge branch into current | `/git-merge feature-branch` |
| `/git-branch-create` | `<branch_name>` | Create new branch | `/git-branch-create hotfix/urgent` |
| `/git-branches` | _none_ | List all branches | `/git-branches` |
| `/git-checkout` | `<branch_name>` | Switch to branch | `/git-checkout main` |
| `/git-diff` | `[staged]` | Show file changes | `/git-diff true` |

## 💼 Common Workflows

### 🆕 Creating and Committing New Content

```bash
# Create a new document
/md-create project-plan "# Project Plan\n\n## Goals\n- Implement feature X"

# Check what's changed
/git-status

# Stage changes
/git-add

# Create commit
/git-commit "Add initial project plan"

# Push to remote
/git-push
```

### 🔄 Feature Branch Workflow

```bash
# Create and switch to feature branch
/git-branch-create feature/user-auth
/git-checkout feature/user-auth

# Make changes
/md-create auth-spec "# Authentication Specification"

# Commit changes
/git-add
/git-commit "Add authentication specification"

# Switch back and merge
/git-checkout main
/git-merge feature/user-auth

# Push merged changes
/git-push
```

### 📋 Content Management

```bash
# List all documents
/md-list

# Read existing document
/md-read meeting-notes

# Add more content
/md-append meeting-notes "\n\n## Action Items\n- Follow up on proposal"

# Review changes
/git-diff

# Commit updates
/git-add
/git-commit "Update meeting notes with action items"
```

## 🔧 Configuration Options

### Channel Restrictions

Limit bot usage to specific channels:

```env
# Only allow in these channels (use channel IDs)
DISCORD_ALLOWED_CHANNELS=123456789012345678,987654321098765432
```

### Role-Based Access

Restrict commands to users with specific roles:

```env
# Only allow users with these roles
DISCORD_ALLOWED_ROLES=Admin,Developer,GitOps,ContentManager
```

### Command Prefix

Change the command prefix (default is "/"):

```env
# Use different prefix
DISCORD_COMMAND_PREFIX=!
# Commands would then be: !git-status, !md-create, etc.
```

## 🏗️ Architecture

### Project Structure

```
apps/discord_bot/
├── 📄 bot.py                  # Main bot application
├── 📄 README.md               # This file
├── 📂 commands/
│   ├── 📄 __init__.py
│   ├── 📄 git_commands.py     # Git operation commands
│   └── 📄 markdown_commands.py # Markdown operation commands
└── 📂 utils/
    ├── 📄 __init__.py
    ├── 📄 api_client.py       # FastAPI communication
    └── 📄 helpers.py          # Utility functions
```

### Command Flow

1. **User Input**: User types command in Discord
2. **Authorization**: Bot checks channel/role permissions
3. **Validation**: Command parameters are validated
4. **API Request**: Bot calls FastAPI backend
5. **Response Handling**: Results are formatted and displayed
6. **Error Management**: Errors are caught and user-friendly messages shown

### API Integration

The bot communicates with the FastAPI backend through HTTP requests:

```python
# Example API integration
async def create_markdown(self, ctx, filename: str, *, content: str = ""):
    # Authorization check
    if not self.bot.check_authorization(ctx):
        await ctx.send("❌ **You don't have permission to use this command.**")
        return

    # API call with typing indicator
    async with ctx.typing():
        response = await self.bot.api_client.create_markdown(filename, content)

    # Format and send response
    result_msg = format_response(response)
    await ctx.send(result_msg)
```

## 🎨 User Experience Features

### Visual Indicators

- **🔄 Typing Indicators**: Shows bot is processing
- **📊 Rich Embeds**: Formatted output with colors and structure
- **✅ Status Icons**: Visual feedback for success/error states
- **⏱️ Timeouts**: Automatic cleanup of temporary messages

### Interactive Elements

- **🔴 Confirmation Buttons**: Safe delete operations
- **⏰ Timeout Handling**: Auto-cancel after 30 seconds
- **👤 User Validation**: Only command author can confirm actions

### Error Handling

- **📝 Detailed Messages**: Clear error descriptions
- **💡 Helpful Suggestions**: Guidance for resolving issues
- **🔍 Context Information**: Relevant details for troubleshooting

## 🐛 Troubleshooting

### Bot Not Responding

```bash
# Check these common issues:

1. ✅ Bot token is correct in .env
2. ✅ Bot has necessary permissions
3. ✅ FastAPI server is running
4. ✅ Bot is in the correct Discord server
5. ✅ Channel/role restrictions allow your access
```

### Commands Not Working

```bash
# Verify configuration:

1. ✅ Command prefix is correct (check .env)
2. ✅ Spelling and syntax are correct
3. ✅ Required parameters are provided
4. ✅ Bot has permission to send messages
```

### Permission Errors

```bash
# Check access controls:

1. ✅ Your user has required Discord roles
2. ✅ Channel is allowed for bot usage
3. ✅ DISCORD_ALLOWED_CHANNELS is configured correctly
4. ✅ DISCORD_ALLOWED_ROLES includes your roles
```

### File Operation Failures

```bash
# Verify backend configuration:

1. ✅ MARKDOWN_FOLDER_PATH exists and is writable
2. ✅ GIT_FOLDER_PATH points to valid git repository
3. ✅ FastAPI server is accessible
4. ✅ No file system permission issues
```

## 🔄 Development

### Adding New Commands

1. **Create command method** in appropriate command class
2. **Add authorization check** using `check_authorization`
3. **Implement typing indicator** for better UX
4. **Handle API communication** through `api_client`
5. **Format responses** using helper functions
6. **Add error handling** for edge cases

### Testing

```bash
# Test bot locally
uv run python -m apps.discord_bot.bot

# Test specific functions
python -c "from apps.discord_bot.utils.helpers import format_response; print(format_response({'success': True, 'message': 'Test'}))"
```

## 📚 Dependencies

- **discord.py**: Discord API wrapper
- **aiohttp**: Async HTTP client
- **python-dotenv**: Environment variable management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

## 📜 License

This project is part of the Casting API and follows the same license terms.

---

For more information, see the main [project README](../../README.md).