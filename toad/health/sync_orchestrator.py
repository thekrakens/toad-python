"""Health sync orchestrator for TOAD.

Coordinates syncing of health data from multiple sources (Gymaholic, HealthAutoExport)
to Notion (Workouts table, Habit Tracker).
"""

from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import logging

from toad.config import Config
from toad.health.parsers.health_auto_export_metrics import HealthAutoExportMetricsParser
from toad.health.parsers.health_auto_export import HealthAutoExportParser
from toad.health.parsers.gymaholic import GymaholicParser
from toad.health.models import DailyActivityMetrics, WorkoutData

logger = logging.getLogger(__name__)


class HealthSyncOrchestrator:
    """Orchestrates health data sync operations."""

    def __init__(self, dry_run: bool = False):
        """Initialize the health sync orchestrator.

        Args:
            dry_run: If True, only simulate sync without updating Notion
        """
        self.dry_run = dry_run
        self.metrics_parser = HealthAutoExportMetricsParser()
        self.workouts_parser = HealthAutoExportParser()
        self.gymaholic_parser = GymaholicParser()

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

        # Process Gymaholic CSVs from inbox (scan once, filter by date range)
        if gymaholic_inbox:
            try:
                gymaholic_workouts = self._sync_gymaholic_inbox(gymaholic_inbox, start_date, end_date)
                summary['gymaholic_workouts_processed'] = len(gymaholic_workouts)
                if gymaholic_workouts:
                    logger.info(f"✅ Synced {len(gymaholic_workouts)} Gymaholic workout(s)")
            except Exception as e:
                error = f"Gymaholic inbox: {str(e)}"
                logger.error(f"❌ {error}")
                summary['errors'].append(error)

        # Process each date in range for HealthAutoExport data
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
                            logger.info(f"✅ Synced activity metrics for {date_str}")
                    except Exception as e:
                        error = f"{date_str} activity metrics: {str(e)}"
                        logger.error(f"❌ {error}")
                        summary['errors'].append(error)
                else:
                    logger.debug(f"No activity metrics file for {date_str}")

            # Sync workouts for this date
            if workouts_path:
                workouts_file = workouts_path / f"HealthAutoExport-{date_str}.json"
                if workouts_file.exists():
                    try:
                        workouts = self._sync_workouts(workouts_file)
                        if workouts:
                            summary['workouts_processed'] += len(workouts)
                            logger.info(f"✅ Synced {len(workouts)} HealthAutoExport workout(s) for {date_str}")
                    except Exception as e:
                        error = f"{date_str} workouts: {str(e)}"
                        logger.error(f"❌ {error}")
                        summary['errors'].append(error)
                else:
                    logger.debug(f"No workouts file for {date_str}")

            # Move to next date
            from datetime import timedelta
            current_date += timedelta(days=1)

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
            # TODO: Implement Notion update
            logger.warning(f"  → Notion update not yet implemented for metrics")

        return metrics

    def _sync_workouts(self, file_path: Path) -> List[WorkoutData]:
        """Sync workouts from a file.

        Args:
            file_path: Path to HealthAutoExport workouts JSON

        Returns:
            List of parsed WorkoutData objects
        """
        workouts = self.workouts_parser.parse(file_path)

        if self.dry_run:
            for workout in workouts:
                self._log_workout_dry_run(workout)
        else:
            # TODO: Implement Notion update
            logger.warning(f"  → Notion update not yet implemented for workouts")

        return workouts

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

    def _sync_gymaholic_inbox(self, inbox_path: Path, start_date: date, end_date: date) -> List[WorkoutData]:
        """Sync Gymaholic CSVs from inbox directory.

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

                    if self.dry_run:
                        self._log_gymaholic_workout_dry_run(workout)
                    else:
                        # TODO: Implement Notion update
                        logger.warning(f"  → Notion update not yet implemented for Gymaholic")

            except Exception as e:
                logger.error(f"❌ Failed to parse {csv_file.name}: {e}")

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
