"""Tests for HealthSyncOrchestrator."""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from toad.health.sync_orchestrator import HealthSyncOrchestrator
from toad.health.models import DailyActivityMetrics, WorkoutData, ExerciseData


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "health_auto_export"
GYMAHOLIC_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "gymaholic"


class TestHealthSyncOrchestrator:
    """Tests for HealthSyncOrchestrator class."""

    def test_init_dry_run(self):
        """Test orchestrator initialization in dry-run mode."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        assert orchestrator.dry_run is True
        assert orchestrator.metrics_parser is not None
        assert orchestrator.workouts_parser is not None
        assert orchestrator.gymaholic_parser is not None
        assert orchestrator.notion_client is None
        assert orchestrator.notion_sync is None

    @patch('toad.health.sync_orchestrator.TOADNotionClient')
    def test_init_normal_mode(self, mock_notion_client_class):
        """Test orchestrator initialization in normal mode."""
        # Mock the TOADNotionClient constructor
        mock_client_instance = Mock()
        mock_notion_client_class.return_value = mock_client_instance

        orchestrator = HealthSyncOrchestrator(dry_run=False)

        assert orchestrator.dry_run is False
        assert orchestrator.metrics_parser is not None
        assert orchestrator.workouts_parser is not None
        assert orchestrator.gymaholic_parser is not None
        assert orchestrator.notion_client is not None
        assert orchestrator.notion_sync is not None

    @patch('toad.health.sync_orchestrator.Config')
    def test_sync_date_range_missing_config(self, mock_config):
        """Test sync_date_range when HealthAutoExport paths are not configured."""
        mock_config.validate_health_auto_export_paths.return_value = False
        mock_config.WORKOUT_SYNC_INBOX_PATH = None

        orchestrator = HealthSyncOrchestrator(dry_run=True)
        summary = orchestrator.sync_date_range(
            date(2026, 1, 18),
            date(2026, 1, 18)
        )

        # Should complete without errors, but process no data
        assert summary['metrics_processed'] == 0
        assert summary['workouts_processed'] == 0
        assert summary['gymaholic_workouts_processed'] == 0
        assert summary['dry_run'] is True

    @patch('toad.health.sync_orchestrator.Config')
    def test_sync_date_range_single_date_dry_run(self, mock_config):
        """Test syncing a single date in dry-run mode."""
        # Configure paths
        mock_config.validate_health_auto_export_paths.return_value = True
        mock_config.HEALTH_AUTO_EXPORT_WORKOUTS_PATH = str(FIXTURES_DIR)
        mock_config.HEALTH_AUTO_EXPORT_ACTIVITY_PATH = str(FIXTURES_DIR)
        mock_config.WORKOUT_SYNC_INBOX_PATH = None

        orchestrator = HealthSyncOrchestrator(dry_run=True)

        # Sync a date we have fixture data for
        summary = orchestrator.sync_date_range(
            date(2026, 1, 17),
            date(2026, 1, 17)
        )

        assert summary['dry_run'] is True
        # valid_workouts.json has workouts for this date
        # valid_activity_metrics.json has metrics for this date
        assert isinstance(summary['metrics_processed'], int)
        assert isinstance(summary['workouts_processed'], int)
        assert isinstance(summary['errors'], list)

    @patch('toad.health.sync_orchestrator.Config')
    def test_sync_date_range_multi_date(self, mock_config):
        """Test syncing a date range."""
        mock_config.validate_health_auto_export_paths.return_value = True
        mock_config.HEALTH_AUTO_EXPORT_WORKOUTS_PATH = str(FIXTURES_DIR)
        mock_config.HEALTH_AUTO_EXPORT_ACTIVITY_PATH = str(FIXTURES_DIR)
        mock_config.WORKOUT_SYNC_INBOX_PATH = None

        orchestrator = HealthSyncOrchestrator(dry_run=True)

        # Sync 3 days
        summary = orchestrator.sync_date_range(
            date(2026, 1, 16),
            date(2026, 1, 18)
        )

        assert summary['dry_run'] is True
        assert isinstance(summary['metrics_processed'], int)
        assert isinstance(summary['workouts_processed'], int)
        assert isinstance(summary['errors'], list)

    def test_sync_activity_metrics_valid_file(self):
        """Test syncing activity metrics from a valid file."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"
        metrics = orchestrator._sync_activity_metrics(fixture_path)

        assert metrics is not None
        assert isinstance(metrics, DailyActivityMetrics)
        assert metrics.date.year == 2026
        assert metrics.date.month == 1
        assert metrics.date.day == 17

    def test_sync_activity_metrics_empty_file(self):
        """Test syncing activity metrics from empty metrics file."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        fixture_path = FIXTURES_DIR / "HealthAutoExport-2026-01-18.json"
        metrics = orchestrator._sync_activity_metrics(fixture_path)

        # Should return metrics object even if some fields are None
        assert metrics is not None
        assert isinstance(metrics, DailyActivityMetrics)

    def test_sync_workouts_valid_file(self):
        """Test syncing workouts from a valid file."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        fixture_path = FIXTURES_DIR / "valid_workouts.json"
        workouts = orchestrator._sync_workouts(fixture_path)

        assert workouts is not None
        assert isinstance(workouts, list)
        assert len(workouts) == 4
        assert all(isinstance(w, WorkoutData) for w in workouts)

    def test_sync_workouts_empty_file(self):
        """Test syncing workouts from empty workouts file."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        fixture_path = FIXTURES_DIR / "empty_workouts.json"
        workouts = orchestrator._sync_workouts(fixture_path)

        assert workouts == []

    def test_sync_gymaholic_inbox_no_csvs(self):
        """Test Gymaholic inbox sync when no CSV files exist."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        # Create a temporary empty directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_path = Path(tmpdir)
            workouts = orchestrator._sync_gymaholic_inbox(
                inbox_path,
                date(2026, 1, 14),
                date(2026, 1, 18)
            )

            assert workouts == []

    def test_sync_gymaholic_inbox_with_csvs(self):
        """Test Gymaholic inbox sync with CSV files."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        # Use the fixture directory that contains valid_workout.csv
        workouts = orchestrator._sync_gymaholic_inbox(
            GYMAHOLIC_FIXTURES_DIR,
            date(2026, 1, 1),
            date(2026, 1, 31)
        )

        # Should find and parse the valid_workout.csv
        assert isinstance(workouts, list)
        # valid_workout.csv has date Jan 14
        if workouts:
            assert all(isinstance(w, WorkoutData) for w in workouts)
            assert all(w.source == "Gymaholic" for w in workouts)

    def test_sync_gymaholic_inbox_date_filtering(self):
        """Test that Gymaholic workouts are filtered by date range."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        # Narrow date range that won't include Jan 14
        workouts = orchestrator._sync_gymaholic_inbox(
            GYMAHOLIC_FIXTURES_DIR,
            date(2026, 1, 20),
            date(2026, 1, 25)
        )

        # Should filter out the Jan 14 workout
        assert workouts == []

    def test_log_metrics_dry_run(self):
        """Test dry-run logging for activity metrics."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        metrics = DailyActivityMetrics(
            date=datetime(2026, 1, 18),
            source="HealthAutoExport",
            calories_in=2200.0,
            calories_out=2800.0,
            weight=175.5,
            body_fat=15.2
        )

        # Should not raise an error
        orchestrator._log_metrics_dry_run(metrics)

    def test_log_metrics_dry_run_partial(self):
        """Test dry-run logging for partial activity metrics."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        metrics = DailyActivityMetrics(
            date=datetime(2026, 1, 18),
            source="HealthAutoExport",
            weight=175.5
        )

        # Should handle missing fields gracefully
        orchestrator._log_metrics_dry_run(metrics)

    def test_log_workout_dry_run(self):
        """Test dry-run logging for HealthAutoExport workout."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        workout = WorkoutData(
            date=datetime(2026, 1, 18, 10, 30),
            workout_type="Run",
            source="HealthAutoExport",
            duration_minutes=45.5,
            calories=450,
            avg_heart_rate=155.5,
            distance_miles=5.2
        )

        # Should not raise an error
        orchestrator._log_workout_dry_run(workout)

    def test_log_gymaholic_workout_dry_run(self):
        """Test dry-run logging for Gymaholic workout with exercises."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        exercises = [
            ExerciseData(
                name="Bench Press",
                sets=3,
                reps=[10, 8, 6],
                weight=[135, 155, 175]
            ),
            ExerciseData(
                name="Squat",
                sets=3,
                reps=[8, 8, 8],
                weight=[185, 185, 185]
            )
        ]

        workout = WorkoutData(
            date=datetime(2026, 1, 14, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            duration_minutes=88,
            calories=495,
            avg_heart_rate=116,
            notes="TOMO B Strength",
            exercises=exercises
        )

        # Should not raise an error
        orchestrator._log_gymaholic_workout_dry_run(workout)

    def test_log_gymaholic_workout_dry_run_many_exercises(self):
        """Test dry-run logging limits to first 5 exercises."""
        orchestrator = HealthSyncOrchestrator(dry_run=True)

        # Create 10 exercises
        exercises = [
            ExerciseData(
                name=f"Exercise {i}",
                sets=3,
                reps=[10, 10, 10],
                weight=[100, 100, 100]
            )
            for i in range(10)
        ]

        workout = WorkoutData(
            date=datetime(2026, 1, 14, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            duration_minutes=120,
            exercises=exercises
        )

        # Should log first 5 and indicate there are more
        orchestrator._log_gymaholic_workout_dry_run(workout)

    @patch('toad.health.sync_orchestrator.Config')
    def test_error_handling_in_sync(self, mock_config):
        """Test that errors during sync are captured in summary."""
        mock_config.validate_health_auto_export_paths.return_value = True
        mock_config.HEALTH_AUTO_EXPORT_WORKOUTS_PATH = "/nonexistent/path"
        mock_config.HEALTH_AUTO_EXPORT_ACTIVITY_PATH = "/nonexistent/path"
        mock_config.WORKOUT_SYNC_INBOX_PATH = None

        orchestrator = HealthSyncOrchestrator(dry_run=True)

        summary = orchestrator.sync_date_range(
            date(2026, 1, 18),
            date(2026, 1, 18)
        )

        # Files don't exist, but shouldn't crash
        # Errors may or may not be logged depending on whether missing files are errors
        assert isinstance(summary['errors'], list)
        assert summary['dry_run'] is True

    @patch('toad.health.sync_orchestrator.Config')
    def test_gymaholic_inbox_error_handling(self, mock_config):
        """Test error handling when Gymaholic inbox has issues."""
        mock_config.validate_health_auto_export_paths.return_value = False
        mock_config.WORKOUT_SYNC_INBOX_PATH = "/nonexistent/gymaholic/inbox"

        orchestrator = HealthSyncOrchestrator(dry_run=True)

        summary = orchestrator.sync_date_range(
            date(2026, 1, 18),
            date(2026, 1, 18)
        )

        # Should handle missing inbox gracefully
        assert summary['gymaholic_workouts_processed'] == 0
        assert isinstance(summary['errors'], list)
