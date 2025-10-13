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

def cmd_sync(args):
    """
    Simplified sync command with 3 modes:
    1. Default (incremental): toad sync
    2. Date sync: toad sync 10-12-25 or toad sync 10-10-25 10-12-25
    3. Full sync: toad sync --full
    """
    print("🐸 TOAD - Productivity Data Sync")
    
    # Initialize components
    notion_client = TOADNotionClient()
    sync_cache = get_sync_cache()
    
    # Handle --clear-cache flag
    if args.clear_cache:
        print("🗑️  Clearing sync cache...")
        sync_cache.clear_all()
        print("✅ Cache cleared successfully")
        return
    
    try:
        # Determine sync mode
        if args.full:
            # MODE 3: Full Sync
            print("🔄 Mode: Full Sync (last 30 days)")
            dates = []
            current_date = date.today()
            for i in range(30):
                dates.append(current_date - timedelta(days=i))
            dates.reverse()
            use_cache = False
            print(f"📅 Syncing {len(dates)} days")
        elif args.dates:
            # MODE 2: Date Sync
            dates = parse_date_range(args.dates)
            use_cache = True
            if len(dates) == 1:
                print(f"🔄 Mode: Date Sync")
                print(f"📅 Syncing for {dates[0]}")
            else:
                print(f"🔄 Mode: Date Range Sync")
                print(f"📅 Syncing {dates[0]} to {dates[-1]} ({len(dates)} days)")
        else:
            # MODE 1: Default Incremental Sync (today only)
            dates = [date.today()]
            use_cache = True
            print(f"🔄 Mode: Incremental Sync (today only)")
            print(f"📅 Syncing for {dates[0]}")
        
        # Check cache for last sync times
        last_task_sync = sync_cache.get_last_sync_time('tasks')
        last_entry_sync = sync_cache.get_last_sync_time('time_entries')
        
        if use_cache and last_task_sync and last_entry_sync:
            print(f"⏱️  Last sync: tasks={last_task_sync.strftime('%Y-%m-%d %H:%M:%S')}, entries={last_entry_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📥 Fetching only modified data...")
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
        
        print(f"✅ Loaded {len(tasks_df)} tasks and {len(time_entries_df)} time entries")
        
        # Process task relations for each date
        relations_manager = TaskRelationsManager(notion_client)
        
        total_relations = 0
        errors = []
        
        for target_date in dates:
            result = relations_manager.process_daily_task_relations_with_data(
                target_date, tasks_df, time_entries_df
            )
            
            if "error" in result:
                error_msg = f"{target_date}: {result['error']}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)
            else:
                # Count total tasks across all relation types
                task_count = sum(
                    result[rel_type]['task_count'] 
                    for rel_type in ['planned', 'active', 'worked', 'done']
                    if result[rel_type]['success']
                )
                total_relations += task_count
                print(f"  ✅ {target_date}: {task_count} task relations updated")
        
        # Update cache timestamps
        if not args.full and errors == []:
            # Only update cache if no errors occurred
            sync_cache.update_last_sync_time('tasks')
            sync_cache.update_last_sync_time('time_entries')
            print(f"💾 Cache updated")
        elif args.full:
            # Reset cache for full sync
            sync_cache.update_last_sync_time('tasks')
            sync_cache.update_last_sync_time('time_entries')
            print(f"💾 Cache reset")
        
        # Display summary
        print(f"\n🎉 Sync complete!")
        print(f"  📋 Dates processed: {len(dates) - len(errors)}/{len(dates)}")
        print(f"  📊 Total relations updated: {total_relations}")
        
        if errors:
            print(f"\n⚠️  {len(errors)} errors encountered:")
            for error in errors[:5]:
                print(f"  • {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")
        
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='🐸 TOAD Productivity Analytics CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Incremental sync (today only, uses cache)
  toad sync
  
  # Sync specific date
  toad sync 10-12-25
  
  # Sync date range
  toad sync 10-10-25 10-12-25
  
  # Full sync (last 30 days, ignores cache)
  toad sync --full
  
  # Clear cache
  toad sync --clear-cache

Performance Targets:
  - Incremental sync: 2-5 seconds
  - Date sync: 5-10 seconds per date
  - Full sync: 20-30 seconds
        """
    )
    
    # Main sync command (now the only command)
    parser.add_argument(
        'command',
        nargs='?',
        default='sync',
        help='Command to run (currently only "sync" is supported)'
    )
    parser.add_argument(
        'dates', 
        nargs='*', 
        help='Date(s) to sync. Formats: YYYY-MM-DD, MM-DD-YY, MM/DD/YY. '
             'Provide 1 date for single day, or 2 dates for range. Defaults to today (incremental).'
    )
    parser.add_argument(
        '--full', 
        action='store_true', 
        help='Full sync mode: sync last 30 days and reset cache'
    )
    parser.add_argument(
        '--clear-cache', 
        action='store_true', 
        help='Clear sync cache and exit'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate command
    if args.command and args.command != 'sync':
        print(f"❌ Unknown command: {args.command}")
        print("Available command: sync")
        parser.print_help()
        sys.exit(1)
    
    # Execute sync command
    cmd_sync(args)

if __name__ == '__main__':
    main()
