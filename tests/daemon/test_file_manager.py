"""Tests for daemon file manager."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from toad.daemon.file_manager import FileManager


@pytest.fixture
def temp_daemon_dir(tmp_path):
    """Create temporary daemon directory structure."""
    daemon_dir = tmp_path / ".toad"
    daemon_dir.mkdir()

    # Create subdirectories
    (daemon_dir / "inbox/health/activity").mkdir(parents=True)
    (daemon_dir / "inbox/health/workouts").mkdir(parents=True)
    (daemon_dir / "inbox/gymaholic").mkdir(parents=True)
    (daemon_dir / "staging/health/activity").mkdir(parents=True)
    (daemon_dir / "staging/health/workouts").mkdir(parents=True)
    (daemon_dir / "staging/gymaholic").mkdir(parents=True)
    (daemon_dir / "processed").mkdir()
    (daemon_dir / "failed").mkdir()

    return daemon_dir


@pytest.fixture
def file_manager(temp_daemon_dir):
    """Create FileManager instance with temp directory."""
    return FileManager(temp_daemon_dir)


@pytest.fixture
def sample_file(temp_daemon_dir):
    """Create a sample file in inbox."""
    file_path = temp_daemon_dir / "inbox/health/activity/test_activity.csv"
    file_path.write_text("sample,data,here\n1,2,3")
    return file_path


class TestMoveToStaging:
    """Tests for move_to_staging method."""

    def test_move_to_staging_with_category(self, file_manager, sample_file):
        """Test moving file to staging with category."""
        result = file_manager.move_to_staging(
            sample_file,
            service="health",
            category="activity"
        )

        assert result is not None
        assert result.exists()
        assert result.parent.name == "activity"
        assert result.parent.parent.name == "health"
        assert not sample_file.exists()  # Original should be moved

    def test_move_to_staging_without_category(self, file_manager, temp_daemon_dir):
        """Test moving file to staging without category."""
        file_path = temp_daemon_dir / "inbox/gymaholic/workout.csv"
        file_path.write_text("workout,data")

        result = file_manager.move_to_staging(
            file_path,
            service="gymaholic"
        )

        assert result is not None
        assert result.exists()
        assert result.parent.name == "gymaholic"
        assert not file_path.exists()

    def test_move_to_staging_filename_collision(self, file_manager, sample_file):
        """Test handling filename collision in staging."""
        # Create existing file in staging
        existing = file_manager.staging_dir / "health/activity/test_activity.csv"
        existing.write_text("existing data")

        result = file_manager.move_to_staging(
            sample_file,
            service="health",
            category="activity"
        )

        assert result is not None
        assert result.exists()
        assert result != existing  # Should have different name
        assert "_" in result.stem  # Should have timestamp
        assert existing.exists()  # Original staging file preserved

    def test_move_to_staging_creates_missing_dirs(self, file_manager, temp_daemon_dir):
        """Test that missing directories are created."""
        file_path = temp_daemon_dir / "inbox/health/body/weight.csv"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("weight,data")

        result = file_manager.move_to_staging(
            file_path,
            service="health",
            category="body"
        )

        assert result is not None
        assert result.exists()
        assert (file_manager.staging_dir / "health/body").exists()

    def test_move_to_staging_invalid_file(self, file_manager, temp_daemon_dir):
        """Test moving non-existent file returns None."""
        non_existent = temp_daemon_dir / "inbox/health/nonexistent.csv"

        result = file_manager.move_to_staging(
            non_existent,
            service="health",
            category="activity"
        )

        assert result is None


class TestMoveToProcessed:
    """Tests for move_to_processed method."""

    def test_move_to_processed_preserves_structure(self, file_manager, temp_daemon_dir):
        """Test moving to processed with structure preservation."""
        # Create file in staging
        staging_file = file_manager.staging_dir / "health/activity/test.csv"
        staging_file.write_text("test data")

        result = file_manager.move_to_processed(
            staging_file,
            preserve_structure=True
        )

        assert result is not None
        assert result.exists()
        # Should be in processed/YYYY-MM-DD/health/activity/
        assert result.parent.name == "activity"
        assert result.parent.parent.name == "health"
        assert not staging_file.exists()

    def test_move_to_processed_flat_structure(self, file_manager, temp_daemon_dir):
        """Test moving to processed without structure preservation."""
        staging_file = file_manager.staging_dir / "health/activity/test.csv"
        staging_file.write_text("test data")

        result = file_manager.move_to_processed(
            staging_file,
            preserve_structure=False
        )

        assert result is not None
        assert result.exists()
        # Should be in processed/YYYY-MM-DD/ only
        date_str = datetime.now().strftime("%Y-%m-%d")
        assert result.parent.name == date_str
        assert not staging_file.exists()

    def test_move_to_processed_date_subdirectory(self, file_manager, temp_daemon_dir):
        """Test that processed files go into date-based subdirectory."""
        staging_file = file_manager.staging_dir / "health/test.csv"
        staging_file.write_text("test data")

        result = file_manager.move_to_processed(staging_file)

        date_str = datetime.now().strftime("%Y-%m-%d")
        assert result is not None
        assert date_str in str(result)

    def test_move_to_processed_filename_collision(self, file_manager, temp_daemon_dir):
        """Test handling filename collision in processed."""
        # Create existing processed file
        date_str = datetime.now().strftime("%Y-%m-%d")
        processed_dir = file_manager.processed_dir / date_str / "health"
        processed_dir.mkdir(parents=True)
        existing = processed_dir / "test.csv"
        existing.write_text("existing")

        # Create staging file
        staging_file = file_manager.staging_dir / "health/test.csv"
        staging_file.write_text("new data")

        result = file_manager.move_to_processed(staging_file)

        assert result is not None
        assert result.exists()
        assert result != existing
        assert "_" in result.stem  # Timestamp added
        assert existing.exists()  # Original preserved


class TestMoveToFailed:
    """Tests for move_to_failed method."""

    def test_move_to_failed_creates_error_log(self, file_manager, sample_file):
        """Test that error log is created alongside failed file."""
        error_msg = "Parse error: invalid CSV format"

        failed_file, error_log = file_manager.move_to_failed(
            sample_file,
            error_message=error_msg,
            preserve_structure=True
        )

        assert failed_file is not None
        assert error_log is not None
        assert failed_file.exists()
        assert error_log.exists()
        assert error_msg in error_log.read_text()
        assert sample_file.name in error_log.read_text()
        assert not sample_file.exists()

    def test_move_to_failed_preserves_structure(self, file_manager, temp_daemon_dir):
        """Test moving to failed with structure preservation."""
        staging_file = file_manager.staging_dir / "health/activity/bad.csv"
        staging_file.write_text("bad data")

        failed_file, error_log = file_manager.move_to_failed(
            staging_file,
            error_message="Test error",
            preserve_structure=True
        )

        assert failed_file is not None
        # Should be in failed/YYYY-MM-DD/health/activity/
        assert failed_file.parent.name == "activity"
        assert failed_file.parent.parent.name == "health"

    def test_move_to_failed_from_inbox(self, file_manager, sample_file):
        """Test moving to failed from inbox (before staging)."""
        failed_file, error_log = file_manager.move_to_failed(
            sample_file,
            error_message="Failed before staging",
            preserve_structure=True
        )

        assert failed_file is not None
        assert error_log is not None
        # Should preserve inbox structure
        assert "health" in str(failed_file)

    def test_move_to_failed_error_log_content(self, file_manager, sample_file):
        """Test error log contains all required information."""
        error_msg = "Connection timeout"

        failed_file, error_log = file_manager.move_to_failed(
            sample_file,
            error_message=error_msg
        )

        log_content = error_log.read_text()
        assert f"File: {sample_file.name}" in log_content
        assert f"Error: {error_msg}" in log_content
        assert "Timestamp:" in log_content


class TestCleanupOldProcessedFiles:
    """Tests for cleanup_old_processed_files method."""

    def test_cleanup_deletes_old_directories(self, file_manager, temp_daemon_dir):
        """Test that old processed directories are deleted."""
        # Create old and recent processed directories
        old_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        recent_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        old_dir = file_manager.processed_dir / old_date
        recent_dir = file_manager.processed_dir / recent_date

        old_dir.mkdir()
        recent_dir.mkdir()

        (old_dir / "old_file.csv").write_text("old data")
        (recent_dir / "recent_file.csv").write_text("recent data")

        deleted_count = file_manager.cleanup_old_processed_files(days=30)

        assert deleted_count == 1
        assert not old_dir.exists()
        assert recent_dir.exists()

    def test_cleanup_preserves_recent_files(self, file_manager, temp_daemon_dir):
        """Test that recent files are not deleted."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        today_dir = file_manager.processed_dir / today
        yesterday_dir = file_manager.processed_dir / yesterday

        today_dir.mkdir()
        yesterday_dir.mkdir()

        (today_dir / "file1.csv").write_text("data1")
        (yesterday_dir / "file2.csv").write_text("data2")

        deleted_count = file_manager.cleanup_old_processed_files(days=30)

        assert deleted_count == 0
        assert today_dir.exists()
        assert yesterday_dir.exists()

    def test_cleanup_handles_non_date_directories(self, file_manager, temp_daemon_dir):
        """Test that non-date directories are skipped."""
        non_date_dir = file_manager.processed_dir / "not_a_date"
        non_date_dir.mkdir()

        date_dir = (file_manager.processed_dir /
                   (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d"))
        date_dir.mkdir()

        deleted_count = file_manager.cleanup_old_processed_files(days=30)

        assert non_date_dir.exists()  # Should not be deleted
        assert not date_dir.exists()  # Old date should be deleted
