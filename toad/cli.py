#!/usr/bin/env python3
"""
TOAD CLI - Command-line interface for TOAD productivity system.
"""

import argparse
import sys
from datetime import datetime, date
import logging

from toad.notion_client import TOADNotionClient
from toad.productivity.task_relations import TaskRelationsManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cmd_sync(args):
    """Sync tasks and daily productivity metrics for a given date."""
    print("🐸 TOAD - Syncing Tasks and Daily Productivity Metrics")
    
    # Parse target date (now required)
    try:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    except ValueError:
        print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD format.")
        sys.exit(1)
    
    print(f"📅 Processing data for {target_date}")
    
    try:
        # Initialize components
        notion_client = TOADNotionClient()
        relations_manager = TaskRelationsManager(notion_client)
        
        print("🔄 Processing task relations...")
        
        # Process task relations
        result = relations_manager.process_daily_task_relations(target_date)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        print(f"✅ Task relations processed successfully")
        print(f"📄 Daily metrics entry: {result['metrics_entry_id']}")
        
        # Display results
        for relation_type in ['planned', 'active', 'worked', 'done']:
            relation_result = result[relation_type]
            if relation_result['success']:
                print(f"  📋 {relation_type.title()}: {relation_result['task_count']} tasks")
            else:
                print(f"  ❌ {relation_type.title()}: ERROR - {relation_result['error']}")
        
        # TODO: Add other sync operations here (task metrics updates, etc.)
        
        print(f"\n🎉 Sync complete for {target_date}!")
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_status(args):
    """Show task relations status for a given date."""
    print("🐸 TOAD - Task Relations Status")
    
    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD format.")
            sys.exit(1)
    else:
        target_date = date.today()
    
    print(f"📅 Status for {target_date}")
    
    try:
        # Initialize components
        notion_client = TOADNotionClient()
        relations_manager = TaskRelationsManager(notion_client)
        
        # Get summary
        summary = relations_manager.get_relation_summary(target_date)
        
        if "error" in summary:
            print(f"❌ Error: {summary['error']}")
            sys.exit(1)
        
        print(f"\n📊 Task Relations Summary:")
        print(f"  📋 Planned: {summary['planned_count']} tasks")
        print(f"  🎯 Active:  {summary['active_count']} tasks")
        print(f"  ⏰ Worked:  {summary['worked_count']} tasks")
        print(f"  ✅ Done:    {summary['done_count']} tasks")
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        print(f"❌ Status check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='🐸 TOAD Productivity Analytics CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync tasks and daily productivity metrics')
    sync_parser.add_argument('date', help='Date to sync (YYYY-MM-DD format required)')
    sync_parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making changes')
    sync_parser.set_defaults(func=cmd_sync)
    
    # Status command  
    status_parser = subparsers.add_parser('status', help='Show task relations status')
    status_parser.add_argument('date', nargs='?', help='Date to check status for (YYYY-MM-DD). Defaults to today.')
    status_parser.set_defaults(func=cmd_status)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    args.func(args)

if __name__ == '__main__':
    main()
