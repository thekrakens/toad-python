"""File management utilities for TOAD daemon.

Handles safe file movement between directories (inbox → staging → processed/failed)
with timestamp collision handling and error logging.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for the daemon."""

    def __init__(self, base_dir: Path):
        """
        Initialize file manager.

        Args:
            base_dir: Base daemon directory (typically ~/.toad/)
        """
        self.base_dir = base_dir
        self.inbox_dir = base_dir / "inbox"
        self.staging_dir = base_dir / "staging"
        self.processed_dir = base_dir / "processed"
        self.failed_dir = base_dir / "failed"

    def move_to_staging(
        self,
        source_file: Path,
        service: str,
        category: Optional[str] = None
    ) -> Optional[Path]:
        """
        Move file from inbox to staging directory.

        Args:
            source_file: Source file path in inbox/
            service: Service name (e.g., 'health', 'gymaholic')
            category: Optional category (e.g., 'activity', 'workouts')

        Returns:
            Path to file in staging, or None if move failed
        """
        try:
            # Determine destination
            if category:
                dest_dir = self.staging_dir / service / category
            else:
                dest_dir = self.staging_dir / service

            dest_dir.mkdir(parents=True, exist_ok=True)

            # Handle filename collision
            dest_file = self._get_unique_filename(dest_dir, source_file.name)

            # Move file
            shutil.move(str(source_file), str(dest_file))

            logger.info(
                f"[FILE_MANAGER] Moved to staging: {source_file.name} -> "
                f"{dest_file.relative_to(self.base_dir)}"
            )

            return dest_file

        except Exception as e:
            logger.error(
                f"[FILE_MANAGER] Failed to move {source_file.name} to staging: {e}"
            )
            return None

    def move_to_processed(
        self,
        source_file: Path,
        preserve_structure: bool = True
    ) -> Optional[Path]:
        """
        Move file from staging to processed directory.

        Args:
            source_file: Source file path in staging/
            preserve_structure: If True, preserve service/category subdirs

        Returns:
            Path to file in processed, or None if move failed
        """
        try:
            # Create date-based subdirectory
            date_str = datetime.now().strftime("%Y-%m-%d")
            dest_dir = self.processed_dir / date_str

            if preserve_structure:
                # Preserve service/category structure
                try:
                    rel_path = source_file.relative_to(self.staging_dir)
                    dest_dir = dest_dir / rel_path.parent
                except ValueError:
                    pass  # File not in staging, use flat structure

            dest_dir.mkdir(parents=True, exist_ok=True)

            # Handle filename collision with timestamp
            dest_file = self._get_unique_filename(dest_dir, source_file.name)

            # Move file
            shutil.move(str(source_file), str(dest_file))

            logger.info(
                f"[FILE_MANAGER] Moved to processed: {source_file.name} -> "
                f"{dest_file.relative_to(self.base_dir)}"
            )

            return dest_file

        except Exception as e:
            logger.error(
                f"[FILE_MANAGER] Failed to move {source_file.name} to processed: {e}"
            )
            return None

    def move_to_failed(
        self,
        source_file: Path,
        error_message: str,
        preserve_structure: bool = True
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Move file to failed directory with error log.

        Args:
            source_file: Source file path
            error_message: Error details to log
            preserve_structure: If True, preserve service/category subdirs

        Returns:
            Tuple of (failed_file_path, error_log_path), or (None, None) if move failed
        """
        try:
            # Create date-based subdirectory
            date_str = datetime.now().strftime("%Y-%m-%d")
            dest_dir = self.failed_dir / date_str

            if preserve_structure:
                # Preserve service/category structure
                try:
                    # Try to get relative path from staging or inbox
                    for parent in [self.staging_dir, self.inbox_dir]:
                        try:
                            rel_path = source_file.relative_to(parent)
                            dest_dir = dest_dir / rel_path.parent
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass  # Use flat structure

            dest_dir.mkdir(parents=True, exist_ok=True)

            # Move file with unique name
            dest_file = self._get_unique_filename(dest_dir, source_file.name)
            shutil.move(str(source_file), str(dest_file))

            # Create error log
            error_log = dest_file.with_suffix(dest_file.suffix + ".error.log")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_content = f"""File: {source_file.name}
Timestamp: {timestamp}
Error: {error_message}
"""
            error_log.write_text(error_content)

            logger.error(
                f"[FILE_MANAGER] Moved to failed: {source_file.name} -> "
                f"{dest_file.relative_to(self.base_dir)}"
            )
            logger.error(f"[FILE_MANAGER] Error log: {error_log.relative_to(self.base_dir)}")

            return dest_file, error_log

        except Exception as e:
            logger.error(
                f"[FILE_MANAGER] Failed to move {source_file.name} to failed dir: {e}"
            )
            return None, None

    def _get_unique_filename(self, directory: Path, filename: str) -> Path:
        """
        Get unique filename in directory, adding timestamp if collision.

        Args:
            directory: Destination directory
            filename: Desired filename

        Returns:
            Unique file path
        """
        dest_file = directory / filename

        if not dest_file.exists():
            return dest_file

        # Collision detected, add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(filename).stem
        suffix = Path(filename).suffix

        unique_name = f"{stem}_{timestamp}{suffix}"
        unique_file = directory / unique_name

        logger.warning(
            f"[FILE_MANAGER] Filename collision, renamed: {filename} -> {unique_name}"
        )

        return unique_file

    def cleanup_old_processed_files(self, days: int = 30) -> int:
        """
        Clean up processed files older than specified days.

        Args:
            days: Number of days to retain processed files

        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

            deleted_count = 0

            for date_dir in self.processed_dir.iterdir():
                if not date_dir.is_dir():
                    continue

                try:
                    # Parse date from directory name (YYYY-MM-DD)
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")

                    if dir_date < cutoff_date:
                        shutil.rmtree(date_dir)
                        deleted_count += 1
                        logger.info(
                            f"[FILE_MANAGER] Deleted old processed directory: {date_dir.name}"
                        )

                except ValueError:
                    # Not a date directory, skip
                    continue

            if deleted_count > 0:
                logger.info(
                    f"[FILE_MANAGER] Cleanup complete: deleted {deleted_count} old directories"
                )

            return deleted_count

        except Exception as e:
            logger.error(f"[FILE_MANAGER] Cleanup failed: {e}")
            return 0
