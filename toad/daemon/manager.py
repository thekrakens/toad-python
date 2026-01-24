"""Daemon process management for TOAD.

Handles starting, stopping, and checking status of the TOAD daemon process.
"""

import os
import sys
import signal
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


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
            # Fork process to run in background
            pid = os.fork()

            if pid > 0:
                # Parent process
                # Wait briefly to ensure child started
                time.sleep(0.5)

                # Verify child is still running
                if self.is_running():
                    child_pid = self._read_pid()
                    return {
                        "success": True,
                        "message": f"Daemon started successfully (PID: {child_pid})",
                        "pid": child_pid
                    }
                else:
                    return {
                        "success": False,
                        "message": "Daemon failed to start (check logs)",
                        "pid": None
                    }

        except OSError as e:
            return {
                "success": False,
                "message": f"Fork failed: {e}",
                "pid": None
            }

        # Child process continues here
        self._daemonize()
        return {"success": True, "message": "Daemon started", "pid": os.getpid()}

    def _daemonize(self):
        """
        Daemonize the current process.

        This runs in the child process after fork.
        """
        # Write PID file
        self._write_pid(os.getpid())

        # Detach from terminal
        os.setsid()

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        # Redirect stdin/stdout/stderr to log file
        with open(self.log_file, 'a+') as log_f:
            os.dup2(log_f.fileno(), sys.stdout.fileno())
            os.dup2(log_f.fileno(), sys.stderr.fileno())

        with open(os.devnull, 'r') as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())

        # Start the daemon
        from toad.daemon.daemon import TOADDaemon
        from toad.logging_config import setup_daemon_logging

        setup_daemon_logging(log_file=self.log_file)
        daemon = TOADDaemon()

        try:
            daemon.run()
        except Exception as e:
            logger.error(f"Daemon crashed: {e}", exc_info=True)
        finally:
            # Clean up PID file on exit
            self._remove_pid()

    def stop(self, timeout: int = 10) -> Dict[str, Any]:
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
                time.sleep(0.1)

            # If still running after timeout, force kill
            if self._is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
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
            time.sleep(1)

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
                import subprocess
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
