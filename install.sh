#!/bin/bash

# ClickUp CLI Integration Installer for Claude CLI
# This script sets up the ClickUp CLI tool for use with Claude CLI

set -e

echo "================================================"
echo "ClickUp CLI Integration Installer"
echo "For Claude CLI users"
echo "================================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "✅ Python is installed (version: $PYTHON_VERSION)"

# Create virtual environment
echo ""
echo "📦 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📚 Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✅ Dependencies installed"

# Create CLI wrapper script
echo ""
echo "🔧 Creating CLI wrapper..."
cat > clickup << 'EOF'
#!/bin/bash
# ClickUp CLI wrapper script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate" 2>/dev/null
python3 "$SCRIPT_DIR/clickup_cli.py" "$@"
EOF

chmod +x clickup
echo "✅ CLI wrapper created"

# Install to user's local bin (optional)
echo ""
read -p "Would you like to install 'clickup' command globally? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create local bin if it doesn't exist
    mkdir -p ~/.local/bin
    
    # Create symlink
    ln -sf "$(pwd)/clickup" ~/.local/bin/clickup
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        echo "⚠️  Note: ~/.local/bin is not in your PATH"
        echo "   Add this line to your ~/.bashrc or ~/.zshrc:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    
    echo "✅ Global installation complete"
fi

# Setup API token
echo ""
echo "================================================"
echo "⚠️  IMPORTANT: Personal ClickUp API Token Required"
echo "================================================"
echo ""
echo "Each user must use their OWN personal ClickUp API token."
echo ""
echo "To get YOUR personal token:"
echo "1. Log into ClickUp with YOUR account"
echo "2. Go to Settings > Apps"
echo "3. Generate a Personal API Token"
echo "4. Copy the token (starts with 'pk_')"
echo ""
read -p "Enter YOUR personal ClickUp API token (or press Enter to skip): " API_TOKEN

if [ ! -z "$API_TOKEN" ]; then
    source venv/bin/activate
    python3 clickup_cli.py setup "$API_TOKEN"
else
    echo ""
    echo "⚠️  Skipping token setup. You can configure it later with:"
    echo "   ./clickup setup YOUR_API_TOKEN"
fi

echo ""
echo "================================================"
echo "🎉 Installation Complete!"
echo "================================================"
echo ""
echo "Usage examples:"
echo "  ./clickup whoami                    # Show authenticated user"
echo "  ./clickup teams                     # List your teams"
echo "  ./clickup tasks --due-this-week     # Show tasks due this week"
echo "  ./clickup tasks --assigned-to-me    # Show tasks assigned to you"
echo "  ./clickup create LIST_ID 'Task name' # Create a new task"
echo ""
echo "For more help: ./clickup --help"
echo ""
echo "To use with Claude CLI:"
echo "  claude 'Run ./clickup tasks --due-this-week and summarize'"
echo "  claude 'Use ./clickup to create a task for reviewing PR #123'"