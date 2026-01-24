"""Tests for event-driven health data handler."""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, call

from toad.daemon.event_driven_handler import EventDrivenHealthHandler
from toad.daemon.file_watcher import FileType
from toad.health.models import WorkoutData, ExerciseData, DailyActivityMetrics


@pytest.fixture
def temp_daemon_dir(tmp_path):
    """Create temporary daemon directory structure (iCloud-based)."""
    # TOAD iCloud base
    base_dir = tmp_path / "TOAD"
    (base_dir / "inbox" / "gymaholic").mkdir(parents=True)
    (base_dir / "staging").mkdir(parents=True)
    (base_dir / "processed").mkdir(parents=True)
    (base_dir / "failed").mkdir(parents=True)

    return base_dir


@pytest.fixture
def temp_health_export_dir(tmp_path):
    """Create temporary Health Export iCloud directory structure."""
    health_export_dir = tmp_path / "HealthExport"
    (health_export_dir / "TOAD_Activity").mkdir(parents=True)
    (health_export_dir / "TOAD_workouts").mkdir(parents=True)
    return health_export_dir


@pytest.fixture
def mock_notion_client():
    """Create mock Notion client."""
    client = MagicMock()
    client.databases.query.return_value = {"results": []}
    client.pages.update.return_value = {"id": "page-123"}
    return client


@pytest.fixture
def mock_notion_sync():
    """Create mock HealthNotionSync."""
    sync = MagicMock()
    sync.sync_workout.return_value = {"success": True}
    sync.update_habit_tracker_metrics.return_value = {
        "success": True,
        "updated_fields": ["CaloriesOut", "Weight"]
    }
    return sync


@pytest.fixture
def handler(temp_daemon_dir, mock_notion_client, mock_notion_sync):
    """Create EventDrivenHealthHandler with mocked dependencies."""
    # Create a proper mock for Config class
    mock_config_class = Mock()
    mock_config_class.NOTION_WORKOUTS_DATABASE_ID = "test-workout-db-id"

    with patch("toad.daemon.event_driven_handler.TOADNotionClient", return_value=mock_notion_client), \
         patch("toad.daemon.event_driven_handler.HealthNotionSync", return_value=mock_notion_sync), \
         patch("toad.daemon.event_driven_handler.Config", mock_config_class):
        handler = EventDrivenHealthHandler(temp_daemon_dir)
        handler.notion_client = mock_notion_client
        handler.notion_sync = mock_notion_sync
        return handler


@pytest.fixture
def sample_gymaholic_csv_content():
    """Sample Gymaholic CSV content (semicolon-delimited format)."""
    return """;-----------------
;TOMO B Strength
;-----------------
;Date;Jan 21., 18:30
;Duration;1h:28m
;KCAL;495
;Heart rate;116 bpm
;-----------------
#;Barbell Squat
1;;225 lbs x 5
2;;225 lbs x 5
3;;225 lbs x 5
#;Bench Press
1;;185 lbs x 8
2;;185 lbs x 8
3;;185 lbs x 7
"""


@pytest.fixture
def sample_health_workout_json_content():
    """Sample HealthAutoExport workout JSON content."""
    return """{
    "data": {
        "workouts": [
            {
                "name": "Cross Training",
                "start": "2026-01-21 18:25:00 +0000",
                "duration": 5520,
                "activeEnergyBurned": {"qty": 510},
                "avgHeartRate": {"qty": 118}
            }
        ]
    }
}"""


@pytest.fixture
def sample_activity_json_content():
    """Sample HealthAutoExport activity JSON content."""
    return """{
    "data": {
        "metrics": [
            {
                "name": "dietary_energy",
                "data": [
                    {"date": "2026-01-21 00:00:00 -0800", "qty": 2400}
                ]
            },
            {
                "name": "active_energy",
                "data": [
                    {"date": "2026-01-21 00:00:00 -0800", "qty": 650}
                ]
            },
            {
                "name": "weight_body_mass",
                "data": [
                    {"date": "2026-01-21 00:00:00 -0800", "qty": 185.5}
                ]
            },
            {
                "name": "body_fat_percentage",
                "data": [
                    {"date": "2026-01-21 00:00:00 -0800", "qty": 18.2}
                ]
            }
        ]
    }
}"""


class TestGymaholicWorkoutHandling:
    """Tests for Gymaholic workout processing."""

    def test_gymaholic_no_match_creates_new_workout(
        self,
        handler,
        temp_daemon_dir,
        sample_gymaholic_csv_content,
        mock_notion_client
    ):
        """Test that new Gymaholic workout creates new Notion page when no match."""
        # Create CSV file in inbox
        csv_file = temp_daemon_dir / "inbox" / "gymaholic" / "workout.csv"
        csv_file.write_text(sample_gymaholic_csv_content)

        # No existing workouts (no match)
        mock_notion_client.databases.query.return_value = {"results": []}

        # Process file
        result = handler.handle_file(csv_file, FileType.GYMAHOLIC_CSV)

        assert result is True

        # Should have called sync_workout to create new
        handler.notion_sync.sync_workout.assert_called_once()

        # File should be in processed directory
        processed_files = list((temp_daemon_dir / "processed").rglob("*.csv"))
        assert len(processed_files) == 1

    def test_gymaholic_match_merges_with_existing(
        self,
        handler,
        temp_daemon_dir,
        sample_gymaholic_csv_content,
        mock_notion_client
    ):
        """Test that Gymaholic workout merges when matching HealthAutoExport workout found."""
        # Create CSV file in inbox
        csv_file = temp_daemon_dir / "inbox" / "gymaholic" / "workout.csv"
        csv_file.write_text(sample_gymaholic_csv_content)

        # Mock existing HealthAutoExport workout with compatible type
        # Gymaholic returns "Strength", so use "Traditional Strength Training" (compatible)
        existing_workout = {
            "id": "workout-123",
            "properties": {
                "Type": {"select": {"name": "Traditional Strength Training"}},
                "Date": {"date": {"start": "2026-01-21T18:25:00+00:00"}},
                "Duration": {"number": 92},
                "Calories": {"number": 510},
                "Avg HR": {"number": 118},
                "Source": {"select": {"name": "Health Auto Export"}}
            }
        }

        mock_notion_client.databases.query.return_value = {"results": [existing_workout]}

        # Process file
        result = handler.handle_file(csv_file, FileType.GYMAHOLIC_CSV)

        assert result is True

        # Should have called pages.update to merge
        mock_notion_client.pages.update.assert_called_once()
        update_call = mock_notion_client.pages.update.call_args

        assert update_call[1]["page_id"] == "workout-123"
        # Should update source to merged
        assert "Source" in update_call[1]["properties"]

        # Should NOT have called sync_workout (merge, not create)
        handler.notion_sync.sync_workout.assert_not_called()

        # File should be in processed
        processed_files = list((temp_daemon_dir / "processed").rglob("*.csv"))
        assert len(processed_files) == 1

    def test_gymaholic_parser_error_moves_to_failed(
        self,
        handler,
        temp_daemon_dir
    ):
        """Test that parser errors move file to failed directory."""
        # Create invalid CSV file
        csv_file = temp_daemon_dir / "inbox" / "gymaholic" / "invalid.csv"
        csv_file.write_text("invalid,csv,data")

        # Process file (should fail during parsing)
        result = handler.handle_file(csv_file, FileType.GYMAHOLIC_CSV)

        assert result is False

        # File should be in failed directory
        failed_files = list((temp_daemon_dir / "failed").rglob("*.csv"))
        assert len(failed_files) == 1

        # Error log should exist
        error_logs = list((temp_daemon_dir / "failed").rglob("*.error.log"))
        assert len(error_logs) == 1


class TestHealthWorkoutHandling:
    """Tests for HealthAutoExport workout processing."""

    def test_health_workout_no_match_creates_new(
        self,
        handler,
        temp_daemon_dir,
        temp_health_export_dir,
        sample_health_workout_json_content,
        mock_notion_client
    ):
        """Test that HealthAutoExport workout creates new page when no match."""
        # Create JSON file in Health Export inbox
        json_file = temp_health_export_dir / "TOAD_workouts" / "2026-01-21.json"
        json_file.write_text(sample_health_workout_json_content)

        # No existing workouts
        mock_notion_client.databases.query.return_value = {"results": []}

        # Process file
        result = handler.handle_file(json_file, FileType.HEALTH_WORKOUT_JSON)

        assert result is True

        # Should have created new workout
        handler.notion_sync.sync_workout.assert_called_once()

        # File should be in processed
        processed_files = list((temp_daemon_dir / "processed").rglob("*.json"))
        assert len(processed_files) == 1

    def test_health_workout_match_merges_with_gymaholic(
        self,
        handler,
        temp_daemon_dir,
        temp_health_export_dir,
        sample_health_workout_json_content,
        mock_notion_client
    ):
        """Test that HealthAutoExport merges when matching Gymaholic workout found."""
        # Create JSON file in Health Export inbox
        json_file = temp_health_export_dir / "TOAD_workouts" / "2026-01-21.json"
        json_file.write_text(sample_health_workout_json_content)

        # Mock existing Gymaholic workout
        existing_workout = {
            "id": "workout-456",
            "properties": {
                "Type": {"select": {"name": "Functional Training"}},
                "Date": {"date": {"start": "2026-01-21T18:30:00+00:00"}},
                "Duration": {"number": 88},
                "Source": {"select": {"name": "Gymaholic"}},
                "Notes": {"rich_text": [{"text": {"content": "TOMO B Strength"}}]}
            }
        }

        mock_notion_client.databases.query.return_value = {"results": [existing_workout]}

        # Process file
        result = handler.handle_file(json_file, FileType.HEALTH_WORKOUT_JSON)

        assert result is True

        # Should have merged with existing
        mock_notion_client.pages.update.assert_called_once()
        update_call = mock_notion_client.pages.update.call_args

        assert update_call[1]["page_id"] == "workout-456"

        # Should NOT create new
        handler.notion_sync.sync_workout.assert_not_called()

        # File should be in processed
        processed_files = list((temp_daemon_dir / "processed").rglob("*.json"))
        assert len(processed_files) == 1


class TestActivityMetricsHandling:
    """Tests for activity metrics processing."""

    def test_activity_metrics_syncs_successfully(
        self,
        handler,
        temp_daemon_dir,
        temp_health_export_dir,
        sample_activity_json_content
    ):
        """Test that activity metrics are synced to Habit Tracker."""
        # Create JSON file in Health Export inbox with proper filename format
        json_file = temp_health_export_dir / "TOAD_Activity" / "HealthAutoExport-2026-01-21.json"
        json_file.write_text(sample_activity_json_content)

        # Process file
        result = handler.handle_file(json_file, FileType.HEALTH_ACTIVITY_CSV)

        assert result is True

        # Should have synced metrics
        handler.notion_sync.update_habit_tracker_metrics.assert_called_once()

        # File should be in processed
        processed_files = list((temp_daemon_dir / "processed").rglob("*.json"))
        assert len(processed_files) == 1

    def test_activity_metrics_error_moves_to_failed(
        self,
        handler,
        temp_daemon_dir,
        temp_health_export_dir
    ):
        """Test that metrics sync errors move file to failed."""
        # Create invalid JSON file in Health Export inbox with proper filename format
        json_file = temp_health_export_dir / "TOAD_Activity" / "HealthAutoExport-invalid.json"
        json_file.write_text("{invalid json}")

        # Process file
        result = handler.handle_file(json_file, FileType.HEALTH_ACTIVITY_CSV)

        assert result is False

        # File should be in failed
        failed_files = list((temp_daemon_dir / "failed").rglob("*.json"))
        assert len(failed_files) == 1

        # Error log should exist
        error_logs = list((temp_daemon_dir / "failed").rglob("*.error.log"))
        assert len(error_logs) == 1


class TestFileMovement:
    """Tests for file movement through staging/processed/failed."""

    def test_successful_processing_moves_through_staging_to_processed(
        self,
        handler,
        temp_daemon_dir,
        sample_gymaholic_csv_content,
        mock_notion_client
    ):
        """Test that successful processing moves file: inbox → staging → processed."""
        csv_file = temp_daemon_dir / "inbox" / "gymaholic" / "workout.csv"
        csv_file.write_text(sample_gymaholic_csv_content)

        # No existing workouts
        mock_notion_client.databases.query.return_value = {"results": []}

        # Verify file starts in inbox
        assert csv_file.exists()
        assert not list((temp_daemon_dir / "staging").rglob("*.csv"))
        assert not list((temp_daemon_dir / "processed").rglob("*.csv"))

        # Process
        result = handler.handle_file(csv_file, FileType.GYMAHOLIC_CSV)

        assert result is True

        # File should no longer be in inbox or staging
        assert not csv_file.exists()
        assert not list((temp_daemon_dir / "staging").rglob("*.csv"))

        # File should be in processed
        processed_files = list((temp_daemon_dir / "processed").rglob("*.csv"))
        assert len(processed_files) == 1

    def test_failed_processing_moves_to_failed_with_error_log(
        self,
        handler,
        temp_daemon_dir
    ):
        """Test that failed processing moves file to failed with error log."""
        csv_file = temp_daemon_dir / "inbox" / "gymaholic" / "invalid.csv"
        csv_file.write_text("invalid,data")

        # Process (will fail)
        result = handler.handle_file(csv_file, FileType.GYMAHOLIC_CSV)

        assert result is False

        # File should be in failed
        failed_files = list((temp_daemon_dir / "failed").rglob("*.csv"))
        assert len(failed_files) == 1

        # Error log should exist
        error_logs = list((temp_daemon_dir / "failed").rglob("*.error.log"))
        assert len(error_logs) == 1

        # Error log should contain details
        error_log = error_logs[0]
        error_content = error_log.read_text()
        assert "invalid.csv" in error_content
        assert "Error:" in error_content


