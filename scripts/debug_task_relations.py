#!/usr/bin/env python3
"""
Debug script to investigate task relation issues.

Usage:
    python scripts/debug_task_relations.py 2026-01-16
"""

import sys
from pathlib import Path
from datetime import date, datetime
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from toad.notion_client import TOADNotionClient
from toad.productivity.task_relations import TaskRelationsManager


def debug_date(target_date_str: str):
    """Debug task relations for a specific date."""

    # Parse target date
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

    print("=" * 80)
    print(f"DEBUGGING TASK RELATIONS FOR: {target_date}")
    print("=" * 80)
    print()

    # Initialize
    client = TOADNotionClient()
    manager = TaskRelationsManager(client)

    # Get relation summary (without updating)
    print("📊 Getting relation summary...")
    summary = manager.get_relation_summary(target_date)

    if "error" in summary:
        print(f"❌ Error: {summary['error']}")
        return

    print()
    print("SUMMARY:")
    print(f"  Planned tasks: {summary['planned_count']}")
    print(f"  Active tasks: {summary['active_count']}")
    print(f"  Worked tasks: {summary['worked_count']}")
    print(f"  Done tasks: {summary['done_count']}")
    print()

    # Get task details
    print("=" * 80)
    print("PLANNED TASKS DETAILS")
    print("=" * 80)

    planned_ids = summary.get('planned_ids', [])
    if planned_ids:
        print(f"\nFound {len(planned_ids)} planned tasks:")
        for task_id in planned_ids:
            task = client.client.pages.retrieve(page_id=task_id)
            task_name = task['properties'].get('Name', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')

            # Get Planned property
            planned_prop = task['properties'].get('Planned', {})
            planned_value = planned_prop.get('date', {})

            print(f"\n  • {task_name}")
            print(f"    ID: {task_id}")
            print(f"    Planned property: {planned_value}")

    else:
        print("\n  No planned tasks found!")

    # Now let's check ALL tasks with a Planned date and see why they might be excluded
    print()
    print("=" * 80)
    print("ALL TASKS WITH PLANNED DATES AROUND THIS DATE")
    print("=" * 80)

    # Query all tasks
    tasks = manager.task_extractor.extract_tasks_to_dataframe()

    print(f"\nTotal tasks in database: {len(tasks)}")

    if 'Planned' in tasks.columns or 'planned_start' in tasks.columns:
        # Filter to tasks with Planned dates around our target
        pst = pytz.timezone('America/Los_Angeles')
        utc_start, utc_end = manager._get_pst_day_boundaries_utc(target_date)

        print(f"\nPST day boundaries for {target_date}:")
        pst_start_dt = datetime.fromtimestamp(utc_start, tz=pytz.UTC).astimezone(pst)
        pst_end_dt = datetime.fromtimestamp(utc_end, tz=pytz.UTC).astimezone(pst)
        print(f"  Start (PST): {pst_start_dt}")
        print(f"  Start (UTC): {datetime.fromtimestamp(utc_start, tz=pytz.UTC)}")
        print(f"  End (PST): {pst_end_dt}")
        print(f"  End (UTC): {datetime.fromtimestamp(utc_end, tz=pytz.UTC)}")

        # Check each task
        print(f"\nChecking tasks with 'Planned' containing '{target_date_str}':")

        for idx, row in tasks.iterrows():
            # Get task name
            task_name = row.get('Name', 'Untitled')

            # Check if Planned column has our date
            planned_value = row.get('Planned')
            planned_start = row.get('planned_start')
            planned_end = row.get('planned_end')

            # Check if this task mentions our target date
            if planned_value and target_date_str in str(planned_value):
                print(f"\n  📌 {task_name}")
                print(f"     Planned (raw): {planned_value}")
                print(f"     planned_start: {planned_start}")
                print(f"     planned_end: {planned_end}")

                # Check if it passes the filter
                if planned_start and planned_end:
                    import pandas as pd
                    planned_start_ts = int(pd.to_datetime(planned_start, utc=True).timestamp())
                    planned_end_ts = int(pd.to_datetime(planned_end, utc=True).timestamp())

                    check1 = planned_start_ts > 0
                    check2 = planned_start_ts <= utc_end
                    check3 = planned_end_ts >= utc_start

                    passes = check1 and check2 and check3

                    print(f"     Filter checks:")
                    print(f"       ✓ Has valid start: {check1}")
                    print(f"       {'✓' if check2 else '✗'} Starts before/during day: {check2}")
                    print(f"           (planned_start {planned_start_ts} <= utc_end {utc_end})")
                    print(f"       {'✓' if check3 else '✗'} Ends during/after day: {check3}")
                    print(f"           (planned_end {planned_end_ts} >= utc_start {utc_start})")
                    print(f"     → {'✅ PASSES' if passes else '❌ FAILS'}")

                    if not passes and not check3:
                        # Explain timezone issue
                        print(f"\n     🐛 TIMEZONE ISSUE DETECTED!")
                        print(f"        Notion date '2026-01-16' is being parsed as:")
                        print(f"          {planned_end} (UTC)")
                        print(f"        But PST day starts at:")
                        print(f"          {datetime.fromtimestamp(utc_start, tz=pytz.UTC)} (UTC)")
                        print(f"        The date needs to be interpreted as PST, not UTC!")

    print()
    print("=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_task_relations.py YYYY-MM-DD")
        print("Example: python scripts/debug_task_relations.py 2026-01-16")
        sys.exit(1)

    debug_date(sys.argv[1])
