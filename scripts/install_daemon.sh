#!/bin/bash
# TOAD Daemon Installation Script
# Installs the TOAD daemon as a launchd service on macOS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
PLIST_TEMPLATE="$SCRIPT_DIR/com.toad.daemon.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/com.toad.daemon.plist"
SERVICE_NAME="com.toad.daemon"

print_info "TOAD Daemon Installation"
print_info "========================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is only for macOS"
    exit 1
fi

# Check if template exists
if [ ! -f "$PLIST_TEMPLATE" ]; then
    print_error "Template file not found: $PLIST_TEMPLATE"
    exit 1
fi

# Detect Python path
print_info "Detecting Python interpreter..."
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    print_error "Python 3 not found in PATH"
    exit 1
fi
print_info "Using Python: $PYTHON_PATH"

# Check if Python can import toad
print_info "Checking TOAD installation..."
if ! $PYTHON_PATH -c "import toad" 2>/dev/null; then
    print_warn "TOAD package not found in Python path"
    print_warn "Please install TOAD first:"
    print_warn "  cd $PROJECT_DIR"
    print_warn "  pip install -e ."
    print_warn "  or: poetry install"
    exit 1
fi
print_info "TOAD package found"

# Get user info
USER_NAME=$(whoami)
HOME_DIR="$HOME"

print_info "Configuration:"
print_info "  User: $USER_NAME"
print_info "  Home: $HOME_DIR"
print_info "  Python: $PYTHON_PATH"
echo ""

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create .toad directory if it doesn't exist
mkdir -p "$HOME/.toad"

# Generate plist from template
print_info "Generating plist file..."
sed -e "s|{{PYTHON_PATH}}|$PYTHON_PATH|g" \
    -e "s|{{HOME_DIR}}|$HOME_DIR|g" \
    -e "s|{{USER_NAME}}|$USER_NAME|g" \
    "$PLIST_TEMPLATE" > "$PLIST_DEST"

print_info "Plist created: $PLIST_DEST"

# Check if service is already loaded
if launchctl list | grep -q "$SERVICE_NAME"; then
    print_warn "Service already loaded. Unloading first..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Load the service
print_info "Loading service..."
launchctl load "$PLIST_DEST"

# Verify service loaded
sleep 1
if launchctl list | grep -q "$SERVICE_NAME"; then
    print_info "Service loaded successfully"
else
    print_error "Failed to load service"
    exit 1
fi

# Start the service
print_info "Starting daemon..."
launchctl start "$SERVICE_NAME"

# Wait a moment and check status
sleep 2

# Check if daemon is running
if pgrep -f "toad.daemon.daemon" > /dev/null; then
    PID=$(pgrep -f "toad.daemon.daemon")
    print_info "Daemon started successfully (PID: $PID)"
else
    print_warn "Daemon may not have started. Check logs:"
    print_warn "  tail -f $HOME/.toad/daemon.log"
fi

echo ""
print_info "Installation complete!"
print_info ""
print_info "The TOAD daemon will now:"
print_info "  - Start automatically on system boot"
print_info "  - Restart automatically if it crashes"
print_info "  - Log to: $HOME/.toad/daemon.log"
print_info ""
print_info "Useful commands:"
print_info "  View status:  launchctl list | grep toad"
print_info "  Stop daemon:  launchctl stop $SERVICE_NAME"
print_info "  Start daemon: launchctl start $SERVICE_NAME"
print_info "  View logs:    tail -f $HOME/.toad/daemon.log"
print_info "  Uninstall:    $SCRIPT_DIR/uninstall_daemon.sh"
