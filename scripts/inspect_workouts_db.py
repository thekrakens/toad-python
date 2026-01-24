#!/usr/bin/env python3
"""Inspect the newly created Workouts database."""

from toad.notion_client import TOADNotionClient

WORKOUTS_DB = "2ed2579666bd80f28e7bdc014f3280d8"

def main():
    client = TOADNotionClient()
    schema = client.analyze_database_schema(WORKOUTS_DB)

    print(f"\n{'='*80}")
    print(f"Database: {schema['database_title']}")
    print(f"Total Properties: {schema['total_properties']}")
    print(f"{'='*80}\n")

    print("Properties:")
    print("-" * 80)
    for prop_name, prop_info in schema['properties'].items():
        prop_type = prop_info['type']
        print(f"  • {prop_name}")
        print(f"    Type: {prop_type}")

        if prop_type == 'relation':
            config = prop_info.get('config', {})
            if 'database_id' in config:
                print(f"    Related DB ID: {config['database_id']}")
        elif prop_type == 'select':
            config = prop_info.get('config', {})
            if 'options' in config:
                options = [opt['name'] for opt in config['options']]
                print(f"    Options: {', '.join(options)}")
        print()

    print("\nProperty Type Summary:")
    for prop_type, count in schema['property_types'].items():
        print(f"  {prop_type}: {count}")

    print(f"\n{'='*80}")
    print("✅ Database inspection complete!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
