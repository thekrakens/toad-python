"""Event-driven health data processor for TOAD daemon.

Processes health files immediately as they arrive in the inbox,
using the reconciliation engine to handle late exports.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, date
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

logger = logging.getLogger(__name__)

# Timing/tolerance constants
RECONCILIATION_TOLERANCE_SECONDS = 5  # DateTime matching tolerance for reconciliation
WORKOUT_DATE_LOOKUP_DAYS = 1  # Days before/after workout date to search


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

        # Initialize reconciliation engine
        self.reconciler = WorkoutReconciler(tolerance_seconds=RECONCILIATION_TOLERANCE_SECONDS)

        # Initialize Notion sync
        self.notion_client = TOADNotionClient()
        self.notion_sync = HealthNotionSync(self.notion_client)

    def write_staging_file(
        self,
        staging_data: Dict[str, Any],
        workout_name: str
    ) -> Path:
        """
        Write staging JSON to staging directory (flat structure).

        Args:
            staging_data: Complete staging data dict (Notion-ready)
            workout_name: Workout name for filename (e.g., 'TOMO_A_Strength', 'Run', 'HealthActivity')

        Returns:
            Path to staging JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Flat structure - no subdirectories
        self.file_manager.staging_dir.mkdir(parents=True, exist_ok=True)

        # Clean workout name for filename (remove spaces, special chars)
        clean_name = workout_name.replace(" ", "_").replace("/", "_")
        staging_file = self.file_manager.staging_dir / f"{clean_name}_{timestamp}.json"

        # Write JSON
        staging_file.write_text(json.dumps(staging_data, indent=2, default=str))

        logger.info(f"[HANDLER] Wrote staging file: {staging_file.name}")

        return staging_file

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
                error_message=str(e)
            )
            return False

    def _handle_gymaholic_workout(self, file_path: Path) -> bool:
        """
        Handle Gymaholic workout CSV.

        CORRECT FLOW:
        1. Parse workout from CSV (in memory)
        2. Generate Notion properties (in memory)
        3. Check reconciliation
        4. Build staging data (Notion-ready JSON)
        5. Write staging JSON
        6. Archive raw file
        7. Sync to Notion using staging data
        8. Update staging with sync result
        9. Move staging to processed

        Args:
            file_path: Path to Gymaholic CSV file in inbox

        Returns:
            True if successful
        """
        try:
            # STEP 1: Parse workout from raw file (in memory)
            logger.info(f"[HANDLER] Parsing Gymaholic workout: {file_path.name}")
            workout = self.gymaholic_parser.parse(file_path)
            logger.info(
                f"[HANDLER] Parsed workout: source={workout.source}, "
                f"notes={workout.notes}, exercises={len(workout.exercises) if workout.exercises else 0}"
            )

            workout_date = workout.date.date()

            # STEP 2: Generate summaries and Notion properties (in memory)
            logger.info(f"[HANDLER] Generating workout summaries...")

            # Generate workout summary with progression
            workout_summary = self.notion_sync._generate_workout_summary_with_progression(workout)

            # Generate name summary
            name_summary = self.notion_sync.generate_workout_summary(workout)

            # Build Notion properties with both summaries
            notion_properties = self.notion_sync._build_workout_properties(
                workout,
                name_summary,
                workout_summary
            )

            # STEP 3: Check reconciliation
            existing_workouts = self._get_notion_workouts_for_date(workout_date)
            logger.info(
                f"[HANDLER] Found {len(existing_workouts)} existing workout(s) "
                f"for {workout_date.strftime('%Y-%m-%d')}"
            )

            matched_workout = self.reconciler.match_workout(workout, existing_workouts)
            logger.info(
                f"[HANDLER] Reconciliation result: "
                f"{'MATCH FOUND' if matched_workout else 'NO MATCH - WILL CREATE NEW'}"
            )

            reconciliation_info = {
                "action": "merge" if matched_workout else "create",
                "matched_page_id": matched_workout["id"] if matched_workout else None,
                "reason": "Found existing workout within tolerance" if matched_workout else "No match found"
            }

            # STEP 4: Build staging data (Notion-ready JSON)
            staging_data = {
                "version": "1.0",
                "type": "workout",
                "source_file": {
                    "path": str(file_path),
                    "filename": file_path.name,
                    "source": "Gymaholic"
                },
                "parsed_at": datetime.now().isoformat(),
                "workout_data": {
                    "date": workout.date.isoformat(),
                    "workout_type": workout.workout_type,
                    "notes": workout.notes,
                    "duration_minutes": workout.duration_minutes,
                    "calories": workout.calories,
                    "exercise_count": len(workout.exercises) if workout.exercises else 0
                },
                "notion_properties": notion_properties,
                "reconciliation": reconciliation_info,
                "sync_result": {}  # Will be filled after sync
            }

            # STEP 5: Write staging JSON
            # Use workout notes as filename (e.g., "TOMO_A_Strength")
            workout_name = workout.notes if workout.notes else workout.workout_type
            staging_file = self.write_staging_file(staging_data, workout_name)

            # STEP 6: Archive raw file
            archive_file = self.file_manager.move_to_archive(
                file_path,
                source_type="GYMAHOLIC"
            )

            if not archive_file:
                raise Exception("Failed to archive raw file")

            # STEP 7: Sync to Notion
            if matched_workout:
                # MERGE: Update existing workout
                logger.info(
                    f"[HANDLER] Merging with existing workout {matched_workout['id']}"
                )

                updated_properties = self.reconciler.merge_workouts(
                    workout,
                    matched_workout
                )

                # For Gymaholic merges, always include Name, Type, and Summary from staging
                # (Gymaholic data takes priority over HealthAutoExport)
                updated_properties["Name"] = notion_properties["Name"]
                updated_properties["Type"] = notion_properties["Type"]

                if workout_summary:
                    updated_properties["Summary"] = {
                        "rich_text": [{"text": {"content": workout_summary}}]
                    }

                result = self.notion_client.client.pages.update(
                    page_id=matched_workout["id"],
                    properties=updated_properties
                )

                sync_result = {
                    "success": True,
                    "action": "merged",
                    "notion_page_id": matched_workout["id"],
                    "synced_at": datetime.now().isoformat(),
                    "error": None
                }

                logger.info(
                    f"[HANDLER] Successfully merged Gymaholic workout with existing workout"
                )

            else:
                # CREATE: New workout
                logger.info(f"[HANDLER] Creating new workout")

                result = self.notion_sync.sync_workout(workout)

                if not result["success"]:
                    raise Exception(f"Failed to create workout: {result.get('error')}")

                sync_result = {
                    "success": True,
                    "action": "created",
                    "notion_page_id": result.get("workout_page_id"),
                    "synced_at": datetime.now().isoformat(),
                    "error": None
                }

                logger.info(f"[HANDLER] Created new Gymaholic workout successfully")

            # STEP 8: Update staging file with sync result
            staging_data["sync_result"] = sync_result
            staging_file.write_text(json.dumps(staging_data, indent=2, default=str))

            # STEP 9: Move staging to processed
            self.file_manager.move_to_processed(staging_file)

            return True

        except Exception as e:
            logger.error(
                f"[HANDLER] Error processing Gymaholic workout: {e}",
                exc_info=True,
                extra={'workout_file': file_path.name}
            )

            # Move to failed
            self.file_manager.move_to_failed(
                file_path,
                error_message=str(e)
            )
            return False

    def _handle_health_workouts(self, file_path: Path) -> bool:
        """
        Handle HealthAutoExport workout JSON.

        CORRECT FLOW:
        1. Parse workouts from JSON (in memory, may be multiple)
        2. For each workout:
           - Generate Notion properties
           - Check reconciliation
           - Build staging data
           - Write staging JSON
        3. Archive raw file (once for all workouts)
        4. For each workout: Sync to Notion
        5. Move staging files to processed

        Args:
            file_path: Path to HealthAutoExport workout JSON in inbox

        Returns:
            True if successful
        """
        try:
            # STEP 1: Parse workouts from raw file (in memory)
            logger.info(f"[HANDLER] Parsing HealthAutoExport workouts: {file_path.name}")
            workouts = self.workouts_parser.parse(file_path)
            logger.info(f"[HANDLER] Found {len(workouts)} workout(s) in file")

            staging_files = []

            # Process each workout
            for workout in workouts:
                workout_date = workout.date.date()

                # STEP 2: Generate summaries and Notion properties (in memory)
                workout_summary = self.notion_sync._generate_workout_summary_with_progression(workout)
                name_summary = self.notion_sync.generate_workout_summary(workout)

                # Build Notion properties with both summaries
                notion_properties = self.notion_sync._build_workout_properties(
                    workout,
                    name_summary,
                    workout_summary
                )

                # STEP 3: Check reconciliation
                existing_workouts = self._get_notion_workouts_for_date(workout_date)
                matched_workout = self.reconciler.match_workout(workout, existing_workouts)

                logger.info(
                    f"[HANDLER] {workout.workout_type}: "
                    f"{'MATCH FOUND' if matched_workout else 'NO MATCH - WILL CREATE NEW'}"
                )

                reconciliation_info = {
                    "action": "merge" if matched_workout else "create",
                    "matched_page_id": matched_workout["id"] if matched_workout else None,
                    "reason": "Found existing workout within tolerance" if matched_workout else "No match found"
                }

                # STEP 4: Build staging data
                staging_data = {
                    "version": "1.0",
                    "type": "workout",
                    "source_file": {
                        "path": str(file_path),
                        "filename": file_path.name,
                        "source": "HealthAutoExport"
                    },
                    "parsed_at": datetime.now().isoformat(),
                    "workout_data": {
                        "date": workout.date.isoformat(),
                        "workout_type": workout.workout_type,
                        "notes": workout.notes,
                        "duration_minutes": workout.duration_minutes,
                        "calories": workout.calories,
                        "avg_heart_rate": workout.avg_heart_rate,
                        "distance_miles": workout.distance_miles
                    },
                    "notion_properties": notion_properties,
                    "reconciliation": reconciliation_info,
                    "sync_result": {}
                }

                # STEP 5: Write staging JSON
                workout_name = workout.workout_type  # e.g., "Run", "Strength", "Climb"
                staging_file = self.write_staging_file(staging_data, workout_name)
                staging_files.append((staging_file, staging_data, workout, matched_workout))

            # STEP 6: Archive raw file (once for all workouts)
            archive_file = self.file_manager.move_to_archive(
                file_path,
                source_type="TOAD_Workouts"
            )

            if not archive_file:
                raise Exception("Failed to archive raw file")

            # STEP 7: Sync each workout to Notion
            for staging_file, staging_data, workout, matched_workout in staging_files:
                if matched_workout:
                    # MERGE: Update existing workout
                    logger.info(
                        f"[HANDLER] Merging {workout.workout_type} with {matched_workout['id']}"
                    )

                    updated_properties = self.reconciler.merge_workouts(
                        workout,
                        matched_workout
                    )

                    result = self.notion_client.client.pages.update(
                        page_id=matched_workout["id"],
                        properties=updated_properties
                    )

                    sync_result = {
                        "success": True,
                        "action": "merged",
                        "notion_page_id": matched_workout["id"],
                        "synced_at": datetime.now().isoformat(),
                        "error": None
                    }

                    logger.info(
                        f"[HANDLER] Successfully merged HealthAutoExport workout"
                    )

                else:
                    # CREATE: New workout
                    logger.info(
                        f"[HANDLER] Creating new workout for {workout.workout_type}"
                    )

                    result = self.notion_sync.sync_workout(workout)

                    if not result["success"]:
                        raise Exception(
                            f"Failed to create workout {workout.workout_type}: "
                            f"{result.get('error')}"
                        )

                    sync_result = {
                        "success": True,
                        "action": "created",
                        "notion_page_id": result.get("workout_page_id"),
                        "synced_at": datetime.now().isoformat(),
                        "error": None
                    }

                    logger.info(f"[HANDLER] Created new HealthAutoExport workout")

                # STEP 8: Update staging file with sync result
                staging_data["sync_result"] = sync_result
                staging_file.write_text(json.dumps(staging_data, indent=2, default=str))

                # STEP 9: Move staging to processed
                self.file_manager.move_to_processed(staging_file)

            return True

        except Exception as e:
            logger.error(
                f"[HANDLER] Error processing HealthAutoExport workouts: {e}",
                exc_info=True
            )

            # Move to failed
            self.file_manager.move_to_failed(
                file_path,
                error_message=str(e)
            )
            return False

    def _handle_health_activity(self, file_path: Path) -> bool:
        """
        Handle HealthAutoExport activity metrics CSV.

        CORRECT FLOW:
        1. Parse metrics from CSV (in memory)
        2. Build staging data (Notion-ready)
        3. Write staging JSON
        4. Archive raw file
        5. Sync to Notion (update Habit Tracker)
        6. Update staging with sync result
        7. Move staging to processed

        Args:
            file_path: Path to activity metrics CSV in inbox

        Returns:
            True if successful
        """
        try:
            # STEP 1: Parse metrics from raw file (in memory)
            logger.info(f"[HANDLER] Parsing activity metrics: {file_path.name}")
            metrics = self.metrics_parser.parse(file_path)

            # Use metrics date for organization
            metrics_date = metrics.date

            # STEP 2: Build staging data
            staging_data = {
                "version": "1.0",
                "type": "activity_metrics",
                "source_file": {
                    "path": str(file_path),
                    "filename": file_path.name,
                    "source": "HealthAutoExport"
                },
                "parsed_at": datetime.now().isoformat(),
                "metrics_data": {
                    "date": metrics_date.isoformat(),
                    "calories_in": metrics.calories_in,
                    "calories_out": metrics.calories_out,
                    "weight": metrics.weight,
                    "body_fat": metrics.body_fat
                },
                "sync_result": {}
            }

            # STEP 3: Write staging JSON
            staging_file = self.write_staging_file(staging_data, "HealthActivity")

            # STEP 4: Archive raw file
            archive_file = self.file_manager.move_to_archive(
                file_path,
                source_type="TOAD_Activity"
            )

            if not archive_file:
                raise Exception("Failed to archive raw file")

            # STEP 5: Sync to Notion
            result = self.notion_sync.update_habit_tracker_metrics(metrics)

            if not result["success"]:
                raise Exception(f"Failed to sync metrics: {result.get('error')}")

            sync_result = {
                "success": True,
                "updated_fields": result.get("updated_fields", []),
                "synced_at": datetime.now().isoformat(),
                "error": None
            }

            if result["updated_fields"]:
                logger.info(
                    f"[HANDLER] Updated Habit Tracker: "
                    f"{', '.join(result['updated_fields'])}"
                )
            else:
                logger.info(f"[HANDLER] No changes needed for metrics")

            # STEP 6: Update staging file with sync result
            staging_data["sync_result"] = sync_result
            staging_file.write_text(json.dumps(staging_data, indent=2, default=str))

            # STEP 7: Move staging to processed
            self.file_manager.move_to_processed(staging_file)

            return True

        except Exception as e:
            logger.error(
                f"[HANDLER] Error processing activity metrics: {e}",
                exc_info=True
            )

            # Move to failed
            self.file_manager.move_to_failed(
                file_path,
                error_message=str(e)
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
        # Query workouts for this date (with day tolerance)
        start_date = target_date - timedelta(days=WORKOUT_DATE_LOOKUP_DAYS)
        end_date = target_date + timedelta(days=WORKOUT_DATE_LOOKUP_DAYS)

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
            # Use TOADNotionClient's method instead of accessing client directly
            workouts = self.notion_client.get_database_pages(
                database_id=workouts_db_id,
                filter_dict=filter_params
            )

            return workouts

        except Exception as e:
            logger.error(f"[HANDLER] Failed to query Notion workouts: {e}")
            return []
