"""Tests for Health Notion sync module."""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch

from toad.health.notion_sync import HealthNotionSync
from toad.health.models import DailyActivityMetrics


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
