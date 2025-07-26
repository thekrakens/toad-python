"""
Command-line interface for TOAD productivity system.
Handles metrics synchronization and visualization commands.
"""

import argparse
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from toad.notion_client import TOADNotionClient
from toad.config import Config
from toad.productivity.data_extractor import TaskDataExtractor, TimeBlockExtractor, TimeEntryExtractor
from toad.productivity.analytics import TimeBlockAnalytics
from toad.productivity.daily_metrics import DailyMetricsCalculator, DailyMetrics
from toad.plants.tracker import PlantTracker
from toad.plants.notion_database import PlantNotionDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_toad_system():
    """Initialize TOAD system components."""
    if not Config.validate_notion_config():
        print("❌ Missing Notion configuration. Please check .env file.")
        sys.exit(1)
    
    client = TOADNotionClient()
    task_extractor = TaskDataExtractor(client)
    time_block_extractor = TimeBlockExtractor(client)
    analytics = TimeBlockAnalytics()
    
    return client, task_extractor, time_block_extractor, analytics

def cmd_sync_daily(args):
    """Sync daily metrics and timeline."""
    print("🐸 TOAD - Syncing Daily Metrics")
    
    client, task_extractor, time_block_extractor, analytics = setup_toad_system()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    else:
        target_date = datetime.now(timezone.utc)
    
    print(f"📅 Processing metrics for {target_date.date()}")
    
    try:
        # Extract data
        print("📊 Extracting task data...")
        tasks_df = task_extractor.extract_tasks_to_dataframe()
        print(f"✅ Extracted {len(tasks_df)} tasks")
        
        # Extract time blocks if configured
        time_blocks_df = None
        if Config.validate_time_blocks_config():
            print("⏰ Extracting time block data...")
            time_blocks_df = time_block_extractor.extract_time_blocks_to_dataframe()
            print(f"✅ Extracted {len(time_blocks_df)} time blocks")
        else:
            print("⚠️  Time blocks database not configured, using task data only")
            import pandas as pd
            time_blocks_df = pd.DataFrame()
        
        # Calculate metrics
        print("🧮 Calculating daily metrics...")
        calculator = DailyMetricsCalculator(tasks_df, time_blocks_df)
        metrics = calculator.calculate_metrics_for_date(target_date)
        
        # Display key metrics
        print(f"\n📊 Daily Metrics Summary for {target_date.date()}:")
        print(f"  🎯 Daily Productivity Score: {metrics.productivity_score}")
        print(f"  ✅ Task Completion Rate: {metrics.task_completion_rate_pct}%")
        print(f"  📅 Schedule Adherence: {metrics.schedule_adherence_pct}%") 
        print(f"  ⚡ Efficiency Score: {metrics.schedule_adherence_pct}") # Placeholder
        print(f"  ⏰ Work Hours Achieved: {metrics.effective_hours_worked}")
        
        print("\n🎉 Daily metrics sync complete!")
        
    except Exception as e:
        logger.error(f"Daily sync failed: {e}")
        print(f"❌ Sync failed: {e}")
        sys.exit(1)

def cmd_sync_timeline(args):
    """Generate and sync timeline visualization only."""
    print("🐸 TOAD - Generating Timeline Visualization")
    print("⚠️  This command is deprecated and will be removed in a future version.")

def cmd_create_database(args):
    """Create the Daily Productivity Metrics database."""
    print("🐸 TOAD - Creating Daily Productivity Metrics Database")
    print("⚠️  This command is deprecated and will be removed in a future version.")

def cmd_test_analytics(args):
    """Test analytics functionality."""
    print("🐸 TOAD - Testing Analytics")
    
    client, task_extractor, time_block_extractor, analytics = setup_toad_system()
    
    try:
        # Extract data
        print("📊 Extracting data...")
        tasks_df = task_extractor.extract_tasks_to_dataframe()
        print(f"✅ Extracted {len(tasks_df)} tasks")
        
        if Config.validate_time_blocks_config():
            time_blocks_df = time_block_extractor.extract_time_blocks_to_dataframe()
            print(f"✅ Extracted {len(time_blocks_df)} time blocks")
        else:
            print("⚠️  Using sample time block data for testing")
            import pandas as pd
            time_blocks_df = pd.DataFrame()
        
        # Calculate metrics
        print("🧮 Testing metrics calculation...")
        calculator = DailyMetricsCalculator(tasks_df, time_blocks_df)
        target_date = datetime.now(timezone.utc)
        metrics = calculator.calculate_metrics_for_date(target_date)
        
        print("✅ Metrics calculation successful!")
        print(f"  🎯 Daily Productivity Score: {metrics.productivity_score}")
        print(f"  ✅ Task Completion Rate: {metrics.task_completion_rate_pct}%")
        print(f"  📅 Schedule Adherence: {metrics.schedule_adherence_pct}%")
        print(f"  ⏰ Work Hours Achieved: {metrics.effective_hours_worked}")
        
        print("🎉 Analytics test complete!")
        
    except Exception as e:
        logger.error(f"Analytics test failed: {e}")
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_plants_status(args):
    """Show plant watering status from Notion."""
    print("🐸 TOAD - Plant Watering Status")
    
    try:
        if not Config.validate_notion_config():
            print("❌ Missing Notion configuration. Please check .env file.")
            sys.exit(1)
        
        client = TOADNotionClient()
        notion_db = PlantNotionDatabase(client.client)
        
        # Show quick status
        stats = notion_db.get_dashboard_stats()
        
        print(f"\n📊 Quick Status:")
        print(f"Total Plants: {stats.get('total_plants', 0)}")
        print(f"Need Watering: {stats.get('needs_watering', 0)}")
        print(f"Watered Today: {stats.get('watered_today', 0)}")
        if stats.get('average_moisture'):
            print(f"Average Moisture: {stats['average_moisture']}/9")
        
        if stats.get('needs_watering', 0) > 0:
            print(f"\n💧 Plants needing water:")
            plants_needing_water = notion_db.get_plants_needing_water()
            
            for plant in plants_needing_water[:5]:  # Show top 5
                urgency_icon = "🚨" if "Urgent" in plant['urgency'] else "⚠️" if "Soon" in plant['urgency'] else "💧"
                moisture_str = str(plant['moisture']) if plant['moisture'] else 'N/A'
                days_str = str(plant['days_since_watered']) if plant['days_since_watered'] else 'N/A'
                print(f"  {urgency_icon} {plant['name']} (moisture: {moisture_str}, {days_str} days ago)")
            
            if len(plants_needing_water) > 5:
                print(f"  ... and {len(plants_needing_water) - 5} more")
        
        print(f"\n💡 View full details in your Notion Plants database")
        
    except Exception as e:
        print(f"❌ Plant status failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_plants_import(args):
    """Import plants from checklist to Notion."""
    print("🐸 TOAD - Import Plant Checklist to Notion")
    
    try:
        if not Config.validate_notion_config():
            print("❌ Missing Notion configuration. Please check .env file.")
            sys.exit(1)
        
        client = TOADNotionClient()
        notion_db = PlantNotionDatabase(client.client)
        
        # Read checklist from file or stdin
        if args.file:
            with open(args.file, 'r') as f:
                checklist_text = f.read()
        else:
            print("Enter your plant checklist (Ctrl+D when done):")
            checklist_text = sys.stdin.read()
        
        result = notion_db.import_from_checklist(checklist_text)
        
        print(f"✅ {result['message']}")
        print(f"Database ID: {result['database_id']}")
        
        # Show quick status after import
        stats = notion_db.get_dashboard_stats()
        if stats.get('needs_watering', 0) > 0:
            print(f"\n💧 {stats['needs_watering']} plants need watering")
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_plants_water(args):
    """Record watering for a plant."""
    print("🐸 TOAD - Record Plant Watering")
    
    try:
        tracker = PlantTracker()
        
        success = tracker.water_plant(
            name=args.name,
            amount=args.amount,
            moisture_before=args.moisture_before,
            moisture_after=args.moisture_after,
            notes=args.notes
        )
        
        if success:
            print(f"✅ Recorded watering for {args.name}")
            
            # Show updated plant status
            plant_list = tracker.list_plants()
            plant_info = next((p for p in plant_list if p['name'] == args.name), None)
            if plant_info:
                next_watering = plant_info['next_watering']
                if next_watering:
                    print(f"💡 Next watering estimated: {next_watering}")
        else:
            print(f"❌ Plant '{args.name}' not found")
            
    except Exception as e:
        print(f"❌ Recording watering failed: {e}")
        sys.exit(1)

def cmd_plants_add(args):
    """Add a new plant."""
    print("🐸 TOAD - Add New Plant")
    
    try:
        tracker = PlantTracker()
        
        plant = tracker.add_plant(
            name=args.name,
            species=args.species,
            location=args.location,
            watering_frequency_days=args.frequency,
            current_moisture=args.moisture
        )
        
        print(f"✅ Added plant: {plant.name}")
        if plant.species:
            print(f"Species: {plant.species}")
        if plant.location:
            print(f"Location: {plant.location}")
        print(f"Watering frequency: {plant.watering_frequency_days} days")
        
    except Exception as e:
        print(f"❌ Adding plant failed: {e}")
        sys.exit(1)

def cmd_plants_list(args):
    """List all plants."""
    print("🐸 TOAD - Plant List")
    
    try:
        tracker = PlantTracker()
        plants = tracker.list_plants()
        
        if not plants:
            print("No plants in database. Use 'toad plants import' or 'toad plants add' to get started.")
            return
        
        from tabulate import tabulate
        
        table_data = []
        for plant in plants:
            moisture_str = str(plant['moisture']) if plant['moisture'] else 'N/A'
            days_since = plant['days_since_watered'] if plant['days_since_watered'] is not None else 'Never'
            next_water = plant['next_watering'].strftime('%m/%d') if plant['next_watering'] else 'TBD'
            
            table_data.append([
                plant['name'],
                plant['species'] or 'Unknown',
                moisture_str,
                days_since,
                next_water,
                plant['urgency'].upper()
            ])
        
        headers = ['Name', 'Species', 'Moisture', 'Days Since', 'Next Water', 'Urgency']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
    except Exception as e:
        print(f"❌ Listing plants failed: {e}")
        sys.exit(1)

def cmd_plants_create_database(args):
    """Create the Plants database in Notion."""
    print("🐸 TOAD - Creating Plants Database")
    
    try:
        if not Config.validate_notion_config():
            print("❌ Missing Notion configuration. Please check .env file.")
            sys.exit(1)
        
        client = TOADNotionClient()
        notion_db = PlantNotionDatabase(client.client)
        
        database_id = notion_db.create_plants_database()
        
        print(f"✅ Created Plants database")
        print(f"📊 Database ID: {database_id}")
        print(f"💡 Add this to your .env file: NOTION_PLANTS_DATABASE_ID={database_id}")
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_plants_create_tasks(args):
    """Create watering tasks for plants that need water."""
    print("🐸 TOAD - Creating Plant Watering Tasks")
    
    try:
        if not Config.validate_notion_config():
            print("❌ Missing Notion configuration. Please check .env file.")
            sys.exit(1)
        
        client = TOADNotionClient()
        notion_db = PlantNotionDatabase(client.client)
        
        # Determine target date
        if args.date:
            from datetime import date
            target_date = date.fromisoformat(args.date)
        else:
            from datetime import date
            target_date = date.today()
        
        print(f"📅 Creating watering tasks for {target_date}")
        
        # Create tasks
        created_count = notion_db.create_watering_tasks(target_date)
        
        if created_count > 0:
            print(f"✅ Created {created_count} watering tasks")
            print(f"💡 Check your tasks database for new watering tasks")
        else:
            print("🎉 No plants need watering today, or tasks already exist")
        
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_metrics_sync(args):
    """Calculate and sync daily metrics to Notion."""
    print("🐸 TOAD - Daily Metrics Sync")
    
    # Use hardcoded database ID for now
    METRICS_DATABASE_ID = "2352579666bd8017a464c1a7d32d35c4"
    
    try:
        # Initialize TOAD system
        client, task_extractor, time_block_extractor, analytics = setup_toad_system()
        
        # Determine target date
        if args.date:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        else:
            target_date = datetime.now(timezone.utc)
        
        print(f"📅 Processing metrics for {target_date.date()}")
        
        # Extract data
        print("📊 Extracting task data...")
        tasks_df = task_extractor.extract_tasks_to_dataframe()
        print(f"✅ Extracted {len(tasks_df)} tasks")
        
        # Extract time blocks if configured
        time_blocks_df = None
        if Config.validate_time_blocks_config():
            print("⏰ Extracting time block data...")
            time_blocks_df = time_block_extractor.extract_time_blocks_to_dataframe()
            print(f"✅ Extracted {len(time_blocks_df)} time blocks")
        else:
            print("⚠️  Time blocks database not configured, using task data only")
            import pandas as pd
            time_blocks_df = pd.DataFrame()
        
        # Extract time entries if configured
        time_entries_df = None
        if Config.validate_time_entries_config():
            print("⏰ Extracting time entry data...")
            time_entry_extractor = TimeEntryExtractor(client)
            time_entries_df = time_entry_extractor.extract_time_entries_to_dataframe()
            print(f"✅ Extracted {len(time_entries_df)} time entries")
        else:
            print("⚠️  Time entries database not configured, using task data only")
            import pandas as pd
            time_entries_df = pd.DataFrame()

        # Calculate metrics using our new calculator
        print("🧮 Calculating daily metrics...")
        calculator = DailyMetricsCalculator(tasks_df, time_blocks_df, time_entries_df)
        daily_metrics = calculator.calculate_metrics_for_date(target_date)
        
        # Display results
        print(f"\n📊 Daily Metrics for {target_date.date()}:")
        print(f"  📋 Planned Working Hours: {daily_metrics.planned_working_hours}")
        print(f"  ⏰ Effective Hours Worked: {daily_metrics.effective_hours_worked}")
        print(f"  📈 Time on Planned Tasks: {daily_metrics.time_on_planned_tasks}h")
        print(f"  📉 Time on Unplanned Tasks: {daily_metrics.time_on_unplanned_tasks}h")
        print(f"  📊 Planned vs Unplanned: {daily_metrics.planned_vs_unplanned_pct}%")
        print(f"  📋 Tasks Planned Count: {daily_metrics.tasks_planned_count}")
        print(f"  🎯 Tasks Active Count: {daily_metrics.tasks_active_count}")
        print(f"  🆕 Unplanned Tasks Created: {daily_metrics.unplanned_tasks_created}")
        print(f"  🧊 Cold Tasks Count: {daily_metrics.cold_tasks_count}")
        print(f"  🎯 Productivity Score: {daily_metrics.productivity_score}")
        print(f"  📅 Schedule Adherence: {daily_metrics.schedule_adherence_pct}%")
        print(f"  ✅ Task Completion Rate: {daily_metrics.task_completion_rate_pct}%")
        print(f"  🔄 Context Switches: {daily_metrics.context_switches}")
        
        # Sync to Notion unless dry run
        if not args.dry_run:
            print(f"\n☁️  Syncing to Notion database...")
            database_id = args.database_id or METRICS_DATABASE_ID
            
            # Use upsert to create or update existing entry
            result = calculator.upsert_metrics_to_notion(daily_metrics, database_id, client)
            
            action_msg = "updated" if result["action"] == "updated" else "synced"
            print(f"✅ Metrics {action_msg} successfully!")
            print(f"📄 Notion page: {result['url']}")
            
            if result["action"] == "updated":
                print(f"🔄 Updated existing entry for {target_date.date()}")
            else:
                print(f"🆕 Created new entry for {target_date.date()}")
        else:
            print(f"\n🏃 Dry run mode - metrics calculated but not synced")
        
        print(f"\n🎉 Daily metrics sync complete!")
        
    except Exception as e:
        logger.error(f"Metrics sync failed: {e}")
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_metrics_test(args):
    """Test metrics calculation without syncing."""
    print("🐸 TOAD - Metrics Calculation Test")
    
    try:
        # Initialize TOAD system
        client, task_extractor, time_block_extractor, analytics = setup_toad_system()
        
        # Determine target date
        if args.date:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        else:
            target_date = datetime.now(timezone.utc)
        
        print(f"📅 Testing metrics for {target_date.date()}")
        
        # Extract data
        print("📊 Extracting data...")
        tasks_df = task_extractor.extract_tasks_to_dataframe()
        print(f"✅ Extracted {len(tasks_df)} tasks")
        
        # Show sample task data structure
        if not tasks_df.empty:
            print(f"📋 Available task columns: {list(tasks_df.columns)}")
            
        # Extract time blocks if configured
        time_blocks_df = None
        if Config.validate_time_blocks_config():
            time_blocks_df = time_block_extractor.extract_time_blocks_to_dataframe()
            print(f"✅ Extracted {len(time_blocks_df)} time blocks")
            if not time_blocks_df.empty:
                print(f"⏰ Available time block columns: {list(time_blocks_df.columns)}")
        else:
            print("⚠️  Time blocks database not configured")
            import pandas as pd
            time_blocks_df = pd.DataFrame()
        
        # Test metrics calculation
        print("🧮 Testing metrics calculation...")
        calculator = DailyMetricsCalculator(tasks_df, time_blocks_df)
        daily_metrics = calculator.calculate_metrics_for_date(target_date)
        
        print("✅ Metrics calculation successful!")
        
        # Show detailed results
        print(f"\n📊 Complete Metrics Breakdown:")
        metrics_dict = {
            "Date": daily_metrics.date.date(),
            "Planned Working Hours": daily_metrics.planned_working_hours,
            "Effective Hours Worked": daily_metrics.effective_hours_worked,
            "Time on Planned Tasks": daily_metrics.time_on_planned_tasks,
            "Time on Unplanned Tasks": daily_metrics.time_on_unplanned_tasks,
            "Planned vs Unplanned %": daily_metrics.planned_vs_unplanned_pct,
            "Tasks Planned Count": daily_metrics.tasks_planned_count,
            "Tasks Active Count": daily_metrics.tasks_active_count,
            "Unplanned Tasks Created": daily_metrics.unplanned_tasks_created,
            "Cold Tasks Count": daily_metrics.cold_tasks_count,
            "Productivity Score": daily_metrics.productivity_score,
            "Schedule Adherence %": daily_metrics.schedule_adherence_pct,
            "Task Completion Rate %": daily_metrics.task_completion_rate_pct,
            "Context Switches": daily_metrics.context_switches
        }
        
        for key, value in metrics_dict.items():
            print(f"  {key}: {value}")
        
        print(f"\n🎉 Metrics test complete!")
        
    except Exception as e:
        logger.error(f"Metrics test failed: {e}")
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_web_dashboard(args):
    """Start the web dashboard server."""
    print("🐸 TOAD - Starting Web Dashboard")
    
    try:
        if not Config.validate_notion_config():
            print("❌ Missing Notion configuration. Please check .env file.")
            sys.exit(1)
        
        # Import Flask app
        from toad.web.app import app
        
        host = args.host or '0.0.0.0'
        port = args.port or 5000
        debug = args.debug or False
        
        print(f"🌐 Starting TOAD web dashboard...")
        print(f"📡 Server: http://{host}:{port}")
        print(f"🔗 Timeline URL: http://{host}:{port}/dashboard/timeline/2025-07-19")
        print(f"📊 Weekly URL: http://{host}:{port}/dashboard/weekly/2025-W29")
        print()
        print("💡 For Notion embedding:")
        print(f"   Copy URL: http://{host}:{port}/dashboard/timeline/{{DATE}}")
        print("   Use /embed command in Notion to embed the dashboard")
        print()
        print("🛑 Press Ctrl+C to stop the server")
        print()
        
        # Start the Flask development server
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped")
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='🐸 TOAD Productivity Analytics CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync daily metrics
    sync_daily = subparsers.add_parser('sync-daily', help='Sync daily metrics and timeline')
    sync_daily.add_argument('--date', help='Date to process (YYYY-MM-DD), defaults to today')
    sync_daily.add_argument('--local-only', action='store_true', help='Calculate metrics locally only')
    sync_daily.add_argument('--save-local', action='store_true', help='Save timeline image locally')
    sync_daily.set_defaults(func=cmd_sync_daily)
    
    # Generate timeline only
    timeline = subparsers.add_parser('timeline', help='Generate timeline visualization')
    timeline.add_argument('--date', help='Date to visualize (YYYY-MM-DD), defaults to today')
    timeline.add_argument('--output', help='Output file path')
    timeline.set_defaults(func=cmd_sync_timeline)
    
    # Create database
    create_db = subparsers.add_parser('create-database', help='Create Daily Productivity Metrics database')
    create_db.set_defaults(func=cmd_create_database)
    
    # Test analytics
    test = subparsers.add_parser('test', help='Test analytics functionality')
    test.add_argument('--with-viz', action='store_true', help='Include visualization test')
    test.set_defaults(func=cmd_test_analytics)
    
    # Plant tracking commands
    plants = subparsers.add_parser('plants', help='Plant watering management')
    plants_sub = plants.add_subparsers(dest='plants_command', help='Plant commands')
    
    # Plant status
    status = plants_sub.add_parser('status', help='Show plant watering status')
    status.add_argument('--report', action='store_true', help='Generate full report')
    status.set_defaults(func=cmd_plants_status)
    
    # Import from checklist
    import_cmd = plants_sub.add_parser('import', help='Import plants from checklist')
    import_cmd.add_argument('--file', help='File containing checklist (defaults to stdin)')
    import_cmd.set_defaults(func=cmd_plants_import)
    
    # Record watering
    water = plants_sub.add_parser('water', help='Record watering for a plant')
    water.add_argument('name', help='Plant name')
    water.add_argument('--amount', help='Amount watered (e.g., "2.5 jugs")')
    water.add_argument('--moisture-before', type=int, help='Moisture before watering (1-9)')
    water.add_argument('--moisture-after', type=int, help='Moisture after watering (1-9)')
    water.add_argument('--notes', help='Additional notes')
    water.set_defaults(func=cmd_plants_water)
    
    # Add new plant
    add = plants_sub.add_parser('add', help='Add a new plant')
    add.add_argument('name', help='Plant name')
    add.add_argument('--species', help='Plant species')
    add.add_argument('--location', help='Plant location')
    add.add_argument('--frequency', type=int, default=7, help='Watering frequency in days (default: 7)')
    add.add_argument('--moisture', type=int, help='Current moisture level (1-9)')
    add.set_defaults(func=cmd_plants_add)
    
    # List plants
    list_cmd = plants_sub.add_parser('list', help='List all plants')
    list_cmd.set_defaults(func=cmd_plants_list)
    
    # Create database
    create_db = plants_sub.add_parser('create-database', help='Create Plants database in Notion')
    create_db.set_defaults(func=cmd_plants_create_database)
    
    # Create daily tasks
    create_tasks = plants_sub.add_parser('create-tasks', help='Create watering tasks for today')
    create_tasks.add_argument('--date', help='Date to create tasks for (YYYY-MM-DD), defaults to today')
    create_tasks.set_defaults(func=cmd_plants_create_tasks)
    
    # Metrics sync commands
    metrics = subparsers.add_parser('metrics', help='Daily productivity metrics sync')
    metrics_sub = metrics.add_subparsers(dest='metrics_command', help='Metrics commands')
    
    # Sync metrics
    sync_metrics = metrics_sub.add_parser('sync', help='Calculate and sync daily metrics to Notion')
    sync_metrics.add_argument('--date', help='Date to sync (YYYY-MM-DD), defaults to today')
    sync_metrics.add_argument('--database-id', help='Override metrics database ID')
    sync_metrics.add_argument('--dry-run', action='store_true', help='Calculate metrics without syncing to Notion')
    sync_metrics.set_defaults(func=cmd_metrics_sync)
    
    # Test metrics calculation
    test_metrics = metrics_sub.add_parser('test', help='Test metrics calculation')
    test_metrics.add_argument('--date', help='Date to test (YYYY-MM-DD), defaults to today')
    test_metrics.set_defaults(func=cmd_metrics_test)
    
    # Web dashboard command
    web = subparsers.add_parser('web', help='Start web dashboard server')
    web.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    web.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    web.add_argument('--debug', action='store_true', help='Enable debug mode')
    web.set_defaults(func=cmd_web_dashboard)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle plants subcommands
    if args.command == 'plants':
        if not hasattr(args, 'plants_command') or not args.plants_command:
            plants.print_help()
            return
    
    # Handle metrics subcommands
    if args.command == 'metrics':
        if not hasattr(args, 'metrics_command') or not args.metrics_command:
            metrics.print_help()
            return
    
    # Execute command
    args.func(args)

if __name__ == '__main__':
    main()
