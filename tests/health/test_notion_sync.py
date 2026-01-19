"""Tests for Health Notion sync module."""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch

from toad.health.notion_sync import HealthNotionSync
from toad.health.models import DailyActivityMetrics, WorkoutData, ExerciseData


@pytest.fixture
def mock_notion_client():
    """Create a mock Notion client."""
    client = Mock()
    # Mock the nested client.client for direct API calls
    client.client = Mock()
    return client


@pytest.fixture
def health_sync(mock_notion_client):
    """Create HealthNotionSync with mocked client."""
    return HealthNotionSync(mock_notion_client)


@pytest.fixture
def sample_metrics():
    """Create sample DailyActivityMetrics."""
    return DailyActivityMetrics(
        date=datetime(2026, 1, 18),
        source="HealthAutoExport",
        calories_in=2200.5,
        calories_out=2850.0,
        weight=175.2,
        body_fat=15.3
    )


class TestHealthNotionSync:
    """Tests for HealthNotionSync class."""

    def test_update_habit_tracker_metrics_all_fields(self, health_sync, mock_notion_client, sample_metrics):
        """Test updating all metrics fields successfully."""
        # Mock get_or_create_page to return a page ID
        mock_notion_client.get_or_create_page.return_value = "test-page-id-123"

        # Mock smart update to return success
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": True,
            "updated_fields": ["CaloriesIn", "CaloriesOut", "Weight", "BodyFat"],
            "unchanged_fields": [],
            "changes": {
                "CaloriesIn": {"old": 2000.0, "new": 2200.5},
                "CaloriesOut": {"old": 2700.0, "new": 2850.0},
                "Weight": {"old": 174.0, "new": 175.2},
                "BodyFat": {"old": 15.0, "new": 15.3}
            }
        }

        # Call the sync method
        result = health_sync.update_habit_tracker_metrics(sample_metrics)

        # Verify get_or_create_page was called correctly
        mock_notion_client.get_or_create_page.assert_called_once()
        call_args = mock_notion_client.get_or_create_page.call_args
        assert call_args.kwargs["query_property"] == "Date"
        assert call_args.kwargs["query_value"] == "2026-01-18"

        # Verify smart update was called
        mock_notion_client.update_page_properties_smart.assert_called_once()
        update_call_args = mock_notion_client.update_page_properties_smart.call_args
        assert update_call_args.args[0] == "test-page-id-123"

        # Verify properties dict has all 4 metrics
        properties = update_call_args.args[1]
        assert "CaloriesIn" in properties
        assert "CaloriesOut" in properties
        assert "Weight" in properties
        assert "BodyFat" in properties

        # Verify result
        assert result["success"] is True
        assert result["date"] == "2026-01-18"
        assert result["page_id"] == "test-page-id-123"
        assert len(result["updated_fields"]) == 4

    def test_update_habit_tracker_metrics_partial_fields(self, health_sync, mock_notion_client):
        """Test updating with only some metrics present."""
        # Metrics with only weight and body fat
        partial_metrics = DailyActivityMetrics(
            date=datetime(2026, 1, 18),
            source="HealthAutoExport",
            weight=175.0,
            body_fat=15.5
        )

        mock_notion_client.get_or_create_page.return_value = "test-page-id-456"
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": True,
            "updated_fields": ["Weight", "BodyFat"],
            "unchanged_fields": [],
            "changes": {
                "Weight": {"old": None, "new": 175.0},
                "BodyFat": {"old": None, "new": 15.5}
            }
        }

        result = health_sync.update_habit_tracker_metrics(partial_metrics)

        # Verify only 2 properties were sent
        update_call_args = mock_notion_client.update_page_properties_smart.call_args
        properties = update_call_args.args[1]
        assert len(properties) == 2
        assert "Weight" in properties
        assert "BodyFat" in properties
        assert "CaloriesIn" not in properties
        assert "CaloriesOut" not in properties

        assert result["success"] is True
        assert len(result["updated_fields"]) == 2

    def test_update_habit_tracker_metrics_no_changes(self, health_sync, mock_notion_client, sample_metrics):
        """Test when all values match existing values (no update needed)."""
        mock_notion_client.get_or_create_page.return_value = "test-page-id-789"

        # Mock smart update detecting no changes
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": True,
            "updated_fields": [],
            "unchanged_fields": ["CaloriesIn", "CaloriesOut", "Weight", "BodyFat"],
            "changes": {}
        }

        result = health_sync.update_habit_tracker_metrics(sample_metrics)

        # Verify smart update was still called
        mock_notion_client.update_page_properties_smart.assert_called_once()

        # Verify result shows no updates
        assert result["success"] is True
        assert result["updated_fields"] == []
        assert len(result["unchanged_fields"]) == 4

    def test_update_habit_tracker_metrics_creates_entry(self, health_sync, mock_notion_client, sample_metrics):
        """Test that new Habit Tracker entry is created if missing."""
        # Mock get_or_create_page to simulate creation
        mock_notion_client.get_or_create_page.return_value = "new-page-id"
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": True,
            "updated_fields": ["CaloriesIn", "CaloriesOut", "Weight", "BodyFat"],
            "unchanged_fields": [],
            "changes": {}
        }

        result = health_sync.update_habit_tracker_metrics(sample_metrics)

        # Verify get_or_create_page was called with create_properties
        call_args = mock_notion_client.get_or_create_page.call_args
        create_props = call_args.kwargs["create_properties"]
        assert "Name" in create_props
        assert "Date" in create_props
        assert create_props["Date"]["date"]["start"] == "2026-01-18"

        assert result["success"] is True
        assert result["page_id"] == "new-page-id"

    def test_update_habit_tracker_metrics_empty_metrics(self, health_sync, mock_notion_client):
        """Test with metrics that have all None values."""
        empty_metrics = DailyActivityMetrics(
            date=datetime(2026, 1, 18),
            source="HealthAutoExport"
        )

        mock_notion_client.get_or_create_page.return_value = "test-page-id"

        result = health_sync.update_habit_tracker_metrics(empty_metrics)

        # Should return early without calling smart update
        mock_notion_client.update_page_properties_smart.assert_not_called()

        assert result["success"] is True
        assert result["updated_fields"] == []

    @patch('toad.health.notion_sync.Config')
    def test_update_habit_tracker_metrics_missing_database_id(self, mock_config, health_sync, sample_metrics):
        """Test error when NOTION_HABITS_DATABASE_ID is not configured."""
        mock_config.NOTION_HABITS_DATABASE_ID = None

        result = health_sync.update_habit_tracker_metrics(sample_metrics)

        assert result["success"] is False
        assert "not configured" in result["error"]

    def test_update_habit_tracker_metrics_page_creation_fails(self, health_sync, mock_notion_client, sample_metrics):
        """Test handling when page creation fails."""
        # Mock get_or_create_page to return None (failure)
        mock_notion_client.get_or_create_page.return_value = None

        result = health_sync.update_habit_tracker_metrics(sample_metrics)

        assert result["success"] is False
        assert "Failed to find or create" in result["error"]

    def test_update_habit_tracker_metrics_update_fails(self, health_sync, mock_notion_client, sample_metrics):
        """Test handling when smart update fails."""
        mock_notion_client.get_or_create_page.return_value = "test-page-id"

        # Mock smart update failure
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": False,
            "error": "API rate limit exceeded",
            "updated_fields": [],
            "unchanged_fields": [],
            "changes": {}
        }

        result = health_sync.update_habit_tracker_metrics(sample_metrics)

        assert result["success"] is False
        assert "error" in result

    def test_update_habit_tracker_metrics_date_conversion(self, health_sync, mock_notion_client):
        """Test that datetime is properly converted to date."""
        # Create metrics with datetime
        metrics_with_datetime = DailyActivityMetrics(
            date=datetime(2026, 1, 18, 14, 30, 0),  # Include time
            source="HealthAutoExport",
            weight=175.0
        )

        mock_notion_client.get_or_create_page.return_value = "test-page-id"
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": True,
            "updated_fields": ["Weight"],
            "unchanged_fields": [],
            "changes": {}
        }

        result = health_sync.update_habit_tracker_metrics(metrics_with_datetime)

        # Verify date was converted correctly (time stripped)
        call_args = mock_notion_client.get_or_create_page.call_args
        assert call_args.kwargs["query_value"] == "2026-01-18"

        assert result["date"] == "2026-01-18"

    def test_update_habit_tracker_metrics_property_format(self, health_sync, mock_notion_client, sample_metrics):
        """Test that properties are formatted correctly for Notion API."""
        mock_notion_client.get_or_create_page.return_value = "test-page-id"
        mock_notion_client.update_page_properties_smart.return_value = {
            "success": True,
            "updated_fields": [],
            "unchanged_fields": ["CaloriesIn"],
            "changes": {}
        }

        health_sync.update_habit_tracker_metrics(sample_metrics)

        # Check property format
        update_call_args = mock_notion_client.update_page_properties_smart.call_args
        properties = update_call_args.args[1]

        # Verify number properties have correct structure
        assert properties["CaloriesIn"]["type"] == "number"
        assert properties["CaloriesIn"]["number"] == 2200.5
        assert properties["Weight"]["type"] == "number"
        assert properties["Weight"]["number"] == 175.2


class TestWorkoutDuplicateDetection:
    """Tests for workout duplicate detection methods."""

    def test_find_workout_by_healthautoexport_id_found(self, health_sync, mock_notion_client):
        """Test finding a workout by HealthAutoExport ID successfully."""
        # Mock database query response with a result
        mock_response = {
            "results": [
                {"id": "workout-page-id-123"}
            ]
        }
        mock_notion_client.client.databases.query.return_value = mock_response

        result = health_sync.find_workout_by_healthautoexport_id("abc-123-def")

        # Verify query was called correctly
        mock_notion_client.client.databases.query.assert_called_once()
        call_args = mock_notion_client.client.databases.query.call_args

        # Check filter structure
        filter_arg = call_args.kwargs["filter"]
        assert filter_arg["property"] == "Notes"
        assert "HealthAutoExport ID: abc-123-def" in filter_arg["rich_text"]["contains"]

        # Verify correct page ID returned
        assert result == "workout-page-id-123"

    def test_find_workout_by_healthautoexport_id_not_found(self, health_sync, mock_notion_client):
        """Test when no workout matches the HealthAutoExport ID."""
        # Mock empty response
        mock_response = {"results": []}
        mock_notion_client.client.databases.query.return_value = mock_response

        result = health_sync.find_workout_by_healthautoexport_id("nonexistent-id")

        assert result is None

    @patch('toad.health.notion_sync.Config')
    def test_find_workout_by_healthautoexport_id_missing_db_id(self, mock_config, health_sync):
        """Test error handling when NOTION_WORKOUTS_DATABASE_ID is not configured."""
        mock_config.NOTION_WORKOUTS_DATABASE_ID = None

        result = health_sync.find_workout_by_healthautoexport_id("some-id")

        assert result is None

    def test_find_workout_by_healthautoexport_id_error_handling(self, health_sync, mock_notion_client):
        """Test error handling when database query fails."""
        # Mock query to raise an exception
        mock_notion_client.client.databases.query.side_effect = Exception("API error")

        result = health_sync.find_workout_by_healthautoexport_id("some-id")

        assert result is None

    def test_find_workout_by_attributes_found(self, health_sync, mock_notion_client):
        """Test finding a workout by date, type, and source."""
        # Mock database query response
        mock_response = {
            "results": [
                {"id": "gymaholic-workout-id-456"}
            ]
        }
        mock_notion_client.client.databases.query.return_value = mock_response

        workout_date = datetime(2026, 1, 14, 6, 4)
        result = health_sync.find_workout_by_attributes(
            workout_date=workout_date,
            workout_type="Strength",
            source="Gymaholic"
        )

        # Verify query was called with compound filter
        mock_notion_client.client.databases.query.assert_called_once()
        call_args = mock_notion_client.client.databases.query.call_args

        filter_arg = call_args.kwargs["filter"]
        assert "and" in filter_arg
        assert len(filter_arg["and"]) == 3

        # Verify date filter
        date_filter = next(f for f in filter_arg["and"] if f["property"] == "Date")
        assert date_filter["date"]["equals"] == "2026-01-14"

        # Verify type filter
        type_filter = next(f for f in filter_arg["and"] if f["property"] == "Type")
        assert type_filter["select"]["equals"] == "Strength"

        # Verify source filter
        source_filter = next(f for f in filter_arg["and"] if f["property"] == "Source")
        assert source_filter["select"]["equals"] == "Gymaholic"

        assert result == "gymaholic-workout-id-456"

    def test_find_workout_by_attributes_not_found(self, health_sync, mock_notion_client):
        """Test when no workout matches the attributes."""
        mock_response = {"results": []}
        mock_notion_client.client.databases.query.return_value = mock_response

        workout_date = datetime(2026, 1, 14, 6, 4)
        result = health_sync.find_workout_by_attributes(
            workout_date=workout_date,
            workout_type="Run",
            source="Gymaholic"
        )

        assert result is None

    @patch('toad.health.notion_sync.Config')
    def test_find_workout_by_attributes_missing_db_id(self, mock_config, health_sync):
        """Test error handling when database ID is missing."""
        mock_config.NOTION_WORKOUTS_DATABASE_ID = None

        workout_date = datetime(2026, 1, 14, 6, 4)
        result = health_sync.find_workout_by_attributes(
            workout_date=workout_date,
            workout_type="Strength",
            source="Gymaholic"
        )

        assert result is None

    def test_find_workout_by_attributes_error_handling(self, health_sync, mock_notion_client):
        """Test error handling when query fails."""
        mock_notion_client.client.databases.query.side_effect = Exception("API timeout")

        workout_date = datetime(2026, 1, 14, 6, 4)
        result = health_sync.find_workout_by_attributes(
            workout_date=workout_date,
            workout_type="Strength",
            source="Gymaholic"
        )

        assert result is None

    def test_is_workout_duplicate_healthautoexport_found(self, health_sync, mock_notion_client):
        """Test duplicate detection for HealthAutoExport workout with ID."""
        # Create a HealthAutoExport workout with ID in notes
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Run",
            source="HealthAutoExport",
            duration_minutes=45,
            notes="HealthAutoExport ID: abc-123-def-456"
        )

        # Mock the ID-based lookup
        mock_response = {
            "results": [{"id": "existing-workout-page-id"}]
        }
        mock_notion_client.client.databases.query.return_value = mock_response

        result = health_sync.is_workout_duplicate(workout)

        # Should use ID-based lookup first
        assert result == "existing-workout-page-id"

        # Verify ID-based query was called
        call_args = mock_notion_client.client.databases.query.call_args
        filter_arg = call_args.kwargs["filter"]
        assert "HealthAutoExport ID: abc-123-def-456" in filter_arg["rich_text"]["contains"]

    def test_is_workout_duplicate_healthautoexport_not_found(self, health_sync, mock_notion_client):
        """Test when HealthAutoExport workout is not a duplicate."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Run",
            source="HealthAutoExport",
            duration_minutes=45,
            notes="HealthAutoExport ID: new-workout-id"
        )

        # Mock empty responses for both strategies
        mock_notion_client.client.databases.query.return_value = {"results": []}

        result = health_sync.is_workout_duplicate(workout)

        assert result is None

    def test_is_workout_duplicate_gymaholic_found(self, health_sync, mock_notion_client):
        """Test duplicate detection for Gymaholic workout (attribute-based)."""
        workout = WorkoutData(
            date=datetime(2026, 1, 14, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            duration_minutes=88,
            notes="TOMO B Strength"
        )

        # Mock the attribute-based lookup
        mock_response = {
            "results": [{"id": "gymaholic-page-id-789"}]
        }
        mock_notion_client.client.databases.query.return_value = mock_response

        result = health_sync.is_workout_duplicate(workout)

        assert result == "gymaholic-page-id-789"

        # Verify compound filter was used
        call_args = mock_notion_client.client.databases.query.call_args
        filter_arg = call_args.kwargs["filter"]
        assert "and" in filter_arg

    def test_is_workout_duplicate_gymaholic_not_found(self, health_sync, mock_notion_client):
        """Test when Gymaholic workout is not a duplicate."""
        workout = WorkoutData(
            date=datetime(2026, 1, 15, 7, 0),
            workout_type="Strength",
            source="Gymaholic",
            duration_minutes=90
        )

        mock_notion_client.client.databases.query.return_value = {"results": []}

        result = health_sync.is_workout_duplicate(workout)

        assert result is None

    def test_is_workout_duplicate_no_notes_fallback(self, health_sync, mock_notion_client):
        """Test fallback to attribute-based lookup when HealthAutoExport has no notes."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Run",
            source="HealthAutoExport",
            duration_minutes=45,
            notes=None  # No notes field
        )

        # Mock attribute-based lookup
        mock_response = {
            "results": [{"id": "found-by-attributes"}]
        }
        mock_notion_client.client.databases.query.return_value = mock_response

        result = health_sync.is_workout_duplicate(workout)

        # Should fall back to attribute-based search
        assert result == "found-by-attributes"

        # Verify compound filter was used (not ID-based)
        call_args = mock_notion_client.client.databases.query.call_args
        filter_arg = call_args.kwargs["filter"]
        assert "and" in filter_arg

    def test_is_workout_duplicate_malformed_id_in_notes(self, health_sync, mock_notion_client):
        """Test fallback when notes don't contain properly formatted ID."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Run",
            source="HealthAutoExport",
            duration_minutes=45,
            notes="Some random notes without ID format"
        )

        # Mock attribute-based lookup
        mock_response = {
            "results": [{"id": "found-by-attributes-backup"}]
        }
        mock_notion_client.client.databases.query.return_value = mock_response

        result = health_sync.is_workout_duplicate(workout)

        # Should fall back to attribute-based search when regex doesn't match
        assert result == "found-by-attributes-backup"


class TestWorkoutSummarizer:
    """Tests for workout summary generation."""

    def test_generate_summary_strength_with_exercises(self, health_sync):
        """Test summary for strength workout with exercise details."""
        exercises = [
            ExerciseData(
                name="Bench Press",
                sets=3,
                reps=[10, 8, 6],
                weight=[135, 155, 175]
            ),
            ExerciseData(
                name="Squat",
                sets=4,
                reps=[8, 8, 8, 8],
                weight=[185, 185, 185, 185]
            ),
            ExerciseData(
                name="Deadlift",
                sets=3,
                reps=[5, 5, 5],
                weight=[225, 245, 265]
            )
        ]

        workout = WorkoutData(
            date=datetime(2026, 1, 14, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            duration_minutes=88,
            exercises=exercises
        )

        summary = health_sync.generate_workout_summary(workout)

        # Should list all exercises with set counts
        assert "Bench Press (3 sets)" in summary
        assert "Squat (4 sets)" in summary
        assert "Deadlift (3 sets)" in summary
        assert summary.count(",") == 2  # Two commas separating three exercises

    def test_generate_summary_run_with_distance_and_duration(self, health_sync):
        """Test summary for cardio workout with distance and duration."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Run",
            source="HealthAutoExport",
            duration_minutes=45,
            distance_miles=5.2,
            calories=450
        )

        summary = health_sync.generate_workout_summary(workout)

        # Should include type, distance, and duration
        assert "Run" in summary
        assert "5.2 mi" in summary
        assert "45m" in summary

    def test_generate_summary_run_with_hours_and_minutes(self, health_sync):
        """Test summary for long cardio workout with hours."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 8, 0),
            workout_type="Hike",
            source="HealthAutoExport",
            duration_minutes=135,  # 2h 15m
            distance_miles=8.5
        )

        summary = health_sync.generate_workout_summary(workout)

        assert "Hike" in summary
        assert "8.5 mi" in summary
        assert "2h 15m" in summary

    def test_generate_summary_run_without_distance(self, health_sync):
        """Test summary for cardio workout with only duration."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Climb",
            source="HealthAutoExport",
            duration_minutes=90
        )

        summary = health_sync.generate_workout_summary(workout)

        assert "Climb" in summary
        assert "1h 30m" in summary

    def test_generate_summary_run_without_duration(self, health_sync):
        """Test summary for cardio workout with only distance."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Walk",
            source="HealthAutoExport",
            distance_miles=3.1
        )

        summary = health_sync.generate_workout_summary(workout)

        assert "Walk" in summary
        assert "3.1 mi" in summary

    def test_generate_summary_fallback_to_notes(self, health_sync):
        """Test summary fallback to notes field."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Other",
            source="Manual",
            notes="Morning yoga session - 30 min",
            duration_minutes=30
        )

        summary = health_sync.generate_workout_summary(workout)

        # Should use notes since no exercises and not a cardio type
        assert summary == "Morning yoga session - 30 min"

    def test_generate_summary_notes_with_healthautoexport_id(self, health_sync):
        """Test that HealthAutoExport ID is stripped from notes in summary."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Other",
            source="HealthAutoExport",
            notes="Cool down stretching HealthAutoExport ID: abc-123-def-456"
        )

        summary = health_sync.generate_workout_summary(workout)

        # Should strip out the ID part
        assert "Cool down stretching" in summary
        assert "HealthAutoExport ID" not in summary
        assert "abc-123-def-456" not in summary

    def test_generate_summary_fallback_to_workout_type(self, health_sync):
        """Test summary fallback to just workout type."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Strength",
            source="HealthAutoExport"
        )

        summary = health_sync.generate_workout_summary(workout)

        # Should just return workout type as last resort
        assert summary == "Strength"

    def test_generate_summary_empty_exercises_list(self, health_sync):
        """Test summary when exercises list is empty."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Strength",
            source="Gymaholic",
            exercises=[],  # Empty list
            notes="Rest day - light stretching"
        )

        summary = health_sync.generate_workout_summary(workout)

        # Should fall through to notes since exercises is empty
        assert summary == "Rest day - light stretching"

    def test_generate_summary_single_exercise(self, health_sync):
        """Test summary with only one exercise."""
        exercises = [
            ExerciseData(
                name="Pull-ups",
                sets=5,
                reps=[10, 10, 10, 10, 10],
                weight=[0, 0, 0, 0, 0]
            )
        ]

        workout = WorkoutData(
            date=datetime(2026, 1, 14, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            exercises=exercises
        )

        summary = health_sync.generate_workout_summary(workout)

        assert summary == "Pull-ups (5 sets)"

    def test_generate_summary_bike_cardio(self, health_sync):
        """Test summary for bike workout."""
        workout = WorkoutData(
            date=datetime(2026, 1, 17, 10, 30),
            workout_type="Bike",
            source="HealthAutoExport",
            duration_minutes=60,
            distance_miles=15.0
        )

        summary = health_sync.generate_workout_summary(workout)

        assert "Bike" in summary
        assert "15.0 mi" in summary
        assert "1h 0m" in summary
