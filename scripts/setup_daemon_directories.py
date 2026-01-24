#!/usr/bin/env python3
"""
Setup script for TOAD daemon directory structure.

Creates the required directory hierarchy under ~/.toad/ for the unified daemon:
- inbox/     - Files arrive here from auto-export or manual drops
- staging/   - Parsed, reconciled, ready to sync
- processed/ - Successfully synced to Notion
- failed/    - Failed to sync (with error logs)
- cache/     - Cache files for sync state
"""

import logging
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_directory_structure(base_path: Path) -> bool:
    """
    Create the daemon directory structure.

    Args:
        base_path: Base directory (typically ~/.toad/)

    Returns:
        True if successful, False otherwise
    """
    # Define directory structure
    directories = [
        # Inbox directories
        "inbox/health/activity",
        "inbox/health/workouts",
        "inbox/health/body",
        "inbox/gymaholic",

        # Staging directories
        "staging/health/activity",
        "staging/health/workouts",
        "staging/health/body",
        "staging/gymaholic",

        # Processed directory (will have date subdirectories created dynamically)
        "processed",

        # Failed directory (will have date subdirectories created dynamically)
        "failed",

        # Cache directory
        "cache",
    ]

    try:
        # Create base directory if it doesn't exist
        base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Base directory: {base_path}")

        # Create all subdirectories
        created_count = 0
        for dir_path in directories:
            full_path = base_path / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created: {full_path}")
                created_count += 1
            else:
                logger.info(f"Exists: {full_path}")

        logger.info(f"Directory structure setup complete! Created {created_count} new directories.")

        # Verify permissions
        if not base_path.is_dir():
            logger.error(f"Base path is not a directory: {base_path}")
            return False

        # Check write permissions
        test_file = base_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"Write permissions verified for {base_path}")
        except PermissionError:
            logger.error(f"No write permissions for {base_path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}")
        return False


def print_directory_tree(base_path: Path, prefix: str = "", is_last: bool = True):
    """
    Print directory tree structure (visual representation).

    Args:
        base_path: Directory to display
        prefix: Prefix for tree formatting
        is_last: Whether this is the last item in parent
    """
    if not base_path.exists():
        return

    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{base_path.name}/")

    if base_path.is_dir():
        children = sorted(base_path.iterdir())
        for i, child in enumerate(children):
            if child.name.startswith('.'):
                continue  # Skip hidden files
            is_last_child = (i == len(children) - 1)
            extension = "    " if is_last else "│   "
            if child.is_dir():
                print_directory_tree(child, prefix + extension, is_last_child)
            else:
                connector = "└── " if is_last_child else "├── "
                print(f"{prefix}{extension}{connector}{child.name}")


def migrate_existing_files(icloud_path: Path, toad_path: Path) -> bool:
    """
    Migrate existing files from iCloud workout_sync to ~/.toad/ structure.

    Args:
        icloud_path: Path to iCloud workout_sync directory
        toad_path: Path to ~/.toad/ directory

    Returns:
        True if migration successful, False otherwise
    """
    if not icloud_path.exists():
        logger.warning(f"iCloud path does not exist: {icloud_path}")
        return True  # Not an error, just no migration needed

    logger.info(f"Migrating files from {icloud_path} to {toad_path}")

    # Migration mapping: iCloud path -> ~/.toad/ path
    migrations = [
        (icloud_path / "inbox/gymaholic", toad_path / "inbox/gymaholic"),
        (icloud_path / "inbox/health", toad_path / "inbox/health"),
        (icloud_path / "processed", toad_path / "processed"),
        (icloud_path / "failed", toad_path / "failed"),
    ]

    migrated_count = 0
    for src, dst in migrations:
        if src.exists():
            # List files to migrate
            files = list(src.rglob("*"))
            files = [f for f in files if f.is_file() and not f.name.startswith('.')]

            if files:
                logger.info(f"Found {len(files)} files in {src.relative_to(icloud_path)}")
                for file in files:
                    # Get relative path from src
                    rel_path = file.relative_to(src)
                    dest_file = dst / rel_path

                    # Create parent directory if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file (don't move, preserve iCloud copy)
                    import shutil
                    if not dest_file.exists():
                        shutil.copy2(file, dest_file)
                        logger.info(f"Migrated: {rel_path}")
                        migrated_count += 1
                    else:
                        logger.info(f"Skipped (already exists): {rel_path}")

    logger.info(f"Migration complete! Migrated {migrated_count} files.")
    return True


def main():
    """Main setup function."""
    # Define paths
    toad_base = Path.home() / ".toad"
    icloud_workout_sync = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/TOAD/workout_sync"

    logger.info("=" * 60)
    logger.info("TOAD Daemon Directory Structure Setup")
    logger.info("=" * 60)

    # Create directory structure
    logger.info("\n[1/3] Creating directory structure...")
    if not create_directory_structure(toad_base):
        logger.error("Failed to create directory structure. Exiting.")
        return 1

    # Migrate existing files from iCloud (optional)
    logger.info("\n[2/3] Migrating existing files (if any)...")
    if not migrate_existing_files(icloud_workout_sync, toad_base):
        logger.warning("Migration had issues, but continuing...")

    # Display directory tree
    logger.info("\n[3/3] Final directory structure:")
    print("\n" + "=" * 60)
    print(f"{toad_base.name}/")
    for child in sorted(toad_base.iterdir()):
        if child.name.startswith('.'):
            continue
        is_last = child == sorted(toad_base.iterdir())[-1]
        print_directory_tree(child, "", is_last)
    print("=" * 60)

    logger.info("\n✓ Setup complete!")
    logger.info(f"Daemon directories created at: {toad_base}")
    logger.info("\nNext steps:")
    logger.info("  1. Configure HealthAutoExport to export to ~/.toad/inbox/health/")
    logger.info("  2. Export Gymaholic workouts to ~/.toad/inbox/gymaholic/")
    logger.info("  3. Run 'toad daemon start' to begin watching for files")

    return 0


if __name__ == "__main__":
    exit(main())
