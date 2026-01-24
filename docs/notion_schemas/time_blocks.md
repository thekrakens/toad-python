# Planned Time Blocks - Schema

**Database Name:** Planned Time Blocks
**Database ID:** `2282579666bd803db27de8b6b6938b26`
**Last Updated:** 2026-01-19 19:31:56

## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
| Duration (mins) | number | Format: number |
| End Time | formula | Formula: `dateAdd({{notion:block_property:v%3Cgc:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},{{notion:block_property:CtF%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, "minutes")` |
| Name | title | - |
| Start Time | date | Date field |
| Task | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |


## Raw Schema (JSON)

<details>
<summary>Click to expand full schema JSON</summary>

```json
{
  "name": "Planned Time Blocks",
  "database_id": "2282579666bd803db27de8b6b6938b26",
  "title": "Planned Time Blocks",
  "description": "",
  "properties": {
    "Duration (mins)": {
      "type": "number",
      "id": "CtF%5E",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
    },
    "End Time": {
      "type": "formula",
      "id": "HkZ%5C",
      "config": {
        "expression": "dateAdd({{notion:block_property:v%3Cgc:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},{{notion:block_property:CtF%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"minutes\")"
      },
      "config_formatted": "Formula: `dateAdd({{notion:block_property:v%3Cgc:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},{{notion:block_property:CtF%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"minutes\")`"
    },
    "Task": {
      "type": "relation",
      "id": "guM%5E",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Time Blocks",
          "synced_property_id": "nDsi"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Start Time": {
      "type": "date",
      "id": "v%3Cgc",
      "config": {},
      "config_formatted": "Date field"
    },
    "Name": {
      "type": "title",
      "id": "title",
      "config": {},
      "config_formatted": ""
    }
  }
}
```

</details>
