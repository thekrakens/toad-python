#!/usr/bin/env python3
"""Import health data from HealthAutoExport JSON files.

This script can import:
- Activity metrics (calories, weight, body fat) → Habit Tracker
- Workouts (running, climbing, hiking, etc.) → Workouts table

Supports --dry-run mode to preview what would be imported without touching Notion.
"""

import argparse
import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from toad.health.parsers.health_auto_export_metrics import HealthAutoExportMetricsParser
from toad.health.parsers.health_auto_export import HealthAutoExportParser
from toad.health.models import DailyActivityMetrics, WorkoutData


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_metrics_summary(metrics: DailyActivityMetrics, dry_run: bool = True):
    """Print a summary of parsed activity metrics.

    Args:
        metrics: Parsed metrics object
        dry_run: If True, prefix with [DRY RUN]
    """
    prefix = f"{Colors.WARNING}[DRY RUN]{Colors.ENDC} " if dry_run else f"{Colors.OKGREEN}[IMPORTING]{Colors.ENDC} "

    print(f"\n{prefix}{Colors.BOLD}Activity Metrics for {metrics.date.strftime('%Y-%m-%d')}{Colors.ENDC}")
    print(f"  Source: {metrics.source}")

    if metrics.calories_in is not None:
        print(f"  {Colors.OKCYAN}CaloriesIn:{Colors.ENDC} {metrics.calories_in} kcal")
    else:
        print(f"  CaloriesIn: {Colors.WARNING}(no data){Colors.ENDC}")

    if metrics.calories_out is not None:
        print(f"  {Colors.OKCYAN}CaloriesOut:{Colors.ENDC} {metrics.calories_out} kcal")
    else:
        print(f"  CaloriesOut: {Colors.WARNING}(no data){Colors.ENDC}")

    if metrics.weight is not None:
        print(f"  {Colors.OKCYAN}Weight:{Colors.ENDC} {metrics.weight} lbs")
    else:
        print(f"  Weight: {Colors.WARNING}(no data){Colors.ENDC}")

    if metrics.body_fat is not None:
        print(f"  {Colors.OKCYAN}BodyFat:{Colors.ENDC} {metrics.body_fat}%")
    else:
        print(f"  BodyFat: {Colors.WARNING}(no data){Colors.ENDC}")


def print_workout_summary(workout: WorkoutData, dry_run: bool = True):
    """Print a summary of parsed workout data.

    Args:
        workout: Parsed workout object
        dry_run: If True, prefix with [DRY RUN]
    """
    prefix = f"{Colors.WARNING}[DRY RUN]{Colors.ENDC} " if dry_run else f"{Colors.OKGREEN}[IMPORTING]{Colors.ENDC} "

    print(f"\n{prefix}{Colors.BOLD}{workout.workout_type} - {workout.date.strftime('%Y-%m-%d %H:%M')}{Colors.ENDC}")
    print(f"  Source: {workout.source}")

    if workout.duration_minutes:
        hours = int(workout.duration_minutes // 60)
        mins = int(workout.duration_minutes % 60)
        duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        print(f"  Duration: {duration_str}")

    if workout.calories:
        print(f"  Calories: {workout.calories} kcal")

    if workout.avg_heart_rate:
        print(f"  Avg HR: {workout.avg_heart_rate} bpm")

    if workout.distance_miles:
        print(f"  Distance: {workout.distance_miles} mi")

    if workout.notes:
        # Truncate notes if too long
        notes_preview = workout.notes[:60] + "..." if len(workout.notes) > 60 else workout.notes
        print(f"  Notes: {notes_preview}")


def import_activity_metrics(file_path: Path, dry_run: bool = True) -> DailyActivityMetrics:
    """Import activity metrics from a HealthAutoExport file.

    Args:
        file_path: Path to HealthAutoExport JSON file (TOAD_Activity)
        dry_run: If True, only print what would be imported

    Returns:
        Parsed DailyActivityMetrics object

    Raises:
        ValueError: If file cannot be parsed
        FileNotFoundError: If file doesn't exist
    """
    parser = HealthAutoExportMetricsParser()

    try:
        metrics = parser.parse(file_path)
        print_metrics_summary(metrics, dry_run=dry_run)

        if not dry_run:
            # TODO: Implement Notion update logic here
            print(f"{Colors.WARNING}  → Notion update not yet implemented{Colors.ENDC}")

        return metrics

    except Exception as e:
        print(f"{Colors.FAIL}ERROR parsing {file_path}: {e}{Colors.ENDC}")
        raise


def import_workouts(file_path: Path, dry_run: bool = True) -> List[WorkoutData]:
    """Import workouts from a HealthAutoExport file.

    Args:
        file_path: Path to HealthAutoExport JSON file (TOAD_workouts)
        dry_run: If True, only print what would be imported

    Returns:
        List of parsed WorkoutData objects

    Raises:
        ValueError: If file cannot be parsed
        FileNotFoundError: If file doesn't exist
    """
    parser = HealthAutoExportParser()

    try:
        workouts = parser.parse(file_path)
        print(f"\n{Colors.HEADER}Found {len(workouts)} workout(s) in {file_path.name}{Colors.ENDC}")

        for workout in workouts:
            print_workout_summary(workout, dry_run=dry_run)

            if not dry_run:
                # TODO: Implement Notion update logic here
                print(f"{Colors.WARNING}  → Notion update not yet implemented{Colors.ENDC}")

        return workouts

    except Exception as e:
        print(f"{Colors.FAIL}ERROR parsing {file_path}: {e}{Colors.ENDC}")
        raise


def main():
    """Main entry point for health data import CLI."""
    parser = argparse.ArgumentParser(
        description="Import health data from HealthAutoExport JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run: Preview activity metrics import
  python scripts/import_health_data.py --metrics TOAD_Activity/HealthAutoExport-2026-01-17.json --dry-run

  # Dry-run: Preview workouts import
  python scripts/import_health_data.py --workouts TOAD_workouts/HealthAutoExport-2026-01-17.json --dry-run

  # Import activity metrics to Notion (when implemented)
  python scripts/import_health_data.py --metrics TOAD_Activity/HealthAutoExport-2026-01-17.json

  # Import all files in a directory
  python scripts/import_health_data.py --metrics-dir TOAD_Activity/ --dry-run
        """
    )

    parser.add_argument(
        '--metrics',
        type=Path,
        help='Path to HealthAutoExport activity metrics JSON file (TOAD_Activity)'
    )

    parser.add_argument(
        '--metrics-dir',
        type=Path,
        help='Directory containing multiple HealthAutoExport activity metrics files'
    )

    parser.add_argument(
        '--workouts',
        type=Path,
        help='Path to HealthAutoExport workouts JSON file (TOAD_workouts)'
    )

    parser.add_argument(
        '--workouts-dir',
        type=Path,
        help='Directory containing multiple HealthAutoExport workout files'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Preview what would be imported without touching Notion (default: True)'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually import to Notion (disables dry-run)'
    )

    args = parser.parse_args()

    # Determine dry-run mode
    dry_run = not args.execute

    # Validate arguments
    if not any([args.metrics, args.metrics_dir, args.workouts, args.workouts_dir]):
        parser.print_help()
        sys.exit(1)

    print(f"{Colors.HEADER}{Colors.BOLD}HealthAutoExport Data Import Tool{Colors.ENDC}")
    print(f"Mode: {Colors.WARNING}DRY RUN{Colors.ENDC}" if dry_run else f"Mode: {Colors.OKGREEN}EXECUTE{Colors.ENDC}")
    print("=" * 60)

    total_metrics = 0
    total_workouts = 0

    try:
        # Import activity metrics (single file)
        if args.metrics:
            import_activity_metrics(args.metrics, dry_run=dry_run)
            total_metrics += 1

        # Import activity metrics (directory)
        if args.metrics_dir:
            if not args.metrics_dir.is_dir():
                print(f"{Colors.FAIL}ERROR: {args.metrics_dir} is not a directory{Colors.ENDC}")
                sys.exit(1)

            json_files = sorted(args.metrics_dir.glob("HealthAutoExport-*.json"))
            print(f"\n{Colors.HEADER}Found {len(json_files)} file(s) in {args.metrics_dir}{Colors.ENDC}")

            for file_path in json_files:
                import_activity_metrics(file_path, dry_run=dry_run)
                total_metrics += 1

        # Import workouts (single file)
        if args.workouts:
            workouts = import_workouts(args.workouts, dry_run=dry_run)
            total_workouts += len(workouts)

        # Import workouts (directory)
        if args.workouts_dir:
            if not args.workouts_dir.is_dir():
                print(f"{Colors.FAIL}ERROR: {args.workouts_dir} is not a directory{Colors.ENDC}")
                sys.exit(1)

            json_files = sorted(args.workouts_dir.glob("HealthAutoExport-*.json"))
            print(f"\n{Colors.HEADER}Found {len(json_files)} file(s) in {args.workouts_dir}{Colors.ENDC}")

            for file_path in json_files:
                workouts = import_workouts(file_path, dry_run=dry_run)
                total_workouts += len(workouts)

        # Summary
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Activity metrics files processed: {total_metrics}")
        print(f"  Workouts processed: {total_workouts}")

        if dry_run:
            print(f"\n{Colors.WARNING}This was a DRY RUN. No data was imported to Notion.{Colors.ENDC}")
            print(f"Use --execute flag to actually import the data.")
        else:
            print(f"\n{Colors.OKGREEN}Import complete!{Colors.ENDC}")

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Import cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}FATAL ERROR: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
