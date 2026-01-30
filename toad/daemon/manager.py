"""Daemon process management for TOAD.

Handles starting, stopping, and checking status of the TOAD daemon process.
"""

import os
import sys
import signal
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Timing constants
POST_SPAWN_VERIFY_DELAY = 1.0  # Seconds to wait after spawning before verifying
STOP_TIMEOUT_DEFAULT = 10  # Default graceful shutdown timeout
TERMINATION_POLL_INTERVAL = 0.1  # Poll interval during shutdown
POST_KILL_DELAY = 0.5  # Delay after SIGKILL
RESTART_DELAY = 1.0  # Delay between stop and start on restart


class DaemonManager:
    """Manages the TOAD daemon process lifecycle."""

    def __init__(self, pid_file: Optional[Path] = None, log_file: Optional[Path] = None):
        """
        Initialize daemon manager.

        Args:
            pid_file: Path to PID file (default: ~/.toad/daemon.pid)
            log_file: Path to log file (default: ~/.toad/daemon.log)
        """
        toad_dir = Path.home() / ".toad"
        toad_dir.mkdir(exist_ok=True)

        self.pid_file = pid_file or toad_dir / "daemon.pid"
        self.log_file = log_file or toad_dir / "daemon.log"

    def start(self) -> Dict[str, Any]:
        """
        Start the daemon process.

        Returns:
            Dict with result:
                - success: bool
                - message: str
                - pid: Optional[int]
        """
        # Check if already running
        if self.is_running():
            pid = self._read_pid()
            return {
                "success": False,
                "message": f"Daemon already running (PID: {pid})",
                "pid": pid
            }

        try:
            # Spawn daemon as a clean subprocess (avoids macOS fork issues)
            # Run: python -m toad.daemon.daemon
            python_exe = sys.executable

            # Redirect stdout/stderr to log file
            log_file_handle = open(self.log_file, 'a')

            # Start daemon process in background
            process = subprocess.Popen(
                [python_exe, "-m", "toad.daemon.daemon"],
                stdout=log_file_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent session
                cwd=os.path.expanduser("~"),
                env=os.environ.copy()
            )

            # Write PID file
            self._write_pid(process.pid)

            # Wait briefly to ensure daemon started
            time.sleep(POST_SPAWN_VERIFY_DELAY)

            # Verify daemon is still running
            if self.is_running():
                return {
                    "success": True,
                    "message": f"Daemon started successfully (PID: {process.pid})",
                    "pid": process.pid
                }
            else:
                return {
                    "success": False,
                    "message": "Daemon failed to start (check logs)",
                    "pid": None
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start daemon: {e}",
                "pid": None
            }

    def stop(self, timeout: int = STOP_TIMEOUT_DEFAULT) -> Dict[str, Any]:
        """
        Stop the daemon process.

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            Dict with result:
                - success: bool
                - message: str
        """
        if not self.is_running():
            return {
                "success": False,
                "message": "Daemon is not running"
            }

        pid = self._read_pid()
        if not pid:
            return {
                "success": False,
                "message": "Could not read PID file"
            }

        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)

            # Wait for process to exit
            start = time.time()
            while time.time() - start < timeout:
                if not self._is_process_running(pid):
                    self._remove_pid()
                    return {
                        "success": True,
                        "message": f"Daemon stopped successfully (PID: {pid})"
                    }
                time.sleep(TERMINATION_POLL_INTERVAL)

            # If still running after timeout, force kill
            if self._is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
                time.sleep(POST_KILL_DELAY)
                self._remove_pid()
                return {
                    "success": True,
                    "message": f"Daemon force-killed (PID: {pid})"
                }

        except ProcessLookupError:
            # Process already dead
            self._remove_pid()
            return {
                "success": True,
                "message": "Daemon was not running (cleaned up stale PID file)"
            }
        except PermissionError:
            return {
                "success": False,
                "message": f"Permission denied when stopping daemon (PID: {pid})"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error stopping daemon: {e}"
            }

        return {
            "success": False,
            "message": "Failed to stop daemon"
        }

    def restart(self) -> Dict[str, Any]:
        """
        Restart the daemon (stop then start).

        Returns:
            Dict with result:
                - success: bool
                - message: str
                - pid: Optional[int]
        """
        # Stop if running
        if self.is_running():
            stop_result = self.stop()
            if not stop_result["success"]:
                return stop_result

            # Wait for full shutdown
            time.sleep(RESTART_DELAY)

        # Start
        return self.start()

    def status(self) -> Dict[str, Any]:
        """
        Get daemon status.

        Returns:
            Dict with status:
                - running: bool
                - pid: Optional[int]
                - uptime: Optional[str]
                - log_file: str
                - pid_file: str
        """
        running = self.is_running()
        pid = self._read_pid() if running else None

        status = {
            "running": running,
            "pid": pid,
            "uptime": None,
            "log_file": str(self.log_file),
            "pid_file": str(self.pid_file)
        }

        # Get uptime if running
        if running and pid:
            try:
                # Read process start time from /proc (Linux) or ps (macOS)
                if sys.platform == "darwin":
                    # macOS: use ps to get elapsed time
                    result = subprocess.run(
                        ["ps", "-p", str(pid), "-o", "etime="],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        status["uptime"] = result.stdout.strip()
                else:
                    # Linux: could use /proc/[pid]/stat
                    pass
            except Exception:
                pass

        return status

    def is_running(self) -> bool:
        """
        Check if daemon is running.

        Returns:
            True if daemon is running, False otherwise
        """
        pid = self._read_pid()
        if not pid:
            return False

        return self._is_process_running(pid)

    def _is_process_running(self, pid: int) -> bool:
        """
        Check if a process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process exists, False otherwise
        """
        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission
            return True

    def _read_pid(self) -> Optional[int]:
        """
        Read PID from PID file.

        Returns:
            PID if file exists and is valid, None otherwise
        """
        if not self.pid_file.exists():
            return None

        try:
            pid_str = self.pid_file.read_text().strip()
            return int(pid_str)
        except (ValueError, OSError):
            return None

    def _write_pid(self, pid: int):
        """
        Write PID to PID file.

        Args:
            pid: Process ID to write
        """
        self.pid_file.write_text(str(pid))

    def _remove_pid(self):
        """Remove PID file if it exists."""
        if self.pid_file.exists():
            self.pid_file.unlink()
