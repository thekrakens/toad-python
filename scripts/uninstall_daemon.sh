#!/bin/bash
# TOAD Daemon Uninstallation Script
# Removes the TOAD daemon launchd service from macOS

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

# Configuration
PLIST_DEST="$HOME/Library/LaunchAgents/com.toad.daemon.plist"
SERVICE_NAME="com.toad.daemon"

print_info "TOAD Daemon Uninstallation"
print_info "=========================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is only for macOS"
    exit 1
fi

# Check if service is loaded
if launchctl list | grep -q "$SERVICE_NAME"; then
    print_info "Service is loaded. Stopping..."

    # Stop the service
    launchctl stop "$SERVICE_NAME" 2>/dev/null || true
    sleep 1

    # Unload the service
    print_info "Unloading service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    sleep 1

    # Verify unloaded
    if launchctl list | grep -q "$SERVICE_NAME"; then
        print_error "Failed to unload service"
        exit 1
    else
        print_info "Service unloaded successfully"
    fi
else
    print_warn "Service is not loaded"
fi

# Remove plist file
if [ -f "$PLIST_DEST" ]; then
    print_info "Removing plist file..."
    rm -f "$PLIST_DEST"
    print_info "Plist removed: $PLIST_DEST"
else
    print_warn "Plist file not found: $PLIST_DEST"
fi

# Check if daemon process is still running
if pgrep -f "toad.daemon.daemon" > /dev/null; then
    print_warn "Daemon process still running. Killing..."
    pkill -f "toad.daemon.daemon" || true
    sleep 1
fi

# Ask if user wants to clean up data
echo ""
read -p "Do you want to remove TOAD daemon data (~/.toad)? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$HOME/.toad" ]; then
        print_info "Removing $HOME/.toad directory..."
        rm -rf "$HOME/.toad"
        print_info "Data directory removed"
    else
        print_warn "Data directory not found: $HOME/.toad"
    fi
else
    print_info "Keeping data directory: $HOME/.toad"
    print_info "  (logs, PID files, etc. will remain)"
fi

echo ""
print_info "Uninstallation complete!"
print_info ""
print_info "The TOAD daemon has been removed from launchd."
print_info "To reinstall, run: scripts/install_daemon.sh"
