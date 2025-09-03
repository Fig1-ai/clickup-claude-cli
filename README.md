# ClickUp CLI Integration for Claude CLI

A command-line tool that enables Claude CLI users to interact with ClickUp directly from their terminal.

## ⚠️ Important: Individual API Tokens Required

**Each user must use their own personal ClickUp API token.** This ensures:
- Proper access control and permissions
- Individual usage tracking
- Better security practices
- Compliance with ClickUp's API terms

## Features

- 🔐 Secure personal API token storage
- 📋 List tasks with various filters (due dates, assignments, etc.)
- ✅ Create new tasks
- 📝 Update existing tasks
- 🏢 View teams and workspaces
- 👤 Check authenticated user
- 📊 **NEW:** Detailed task tables with descriptions, comments, and subtasks
- 👥 **NEW:** View tasks for specific team members
- 💬 **NEW:** Natural Language Processing interface - talk to ClickUp naturally!
- 🤖 Seamless integration with Claude CLI

## Prerequisites

- **Python 3.7+** - [Download here](https://www.python.org/downloads/)
- **Claude CLI** - [Installation guide](https://github.com/anthropics/claude-cli)
- **Your Personal ClickUp API Token**

## Quick Installation

### Automated Installation (Recommended)

1. Clone this repository:
```bash
git clone https://github.com/Fig1-ai/clickup-claude-cli.git
cd clickup-claude-cli
```

2. Run the installation script:
```bash
./install.sh
```

3. When prompted, enter YOUR personal ClickUp API token

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Setup your API token:
```bash
python3 clickup_cli.py setup YOUR_PERSONAL_API_TOKEN
```

## Getting Your Personal ClickUp API Token

1. Log into ClickUp with **your account**
2. Click on your avatar (bottom left)
3. Go to **Settings**
4. Navigate to **Apps** section
5. Click **Generate** under "Personal API Token"
6. Copy the token (starts with `pk_`)
7. **Keep this token secure and don't share it**

## Usage

### Standalone CLI Commands

```bash
# Check authenticated user
./clickup whoami

# List all teams/workspaces
./clickup teams

# List tasks due this week
./clickup tasks --due-this-week

# List tasks assigned to you
./clickup tasks --assigned-to-me

# Create a new task
./clickup create LIST_ID "Task name" --description "Task details" --priority 2

# Update a task
./clickup update TASK_ID --status "in progress" --name "Updated task name"
```

### Enhanced Commands (NEW)

```bash
# View detailed tasks with table format
python3 clickup_detailed.py

# View tasks for a specific user
python3 clickup_user_tasks.py jeremy
python3 clickup_user_tasks.py rolla

# The detailed view includes:
# - Task descriptions and comments
# - Subtasks and parent tasks
# - Priority levels with visual indicators
# - Due dates with overdue warnings
# - Task locations (space/folder/list)
```

### Natural Language Interface (NEW)

Talk to ClickUp using natural language instead of commands!

```bash
# Interactive chat mode
./clickup-chat
# Then type naturally: "show my tasks", "what's due today?", etc.

# Direct natural language commands
./clickup-chat "show my tasks"
./clickup-chat "what do I need to do this week?"
./clickup-chat "show jeremy's tasks"
./clickup-chat "list urgent tasks"
./clickup-chat "give me a task summary"

# Examples of understood phrases:
# - "what am I working on?"
# - "show overdue tasks"
# - "what is rolla working on?"
# - "show tasks due tomorrow"
# - "list high priority items"
# - "who am i?"
# - "show my teams"
```

### Integration with Claude CLI

Use the ClickUp CLI tool within Claude CLI commands:

```bash
# Get a summary of your tasks
claude "Run './clickup tasks --due-this-week' and create a summary"

# Create tasks based on code review
claude "Review the latest commit and use './clickup create LIST_ID' to create tasks for any issues found"

# Update task status
claude "Use './clickup update TASK_ID --status done' to mark the deployment task as complete"

# Generate a daily standup report
claude "Run './clickup tasks --assigned-to-me' and format as a standup report"
```

### Advanced Examples

```bash
# Complex task creation with Claude's help
claude "Based on our discussion, create a detailed task using './clickup create LIST_ID' with appropriate priority and due date"

# Bulk task management
claude "List all my high-priority tasks using './clickup tasks' and suggest which ones to focus on today"

# Project planning
claude "Help me break down this feature into subtasks and create them using './clickup create'"
```

## Configuration

The CLI stores your configuration in `~/.clickup/config.json` with restricted permissions (readable only by you).

### Update Your API Token

```bash
./clickup setup YOUR_NEW_PERSONAL_TOKEN
```

### Configuration File Location

- **Mac/Linux**: `~/.clickup/config.json`
- **Windows**: `%USERPROFILE%\.clickup\config.json`

## Security Best Practices

1. **Never share your personal API token** with others
2. **Never commit API tokens** to version control
3. **Each user must generate their own token**
4. Store your token in a secure password manager
5. Regularly rotate your API token
6. Revoke tokens when leaving the organization

## Troubleshooting

### "API token not found" error

Run the setup command:
```bash
./clickup setup YOUR_PERSONAL_API_TOKEN
```

### "API Error 401: Unauthorized"

Your token may be invalid or expired. Generate a new token in ClickUp and run setup again.

### Tasks not showing

1. Verify you have access to the workspace
2. Check that you're using YOUR personal token
3. Ensure your token has appropriate permissions

### Python module errors

Reinstall dependencies:
```bash
pip install -r requirements.txt
```

## For IT Administrators

To deploy across your organization:

1. Share this repository with your team
2. Each user must:
   - Generate their own personal ClickUp API token
   - Run the installation script with their token
   - Keep their token secure

**Do NOT use a shared token** - this violates security best practices and ClickUp's terms of service.

## Development

### Project Structure

```
clickup-claude-cli/
├── clickup_cli.py      # Main CLI application
├── requirements.txt    # Python dependencies
├── install.sh         # Installation script
├── clickup           # CLI wrapper (created during install)
└── README.md         # This file
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Add your changes to `clickup_cli.py`
4. Test thoroughly
5. Submit a pull request

## Support

- **ClickUp API Documentation**: https://clickup.com/api
- **Claude CLI Documentation**: https://github.com/anthropics/claude-cli
- **Issues**: [GitHub Issues](https://github.com/Fig1-ai/clickup-claude-cli/issues)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- ClickUp for their comprehensive API
- Anthropic for Claude CLI
- Contributors and users of this integration