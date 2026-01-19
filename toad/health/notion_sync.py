"""
Notion sync module for TOAD health data.

Handles syncing health data (activity metrics, workouts) to Notion databases.
"""

import logging
from typing import Dict, Any, Optional
from datetime import date

from toad.notion_client import TOADNotionClient
from toad.health.models import DailyActivityMetrics
from toad.config import Config

logger = logging.getLogger(__name__)


class HealthNotionSync:
    """Handles syncing health data to Notion databases."""

    def __init__(self, notion_client: TOADNotionClient):
        """
        Initialize the health Notion sync handler.

        Args:
            notion_client: Configured TOAD Notion client
        """
        self.client = notion_client

    def update_habit_tracker_metrics(self, metrics: DailyActivityMetrics) -> Dict[str, Any]:
        """
        Update Habit Tracker with activity metrics using smart batching.

        Updates CaloriesIn, CaloriesOut, Weight, and BodyFat fields in the Habit Tracker
        for the given date. Creates a new entry if one doesn't exist.

        Uses smart update to:
        - Only update fields that have changed
        - Batch all changes into a single API call
        - Return audit trail of what changed

        Args:
            metrics: DailyActivityMetrics object with data to sync

        Returns:
            Dict with success status and details:
                - success: bool
                - date: str
                - page_id: str
                - updated_fields: List of fields that were updated
                - unchanged_fields: List of fields that didn't change
                - changes: Dict of old vs new values
        """
        # Extract date from metrics (convert datetime to date if needed)
        target_date = metrics.date.date() if hasattr(metrics.date, 'date') else metrics.date
        date_str = target_date.strftime('%Y-%m-%d')

        # Get database ID
        database_id = Config.NOTION_HABITS_DATABASE_ID
        if not database_id:
            logger.error("NOTION_HABITS_DATABASE_ID not configured")
            return {
                "success": False,
                "error": "NOTION_HABITS_DATABASE_ID not configured",
                "date": date_str
            }

        # Find or create habit entry using centralized method
        page_id = self.client.get_or_create_page(
            database_id=database_id,
            query_property="Date",
            query_value=date_str,
            create_properties={
                "Name": {
                    "title": [{"text": {"content": date_str}}]
                },
                "Date": {
                    "date": {"start": date_str}
                }
            }
        )

        if not page_id:
            return {
                "success": False,
                "error": "Failed to find or create Habit Tracker entry",
                "date": date_str
            }

        # Build properties dict with only non-None values (in Notion API format)
        properties = {}

        if metrics.calories_in is not None:
            properties["CaloriesIn"] = {"type": "number", "number": metrics.calories_in}

        if metrics.calories_out is not None:
            properties["CaloriesOut"] = {"type": "number", "number": metrics.calories_out}

        if metrics.weight is not None:
            properties["Weight"] = {"type": "number", "number": metrics.weight}

        if metrics.body_fat is not None:
            properties["BodyFat"] = {"type": "number", "number": metrics.body_fat}

        # If no properties to update, return early
        if not properties:
            logger.info(f"No metrics to update for {date_str}")
            return {
                "success": True,
                "date": date_str,
                "page_id": page_id,
                "updated_fields": [],
                "unchanged_fields": [],
                "changes": {}
            }

        # Use smart update - only updates changed fields
        result = self.client.update_page_properties_smart(page_id, properties)

        # Enhance result with our metadata
        result["date"] = date_str
        result["page_id"] = page_id

        if result["success"]:
            if result["updated_fields"]:
                logger.info(f"Updated Habit Tracker for {date_str}: {', '.join(result['updated_fields'])}")
            else:
                logger.info(f"No changes needed for Habit Tracker {date_str}")

        return result
