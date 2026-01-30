"""TOAD Daemon - Unified event-driven health data processor.

Main daemon class that coordinates file watching and health data processing.
"""

import logging
import signal
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from toad.daemon import (
    TOAD_ICLOUD_BASE,
    HEALTH_EXPORT_ACTIVITY_DIR,
    HEALTH_EXPORT_WORKOUTS_DIR,
    INBOX_GYMAHOLIC_DIR,
    WATCHED_DIRECTORIES,
)
from toad.daemon.file_watcher import FileWatcher
from toad.daemon.event_driven_handler import EventDrivenHealthHandler

logger = logging.getLogger(__name__)

# Timing constants
MAIN_LOOP_SLEEP_SECONDS = 1  # Main loop poll interval


class TOADDaemon:
    """Main daemon class for event-driven health data processing.

    Coordinates file watching and processing across multiple iCloud directories.
    Runs as a background process, watching for new files and processing them
    immediately using the reconciliation engine.
    """

    def __init__(self, base_dir: Optional[Path] = None, watch_dirs: Optional[list[Path]] = None):
        """
        Initialize TOAD daemon.

        Args:
            base_dir: Base daemon directory (defaults to TOAD iCloud base)
            watch_dirs: Directories to watch (defaults to WATCHED_DIRECTORIES)
        """
        self.base_dir = base_dir or TOAD_ICLOUD_BASE
        self.watch_dirs = watch_dirs or WATCHED_DIRECTORIES
        self.is_running = False
        self.start_time: Optional[datetime] = None

        # Initialize handler
        logger.info("[DAEMON] Initializing event-driven handler...")
        self.handler = EventDrivenHealthHandler(self.base_dir)

        # Initialize file watcher
        logger.info("[DAEMON] Initializing file watcher...")
        self.watcher = FileWatcher(
            watch_dirs=self.watch_dirs,
            callback=self.handler.handle_file
        )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("[DAEMON] Initialization complete")

    def start(self):
        """Start the daemon."""
        if self.is_running:
            logger.warning("[DAEMON] Already running")
            return

        logger.info("[DAEMON] Starting TOAD daemon...")
        logger.info(f"[DAEMON] Monitoring {len(self.watch_dirs)} directories:")
        for watch_dir in self.watch_dirs:
            logger.info(f"[DAEMON]   - {watch_dir}")

        # Start file watcher
        self.watcher.start()

        self.is_running = True
        self.start_time = datetime.now()

        logger.info("[DAEMON] TOAD daemon started successfully")
        logger.info("[DAEMON] Press Ctrl+C to stop")

    def stop(self):
        """Stop the daemon."""
        logger.info("[DAEMON] Stopping TOAD daemon...")

        # Stop file watcher if it's alive
        if self.watcher.is_alive():
            self.watcher.stop()

        was_running = self.is_running
        self.is_running = False

        if was_running:
            uptime = datetime.now() - self.start_time if self.start_time else None
            logger.info(f"[DAEMON] TOAD daemon stopped (uptime: {uptime})")
        else:
            logger.debug("[DAEMON] Daemon was not running")

    def run(self):
        """Run the daemon main loop.

        Starts the daemon and runs until interrupted.
        """
        self.start()

        try:
            # Main loop - just keep alive while watcher runs in background
            while self.is_running:
                time.sleep(MAIN_LOOP_SLEEP_SECONDS)
        except KeyboardInterrupt:
            logger.info("[DAEMON] Received keyboard interrupt")
        finally:
            self.stop()

    def status(self) -> dict:
        """Get daemon status.

        Returns:
            Dictionary with status information
        """
        uptime = None
        if self.start_time:
            uptime = datetime.now() - self.start_time

        return {
            "running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": str(uptime) if uptime else None,
            "watcher_alive": self.watcher.is_alive() if self.is_running else False,
            "watched_directories": [str(d) for d in self.watch_dirs],
            "base_dir": str(self.base_dir),
        }

    def health_check(self) -> bool:
        """Perform health check.

        Returns:
            True if daemon is healthy, False otherwise
        """
        if not self.is_running:
            return False

        # Check that watcher is alive
        if not self.watcher.is_alive():
            logger.error("[DAEMON] Health check failed: watcher not alive")
            return False

        # Check that watched directories exist
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                logger.error(f"[DAEMON] Health check failed: {watch_dir} does not exist")
                return False

        return True

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"[DAEMON] Received {signal_name} signal")

        self.is_running = False


def main():
    """Main entry point for daemon."""
    # Setup daemon logging with centralized config
    from toad.logging_config import setup_daemon_logging
    setup_daemon_logging()

    # Create and run daemon
    daemon = TOADDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
