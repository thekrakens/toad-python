#!/bin/bash
# TOAD Auto-Sync Setup Script for macOS
# Sets up launchd to run sync every 5 minutes

set -e

echo "🐸 TOAD Auto-Sync Setup"
echo "======================="
echo ""

# Get the current directory
TOAD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "TOAD directory: $TOAD_DIR"

# Get Poetry virtual environment Python path
VENV_PYTHON=$(poetry env info --path)/bin/python
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Poetry virtual environment not found!"
    echo "   Please run 'poetry install' first."
    exit 1
fi
echo "Python path: $VENV_PYTHON"

# Create Launch Agent directory
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENT_DIR"

# Create plist file
PLIST_FILE="$LAUNCH_AGENT_DIR/com.toad.sync.plist"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.toad.sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $TOAD_DIR && $VENV_PYTHON -m toad.cli sync</string>
    </array>
    
    <key>StartInterval</key>
    <integer>300</integer>
    
    <key>StandardOutPath</key>
    <string>/tmp/toad-sync.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/toad-sync-error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

echo ""
echo "✅ Created launch agent plist: $PLIST_FILE"

# Unload if already loaded
if launchctl list | grep -q com.toad.sync; then
    echo "🔄 Unloading existing service..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# Load the launch agent
echo "🚀 Loading launch agent..."
launchctl load "$PLIST_FILE"

# Start the service
echo "▶️  Starting service..."
launchctl start com.toad.sync

echo ""
echo "🎉 Auto-sync setup complete!"
echo ""
echo "📊 Monitor sync:"
echo "   tail -f /tmp/toad-sync.log"
echo ""
echo "🛑 Stop auto-sync:"
echo "   launchctl stop com.toad.sync"
echo ""
echo "🗑️  Remove auto-sync:"
echo "   launchctl unload ~/Library/LaunchAgents/com.toad.sync.plist"
echo "   rm ~/Library/LaunchAgents/com.toad.sync.plist"
echo ""
echo "ℹ️  For more options, see: docs/auto_sync_setup.md"
