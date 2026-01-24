"""Tests for daemon file watcher."""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, call

from toad.daemon.file_watcher import (
    FileWatcher,
    FileProcessor,
    InboxFileHandler,
    FileType,
)


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
def mock_callback():
    """Create mock callback function."""
    return Mock()


@pytest.fixture
def file_handler(mock_callback):
    """Create InboxFileHandler with mock callback."""
    return InboxFileHandler(mock_callback)


class TestFileTypeDetection:
    """Tests for file type detection."""

    def test_detect_gymaholic_csv(self, file_handler, temp_icloud_dirs):
        """Test detecting Gymaholic CSV files."""
        file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "workout.csv"
        file_path.write_text("workout,data")

        file_type = file_handler._detect_file_type(file_path)

        assert file_type == FileType.GYMAHOLIC_CSV

    def test_detect_health_activity_json(self, file_handler, temp_icloud_dirs):
        """Test detecting Health Auto Export activity JSON files."""
        file_path = temp_icloud_dirs["health_export_base"] / "TOAD_Activity" / "HealthAutoExport-2026-01-23.json"
        file_path.write_text('{"data": {"metrics": []}}')

        file_type = file_handler._detect_file_type(file_path)

        assert file_type == FileType.HEALTH_ACTIVITY_CSV  # Reuses constant

    def test_detect_health_workout_json(self, file_handler, temp_icloud_dirs):
        """Test detecting Health Auto Export workout JSON files."""
        file_path = temp_icloud_dirs["health_export_base"] / "TOAD_workouts" / "HealthAutoExport-2026-01-23.json"
        file_path.write_text('{"data": {"workouts": []}}')

        file_type = file_handler._detect_file_type(file_path)

        assert file_type == FileType.HEALTH_WORKOUT_JSON

    def test_detect_unknown_file(self, file_handler, temp_icloud_dirs):
        """Test detecting unknown file type."""
        file_path = temp_icloud_dirs["toad_base"] / "unknown.txt"
        file_path.write_text("random data")

        file_type = file_handler._detect_file_type(file_path)

        assert file_type == FileType.UNKNOWN

    def test_detect_wrong_extension_in_gymaholic(self, file_handler, temp_icloud_dirs):
        """Test that wrong extension in gymaholic dir is unknown."""
        file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "workout.txt"
        file_path.write_text("workout,data")

        file_type = file_handler._detect_file_type(file_path)

        assert file_type == FileType.UNKNOWN


class TestInboxFileHandler:
    """Tests for InboxFileHandler."""

    def test_on_created_triggers_callback(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that file creation triggers callback."""
        file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "workout.csv"
        file_path.write_text("workout,data")

        # Simulate file created event
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(file_path))

        file_handler.on_created(event)

        # Callback should be called with file path and type
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0]
        assert call_args[0] == file_path
        assert call_args[1] == FileType.GYMAHOLIC_CSV

    def test_on_created_ignores_directories(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that directory creation is ignored."""
        dir_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "subdir"
        dir_path.mkdir()

        from watchdog.events import DirCreatedEvent
        event = DirCreatedEvent(str(dir_path))

        file_handler.on_created(event)

        mock_callback.assert_not_called()

    def test_on_created_ignores_hidden_files(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that hidden files are ignored."""
        file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / ".hidden.csv"
        file_path.write_text("data")

        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(file_path))

        file_handler.on_created(event)

        mock_callback.assert_not_called()

    def test_on_created_ignores_temp_files(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that temp files are ignored."""
        file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "~temp.csv"
        file_path.write_text("data")

        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(file_path))

        file_handler.on_created(event)

        mock_callback.assert_not_called()

    def test_on_created_ignores_unknown_types(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that unknown file types are ignored."""
        file_path = temp_icloud_dirs["toad_base"] / "unknown.xyz"
        file_path.write_text("data")

        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(file_path))

        file_handler.on_created(event)

        mock_callback.assert_not_called()

    def test_on_moved_triggers_callback(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that file move triggers callback."""
        toad_base = temp_icloud_dirs["toad_base"]
        src_path = toad_base / "temp.csv"
        dest_path = toad_base / "inbox" / "gymaholic" / "workout.csv"

        src_path.write_text("workout,data")
        src_path.rename(dest_path)

        from watchdog.events import FileMovedEvent
        event = FileMovedEvent(str(src_path), str(dest_path))

        file_handler.on_moved(event)

        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0]
        assert call_args[0] == dest_path
        assert call_args[1] == FileType.GYMAHOLIC_CSV

    def test_duplicate_processing_prevention(self, file_handler, mock_callback, temp_icloud_dirs):
        """Test that same file isn't processed twice simultaneously."""
        file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "workout.csv"
        file_path.write_text("workout,data")

        # Add to processing set manually
        file_handler._processing.add(str(file_path))

        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(file_path))

        file_handler.on_created(event)

        # Should not trigger callback (already processing)
        mock_callback.assert_not_called()


class TestFileWatcher:
    """Tests for FileWatcher."""

    def test_watcher_initialization(self, temp_icloud_dirs, mock_callback):
        """Test file watcher initializes correctly."""
        watch_dirs = temp_icloud_dirs["watch_dirs"]
        watcher = FileWatcher(watch_dirs, mock_callback)

        assert watcher.watch_dirs == watch_dirs
        assert watcher.callback == mock_callback
        assert len(watcher.watch_dirs) == 3  # 3 iCloud directories

    def test_watcher_start_stop(self, temp_icloud_dirs, mock_callback):
        """Test file watcher can start and stop."""
        watcher = FileWatcher(temp_icloud_dirs["watch_dirs"], mock_callback)

        watcher.start()
        assert watcher.is_alive()

        watcher.stop()
        assert not watcher.is_alive()

    def test_watcher_detects_new_file(self, temp_icloud_dirs, mock_callback):
        """Test watcher detects newly created files."""
        watcher = FileWatcher(temp_icloud_dirs["watch_dirs"], mock_callback)

        watcher.start()

        try:
            # Create a new file in gymaholic inbox
            file_path = temp_icloud_dirs["toad_base"] / "inbox" / "gymaholic" / "workout.csv"
            file_path.write_text("workout,data")

            # Wait for watchdog to detect
            time.sleep(1.0)

            # Callback should be triggered
            mock_callback.assert_called()
            call_args = mock_callback.call_args[0]
            assert call_args[0] == file_path
            assert call_args[1] == FileType.GYMAHOLIC_CSV

        finally:
            watcher.stop()

    def test_watcher_handles_nonexistent_directory(self, tmp_path, mock_callback):
        """Test watcher handles missing watch directories gracefully."""
        # Create watch directories that don't exist yet
        missing_dirs = [
            tmp_path / "missing1",
            tmp_path / "missing2",
        ]

        watcher = FileWatcher(missing_dirs, mock_callback)

        # Should not raise exception - will create directories
        watcher.start()
        assert watcher.is_alive()
        watcher.stop()

        # Directories should have been created
        for dir_path in missing_dirs:
            assert dir_path.exists()


class TestFileProcessor:
    """Tests for FileProcessor."""

    def test_register_handler(self):
        """Test registering file type handlers."""
        processor = FileProcessor()
        mock_handler = Mock()

        processor.register_handler(FileType.GYMAHOLIC_CSV, mock_handler)

        assert FileType.GYMAHOLIC_CSV in processor.handlers
        assert processor.handlers[FileType.GYMAHOLIC_CSV] == mock_handler

    def test_process_file_calls_handler(self, tmp_path):
        """Test processing file calls registered handler."""
        processor = FileProcessor()
        mock_handler = Mock()

        processor.register_handler(FileType.GYMAHOLIC_CSV, mock_handler)

        file_path = tmp_path / "workout.csv"
        file_path.write_text("data")

        processor.process_file(file_path, FileType.GYMAHOLIC_CSV)

        mock_handler.assert_called_once_with(file_path)

    def test_process_file_no_handler(self, tmp_path):
        """Test processing file with no registered handler."""
        processor = FileProcessor()

        file_path = tmp_path / "workout.csv"
        file_path.write_text("data")

        # Should not raise exception
        processor.process_file(file_path, FileType.GYMAHOLIC_CSV)

    def test_process_file_handler_exception(self, tmp_path):
        """Test processing file when handler raises exception."""
        processor = FileProcessor()

        def failing_handler(path):
            raise ValueError("Test error")

        processor.register_handler(FileType.GYMAHOLIC_CSV, failing_handler)

        file_path = tmp_path / "workout.csv"
        file_path.write_text("data")

        # Should not raise exception (error is logged)
        processor.process_file(file_path, FileType.GYMAHOLIC_CSV)

    def test_multiple_handlers(self, tmp_path):
        """Test registering and using multiple handlers."""
        processor = FileProcessor()

        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        processor.register_handler(FileType.GYMAHOLIC_CSV, handler1)
        processor.register_handler(FileType.HEALTH_ACTIVITY_CSV, handler2)
        processor.register_handler(FileType.HEALTH_WORKOUT_JSON, handler3)

        file1 = tmp_path / "workout.csv"
        file2 = tmp_path / "activity.csv"
        file3 = tmp_path / "workouts.json"

        for f in [file1, file2, file3]:
            f.write_text("data")

        processor.process_file(file1, FileType.GYMAHOLIC_CSV)
        processor.process_file(file2, FileType.HEALTH_ACTIVITY_CSV)
        processor.process_file(file3, FileType.HEALTH_WORKOUT_JSON)

        handler1.assert_called_once_with(file1)
        handler2.assert_called_once_with(file2)
        handler3.assert_called_once_with(file3)
