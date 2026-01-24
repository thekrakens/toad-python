# Daily Productivity Metrics - Schema

**Database Name:** Daily Productivity Metrics
**Database ID:** `23525796-66bd-8017-a464-c1a7d32d35c4`
**Last Updated:** 2026-01-19 19:31:56

## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
| Active | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Archived | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Backlog | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Date | date | Date field |
| Day of Week | formula | Formula: `formatDate({{notion:block_property:%3Emnq:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, "dddd")` |
| Done | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Effective Hours Worked | formula | Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()` |
| Name | title | - |
| Notes | rich_text | - |
| Planned | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Planned Working Hours | rollup | From: Planned.Planned Hrs. | Function: sum |
| Planned vs Unplanned % | formula | Formula: `if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100), 0)` |
| Planning Quality % | formula | Formula: `` |
| Productivity Score | formula | Formula: `lets(
    completionScore, if({{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, {{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length() / {{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} * 100, 0),
    adherenceScore, if({{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, min({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / 
  {{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, 1) * 100, 0),
    plannedRatio, if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, ({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} /
  {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100, 0),
    qualityScore, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == "Excellent", 100, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == "Good", 
  75, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == "Fair", 50, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == "Poor", 25, 50)))),
    
    round(
      completionScore * 0.4 +
      adherenceScore * 0.3 +
      plannedRatio * 0.2 +
      qualityScore * 0.1
    )
  )` |
| Schedule Adherence % | formula | Formula: `if({{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(min({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, 1) * 100), 0)` |
| Task Completion Rate % | formula | Formula: `if({{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round({{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length() / {{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}), 0)` |
| Tasked Worked Count | formula | Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Tasks Active Count | formula | Formula: `{{notion:block_property:%5Bn~k:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Tasks Archived Count | formula | Formula: `{{notion:block_property:KGI%3E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Tasks Backlog Count | formula | Formula: `{{notion:block_property:%5Ex%5Ey:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Tasks Completed Count | formula | Formula: `{{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Tasks Planned Count | formula | Formula: `{{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Tasks Worked Count | formula | Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()` |
| Time on Planned Tasks (hrs) | formula | Formula: `lets(
    plannedIds, {{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.id()),
    {{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.filter(plannedIds.includes(current.id())).map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()
 )` |
| Time on Unplanned Tasks (hrs) | formula | Formula: `{{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} - {{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}` |
| Unplanned Tasks Created | formula | Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.filter(not current.id().contains(({{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.id()))).length())` |
| Worked | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |


## Raw Schema (JSON)

<details>
<summary>Click to expand full schema JSON</summary>

```json
{
  "name": "Daily Productivity Metrics",
  "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
  "title": "Daily Productivity Metrics",
  "description": "",
  "properties": {
    "Effective Hours Worked": {
      "type": "formula",
      "id": "%3ALE%40",
      "config": {
        "expression": "{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()"
      },
      "config_formatted": "Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()`"
    },
    "Tasked Worked Count": {
      "type": "formula",
      "id": "%3BWsj",
      "config": {
        "expression": "{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Tasks Planned Count": {
      "type": "formula",
      "id": "%3DF%7C%7B",
      "config": {
        "expression": "{{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Schedule Adherence %": {
      "type": "formula",
      "id": "%3DPlB",
      "config": {
        "expression": "if({{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(min({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, 1) * 100), 0)"
      },
      "config_formatted": "Formula: `if({{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(min({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, 1) * 100), 0)`"
    },
    "Date": {
      "type": "date",
      "id": "%3Emnq",
      "config": {},
      "config_formatted": "Date field"
    },
    "Task Completion Rate %": {
      "type": "formula",
      "id": "%3EoDI",
      "config": {
        "expression": "if({{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round({{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length() / {{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}), 0)"
      },
      "config_formatted": "Formula: `if({{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round({{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length() / {{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}), 0)`"
    },
    "Time on Unplanned Tasks (hrs)": {
      "type": "formula",
      "id": "%40%3DHu",
      "config": {
        "expression": "{{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} - {{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}"
      },
      "config_formatted": "Formula: `{{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} - {{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}`"
    },
    "Day of Week": {
      "type": "formula",
      "id": "GCbN",
      "config": {
        "expression": "formatDate({{notion:block_property:%3Emnq:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"dddd\")"
      },
      "config_formatted": "Formula: `formatDate({{notion:block_property:%3Emnq:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"dddd\")`"
    },
    "Archived": {
      "type": "relation",
      "id": "KGI%3E",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Related to Daily Productivity Metrics (Archived)",
          "synced_property_id": "fSjg"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Planned": {
      "type": "relation",
      "id": "M~KU",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Related to Daily Productivity Metrics (Planned Tasks)",
          "synced_property_id": "si%5E%3C"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Notes": {
      "type": "rich_text",
      "id": "Pgor",
      "config": {},
      "config_formatted": ""
    },
    "Planning Quality %": {
      "type": "formula",
      "id": "UdUv",
      "config": {
        "expression": ""
      },
      "config_formatted": "Formula: ``"
    },
    "Tasks Completed Count": {
      "type": "formula",
      "id": "VZdr",
      "config": {
        "expression": "{{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Planned Working Hours": {
      "type": "rollup",
      "id": "Z%5Ekd",
      "config": {
        "rollup_property_name": "Planned Hrs.",
        "relation_property_name": "Planned",
        "rollup_property_id": "ben:",
        "relation_property_id": "M~KU",
        "function": "sum"
      },
      "config_formatted": "From: Planned.Planned Hrs. | Function: sum"
    },
    "Tasks Archived Count": {
      "type": "formula",
      "id": "%5BR%60%3C",
      "config": {
        "expression": "{{notion:block_property:KGI%3E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:KGI%3E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Active": {
      "type": "relation",
      "id": "%5Bn~k",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Related to Daily Productivity Metrics (Active Tasks)",
          "synced_property_id": "N_v%3A"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Tasks Active Count": {
      "type": "formula",
      "id": "%5C%7BZi",
      "config": {
        "expression": "{{notion:block_property:%5Bn~k:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:%5Bn~k:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Tasks Worked Count": {
      "type": "formula",
      "id": "%5DEkb",
      "config": {
        "expression": "{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Planned vs Unplanned %": {
      "type": "formula",
      "id": "%5EYHt",
      "config": {
        "expression": "if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100), 0)"
      },
      "config_formatted": "Formula: `if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100), 0)`"
    },
    "Backlog": {
      "type": "relation",
      "id": "%5Ex%5Ey",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Related to Daily Productivity Metrics (Backlog)",
          "synced_property_id": "UeWq"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Tasks Backlog Count": {
      "type": "formula",
      "id": "l%5Cg%3C",
      "config": {
        "expression": "{{notion:block_property:%5Ex%5Ey:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:%5Ex%5Ey:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length()`"
    },
    "Time on Planned Tasks (hrs)": {
      "type": "formula",
      "id": "mow%3D",
      "config": {
        "expression": "lets(\n    plannedIds, {{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.id()),\n    {{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.filter(plannedIds.includes(current.id())).map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()\n )"
      },
      "config_formatted": "Formula: `lets(\n    plannedIds, {{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.id()),\n    {{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.filter(plannedIds.includes(current.id())).map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()\n )`"
    },
    "Unplanned Tasks Created": {
      "type": "formula",
      "id": "sgDC",
      "config": {
        "expression": "{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.filter(not current.id().contains(({{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.id()))).length())"
      },
      "config_formatted": "Formula: `{{notion:block_property:uz_a:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.filter(not current.id().contains(({{notion:block_property:M~KU:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.id()))).length())`"
    },
    "Worked": {
      "type": "relation",
      "id": "uz_a",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Related to Daily Productivity Metrics (Worked On Tasks)",
          "synced_property_id": "%3BIPk"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Productivity Score": {
      "type": "formula",
      "id": "%7B%3C%3BQ",
      "config": {
        "expression": "lets(\n    completionScore, if({{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, {{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length() / {{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} * 100, 0),\n    adherenceScore, if({{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, min({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / \n  {{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, 1) * 100, 0),\n    plannedRatio, if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, ({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} /\n  {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100, 0),\n    qualityScore, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Excellent\", 100, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Good\", \n  75, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Fair\", 50, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Poor\", 25, 50)))),\n    \n    round(\n      completionScore * 0.4 +\n      adherenceScore * 0.3 +\n      plannedRatio * 0.2 +\n      qualityScore * 0.1\n    )\n  )"
      },
      "config_formatted": "Formula: `lets(\n    completionScore, if({{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, {{notion:block_property:%7Dna%7D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.length() / {{notion:block_property:%3DF%7C%7B:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} * 100, 0),\n    adherenceScore, if({{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, min({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / \n  {{notion:block_property:Z%5Ekd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, 1) * 100, 0),\n    plannedRatio, if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, ({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} /\n  {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100, 0),\n    qualityScore, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Excellent\", 100, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Good\", \n  75, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Fair\", 50, if({{notion:block_property:kv%3Fr:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"Poor\", 25, 50)))),\n    \n    round(\n      completionScore * 0.4 +\n      adherenceScore * 0.3 +\n      plannedRatio * 0.2 +\n      qualityScore * 0.1\n    )\n  )`"
    },
    "Done": {
      "type": "relation",
      "id": "%7Dna%7D",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Related to Daily Productivity Metrics (Completed Tasks)",
          "synced_property_id": "%3ADWM"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
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
