#!/usr/bin/env python3
"""
Upload a Gymaholic workout template to Notion Workout Templates DB.

Usage:
    python scripts/upload_workout_template.py <workout_name>
    python scripts/upload_workout_template.py "TOMO A Strength"
    python scripts/upload_workout_template.py --list  # List available templates

Reads workout definitions from config/workout_config.yaml and uploads
to the Workout Templates database in Notion.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
import argparse
from toad.notion_client import TOADNotionClient

# Workout Templates DB ID
TEMPLATES_DB_ID = "2f72579666bd81b6a5b8fb1e0628d01f"

# Apple Health type mapping
APPLE_HEALTH_TYPE_MAP = {
    "TOMO A Strength": "Traditional Strength Training",
    "TOMO A": "Traditional Strength Training",
    "TOMO B Strength": "Traditional Strength Training",
    "TOMO C": "Traditional Strength Training",
    "Climbing Warmup": "Preparation & Recovery",
    "FRI - Upper Pull": "Functional Strength Training",
}


def load_workout_config() -> dict:
    """Load workout_config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "workout_config.yaml"
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def list_available_workouts(config: dict):
    """Print available workouts from config."""
    workouts = config.get('workouts', {})
    print("\nAvailable workout templates:")
    print("-" * 40)
    for name, data in workouts.items():
        workout_type = data.get('type', 'unknown')
        print(f"  {name} ({workout_type})")
    print()


def upload_template(client: TOADNotionClient, workout_name: str, workout_data: dict) -> bool:
    """Upload or update a workout template in Notion."""

    # Check if template already exists
    filter_dict = {
        "property": "Name",
        "title": {"equals": workout_name}
    }
    existing = client.get_database_pages(TEMPLATES_DB_ID, filter_dict=filter_dict)

    # Determine Apple Health type
    apple_health_type = APPLE_HEALTH_TYPE_MAP.get(workout_name, "Other")

    # Strength workouts require partner data (Gymaholic export)
    requires_partner = apple_health_type in [
        "Traditional Strength Training",
        "Functional Strength Training",
        "Preparation & Recovery",
    ]

    properties = {
        "Name": {
            "title": [{"text": {"content": workout_name}}]
        },
        "Type": {
            "select": {"name": workout_data.get('type', 'general')}
        },
        "Description": {
            "rich_text": [{"text": {"content": workout_data.get('description', '')}}]
        },
        "Active": {
            "checkbox": True
        },
        "Apple Health Type": {
            "select": {"name": apple_health_type}
        },
        "Requires Partner": {
            "checkbox": requires_partner
        }
    }

    try:
        if existing:
            page_id = existing[0]['id']
            client.client.pages.update(page_id=page_id, properties=properties)
            print(f"Updated: {workout_name}")
        else:
            client.client.pages.create(
                parent={"database_id": TEMPLATES_DB_ID},
                properties=properties
            )
            print(f"Created: {workout_name}")
        return True
    except Exception as e:
        print(f"Error uploading {workout_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload workout template to Notion")
    parser.add_argument("workout_name", nargs="?", help="Name of workout to upload")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--all", action="store_true", help="Upload all templates")
    args = parser.parse_args()

    config = load_workout_config()
    workouts = config.get('workouts', {})

    if args.list:
        list_available_workouts(config)
        return

    if not args.workout_name and not args.all:
        parser.print_help()
        print("\nError: Specify a workout name or use --all")
        sys.exit(1)

    client = TOADNotionClient()

    if args.all:
        print("Uploading all workout templates...")
        success = 0
        for name, data in workouts.items():
            if upload_template(client, name, data):
                success += 1
        print(f"\nUploaded {success}/{len(workouts)} templates")
    else:
        if args.workout_name not in workouts:
            print(f"Error: '{args.workout_name}' not found in config")
            list_available_workouts(config)
            sys.exit(1)

        upload_template(client, args.workout_name, workouts[args.workout_name])


if __name__ == "__main__":
    main()
