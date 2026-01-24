"""Event-driven health data processor for TOAD daemon.

Processes health files immediately as they arrive in the inbox,
using the reconciliation engine to handle late exports.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from toad.config import Config
from toad.notion_client import TOADNotionClient
from toad.daemon.file_manager import FileManager
from toad.daemon.file_watcher import FileType
from toad.health.parsers.health_auto_export_metrics import HealthAutoExportMetricsParser
from toad.health.parsers.health_auto_export import HealthAutoExportParser
from toad.health.parsers.gymaholic import GymaholicParser
from toad.health.reconciliation import WorkoutReconciler
from toad.health.notion_sync import HealthNotionSync
from toad.health.models import WorkoutData, DailyActivityMetrics

logger = logging.getLogger(__name__)


class EventDrivenHealthHandler:
    """Handles health data files as they arrive via file watcher."""

    def __init__(self, base_dir: Path):
        """
        Initialize event-driven handler.

        Args:
            base_dir: Base daemon directory (typically ~/.toad/)
        """
        self.base_dir = base_dir
        self.file_manager = FileManager(base_dir)

        # Initialize parsers
        self.metrics_parser = HealthAutoExportMetricsParser()
        self.workouts_parser = HealthAutoExportParser()
        self.gymaholic_parser = GymaholicParser()

        # Initialize reconciliation engine (30-min tolerance)
        self.reconciler = WorkoutReconciler(tolerance_minutes=30)

        # Initialize Notion sync
        self.notion_client = TOADNotionClient()
        self.notion_sync = HealthNotionSync(self.notion_client)

    def handle_file(self, file_path: Path, file_type: str) -> bool:
        """
        Process a file detected by the watcher.

        Args:
            file_path: Path to file in inbox
            file_type: FileType constant

        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"[HANDLER] Processing {file_type}: {file_path.name}")

        try:
            # Route to appropriate handler
            if file_type == FileType.GYMAHOLIC_CSV:
                return self._handle_gymaholic_workout(file_path)
            elif file_type == FileType.HEALTH_ACTIVITY_CSV:
                return self._handle_health_activity(file_path)
            elif file_type == FileType.HEALTH_WORKOUT_JSON:
                return self._handle_health_workouts(file_path)
            else:
                logger.warning(f"[HANDLER] Unknown file type: {file_type}")
                return False

        except Exception as e:
            logger.error(f"[HANDLER] Failed to process {file_path.name}: {e}", exc_info=True)

            # Move to failed directory
            self.file_manager.move_to_failed(
                file_path,
                error_message=str(e),
                preserve_structure=True
            )
            return False

    def _handle_gymaholic_workout(self, file_path: Path) -> bool:
        """
        Handle Gymaholic workout CSV.

        Strategy:
        1. Parse workout from CSV
        2. Check if matching workout exists in Notion (via reconciliation)
        3. If match found: merge exercise data into existing workout
        4. If no match: create new workout
        5. Move file to processed

        Args:
            file_path: Path to Gymaholic CSV file

        Returns:
            True if successful
        """
        # Move to staging first
        staging_path = self.file_manager.move_to_staging(
            file_path,
            service="gymaholic"
        )

        if not staging_path:
            return False

        try:
            # Parse workout
            logger.info(f"[HANDLER] Parsing Gymaholic workout: {staging_path.name}")
            workout = self.gymaholic_parser.parse(staging_path)

            # Query Notion for workouts on same date
            workout_date = workout.date.date()
            existing_workouts = self._get_notion_workouts_for_date(workout_date)

            logger.info(
                f"[HANDLER] Found {len(existing_workouts)} existing workout(s) "
                f"for {workout_date.strftime('%Y-%m-%d')}"
            )

            # Try to find a match
            matched_workout = self.reconciler.match_workout(workout, existing_workouts)

            if matched_workout:
                # MERGE: Update existing workout with Gymaholic exercise data
                logger.info(
                    f"[HANDLER] Match found! Merging with existing workout "
                    f"{matched_workout['id']}"
                )

                updated_properties = self.reconciler.merge_workouts(
                    workout,
                    matched_workout
                )

                # Update in Notion
                result = self.notion_client.pages.update(
                    page_id=matched_workout["id"],
                    properties=updated_properties
                )

                logger.info(
                    f"[HANDLER] Successfully merged Gymaholic workout with existing "
                    f"HealthAutoExport workout"
                )

            else:
                # CREATE: No match found, create new workout
                logger.info(
                    f"[HANDLER] No match found, creating new workout"
                )

                result = self.notion_sync.sync_workout(workout)

                if not result["success"]:
                    raise Exception(f"Failed to create workout: {result.get('error')}")

                logger.info(f"[HANDLER] Created new Gymaholic workout")

            # Move to processed
            self.file_manager.move_to_processed(
                staging_path,
                preserve_structure=True
            )

            return True

        except Exception as e:
            logger.error(f"[HANDLER] Error processing Gymaholic workout: {e}", exc_info=True)

            # Move to failed
            self.file_manager.move_to_failed(
                staging_path,
                error_message=str(e),
                preserve_structure=True
            )
            return False

    def _handle_health_workouts(self, file_path: Path) -> bool:
        """
        Handle HealthAutoExport workout JSON.

        Strategy:
        1. Parse workouts from JSON (may contain multiple workouts)
        2. Check each for existing match in Notion
        3. If match found: merge HealthAutoExport data into existing Gymaholic workout
        4. If no match: create new workout
        5. Move file to processed

        Args:
            file_path: Path to HealthAutoExport workout JSON

        Returns:
            True if successful
        """
        # Move to staging first
        staging_path = self.file_manager.move_to_staging(
            file_path,
            service="health",
            category="workouts"
        )

        if not staging_path:
            return False

        try:
            # Parse workouts
            logger.info(f"[HANDLER] Parsing HealthAutoExport workouts: {staging_path.name}")
            workouts = self.workouts_parser.parse(staging_path)

            logger.info(f"[HANDLER] Found {len(workouts)} workout(s) in file")

            for workout in workouts:
                # Query Notion for workouts on same date
                workout_date = workout.date.date()
                existing_workouts = self._get_notion_workouts_for_date(workout_date)

                # Try to find a match
                matched_workout = self.reconciler.match_workout(workout, existing_workouts)

                if matched_workout:
                    # MERGE: Update existing workout with measured data
                    logger.info(
                        f"[HANDLER] Match found for {workout.workout_type}! "
                        f"Merging with {matched_workout['id']}"
                    )

                    updated_properties = self.reconciler.merge_workouts(
                        workout,
                        matched_workout
                    )

                    # Update in Notion
                    self.notion_client.pages.update(
                        page_id=matched_workout["id"],
                        properties=updated_properties
                    )

                    logger.info(
                        f"[HANDLER] Successfully merged HealthAutoExport data "
                        f"into existing workout"
                    )

                else:
                    # CREATE: No match found, create new workout
                    logger.info(
                        f"[HANDLER] No match found for {workout.workout_type}, "
                        f"creating new workout"
                    )

                    result = self.notion_sync.sync_workout(workout)

                    if not result["success"]:
                        raise Exception(
                            f"Failed to create workout {workout.workout_type}: "
                            f"{result.get('error')}"
                        )

                    logger.info(f"[HANDLER] Created new HealthAutoExport workout")

            # Move to processed
            self.file_manager.move_to_processed(
                staging_path,
                preserve_structure=True
            )

            return True

        except Exception as e:
            logger.error(f"[HANDLER] Error processing HealthAutoExport workouts: {e}", exc_info=True)

            # Move to failed
            self.file_manager.move_to_failed(
                staging_path,
                error_message=str(e),
                preserve_structure=True
            )
            return False

    def _handle_health_activity(self, file_path: Path) -> bool:
        """
        Handle HealthAutoExport activity metrics CSV.

        Strategy:
        1. Parse activity metrics
        2. Update Habit Tracker page
        3. Move file to processed

        Args:
            file_path: Path to activity metrics CSV

        Returns:
            True if successful
        """
        # Move to staging first
        staging_path = self.file_manager.move_to_staging(
            file_path,
            service="health",
            category="activity"
        )

        if not staging_path:
            return False

        try:
            # Parse metrics
            logger.info(f"[HANDLER] Parsing activity metrics: {staging_path.name}")
            metrics = self.metrics_parser.parse(staging_path)

            # Sync to Notion
            result = self.notion_sync.update_habit_tracker_metrics(metrics)

            if not result["success"]:
                raise Exception(f"Failed to sync metrics: {result.get('error')}")

            if result["updated_fields"]:
                logger.info(
                    f"[HANDLER] Updated Habit Tracker: "
                    f"{', '.join(result['updated_fields'])}"
                )
            else:
                logger.info(f"[HANDLER] No changes needed for metrics")

            # Move to processed
            self.file_manager.move_to_processed(
                staging_path,
                preserve_structure=True
            )

            return True

        except Exception as e:
            logger.error(f"[HANDLER] Error processing activity metrics: {e}", exc_info=True)

            # Move to failed
            self.file_manager.move_to_failed(
                staging_path,
                error_message=str(e),
                preserve_structure=True
            )
            return False

    def _get_notion_workouts_for_date(self, target_date) -> List[Dict[str, Any]]:
        """
        Query Notion for workouts on a specific date.

        Args:
            target_date: Date to query for (date object)

        Returns:
            List of Notion workout page dicts
        """
        # Query workouts for this date (and ±1 day for tolerance)
        start_date = target_date - timedelta(days=1)
        end_date = target_date + timedelta(days=1)

        # Use Notion filter to get workouts in date range
        workouts_db_id = Config.NOTION_WORKOUTS_DATABASE_ID

        filter_params = {
            "and": [
                {
                    "property": "Date",
                    "date": {
                        "on_or_after": start_date.isoformat()
                    }
                },
                {
                    "property": "Date",
                    "date": {
                        "on_or_before": end_date.isoformat()
                    }
                }
            ]
        }

        try:
            response = self.notion_client.databases.query(
                database_id=workouts_db_id,
                filter=filter_params
            )

            workouts = response.get("results", [])

            return workouts

        except Exception as e:
            logger.error(f"[HANDLER] Failed to query Notion workouts: {e}")
            return []
