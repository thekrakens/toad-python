#!/usr/bin/env python3
"""
Quick script to inspect Notion database schemas.
Helps understand the structure before designing new databases.
"""

from toad.notion_client import TOADNotionClient

# Database IDs from the URLs you shared
HABIT_TRACKER_DB = "2042579666bd81bf969cd7cfb068264e"
HEALTH_STATS_DB = "2042579666bd811d9d93d6e2426550ec"

def inspect_database(client, db_id, name):
    """Inspect and print database schema."""
    print(f"\n{'='*80}")
    print(f"Database: {name}")
    print(f"ID: {db_id}")
    print(f"{'='*80}\n")

    try:
        schema = client.analyze_database_schema(db_id)

        print(f"Title: {schema['database_title']}")
        print(f"Total Properties: {schema['total_properties']}\n")

        print("Properties:")
        print("-" * 80)

        for prop_name, prop_info in schema['properties'].items():
            prop_type = prop_info['type']
            print(f"  • {prop_name}")
            print(f"    Type: {prop_type}")

            # Show additional config for certain types
            if prop_type == 'relation':
                config = prop_info.get('config', {})
                if 'database_id' in config:
                    print(f"    Related DB: {config['database_id']}")
            elif prop_type == 'select' or prop_type == 'multi_select':
                config = prop_info.get('config', {})
                if 'options' in config:
                    options = [opt['name'] for opt in config['options']]
                    print(f"    Options: {', '.join(options[:5])}")
                    if len(options) > 5:
                        print(f"    ... and {len(options) - 5} more")
            elif prop_type == 'formula':
                config = prop_info.get('config', {})
                if 'expression' in config:
                    expr = config['expression'][:60]
                    print(f"    Formula: {expr}...")

            print()

        print("\nProperty Type Summary:")
        for prop_type, count in schema['property_types'].items():
            print(f"  {prop_type}: {count}")

    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main inspection routine."""
    print("🐸 TOAD - Notion Database Inspector")

    client = TOADNotionClient()

    # Inspect Habit Tracker
    inspect_database(client, HABIT_TRACKER_DB, "Habit Tracker")

    # Inspect Health Stats
    inspect_database(client, HEALTH_STATS_DB, "Health Stats")

    print(f"\n{'='*80}")
    print("✅ Inspection complete!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
