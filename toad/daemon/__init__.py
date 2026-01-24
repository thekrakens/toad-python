"""TOAD Daemon Module.

Unified event-driven daemon for file watching, productivity sync, and UI updates.
"""

from pathlib import Path

# iCloud base directories (symlinked for easy access)
ICLOUD_SYMLINK_DIR = Path.home() / "icloud"
TOAD_ICLOUD_BASE = ICLOUD_SYMLINK_DIR / "TOAD"
HEALTH_EXPORT_ICLOUD_BASE = ICLOUD_SYMLINK_DIR / "HealthExport"

# TOAD iCloud directories (all processing happens here)
STAGING_DIR = TOAD_ICLOUD_BASE / "staging"
PROCESSED_DIR = TOAD_ICLOUD_BASE / "processed"
FAILED_DIR = TOAD_ICLOUD_BASE / "failed"

# TOAD inbox directory
INBOX_GYMAHOLIC_DIR = TOAD_ICLOUD_BASE / "inbox" / "gymaholic"

# Health Auto Export directories (watched directly)
HEALTH_EXPORT_ACTIVITY_DIR = HEALTH_EXPORT_ICLOUD_BASE / "TOAD_Activity"
HEALTH_EXPORT_WORKOUTS_DIR = HEALTH_EXPORT_ICLOUD_BASE / "TOAD_workouts"

# Local cache directory (not on iCloud)
CACHE_DIR = Path.home() / ".toad" / "cache"

# Watched directories (3 total)
WATCHED_DIRECTORIES = [
    HEALTH_EXPORT_ACTIVITY_DIR,
    HEALTH_EXPORT_WORKOUTS_DIR,
    INBOX_GYMAHOLIC_DIR,
]

__all__ = [
    "TOAD_ICLOUD_BASE",
    "HEALTH_EXPORT_ICLOUD_BASE",
    "STAGING_DIR",
    "PROCESSED_DIR",
    "FAILED_DIR",
    "INBOX_GYMAHOLIC_DIR",
    "HEALTH_EXPORT_ACTIVITY_DIR",
    "HEALTH_EXPORT_WORKOUTS_DIR",
    "CACHE_DIR",
    "WATCHED_DIRECTORIES",
]
