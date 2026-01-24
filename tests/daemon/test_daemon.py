"""Tests for TOAD daemon main class."""

import pytest
import signal
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from toad.daemon.daemon import TOADDaemon


@pytest.fixture
def temp_icloud_dirs(tmp_path):
    """Create temporary iCloud directory structure."""
    # TOAD iCloud directories
    toad_base = tmp_path / "TOAD"
    (toad_base / "inbox" / "gymaholic").mkdir(parents=True)
    (toad_base / "staging").mkdir(parents=True)
    (toad_base / "processed").mkdir(parents=True)
    (toad_base / "failed").mkdir(parents=True)

    # Health Export iCloud directories
    health_export_base = tmp_path / "HealthExport"
    (health_export_base / "TOAD_Activity").mkdir(parents=True)
    (health_export_base / "TOAD_workouts").mkdir(parents=True)

    return {
        "toad_base": toad_base,
        "health_export_base": health_export_base,
        "watch_dirs": [
            health_export_base / "TOAD_Activity",
            health_export_base / "TOAD_workouts",
            toad_base / "inbox" / "gymaholic",
        ]
    }


@pytest.fixture
def mock_watcher():
    """Create mock FileWatcher."""
    watcher = MagicMock()
    watcher.is_alive.return_value = True
    return watcher


@pytest.fixture
def mock_handler():
    """Create mock EventDrivenHealthHandler."""
    handler = MagicMock()
    handler.handle_file.return_value = True
    return handler


@pytest.fixture
def daemon(temp_icloud_dirs, mock_watcher, mock_handler):
    """Create TOADDaemon with mocked dependencies."""
    with patch("toad.daemon.daemon.FileWatcher", return_value=mock_watcher), \
         patch("toad.daemon.daemon.EventDrivenHealthHandler", return_value=mock_handler):
        daemon = TOADDaemon(
            base_dir=temp_icloud_dirs["toad_base"],
            watch_dirs=temp_icloud_dirs["watch_dirs"]
        )
        daemon.watcher = mock_watcher
        daemon.handler = mock_handler
        return daemon


class TestDaemonInitialization:
    """Tests for daemon initialization."""

    def test_daemon_initializes_with_default_base_dir(self, mock_watcher, mock_handler):
        """Test daemon initializes with default iCloud base directory."""
        with patch("toad.daemon.daemon.FileWatcher", return_value=mock_watcher), \
             patch("toad.daemon.daemon.EventDrivenHealthHandler", return_value=mock_handler):
            daemon = TOADDaemon()

            assert daemon.base_dir is not None
            assert daemon.is_running is False
            assert daemon.start_time is None

    def test_daemon_initializes_with_custom_base_dir(
        self,
        temp_icloud_dirs,
        mock_watcher,
        mock_handler
    ):
        """Test daemon initializes with custom base directory."""
        custom_base = temp_icloud_dirs["toad_base"]

        with patch("toad.daemon.daemon.FileWatcher", return_value=mock_watcher), \
             patch("toad.daemon.daemon.EventDrivenHealthHandler", return_value=mock_handler):
            daemon = TOADDaemon(base_dir=custom_base)

            assert daemon.base_dir == custom_base

    def test_daemon_creates_handler_and_watcher(
        self,
        temp_icloud_dirs,
        mock_watcher,
        mock_handler
    ):
        """Test daemon creates EventDrivenHealthHandler and FileWatcher."""
        with patch("toad.daemon.daemon.FileWatcher", return_value=mock_watcher) as watcher_cls, \
             patch("toad.daemon.daemon.EventDrivenHealthHandler", return_value=mock_handler) as handler_cls:
            daemon = TOADDaemon(base_dir=temp_icloud_dirs["toad_base"])

            # Handler should be created with base_dir
            handler_cls.assert_called_once_with(temp_icloud_dirs["toad_base"])

            # Watcher should be created with watch_dirs and handler callback
            watcher_cls.assert_called_once()
            call_kwargs = watcher_cls.call_args[1]
            assert "watch_dirs" in call_kwargs
            assert "callback" in call_kwargs


class TestDaemonLifecycle:
    """Tests for daemon start/stop lifecycle."""

    def test_start_daemon(self, daemon, mock_watcher):
        """Test starting the daemon."""
        daemon.start()

        assert daemon.is_running is True
        assert daemon.start_time is not None
        mock_watcher.start.assert_called_once()

    def test_start_already_running_daemon(self, daemon, mock_watcher):
        """Test starting daemon that's already running."""
        daemon.start()
        mock_watcher.start.assert_called_once()

        # Try to start again
        daemon.start()

        # Should not call start again
        mock_watcher.start.assert_called_once()

    def test_stop_daemon(self, daemon, mock_watcher):
        """Test stopping the daemon."""
        daemon.start()
        daemon.stop()

        assert daemon.is_running is False
        mock_watcher.stop.assert_called_once()

    def test_stop_not_running_daemon(self, daemon, mock_watcher):
        """Test stopping daemon that's not running."""
        # Set watcher to not be alive (daemon was never started)
        mock_watcher.is_alive.return_value = False

        daemon.stop()

        # Should not crash, and should not call watcher.stop (watcher not alive)
        mock_watcher.stop.assert_not_called()

    def test_start_stop_cycle(self, daemon, mock_watcher):
        """Test full start/stop cycle."""
        # Start
        daemon.start()
        assert daemon.is_running is True
        start_time = daemon.start_time

        # Stop
        daemon.stop()
        assert daemon.is_running is False

        # Start again
        daemon.start()
        assert daemon.is_running is True
        assert daemon.start_time != start_time  # Should be a new start time


class TestDaemonStatus:
    """Tests for daemon status reporting."""

    def test_status_when_not_running(self, daemon):
        """Test status when daemon is not running."""
        status = daemon.status()

        assert status["running"] is False
        assert status["start_time"] is None
        assert status["uptime"] is None
        assert status["watcher_alive"] is False
        assert "watched_directories" in status
        assert "base_dir" in status

    def test_status_when_running(self, daemon, mock_watcher):
        """Test status when daemon is running."""
        daemon.start()

        status = daemon.status()

        assert status["running"] is True
        assert status["start_time"] is not None
        assert status["uptime"] is not None
        assert status["watcher_alive"] is True
        assert len(status["watched_directories"]) == 3

    def test_status_includes_correct_directories(self, daemon, temp_icloud_dirs):
        """Test status includes correct watched directories."""
        status = daemon.status()

        watched_dirs = status["watched_directories"]
        assert len(watched_dirs) == 3
        assert any("TOAD_Activity" in d for d in watched_dirs)
        assert any("TOAD_workouts" in d for d in watched_dirs)
        assert any("gymaholic" in d for d in watched_dirs)


class TestDaemonHealthCheck:
    """Tests for daemon health check."""

    def test_health_check_when_not_running(self, daemon):
        """Test health check returns False when not running."""
        assert daemon.health_check() is False

    def test_health_check_when_healthy(self, daemon, mock_watcher):
        """Test health check returns True when daemon is healthy."""
        daemon.start()

        assert daemon.health_check() is True

    def test_health_check_when_watcher_dead(self, daemon, mock_watcher):
        """Test health check returns False when watcher is not alive."""
        daemon.start()

        # Simulate watcher dying
        mock_watcher.is_alive.return_value = False

        assert daemon.health_check() is False

    def test_health_check_when_directory_missing(
        self,
        daemon,
        temp_icloud_dirs,
        mock_watcher
    ):
        """Test health check returns False when watched directory is missing."""
        daemon.start()

        # Delete one of the watched directories
        watch_dir = temp_icloud_dirs["watch_dirs"][0]
        watch_dir.rmdir()

        assert daemon.health_check() is False


class TestDaemonSignalHandling:
    """Tests for daemon signal handling."""

    def test_sigint_handler_stops_daemon(self, daemon, mock_watcher):
        """Test SIGINT signal handler stops the daemon."""
        daemon.start()

        # Simulate SIGINT
        daemon._signal_handler(signal.SIGINT, None)

        assert daemon.is_running is False

    def test_sigterm_handler_stops_daemon(self, daemon, mock_watcher):
        """Test SIGTERM signal handler stops the daemon."""
        daemon.start()

        # Simulate SIGTERM
        daemon._signal_handler(signal.SIGTERM, None)

        assert daemon.is_running is False


class TestDaemonRun:
    """Tests for daemon run method."""

    def test_run_starts_daemon(self, daemon, mock_watcher):
        """Test run() starts the daemon."""
        # Mock time.sleep to avoid blocking
        with patch("time.sleep") as mock_sleep:
            # Make sleep raise exception to exit loop immediately
            mock_sleep.side_effect = KeyboardInterrupt()

            try:
                daemon.run()
            except KeyboardInterrupt:
                pass

        # Should have started
        mock_watcher.start.assert_called_once()

    def test_run_stops_daemon_on_keyboard_interrupt(self, daemon, mock_watcher):
        """Test run() stops daemon on KeyboardInterrupt."""
        with patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = KeyboardInterrupt()

            daemon.run()

        # Should have stopped
        mock_watcher.stop.assert_called_once()
        assert daemon.is_running is False

    def test_run_handles_signal(self, daemon, mock_watcher):
        """Test run() handles signal gracefully."""
        with patch("time.sleep") as mock_sleep:
            # On first sleep, set is_running to False (simulates signal)
            def stop_daemon(*args):
                if not hasattr(stop_daemon, "called"):
                    stop_daemon.called = True
                    daemon.is_running = False

            mock_sleep.side_effect = stop_daemon

            daemon.run()

        # Should have stopped cleanly
        mock_watcher.stop.assert_called_once()


class TestDaemonIntegration:
    """Integration tests for daemon with real file watcher (short-lived)."""

    def test_daemon_with_real_watcher(self, temp_icloud_dirs):
        """Test daemon with real FileWatcher (short integration test)."""
        with patch("toad.daemon.daemon.EventDrivenHealthHandler") as mock_handler_cls:
            # Create mock handler instance
            mock_handler = MagicMock()
            mock_handler.handle_file.return_value = True
            mock_handler_cls.return_value = mock_handler

            # Create daemon with real watcher
            daemon = TOADDaemon(
                base_dir=temp_icloud_dirs["toad_base"],
                watch_dirs=temp_icloud_dirs["watch_dirs"]
            )

            # Start daemon
            daemon.start()

            try:
                # Verify it's running
                assert daemon.is_running is True
                assert daemon.watcher.is_alive() is True

                # Verify health check passes
                assert daemon.health_check() is True

                # Small delay to let watcher initialize
                time.sleep(0.5)

            finally:
                # Stop daemon
                daemon.stop()

            # Verify it stopped
            assert daemon.is_running is False
            assert daemon.watcher.is_alive() is False
