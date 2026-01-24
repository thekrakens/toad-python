"""Tests for daemon manager."""

import pytest
import os
import signal
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from toad.daemon.manager import DaemonManager


class TestDaemonManagerInit:
    """Tests for DaemonManager initialization."""

    def test_init_default_paths(self):
        """Test initialization with default paths."""
        manager = DaemonManager()

        expected_pid = Path.home() / ".toad" / "daemon.pid"
        expected_log = Path.home() / ".toad" / "daemon.log"

        assert manager.pid_file == expected_pid
        assert manager.log_file == expected_log

    def test_init_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        pid_file = tmp_path / "test.pid"
        log_file = tmp_path / "test.log"

        manager = DaemonManager(pid_file=pid_file, log_file=log_file)

        assert manager.pid_file == pid_file
        assert manager.log_file == log_file

    def test_init_creates_toad_directory(self, tmp_path, monkeypatch):
        """Test that initialization creates .toad directory."""
        # Mock home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()  # Create the fake home directory first
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        manager = DaemonManager()

        toad_dir = fake_home / ".toad"
        assert toad_dir.exists()


class TestDaemonManagerPIDFile:
    """Tests for PID file operations."""

    def test_write_and_read_pid(self, tmp_path):
        """Test writing and reading PID file."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Write PID
        test_pid = 12345
        manager._write_pid(test_pid)

        # Read PID
        read_pid = manager._read_pid()
        assert read_pid == test_pid

    def test_read_pid_nonexistent_file(self, tmp_path):
        """Test reading PID when file doesn't exist."""
        pid_file = tmp_path / "nonexistent.pid"
        manager = DaemonManager(pid_file=pid_file)

        result = manager._read_pid()
        assert result is None

    def test_read_pid_invalid_content(self, tmp_path):
        """Test reading PID with invalid content."""
        pid_file = tmp_path / "invalid.pid"
        pid_file.write_text("not_a_number")

        manager = DaemonManager(pid_file=pid_file)
        result = manager._read_pid()
        assert result is None

    def test_remove_pid(self, tmp_path):
        """Test removing PID file."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Create PID file
        manager._write_pid(12345)
        assert pid_file.exists()

        # Remove it
        manager._remove_pid()
        assert not pid_file.exists()

    def test_remove_pid_nonexistent(self, tmp_path):
        """Test removing PID file that doesn't exist."""
        pid_file = tmp_path / "nonexistent.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Should not raise error
        manager._remove_pid()


class TestDaemonManagerProcessCheck:
    """Tests for process checking."""

    def test_is_process_running_current_process(self):
        """Test checking if current process is running."""
        manager = DaemonManager()
        current_pid = os.getpid()

        assert manager._is_process_running(current_pid) is True

    def test_is_process_running_nonexistent(self):
        """Test checking nonexistent process."""
        manager = DaemonManager()
        # Use a very high PID that's unlikely to exist
        fake_pid = 999999

        assert manager._is_process_running(fake_pid) is False

    def test_is_running_with_valid_pid(self, tmp_path):
        """Test is_running with valid PID file and running process."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Write current process PID
        current_pid = os.getpid()
        manager._write_pid(current_pid)

        assert manager.is_running() is True

    def test_is_running_with_stale_pid(self, tmp_path):
        """Test is_running with stale PID file."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Write a PID that doesn't exist
        manager._write_pid(999999)

        assert manager.is_running() is False

    def test_is_running_no_pid_file(self, tmp_path):
        """Test is_running when PID file doesn't exist."""
        pid_file = tmp_path / "nonexistent.pid"
        manager = DaemonManager(pid_file=pid_file)

        assert manager.is_running() is False


class TestDaemonManagerStatus:
    """Tests for status method."""

    def test_status_not_running(self, tmp_path):
        """Test status when daemon is not running."""
        pid_file = tmp_path / "test.pid"
        log_file = tmp_path / "test.log"
        manager = DaemonManager(pid_file=pid_file, log_file=log_file)

        status = manager.status()

        assert status["running"] is False
        assert status["pid"] is None
        assert status["uptime"] is None
        assert status["log_file"] == str(log_file)
        assert status["pid_file"] == str(pid_file)

    def test_status_running(self, tmp_path):
        """Test status when daemon is running."""
        pid_file = tmp_path / "test.pid"
        log_file = tmp_path / "test.log"
        manager = DaemonManager(pid_file=pid_file, log_file=log_file)

        # Write current process PID
        current_pid = os.getpid()
        manager._write_pid(current_pid)

        status = manager.status()

        assert status["running"] is True
        assert status["pid"] == current_pid
        assert status["log_file"] == str(log_file)
        assert status["pid_file"] == str(pid_file)


class TestDaemonManagerStart:
    """Tests for daemon start method."""

    def test_start_when_already_running(self, tmp_path):
        """Test starting when daemon is already running."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Write current process PID to simulate running daemon
        current_pid = os.getpid()
        manager._write_pid(current_pid)

        result = manager.start()

        assert result["success"] is False
        assert "already running" in result["message"].lower()
        assert result["pid"] == current_pid

    @patch('os.fork')
    def test_start_fork_failure(self, mock_fork, tmp_path):
        """Test start when fork fails."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Simulate fork failure
        mock_fork.side_effect = OSError("Fork failed")

        result = manager.start()

        assert result["success"] is False
        assert "Fork failed" in result["message"]
        assert result["pid"] is None


class TestDaemonManagerStop:
    """Tests for daemon stop method."""

    def test_stop_when_not_running(self, tmp_path):
        """Test stopping when daemon is not running."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        result = manager.stop()

        assert result["success"] is False
        assert "not running" in result["message"].lower()

    def test_stop_with_no_pid_file(self, tmp_path):
        """Test stopping when PID file exists but can't be read."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Create invalid PID file
        pid_file.write_text("invalid")

        result = manager.stop()

        assert result["success"] is False

    @patch('toad.daemon.manager.DaemonManager._is_process_running')
    @patch('os.kill')
    @patch('time.sleep')
    def test_stop_cleans_up_stale_pid(self, mock_sleep, mock_kill, mock_is_running, tmp_path):
        """Test stop cleans up stale PID file."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        # Write a PID
        manager._write_pid(12345)

        # First call to is_running returns True (in is_running()),
        # then os.kill raises ProcessLookupError
        mock_is_running.return_value = True
        mock_kill.side_effect = ProcessLookupError()

        result = manager.stop()

        assert result["success"] is True
        assert "not running" in result["message"].lower() or "cleaned up" in result["message"].lower()
        assert not pid_file.exists()


class TestDaemonManagerRestart:
    """Tests for daemon restart method."""

    def test_restart_when_not_running(self, tmp_path):
        """Test restart when daemon is not running."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        with patch.object(manager, 'start') as mock_start:
            mock_start.return_value = {"success": True, "message": "Started", "pid": 12345}

            result = manager.restart()

            # Should call start directly since not running
            mock_start.assert_called_once()
            assert result["success"] is True

    def test_restart_when_running(self, tmp_path):
        """Test restart when daemon is running."""
        pid_file = tmp_path / "test.pid"
        manager = DaemonManager(pid_file=pid_file)

        with patch.object(manager, 'is_running') as mock_running:
            with patch.object(manager, 'stop') as mock_stop:
                with patch.object(manager, 'start') as mock_start:
                    mock_running.return_value = True
                    mock_stop.return_value = {"success": True, "message": "Stopped"}
                    mock_start.return_value = {"success": True, "message": "Started", "pid": 12345}

                    result = manager.restart()

                    mock_stop.assert_called_once()
                    mock_start.assert_called_once()
                    assert result["success"] is True
