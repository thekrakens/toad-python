"""TOAD Daemon Module.

Unified event-driven daemon for file watching, productivity sync, and UI updates.
"""

from pathlib import Path

# Daemon base directory
DAEMON_BASE = Path.home() / ".toad"

# Directory paths
INBOX_DIR = DAEMON_BASE / "inbox"
STAGING_DIR = DAEMON_BASE / "staging"
PROCESSED_DIR = DAEMON_BASE / "processed"
FAILED_DIR = DAEMON_BASE / "failed"
CACHE_DIR = DAEMON_BASE / "cache"

__all__ = [
    "DAEMON_BASE",
    "INBOX_DIR",
    "STAGING_DIR",
    "PROCESSED_DIR",
    "FAILED_DIR",
    "CACHE_DIR",
]
