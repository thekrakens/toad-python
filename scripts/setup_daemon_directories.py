#!/usr/bin/env python3
"""
Setup script for TOAD daemon directory structure.

Creates the required iCloud-based directory structure with symlinks:
- ~/icloud/TOAD/          - Main TOAD directory on iCloud (symlinked)
  - inbox/                - Files arrive from all devices
  - staging/              - Currently processing (visible for debugging)
  - processed/            - Successfully synced (30-day auto-cleanup)
  - failed/               - Failed files + error logs
- ~/icloud/HealthExport/  - Health Auto Export iCloud location (symlinked)
  - TOAD_Activity/        - Activity metrics from Health Auto Export
  - TOAD_workouts/        - Workouts from Health Auto Export
- ~/.toad/cache/          - Local cache only (not synced)
"""

import logging
import os
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_icloud_symlinks() -> tuple[Path, Path]:
    """
    Create ~/icloud/ symlink directory with TOAD and HealthExport symlinks.

    Returns:
        Tuple of (toad_icloud_path, health_export_path)

    Raises:
        Exception if symlink creation fails
    """
    home = Path.home()

    # Define paths
    icloud_symlink_dir = home / "icloud"
    toad_actual = home / "Library/Mobile Documents/com~apple~CloudDocs/TOAD"
    health_export_actual = home / "Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents"

    # Create ~/icloud/ directory
    icloud_symlink_dir.mkdir(exist_ok=True)
    logger.info(f"Created symlink directory: {icloud_symlink_dir}")

    # Create TOAD symlink
    toad_symlink = icloud_symlink_dir / "TOAD"
    if toad_symlink.exists() or toad_symlink.is_symlink():
        if toad_symlink.is_symlink():
            logger.info(f"TOAD symlink already exists: {toad_symlink} -> {os.readlink(toad_symlink)}")
        else:
            logger.warning(f"TOAD path exists but is not a symlink: {toad_symlink}")
    else:
        # Create actual directory first
        toad_actual.mkdir(parents=True, exist_ok=True)
        # Create symlink
        os.symlink(toad_actual, toad_symlink)
        logger.info(f"Created symlink: {toad_symlink} -> {toad_actual}")

    # Create HealthExport symlink
    health_export_symlink = icloud_symlink_dir / "HealthExport"
    if health_export_symlink.exists() or health_export_symlink.is_symlink():
        if health_export_symlink.is_symlink():
            logger.info(f"HealthExport symlink already exists: {health_export_symlink} -> {os.readlink(health_export_symlink)}")
        else:
            logger.warning(f"HealthExport path exists but is not a symlink: {health_export_symlink}")
    else:
        if not health_export_actual.exists():
            logger.warning(f"Health Auto Export directory not found: {health_export_actual}")
            logger.warning("Please install and configure Health Auto Export app first")
        else:
            os.symlink(health_export_actual, health_export_symlink)
            logger.info(f"Created symlink: {health_export_symlink} -> {health_export_actual}")

    return toad_symlink, health_export_symlink


def create_toad_icloud_structure(toad_icloud_path: Path) -> bool:
    """
    Create TOAD iCloud directory structure.

    Args:
        toad_icloud_path: Path to ~/icloud/TOAD/

    Returns:
        True if successful, False otherwise
    """
    # Define TOAD iCloud directory structure
    directories = [
        "inbox/gymaholic",
        "staging",
        "processed",
        "failed",
    ]

    try:
        # Create all subdirectories
        created_count = 0
        for dir_path in directories:
            full_path = toad_icloud_path / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created: {full_path}")
                created_count += 1
            else:
                logger.info(f"Exists: {full_path}")

        logger.info(f"TOAD iCloud structure complete! Created {created_count} new directories.")

        # Verify permissions
        test_file = toad_icloud_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"Write permissions verified for {toad_icloud_path}")
        except PermissionError:
            logger.error(f"No write permissions for {toad_icloud_path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to create TOAD iCloud structure: {e}")
        return False


def verify_health_export_paths(health_export_path: Path) -> bool:
    """
    Verify Health Auto Export paths exist.

    Args:
        health_export_path: Path to ~/icloud/HealthExport/

    Returns:
        True if paths exist, False otherwise
    """
    required_paths = [
        health_export_path / "TOAD_Activity",
        health_export_path / "TOAD_workouts",
    ]

    all_exist = True
    for path in required_paths:
        if path.exists():
            logger.info(f"✓ Found: {path}")
        else:
            logger.warning(f"✗ Missing: {path}")
            logger.warning(f"  Please create this folder in Health Auto Export app")
            all_exist = False

    return all_exist


def create_local_cache(cache_path: Path) -> bool:
    """
    Create local cache directory (not on iCloud).

    Args:
        cache_path: Path to ~/.toad/cache/

    Returns:
        True if successful, False otherwise
    """
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created local cache: {cache_path}")

        # Verify permissions
        test_file = cache_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"Write permissions verified for {cache_path}")
        except PermissionError:
            logger.error(f"No write permissions for {cache_path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to create local cache: {e}")
        return False


def create_readme(toad_icloud_path: Path) -> bool:
    """
    Create README.md in TOAD iCloud directory.

    Args:
        toad_icloud_path: Path to ~/icloud/TOAD/

    Returns:
        True if successful, False otherwise
    """
    readme_content = """# TOAD iCloud Directory

This directory is monitored by the TOAD daemon for automatic syncing to Notion.

## Directory Structure

- **inbox/** - Files arrive here from configured apps
  - **gymaholic/** - Gymaholic CSV exports (configure in Gymaholic app)

- **staging/** - Files currently being processed (check here if debugging)

- **processed/** - Successfully synced files (auto-deleted after 30 days)

- **failed/** - Failed files with error logs (check here if sync issues occur)

## Data Sources

The daemon monitors 3 directories:

1. **`~/icloud/TOAD/inbox/gymaholic/`** - Gymaholic workout exports
2. **`~/icloud/HealthExport/TOAD_Activity/`** - Activity + body metrics (Health Auto Export)
3. **`~/icloud/HealthExport/TOAD_workouts/`** - Workout data (Health Auto Export)

## How to Use

1. **Configure Gymaholic**: Export Gymaholic workouts → iCloud Drive → TOAD/inbox/gymaholic/
2. **Configure Health Auto Export**: Create "TOAD_Activity" and "TOAD_workouts" folders in app
3. **Daemon auto-processes**: Files move through staging → processed (or failed)
4. **Auto-cleanup**: Processed files are deleted after 30 days to save iCloud space

## Troubleshooting

- **File not syncing?** Check `failed/` directory for error logs
- **Processing stuck?** Check `staging/` directory to see what's being processed
- **Daemon not running?** Run `toad daemon status` on your Mac
"""

    try:
        readme_path = toad_icloud_path / "README.md"
        readme_path.write_text(readme_content)
        logger.info(f"Created README: {readme_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create README: {e}")
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


def migrate_existing_files(old_icloud_path: Path, new_toad_icloud_path: Path) -> bool:
    """
    Migrate existing files from old iCloud workout_sync to new TOAD iCloud structure.

    Args:
        old_icloud_path: Path to old iCloud workout_sync directory
        new_toad_icloud_path: Path to ~/icloud/TOAD/ directory

    Returns:
        True if migration successful, False otherwise
    """
    if not old_icloud_path.exists():
        logger.info(f"No migration needed - old iCloud path does not exist: {old_icloud_path}")
        return True  # Not an error, just no migration needed

    logger.info(f"Migrating files from {old_icloud_path} to {new_toad_icloud_path}")

    # Migration mapping: old iCloud path -> new TOAD iCloud path
    migrations = [
        (old_icloud_path / "inbox/gymaholic", new_toad_icloud_path / "inbox/gymaholic"),
        (old_icloud_path / "processed", new_toad_icloud_path / "processed"),
        (old_icloud_path / "failed", new_toad_icloud_path / "failed"),
    ]

    # Note: old inbox/health files are not migrated - they're obsolete now that
    # Health Auto Export goes directly to ~/icloud/HealthExport/TOAD_* directories

    migrated_count = 0
    for src, dst in migrations:
        if src.exists():
            # List files to migrate
            files = list(src.rglob("*"))
            files = [f for f in files if f.is_file() and not f.name.startswith('.')]

            if files:
                logger.info(f"Found {len(files)} files in {src.relative_to(old_icloud_path)}")
                for file in files:
                    # Get relative path from src
                    rel_path = file.relative_to(src)
                    dest_file = dst / rel_path

                    # Create parent directory if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file (don't move, preserve old copy)
                    import shutil
                    if not dest_file.exists():
                        shutil.copy2(file, dest_file)
                        logger.info(f"Migrated: {rel_path}")
                        migrated_count += 1
                    else:
                        logger.info(f"Skipped (already exists): {rel_path}")

    if migrated_count > 0:
        logger.info(f"Migration complete! Migrated {migrated_count} files.")
    else:
        logger.info("No files to migrate.")

    return True


def main():
    """Main setup function."""
    # Define paths
    home = Path.home()
    local_cache = home / ".toad/cache"
    old_icloud_workout_sync = home / "Library/Mobile Documents/com~apple~CloudDocs/TOAD/workout_sync"

    logger.info("=" * 60)
    logger.info("TOAD Daemon iCloud Directory Structure Setup")
    logger.info("=" * 60)

    # Step 1: Create iCloud symlinks
    logger.info("\n[1/6] Creating iCloud symlinks...")
    try:
        toad_icloud, health_export_icloud = create_icloud_symlinks()
    except Exception as e:
        logger.error(f"Failed to create iCloud symlinks: {e}")
        return 1

    # Step 2: Create TOAD iCloud directory structure
    logger.info("\n[2/6] Creating TOAD iCloud directory structure...")
    if not create_toad_icloud_structure(toad_icloud):
        logger.error("Failed to create TOAD iCloud structure. Exiting.")
        return 1

    # Step 3: Verify Health Auto Export paths
    logger.info("\n[3/6] Verifying Health Auto Export paths...")
    health_export_ok = verify_health_export_paths(health_export_icloud)
    if not health_export_ok:
        logger.warning("⚠️  Health Auto Export paths missing - please configure in the app")
        logger.warning("   This is optional and won't prevent daemon from running")

    # Step 4: Create local cache
    logger.info("\n[4/6] Creating local cache directory...")
    if not create_local_cache(local_cache):
        logger.error("Failed to create local cache. Exiting.")
        return 1

    # Step 5: Create README
    logger.info("\n[5/6] Creating README...")
    if not create_readme(toad_icloud):
        logger.warning("Failed to create README (non-critical)")

    # Step 6: Migrate existing files from old structure (optional)
    logger.info("\n[6/6] Migrating existing files (if any)...")
    if not migrate_existing_files(old_icloud_workout_sync, toad_icloud):
        logger.warning("Migration had issues, but continuing...")

    # Display final structure
    logger.info("\nFinal iCloud directory structure:")
    print("\n" + "=" * 60)
    print("~/icloud/TOAD/")
    for child in sorted(toad_icloud.iterdir()):
        if child.name.startswith('.'):
            continue
        children_list = sorted(toad_icloud.iterdir())
        is_last = child == children_list[-1] if children_list else True
        print_directory_tree(child, "", is_last)
    print("=" * 60)

    logger.info("\n✅ Setup complete!")
    logger.info(f"\nDirectories created:")
    logger.info(f"  • TOAD iCloud: {toad_icloud}")
    logger.info(f"  • Health Export: {health_export_icloud}")
    logger.info(f"  • Local cache: {local_cache}")

    logger.info("\n📱 Next steps:")
    logger.info("  1. Configure Health Auto Export to export to 'TOAD_Activity' and 'TOAD_workouts' folders")
    logger.info("  2. Export Gymaholic workouts → iCloud Drive → TOAD/inbox/gymaholic/")
    logger.info("  3. Run 'toad daemon start' to begin watching for files")

    logger.info("\n💡 Quick access:")
    logger.info(f"  • From Terminal: cd {toad_icloud}")
    logger.info(f"  • From Finder: Open → Go to Folder → {toad_icloud}")
    logger.info(f"  • From iPhone: Files app → iCloud Drive → TOAD/")

    return 0


if __name__ == "__main__":
    exit(main())
