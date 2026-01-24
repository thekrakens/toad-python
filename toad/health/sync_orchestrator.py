"""Health sync orchestrator for TOAD.

Coordinates syncing of health data from multiple sources (Gymaholic, HealthAutoExport)
to Notion (Workouts table, Habit Tracker).
"""

from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import logging
import shutil

from toad.config import Config
from toad.notion_client import TOADNotionClient
from toad.health.parsers.health_auto_export_metrics import HealthAutoExportMetricsParser
from toad.health.parsers.health_auto_export import HealthAutoExportParser
from toad.health.parsers.gymaholic import GymaholicParser
from toad.health.notion_sync import HealthNotionSync
from toad.health.workout_merger import WorkoutMerger
from toad.health.models import DailyActivityMetrics, WorkoutData

logger = logging.getLogger(__name__)


class HealthSyncOrchestrator:
    """Orchestrates health data sync operations."""

    def __init__(self, dry_run: bool = False, notion_client: Optional[TOADNotionClient] = None):
        """Initialize the health sync orchestrator.

        Args:
            dry_run: If True, only simulate sync without updating Notion
            notion_client: Optional TOADNotionClient instance (creates one if not provided)
        """
        self.dry_run = dry_run
        self.metrics_parser = HealthAutoExportMetricsParser()
        self.workouts_parser = HealthAutoExportParser()
        self.gymaholic_parser = GymaholicParser()
        self.workout_merger = WorkoutMerger()

        # Initialize Notion sync (only if not in dry-run mode)
        if not dry_run:
            self.notion_client = notion_client or TOADNotionClient()
            self.notion_sync = HealthNotionSync(self.notion_client)
        else:
            self.notion_client = None
            self.notion_sync = None

    def sync_date_range(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync health data for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Summary dict with counts and errors
        """
        summary = {
            'metrics_processed': 0,
            'workouts_processed': 0,
            'gymaholic_workouts_processed': 0,
            'errors': [],
            'dry_run': self.dry_run
        }

        # Validate config
        config_valid = True
        if not Config.validate_health_auto_export_paths():
            logger.warning("HealthAutoExport paths not configured. Skipping HealthAutoExport data.")
            config_valid = False

        if config_valid:
            workouts_path = Path(Config.HEALTH_AUTO_EXPORT_WORKOUTS_PATH)
            activity_path = Path(Config.HEALTH_AUTO_EXPORT_ACTIVITY_PATH)
        else:
            workouts_path = None
            activity_path = None

        # Get Gymaholic inbox path
        gymaholic_inbox = None
        if Config.WORKOUT_SYNC_INBOX_PATH:
            gymaholic_inbox = Path(Config.WORKOUT_SYNC_INBOX_PATH) / "gymaholic"
            if not gymaholic_inbox.exists():
                logger.warning(f"Gymaholic inbox not found: {gymaholic_inbox}")
                gymaholic_inbox = None

        # Parse all Gymaholic CSVs from inbox (collect, don't sync yet)
        all_gymaholic_workouts = []
        if gymaholic_inbox:
            try:
                all_gymaholic_workouts = self._parse_gymaholic_inbox(gymaholic_inbox, start_date, end_date)
                logger.info(f"Found {len(all_gymaholic_workouts)} Gymaholic workout(s) in date range")
            except Exception as e:
                error = f"Gymaholic inbox: {str(e)}"
                logger.error(f"[HEALTH_SYNC] {error}")
                summary['errors'].append(error)

        # Process each date in range
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            # Sync activity metrics for this date
            if activity_path:
                activity_file = activity_path / f"HealthAutoExport-{date_str}.json"
                if activity_file.exists():
                    try:
                        metrics = self._sync_activity_metrics(activity_file)
                        if metrics:
                            summary['metrics_processed'] += 1
                            logger.info(f"[HEALTH_SYNC] Synced activity metrics for {date_str}")
                    except Exception as e:
                        error = f"{date_str} activity metrics: {str(e)}"
                        logger.error(f"[HEALTH_SYNC] {error}")
                        summary['errors'].append(error)
                else:
                    logger.debug(f"No activity metrics file for {date_str}")

            # Parse HealthAutoExport workouts for this date (don't sync yet)
            healthautoexport_workouts = []
            if workouts_path:
                workouts_file = workouts_path / f"HealthAutoExport-{date_str}.json"
                if workouts_file.exists():
                    try:
                        healthautoexport_workouts = self.workouts_parser.parse(workouts_file)
                        logger.debug(f"Parsed {len(healthautoexport_workouts)} HealthAutoExport workout(s) for {date_str}")
                    except Exception as e:
                        error = f"{date_str} HealthAutoExport workouts: {str(e)}"
                        logger.error(f"[HEALTH_SYNC] {error}")
                        summary['errors'].append(error)

            # Get Gymaholic workouts for this date
            gymaholic_workouts = [w for w in all_gymaholic_workouts if w.date.date() == current_date]

            # Merge workouts from both sources
            merged_workouts = self.workout_merger.merge_workouts_for_day(
                gymaholic_workouts,
                healthautoexport_workouts
            )

            # Sync merged workouts
            if merged_workouts:
                try:
                    synced_workouts = self._sync_merged_workouts(merged_workouts)

                    # Count by source for summary
                    gymaholic_count = sum(1 for w in synced_workouts if w.source == "Gymaholic")
                    healthautoexport_count = len(synced_workouts) - gymaholic_count

                    summary['gymaholic_workouts_processed'] += gymaholic_count
                    summary['workouts_processed'] += healthautoexport_count

                    logger.info(f"[HEALTH_SYNC] Synced {len(synced_workouts)} workout(s) for {date_str} ({gymaholic_count} Gymaholic, {healthautoexport_count} HealthAutoExport)")

                    # Move processed Gymaholic CSVs
                    if not self.dry_run:
                        self._move_processed_gymaholic_csvs(synced_workouts)

                    # Update Habit Tracker page content
                    if not self.dry_run:
                        try:
                            result = self.notion_sync.update_habit_tracker_workout_summary(current_date, synced_workouts)
                            if result["success"]:
                                logger.info(f"  → Updated Habit Tracker page content")
                        except Exception as e:
                            logger.error(f"  → Failed to update Habit Tracker page content: {e}")

                except Exception as e:
                    error = f"{date_str} workout sync: {str(e)}"
                    logger.error(f"[HEALTH_SYNC] {error}")
                    summary['errors'].append(error)

            # Move to next date
            from datetime import timedelta
            current_date += timedelta(days=1)

        # Run Health Stats ETL for the entire date range (after all metrics/workouts synced)
        if not self.dry_run:
            try:
                logger.info("Running Health Stats ETL...")
                etl_result = self.notion_sync.sync_health_stats_for_date_range(start_date, end_date)
                if etl_result["success"]:
                    logger.info(
                        f"[HEALTH_SYNC] Health Stats ETL complete: "
                        f"{etl_result['entries_created']} created, "
                        f"{etl_result['entries_updated']} updated"
                    )
                    summary['health_stats_created'] = etl_result['entries_created']
                    summary['health_stats_updated'] = etl_result['entries_updated']
                else:
                    error = f"Health Stats ETL failed: {etl_result.get('errors', [])}"
                    logger.error(f"[HEALTH_SYNC] {error}")
                    summary['errors'].append(error)
            except Exception as e:
                error = f"Health Stats ETL: {str(e)}"
                logger.error(f"[HEALTH_SYNC] {error}")
                summary['errors'].append(error)

        return summary

    def _sync_activity_metrics(self, file_path: Path) -> Optional[DailyActivityMetrics]:
        """Sync activity metrics from a file.

        Args:
            file_path: Path to HealthAutoExport activity metrics JSON

        Returns:
            Parsed DailyActivityMetrics object or None
        """
        metrics = self.metrics_parser.parse(file_path)

        if self.dry_run:
            self._log_metrics_dry_run(metrics)
        else:
            # Sync to Notion
            result = self.notion_sync.update_habit_tracker_metrics(metrics)
            if result["success"]:
                if result["updated_fields"]:
                    logger.info(f"  → Updated: {', '.join(result['updated_fields'])}")
                else:
                    logger.info(f"  → No changes needed")
            else:
                logger.error(f"  → Sync failed: {result.get('error', 'Unknown error')}")
                raise Exception(f"Failed to sync metrics: {result.get('error')}")

        return metrics

    def _sync_merged_workouts(self, workouts: List[WorkoutData]) -> List[WorkoutData]:
        """Sync merged workouts to Notion.

        Args:
            workouts: List of merged WorkoutData objects to sync

        Returns:
            List of successfully synced workouts
        """
        synced = []

        for workout in workouts:
            if self.dry_run:
                # Log based on source
                if workout.source == "Gymaholic":
                    self._log_gymaholic_workout_dry_run(workout)
                else:
                    self._log_workout_dry_run(workout)
                synced.append(workout)
            else:
                # Sync to Notion
                try:
                    result = self.notion_sync.sync_workout(workout)
                    if result["success"]:
                        if result.get("is_duplicate"):
                            logger.info(f"  → Updated existing workout: {workout.workout_type}")
                        else:
                            logger.info(f"  → Created new workout: {workout.workout_type}")
                        if result.get("habit_tracker_updated"):
                            logger.info(f"  → Updated Habit Tracker checkboxes")
                        synced.append(workout)
                    else:
                        logger.error(f"  → Failed to sync workout: {result.get('error')}")
                except Exception as e:
                    logger.error(f"  → Error syncing workout: {e}")

        return synced

    def _log_metrics_dry_run(self, metrics: DailyActivityMetrics):
        """Log activity metrics in dry-run mode.

        Args:
            metrics: Parsed metrics object
        """
        logger.info(f"  [DRY RUN] Activity Metrics for {metrics.date.strftime('%Y-%m-%d')}")
        if metrics.calories_in is not None:
            logger.info(f"    CaloriesIn: {metrics.calories_in} kcal")
        if metrics.calories_out is not None:
            logger.info(f"    CaloriesOut: {metrics.calories_out} kcal")
        if metrics.weight is not None:
            logger.info(f"    Weight: {metrics.weight} lbs")
        if metrics.body_fat is not None:
            logger.info(f"    BodyFat: {metrics.body_fat}%")

    def _move_processed_gymaholic_csvs(self, synced_workouts: List[WorkoutData]) -> None:
        """Move successfully synced Gymaholic CSVs to processed folder.

        Args:
            synced_workouts: List of successfully synced workouts
        """
        if not Config.WORKOUT_SYNC_INBOX_PATH:
            return

        # Get processed folder path
        processed_folder = Path(Config.WORKOUT_SYNC_INBOX_PATH) / "processed" / "gymaholic"

        # Create processed folder if it doesn't exist
        processed_folder.mkdir(parents=True, exist_ok=True)

        # Move Gymaholic CSV files
        for workout in synced_workouts:
            if workout.source == "Gymaholic" and workout.raw_file_path:
                csv_path = Path(workout.raw_file_path)

                # Only move if file still exists in inbox
                if csv_path.exists() and "inbox" in str(csv_path):
                    try:
                        # Destination path
                        dest_path = processed_folder / csv_path.name

                        # If destination already exists, add timestamp
                        if dest_path.exists():
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            stem = dest_path.stem
                            suffix = dest_path.suffix
                            dest_path = processed_folder / f"{stem}_{timestamp}{suffix}"

                        # Move file
                        shutil.move(str(csv_path), str(dest_path))
                        logger.info(f"  → Moved CSV to processed: {csv_path.name}")

                    except Exception as e:
                        logger.warning(f"  → Failed to move CSV {csv_path.name}: {e}")

    def _parse_gymaholic_inbox(self, inbox_path: Path, start_date: date, end_date: date) -> List[WorkoutData]:
        """Parse Gymaholic CSVs from inbox directory.

        Args:
            inbox_path: Path to Gymaholic inbox directory
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)

        Returns:
            List of WorkoutData objects that fall within date range
        """
        workouts = []

        # Scan for CSV files
        csv_files = list(inbox_path.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} Gymaholic CSV file(s) in inbox")

        for csv_file in csv_files:
            try:
                # Parse the CSV
                workout = self.gymaholic_parser.parse(csv_file)

                # Check if workout date falls within range
                workout_date = workout.date.date()  # Convert datetime to date
                if start_date <= workout_date <= end_date:
                    workouts.append(workout)

            except Exception as e:
                logger.error(f"[HEALTH_SYNC] Failed to parse {csv_file.name}: {e}")

        return workouts

    def _log_workout_dry_run(self, workout: WorkoutData):
        """Log workout data in dry-run mode.

        Args:
            workout: Parsed workout object
        """
        logger.info(f"  [DRY RUN] {workout.workout_type} - {workout.date.strftime('%Y-%m-%d %H:%M')}")
        if workout.duration_minutes:
            hours = int(workout.duration_minutes // 60)
            mins = int(workout.duration_minutes % 60)
            duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            logger.info(f"    Duration: {duration_str}")
        if workout.calories:
            logger.info(f"    Calories: {workout.calories} kcal")
        if workout.avg_heart_rate:
            logger.info(f"    Avg HR: {workout.avg_heart_rate} bpm")
        if workout.distance_miles:
            logger.info(f"    Distance: {workout.distance_miles} mi")

    def _log_gymaholic_workout_dry_run(self, workout: WorkoutData):
        """Log Gymaholic workout data in dry-run mode (includes exercise details).

        Args:
            workout: Parsed Gymaholic workout object
        """
        logger.info(f"  [DRY RUN] Gymaholic: {workout.notes or 'Strength'} - {workout.date.strftime('%Y-%m-%d %H:%M')}")
        if workout.duration_minutes:
            hours = int(workout.duration_minutes // 60)
            mins = int(workout.duration_minutes % 60)
            duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            logger.info(f"    Duration: {duration_str}")
        if workout.calories:
            logger.info(f"    Calories: {workout.calories} kcal")
        if workout.avg_heart_rate:
            logger.info(f"    Avg HR: {workout.avg_heart_rate} bpm")

        # Log exercise details
        if workout.exercises:
            logger.info(f"    Exercises: {len(workout.exercises)} total")
            for i, exercise in enumerate(workout.exercises[:5], 1):  # Show first 5
                # Format exercise details
                if exercise.weight and exercise.reps:
                    sets_info = []
                    for w, r in zip(exercise.weight, exercise.reps):
                        if w > 0:
                            sets_info.append(f"{w}lbs x{r}")
                        else:
                            sets_info.append(f"x{r}")
                    sets_str = ", ".join(sets_info)
                    logger.info(f"      {i}. {exercise.name}: {sets_str}")
                else:
                    logger.info(f"      {i}. {exercise.name}: {exercise.sets} sets")

            if len(workout.exercises) > 5:
                logger.info(f"      ... and {len(workout.exercises) - 5} more exercises")
