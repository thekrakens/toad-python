#!/usr/bin/env python3
"""Review Habit Tracker properties for standardization."""

from toad.notion_client import TOADNotionClient

HABIT_TRACKER_DB = "2042579666bd81bf969cd7cfb068264e"

def main():
    client = TOADNotionClient()
    schema = client.analyze_database_schema(HABIT_TRACKER_DB)

    print(f"\n{'='*80}")
    print(f"Database: {schema['database_title']}")
    print(f"Total Properties: {schema['total_properties']}")
    print(f"{'='*80}\n")

    print("Current Properties:")
    print("-" * 80)

    # Group by type for easier review
    properties_by_type = {}
    for prop_name, prop_info in schema['properties'].items():
        prop_type = prop_info['type']
        if prop_type not in properties_by_type:
            properties_by_type[prop_type] = []
        properties_by_type[prop_type].append(prop_name)

    # Show all properties
    for i, (prop_name, prop_info) in enumerate(schema['properties'].items(), 1):
        prop_type = prop_info['type']
        print(f"{i:2d}. {prop_name:25s} ({prop_type})")

    print(f"\n{'='*80}")
    print("\nProperties by Type:")
    print("-" * 80)
    for prop_type, props in sorted(properties_by_type.items()):
        print(f"\n{prop_type.upper()}:")
        for prop in sorted(props):
            print(f"  - {prop}")

    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
