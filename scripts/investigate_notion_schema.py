#!/usr/bin/env python3
"""
Investigate Notion database schemas and export to markdown.

This script queries Notion databases to extract their full schema including:
- All properties (name, type, configuration)
- Property descriptions
- Database title and description
- Relations and rollups configuration

Usage:
    python scripts/investigate_notion_schema.py [database_name]

    If no database name provided, investigates all productivity databases.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from toad.notion_client import TOADNotionClient
from toad.config import Config


def format_property_config(prop_type: str, config: dict) -> str:
    """Format property configuration as human-readable string."""
    if prop_type == "relation":
        db_id = config.get("database_id", "N/A")
        return f"→ Database: {db_id}"
    elif prop_type == "rollup":
        relation = config.get("relation_property_name", "N/A")
        rollup_prop = config.get("rollup_property_name", "N/A")
        function = config.get("function", "N/A")
        return f"From: {relation}.{rollup_prop} | Function: {function}"
    elif prop_type == "formula":
        expression = config.get("expression", "N/A")
        return f"Formula: `{expression}`"
    elif prop_type == "select":
        options = config.get("options", [])
        option_names = [opt.get("name", "") for opt in options]
        return f"Options: {', '.join(option_names)}"
    elif prop_type == "multi_select":
        options = config.get("options", [])
        option_names = [opt.get("name", "") for opt in options]
        return f"Options: {', '.join(option_names)}"
    elif prop_type == "status":
        options = config.get("options", [])
        option_names = [opt.get("name", "") for opt in options]
        groups = config.get("groups", [])
        group_names = [g.get("name", "") for g in groups]
        return f"Groups: {', '.join(group_names)} | Options: {', '.join(option_names)}"
    elif prop_type == "number":
        format_type = config.get("format", "number")
        return f"Format: {format_type}"
    elif prop_type == "date":
        return "Date field"
    else:
        return ""


def investigate_database_schema(client: TOADNotionClient, database_id: str, database_name: str) -> dict:
    """
    Query Notion database schema and return structured data.

    Args:
        client: TOADNotionClient instance
        database_id: Notion database ID
        database_name: Human-readable database name

    Returns:
        Dictionary with schema information
    """
    print(f"Investigating {database_name}...")

    # Get database metadata
    db_info = client.client.databases.retrieve(database_id=database_id)

    schema = {
        "name": database_name,
        "database_id": database_id,
        "title": db_info.get("title", [{}])[0].get("plain_text", "Untitled"),
        "description": db_info.get("description", [{}])[0].get("plain_text", "") if db_info.get("description") else "",
        "properties": {}
    }

    # Extract all properties
    properties = db_info.get("properties", {})

    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get("type")
        prop_id = prop_data.get("id")

        # Get type-specific configuration
        config = prop_data.get(prop_type, {})

        schema["properties"][prop_name] = {
            "type": prop_type,
            "id": prop_id,
            "config": config,
            "config_formatted": format_property_config(prop_type, config)
        }

    return schema


def export_schema_to_markdown(schema: dict, output_path: Path):
    """
    Export schema to markdown file.

    Args:
        schema: Schema dictionary from investigate_database_schema()
        output_path: Path to output markdown file
    """
    md_content = f"""# {schema['title']} - Schema

**Database Name:** {schema['name']}
**Database ID:** `{schema['database_id']}`
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    if schema['description']:
        md_content += f"""## Description

{schema['description']}

"""

    md_content += """## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
"""

    # Sort properties alphabetically for consistency
    for prop_name in sorted(schema['properties'].keys()):
        prop_data = schema['properties'][prop_name]
        prop_type = prop_data['type']
        config_str = prop_data['config_formatted'] or "-"

        md_content += f"| {prop_name} | {prop_type} | {config_str} |\n"

    md_content += f"""

## Raw Schema (JSON)

<details>
<summary>Click to expand full schema JSON</summary>

```json
{json.dumps(schema, indent=2, default=str)}
```

</details>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content)
    print(f"  ✅ Exported to {output_path}")


def main():
    """Main function to investigate database schemas."""

    # Define databases to investigate
    databases = {
        "tasks": {
            "id": Config.NOTION_DATABASE_ID,  # This is the Tasks database
            "name": "Tasks"
        },
        "time_entries": {
            "id": Config.NOTION_TIME_ENTRIES_DATABASE_ID,
            "name": "Time Entries"
        },
        "daily_metrics": {
            "id": Config.NOTION_DAILY_METRICS_DATABASE_ID,
            "name": "Daily Productivity Metrics"
        },
        "time_blocks": {
            "id": Config.NOTION_TIME_BLOCKS_DATABASE_ID,
            "name": "Planned Time Blocks"
        },
        "projects": {
            "id": "2042579666bd8147a8ccebe5658fbdda",
            "name": "Projects"
        }
    }

    # Check if specific database requested
    if len(sys.argv) > 1:
        db_key = sys.argv[1]
        if db_key not in databases:
            print(f"Error: Unknown database '{db_key}'")
            print(f"Available databases: {', '.join(databases.keys())}")
            sys.exit(1)
        databases = {db_key: databases[db_key]}

    # Initialize Notion client
    client = TOADNotionClient()

    # Output directory
    output_dir = Path(__file__).parent.parent / "docs" / "notion_schemas"

    print("=" * 60)
    print("Notion Schema Investigation")
    print("=" * 60)
    print()

    # Investigate each database
    for db_key, db_info in databases.items():
        try:
            schema = investigate_database_schema(
                client=client,
                database_id=db_info["id"],
                database_name=db_info["name"]
            )

            output_path = output_dir / f"{db_key}.md"
            export_schema_to_markdown(schema, output_path)
            print()

        except Exception as e:
            print(f"  ❌ Error investigating {db_info['name']}: {e}")
            print()

    print("=" * 60)
    print(f"Schema investigation complete!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
