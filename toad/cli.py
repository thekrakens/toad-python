#!/usr/bin/env python3
"""
TOAD CLI - Simplified command-line interface for TOAD productivity system.
"""

import argparse
import sys
from datetime import datetime, date, timedelta
import logging

from toad.notion_client import TOADNotionClient
from toad.productivity.task_relations import TaskRelationsManager
from toad.productivity.data_extractor import TaskDataExtractor, TimeEntryExtractor
from toad.sync_cache import get_sync_cache
from toad.health.sync_orchestrator import HealthSyncOrchestrator
from toad.daemon.manager import DaemonManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Date parsing utilities
def parse_date_flexible(date_str: str) -> date:
    """
    Parse a date string in flexible formats.
    
    Supported formats:
    - YYYY-MM-DD (2025-10-12)
    - MM-DD-YY (10-12-25)
    - MM/DD/YY (10/12/25)
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed date object
        
    Raises:
        ValueError: If date format is invalid
    """
    # Try YYYY-MM-DD format first
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        pass
    
    # Try MM-DD-YY format
    try:
        return datetime.strptime(date_str, '%m-%d-%y').date()
    except ValueError:
        pass
    
    # Try MM/DD/YY format
    try:
        return datetime.strptime(date_str, '%m/%d/%y').date()
    except ValueError:
        pass
    
    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD, MM-DD-YY, or MM/DD/YY")

def parse_date_range(date_args: list) -> list:
    """
    Parse date arguments into a list of dates.
    
    Args:
        date_args: List of date strings (0, 1, or 2 elements)
        
    Returns:
        List of date objects
        
    Raises:
        ValueError: If date format is invalid
    """
    if not date_args:
        # No dates provided, use today
        return [date.today()]
    
    if len(date_args) == 1:
        # Single date
        return [parse_date_flexible(date_args[0])]
    
    if len(date_args) == 2:
        # Date range
        start_date = parse_date_flexible(date_args[0])
        end_date = parse_date_flexible(date_args[1])
        
        if end_date < start_date:
            raise ValueError(f"End date {end_date} is before start date {start_date}")
        
        # Generate list of dates in range
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        return date_list
    
    raise ValueError("Too many date arguments. Provide either 1 date or 2 dates (start and end)")

def cmd_sync_health(args):
    """
    Health data sync command.
    Syncs workouts and activity metrics from HealthAutoExport.
    """
    print("🐸 TOAD - Health Data Sync")

    # Determine dry-run mode
    dry_run = args.dry_run
    if dry_run:
        print("Mode: DRY RUN (no Notion updates)")
    else:
        print("Mode: EXECUTE (will update Notion)")

    try:
        # Determine date range
        if args.full:
            # Full sync: last 30 days
            print("Full sync: last 30 days")
            dates = []
            current_date = date.today()
            for i in range(30):
                dates.append(current_date - timedelta(days=i))
            dates.reverse()
        elif args.dates:
            # Date range provided
            dates = parse_date_range(args.dates)
            if len(dates) == 1:
                print(f"Syncing for {dates[0]}")
            else:
                print(f"Syncing {dates[0]} to {dates[-1]} ({len(dates)} days)")
        else:
            # Default: today only
            dates = [date.today()]
            print(f"Syncing for {dates[0]} (today)")

        # Initialize orchestrator
        orchestrator = HealthSyncOrchestrator(dry_run=dry_run)

        # Sync date range
        start_date = dates[0]
        end_date = dates[-1]
        summary = orchestrator.sync_date_range(start_date, end_date)

        # Display summary
        print(f"\nHealth sync complete!")
        print(f"  Activity metrics processed: {summary['metrics_processed']}")
        print(f"  HealthAutoExport workouts: {summary['workouts_processed']}")
        print(f"  Gymaholic workouts: {summary['gymaholic_workouts_processed']}")

        if summary['errors']:
            print(f"\nWARNING: {len(summary['errors'])} errors encountered:")
            for error in summary['errors'][:5]:
                print(f"  • {error}")
            if len(summary['errors']) > 5:
                print(f"  ... and {len(summary['errors']) - 5} more")

        if dry_run:
            print(f"\nThis was a DRY RUN. No data was updated in Notion.")

    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Health sync failed: {e}")
        print(f"ERROR: Health sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_sync_productivity(args):
    """
    Productivity sync command with 3 modes:
    1. Default (incremental): today only
    2. Date sync: specific date or date range
    3. Full sync: last 30 days
    """
    print("🐸 TOAD - Productivity Data Sync")

    # Determine dry-run mode
    dry_run = args.dry_run
    if dry_run:
        print("Mode: DRY RUN (no Notion updates)")
    else:
        print("Mode: EXECUTE (will update Notion)")
    
    # Initialize components
    if not dry_run:
        notion_client = TOADNotionClient()
        sync_cache = get_sync_cache()
    else:
        notion_client = None
        sync_cache = None
        print("WARNING: Dry-run for productivity sync not fully implemented yet")
        print("    Will still perform read operations but skip Notion updates")
        # TODO: Implement full dry-run support for productivity
        return

    # Handle --clear-cache flag
    if args.clear_cache:
        print("Clearing sync cache...")
        sync_cache.clear_all()
        print("Cache cleared successfully")
        return
    
    try:
        # Determine sync mode
        if args.full:
            # MODE 3: Full Sync
            print("Mode: Full Sync (last 30 days)")
            dates = []
            current_date = date.today()
            for i in range(30):
                dates.append(current_date - timedelta(days=i))
            dates.reverse()
            use_cache = False
            print(f"Syncing {len(dates)} days")
        elif args.dates:
            # MODE 2: Date Sync
            dates = parse_date_range(args.dates)
            use_cache = True
            if len(dates) == 1:
                print(f"Mode: Date Sync")
                print(f"Syncing for {dates[0]}")
            else:
                print(f"Mode: Date Range Sync")
                print(f"Syncing {dates[0]} to {dates[-1]} ({len(dates)} days)")
        else:
            # MODE 1: Default Incremental Sync (today only)
            dates = [date.today()]
            use_cache = True
            print(f"Mode: Incremental Sync (today only)")
            print(f"Syncing for {dates[0]}")
        
        # Check cache for last sync times
        last_task_sync = sync_cache.get_last_sync_time('tasks')
        last_entry_sync = sync_cache.get_last_sync_time('time_entries')
        
        if use_cache and last_task_sync and last_entry_sync:
            print(f"Last sync: tasks={last_task_sync.strftime('%Y-%m-%d %H:%M:%S')}, entries={last_entry_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Fetching only modified data...")
        else:
            print(f"� Fetching all data (no cache or full sync)...")
        
        # Fetch data (with cache if available)
        task_extractor = TaskDataExtractor(notion_client)
        time_entry_extractor = TimeEntryExtractor(notion_client)
        
        if use_cache and not args.full:
            # Use cache timestamps for incremental fetch
            tasks_df = task_extractor.extract_tasks_to_dataframe(
                modified_since=last_task_sync
            )
            time_entries_df = time_entry_extractor.extract_time_entries_to_dataframe(
                modified_since=last_entry_sync
            )
        else:
            # Full fetch (ignore cache)
            tasks_df = task_extractor.extract_tasks_to_dataframe()
            time_entries_df = time_entry_extractor.extract_time_entries_to_dataframe()
        
        print(f"Loaded {len(tasks_df)} tasks and {len(time_entries_df)} time entries")
        
        # Process task relations for each date
        relations_manager = TaskRelationsManager(notion_client)

        total_relations = 0
        errors = []

        # OPTIMIZATION: For single date sync (not today), use filtered query
        if len(dates) == 1 and args.dates:  # Specific date provided, not today's incremental
            print(f"Using optimized filtered query for {dates[0]}...")
            result = relations_manager.process_daily_task_relations(dates[0])

            if "error" in result:
                error_msg = f"{dates[0]}: {result['error']}"
                print(f"  ERROR: {error_msg}")
                errors.append(error_msg)
            else:
                task_count = sum(
                    result[rel_type]['task_count']
                    for rel_type in ['planned', 'active', 'worked', 'done', 'backlog', 'archived']
                    if result[rel_type]['success']
                )
                total_relations += task_count
                print(f"  {dates[0]}: {task_count} task relations updated")
        else:
            # Use pre-loaded data for batch processing or incremental sync
            for target_date in dates:
                result = relations_manager.process_daily_task_relations_with_data(
                    target_date, tasks_df, time_entries_df
                )

                if "error" in result:
                    error_msg = f"{target_date}: {result['error']}"
                    print(f"  ERROR: {error_msg}")
                    errors.append(error_msg)
                else:
                    # Count total tasks across all relation types
                    task_count = sum(
                        result[rel_type]['task_count']
                        for rel_type in ['planned', 'active', 'worked', 'done', 'backlog', 'archived']
                        if result[rel_type]['success']
                    )
                    total_relations += task_count
                    print(f"  {target_date}: {task_count} task relations updated")
        
        # Update cache timestamps
        if not args.full and errors == []:
            # Only update cache if no errors occurred
            sync_cache.update_last_sync_time('tasks')
            sync_cache.update_last_sync_time('time_entries')
            print(f"Cache updated")
        elif args.full:
            # Reset cache for full sync
            sync_cache.update_last_sync_time('tasks')
            sync_cache.update_last_sync_time('time_entries')
            print(f"Cache reset")
        
        # Display summary
        print(f"\nSync complete!")
        print(f"  Dates processed: {len(dates) - len(errors)}/{len(dates)}")
        print(f"  Total relations updated: {total_relations}")
        
        if errors:
            print(f"\nWARNING: {len(errors)} errors encountered:")
            for error in errors[:5]:
                print(f"  • {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")
        
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        print(f"ERROR: Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_daemon_start(args):
    """Start the TOAD daemon."""
    print("TOAD Daemon - Start")

    manager = DaemonManager()
    result = manager.start()

    if result["success"]:
        print(f"✓ {result['message']}")
        print(f"  Log file: {manager.log_file}")
    else:
        print(f"ERROR: {result['message']}")
        sys.exit(1)


def cmd_daemon_stop(args):
    """Stop the TOAD daemon."""
    print("TOAD Daemon - Stop")

    manager = DaemonManager()
    result = manager.stop()

    if result["success"]:
        print(f"✓ {result['message']}")
    else:
        print(f"ERROR: {result['message']}")
        sys.exit(1)


def cmd_daemon_restart(args):
    """Restart the TOAD daemon."""
    print("TOAD Daemon - Restart")

    manager = DaemonManager()
    result = manager.restart()

    if result["success"]:
        print(f"✓ {result['message']}")
        print(f"  Log file: {manager.log_file}")
    else:
        print(f"ERROR: {result['message']}")
        sys.exit(1)


def cmd_daemon_status(args):
    """Show daemon status."""
    print("TOAD Daemon - Status")

    manager = DaemonManager()
    status = manager.status()

    if status["running"]:
        print(f"✓ Daemon is RUNNING")
        print(f"  PID: {status['pid']}")
        if status["uptime"]:
            print(f"  Uptime: {status['uptime']}")
    else:
        print("  Daemon is STOPPED")

    print(f"  PID file: {status['pid_file']}")
    print(f"  Log file: {status['log_file']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='🐸 TOAD Analytics CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync productivity for today
  toad sync productivity

  # Sync health for today
  toad sync health

  # Sync specific date
  toad sync health 01-17-26

  # Sync date range
  toad sync health 01-10-26 01-17-26

  # Dry run (preview without updating Notion)
  toad sync health 01-17-26 --dry-run

  # Full sync (last 30 days)
  toad sync productivity --full
  toad sync health --full

  # Clear cache (productivity only)
  toad sync productivity --clear-cache

Performance Targets:
  - Incremental sync: 2-5 seconds
  - Date sync: 5-10 seconds per date
  - Full sync: 20-30 seconds
        """
    )

    # Subparsers for different modules
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync data to Notion')
    module_subparsers = sync_parser.add_subparsers(dest='module', help='Module to sync')

    # Productivity module
    productivity_parser = module_subparsers.add_parser('productivity', help='Sync productivity data (tasks, time entries)')
    productivity_parser.add_argument(
        'dates',
        nargs='*',
        help='Date(s) to sync. Formats: YYYY-MM-DD, MM-DD-YY, MM/DD/YY. Defaults to today.'
    )
    productivity_parser.add_argument('--full', action='store_true', help='Full sync: last 30 days')
    productivity_parser.add_argument('--clear-cache', action='store_true', help='Clear sync cache and exit')
    productivity_parser.add_argument('--dry-run', action='store_true', help='Preview without updating Notion')

    # Health module
    health_parser = module_subparsers.add_parser('health', help='Sync health data (workouts, metrics)')
    health_parser.add_argument(
        'dates',
        nargs='*',
        help='Date(s) to sync. Formats: YYYY-MM-DD, MM-DD-YY, MM/DD/YY. Defaults to today.'
    )
    health_parser.add_argument('--full', action='store_true', help='Full sync: last 30 days')
    health_parser.add_argument('--dry-run', action='store_true', help='Preview without updating Notion')

    # All modules (future)
    all_parser = module_subparsers.add_parser('all', help='Sync all modules')
    all_parser.add_argument(
        'dates',
        nargs='*',
        help='Date(s) to sync. Defaults to today.'
    )
    all_parser.add_argument('--full', action='store_true', help='Full sync: last 30 days')
    all_parser.add_argument('--dry-run', action='store_true', help='Preview without updating Notion')

    # Daemon command
    daemon_parser = subparsers.add_parser('daemon', help='Manage TOAD daemon')
    daemon_subparsers = daemon_parser.add_subparsers(dest='action', help='Daemon action')

    # Daemon start
    daemon_start_parser = daemon_subparsers.add_parser('start', help='Start the daemon')

    # Daemon stop
    daemon_stop_parser = daemon_subparsers.add_parser('stop', help='Stop the daemon')

    # Daemon restart
    daemon_restart_parser = daemon_subparsers.add_parser('restart', help='Restart the daemon')

    # Daemon status
    daemon_status_parser = daemon_subparsers.add_parser('status', help='Show daemon status')

    # Parse arguments
    args = parser.parse_args()

    # Validate command
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle commands
    if args.command == 'sync':
        # Validate module
        if not args.module:
            sync_parser.print_help()
            sys.exit(1)

        # Execute appropriate sync command
        if args.module == 'productivity':
            cmd_sync_productivity(args)
        elif args.module == 'health':
            cmd_sync_health(args)
        elif args.module == 'all':
            # TODO: Implement all modules sync
            print("WARNING: Sync all modules not yet implemented")
            print("    Use: toad sync productivity or toad sync health")
            sys.exit(1)
        else:
            print(f"ERROR: Unknown module: {args.module}")
            sync_parser.print_help()
            sys.exit(1)

    elif args.command == 'daemon':
        # Validate action
        if not args.action:
            daemon_parser.print_help()
            sys.exit(1)

        # Execute daemon command
        if args.action == 'start':
            cmd_daemon_start(args)
        elif args.action == 'stop':
            cmd_daemon_stop(args)
        elif args.action == 'restart':
            cmd_daemon_restart(args)
        elif args.action == 'status':
            cmd_daemon_status(args)
        else:
            print(f"ERROR: Unknown daemon action: {args.action}")
            daemon_parser.print_help()
            sys.exit(1)

    else:
        print(f"ERROR: Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
