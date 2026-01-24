"""File watcher for TOAD daemon.

Monitors inbox directories for new files and triggers processing.
Uses watchdog library for cross-platform filesystem event monitoring.
"""

import logging
import time
from pathlib import Path
from typing import Callable, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

logger = logging.getLogger(__name__)


class FileType:
    """File type constants."""
    GYMAHOLIC_CSV = "gymaholic_csv"
    HEALTH_ACTIVITY_CSV = "health_activity_csv"
    HEALTH_WORKOUT_JSON = "health_workout_json"
    HEALTH_BODY_CSV = "health_body_csv"
    UNKNOWN = "unknown"


class InboxFileHandler(FileSystemEventHandler):
    """Handles file system events in inbox directories."""

    def __init__(self, callback: Callable[[Path, str], None]):
        """
        Initialize file handler.

        Args:
            callback: Function to call when new file detected.
                      Signature: callback(file_path: Path, file_type: str)
        """
        super().__init__()
        self.callback = callback
        self._processing = set()  # Track files being processed

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore hidden files and temp files
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return

        # Avoid duplicate processing
        if str(file_path) in self._processing:
            return

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        # Verify file still exists and is complete
        if not file_path.exists():
            return

        logger.info(f"[WATCHER] New file detected: {file_path.name}")

        # Detect file type and trigger callback
        file_type = self._detect_file_type(file_path)

        if file_type != FileType.UNKNOWN:
            self._processing.add(str(file_path))
            try:
                self.callback(file_path, file_type)
            finally:
                self._processing.discard(str(file_path))
        else:
            logger.warning(
                f"[WATCHER] Unknown file type, ignoring: {file_path.name}"
            )

    def on_moved(self, event):
        """Handle file move events (treated as new file)."""
        if event.is_directory:
            return

        # Treat destination of move as a new file
        dest_path = Path(event.dest_path)

        if dest_path.name.startswith('.') or dest_path.name.startswith('~'):
            return

        logger.info(f"[WATCHER] File moved to inbox: {dest_path.name}")

        file_type = self._detect_file_type(dest_path)

        if file_type != FileType.UNKNOWN:
            self._processing.add(str(dest_path))
            try:
                self.callback(dest_path, file_type)
            finally:
                self._processing.discard(str(dest_path))

    def _detect_file_type(self, file_path: Path) -> str:
        """
        Detect file type based on path.

        Args:
            file_path: Path to file

        Returns:
            FileType constant
        """
        # Check by directory structure
        parts = file_path.parts

        # Gymaholic CSV in inbox/gymaholic/
        if 'gymaholic' in parts and file_path.suffix.lower() == '.csv':
            return FileType.GYMAHOLIC_CSV

        # Health Auto Export Activity (TOAD_Activity directory)
        # Contains activity metrics + body metrics (weight, body fat, etc.)
        if 'TOAD_Activity' in parts and file_path.suffix.lower() == '.json':
            return FileType.HEALTH_ACTIVITY_CSV  # Reusing constant name

        # Health Auto Export Workouts (TOAD_workouts directory)
        if 'TOAD_workouts' in parts and file_path.suffix.lower() == '.json':
            return FileType.HEALTH_WORKOUT_JSON

        return FileType.UNKNOWN


class FileWatcher:
    """Watches multiple iCloud directories for new files."""

    def __init__(
        self,
        watch_dirs: list[Path],
        callback: Callable[[Path, str], None]
    ):
        """
        Initialize file watcher.

        Args:
            watch_dirs: List of directories to monitor (5 iCloud locations)
            callback: Function to call when new file detected
        """
        self.watch_dirs = watch_dirs
        self.callback = callback
        self.observer = Observer()
        self.event_handler = InboxFileHandler(callback)

    def start(self):
        """Start watching all configured directories."""
        logger.info(f"[WATCHER] Starting file watcher for {len(self.watch_dirs)} directories")

        for watch_dir in self.watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(
                    self.event_handler,
                    str(watch_dir),
                    recursive=False
                )
                logger.info(f"[WATCHER] Monitoring: {watch_dir}")
            else:
                logger.warning(f"[WATCHER] Directory not found (will create): {watch_dir}")
                # Create missing directories
                try:
                    watch_dir.mkdir(parents=True, exist_ok=True)
                    self.observer.schedule(
                        self.event_handler,
                        str(watch_dir),
                        recursive=False
                    )
                    logger.info(f"[WATCHER] Created and monitoring: {watch_dir}")
                except Exception as e:
                    logger.error(f"[WATCHER] Failed to create directory {watch_dir}: {e}")

        self.observer.start()
        logger.info("[WATCHER] File watcher started successfully")

    def stop(self):
        """Stop watching inbox directories."""
        self.observer.stop()
        self.observer.join()
        logger.info("[WATCHER] File watcher stopped")

    def is_alive(self) -> bool:
        """Check if watcher is running."""
        return self.observer.is_alive()


class FileProcessor:
    """Processes files detected by the watcher."""

    def __init__(self):
        """Initialize file processor."""
        self.handlers: Dict[str, Callable[[Path], None]] = {}

    def register_handler(self, file_type: str, handler: Callable[[Path], None]):
        """
        Register a handler for a specific file type.

        Args:
            file_type: FileType constant
            handler: Function to process file
        """
        self.handlers[file_type] = handler
        logger.info(f"[PROCESSOR] Registered handler for: {file_type}")

    def process_file(self, file_path: Path, file_type: str):
        """
        Process a file using registered handler.

        Args:
            file_path: Path to file
            file_type: FileType constant
        """
        handler = self.handlers.get(file_type)

        if handler is None:
            logger.error(f"[PROCESSOR] No handler registered for: {file_type}")
            return

        try:
            logger.info(
                f"[PROCESSOR] Processing {file_type}: {file_path.name}"
            )
            handler(file_path)
            logger.info(
                f"[PROCESSOR] Successfully processed: {file_path.name}"
            )

        except Exception as e:
            logger.error(
                f"[PROCESSOR] Failed to process {file_path.name}: {e}",
                exc_info=True
            )
