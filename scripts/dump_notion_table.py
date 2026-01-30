#!/usr/bin/env python3
"""
Dump Notion database pages to JSON for debugging/analysis.

Usage:
    python scripts/dump_notion_table.py <table_name_or_id> [--start DATE] [--end DATE]

Examples:
    python scripts/dump_notion_table.py workouts --start 2026-01-01 --end 2026-01-31
    python scripts/dump_notion_table.py habits --start 2026-01-20
    python scripts/dump_notion_table.py 2f72579666bd81b6a5b8fb1e0628d01f
    python scripts/dump_notion_table.py --list

Output goes to /tmp/notion_dump_<table>_<timestamp>.json
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent))

from toad.config import Config
from toad.notion_client import TOADNotionClient

# Table name to config attribute mapping
TABLE_MAP = {
    "tasks": "NOTION_DATABASE_ID",
    "time_blocks": "NOTION_TIME_BLOCKS_DATABASE_ID",
    "daily_metrics": "NOTION_DAILY_METRICS_DATABASE_ID",
    "time_entries": "NOTION_TIME_ENTRIES_DATABASE_ID",
    "habits": "NOTION_HABITS_DATABASE_ID",
    "workouts": "NOTION_WORKOUTS_DATABASE_ID",
    "health_stats": "NOTION_HEALTH_STATS_DATABASE_ID",
}


def get_database_id(name_or_id: str) -> tuple[str, str]:
    """
    Resolve table name or ID to database ID.

    Returns:
        Tuple of (database_id, display_name)
    """
    # Check if it's a known table name
    name_lower = name_or_id.lower().replace("-", "_").replace(" ", "_")

    if name_lower in TABLE_MAP:
        config_attr = TABLE_MAP[name_lower]
        db_id = getattr(Config, config_attr, "")
        if not db_id:
            print(f"Error: {config_attr} not configured in environment")
            sys.exit(1)
        return db_id, name_lower

    # Check if it looks like a Notion ID (32 hex chars, possibly with dashes)
    clean_id = name_or_id.replace("-", "")
    if len(clean_id) == 32 and all(c in '0123456789abcdef' for c in clean_id.lower()):
        return name_or_id, "custom"

    print(f"Error: Unknown table '{name_or_id}'")
    print("\nAvailable tables:")
    for name in TABLE_MAP.keys():
        print(f"  {name}")
    sys.exit(1)


def build_date_filter(start_date: date = None, end_date: date = None) -> dict:
    """Build Notion filter for date range."""
    if not start_date and not end_date:
        return None

    # Try common date property names
    date_property = "Date"  # Most common

    conditions = []
    if start_date:
        conditions.append({
            "property": date_property,
            "date": {"on_or_after": start_date.isoformat()}
        })
    if end_date:
        conditions.append({
            "property": date_property,
            "date": {"on_or_before": end_date.isoformat()}
        })

    if len(conditions) == 1:
        return conditions[0]
    return {"and": conditions}


def dump_database(client: TOADNotionClient, db_id: str, table_name: str,
                  start_date: date = None, end_date: date = None) -> Path:
    """
    Dump database pages to JSON file.

    Returns:
        Path to output file
    """
    print(f"Fetching pages from {table_name}...")

    # Build filter
    filter_dict = build_date_filter(start_date, end_date)

    # Fetch pages
    try:
        pages = client.get_database_pages(db_id, filter_dict=filter_dict)
    except Exception as e:
        print(f"Error fetching pages: {e}")
        sys.exit(1)

    print(f"Retrieved {len(pages)} pages")

    # Build output
    output = {
        "database_id": db_id,
        "table_name": table_name,
        "exported_at": datetime.now().isoformat(),
        "filter": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "page_count": len(pages),
        "pages": pages
    }

    # Write to /tmp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"/tmp/notion_dump_{table_name}_{timestamp}.json")

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Wrote {output_path}")
    return output_path


def list_tables():
    """Print available table names."""
    print("\nAvailable tables:")
    print("-" * 50)
    for name, config_attr in TABLE_MAP.items():
        db_id = getattr(Config, config_attr, "")
        status = "configured" if db_id else "NOT CONFIGURED"
        print(f"  {name:15} ({status})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Dump Notion database to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s workouts --start 2026-01-01 --end 2026-01-31
  %(prog)s habits --start 2026-01-20
  %(prog)s --list
        """
    )
    parser.add_argument("table", nargs="?", help="Table name or database ID")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--list", action="store_true", help="List available tables")
    args = parser.parse_args()

    if args.list:
        list_tables()
        return

    if not args.table:
        parser.print_help()
        sys.exit(1)

    # Parse dates
    start_date = None
    end_date = None
    if args.start:
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid start date format: {args.start}")
            sys.exit(1)
    if args.end:
        try:
            end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid end date format: {args.end}")
            sys.exit(1)

    # Resolve database
    db_id, table_name = get_database_id(args.table)

    # Dump
    client = TOADNotionClient()
    output_path = dump_database(client, db_id, table_name, start_date, end_date)

    print(f"\nDone! View with:")
    print(f"  cat {output_path} | jq .")


if __name__ == "__main__":
    main()
