# Daily Productivity Metrics - Schema

**Database Name:** Daily Productivity Metrics
**Database ID:** `23525796-66bd-8017-a464-c1a7d32d35c4`
**Last Updated:** 2026-01-19 13:24:55

## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
| Active | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Cold Tasks Count | number | Format: number |
| Context Switches | number | Format: number |
| Date | date | Date field |
| Day of Week | formula | Formula: `formatDate({{notion:block_property:%3Emnq:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, "dddd")` |
| Done | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Effective Hours Worked | number | Format: number_with_commas |
| Name | title | - |
| Notes | rich_text | - |
| Planned | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Planned Working Hours | number | Format: number_with_commas |
| Planned vs Unplanned % | formula | Formula: `if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100), 0)` |
| Productivity Score | number | Format: number |
| Quality Rating | select | Options: Excellent, Good, Fair, Poor, Not Rated |
| Schedule Adherence % | number | Format: percent |
| Task Completion Rate % | number | Format: percent |
| Tasks Active Count | number | Format: number |
| Tasks Planned Count | number | Format: number |
| Time on Planned Tasks | number | Format: number_with_commas |
| Time on Unplanned Tasks | number | Format: number_with_commas |
| Unplanned Tasks Created | number | Format: number |
| Work Day Type | select | Options: Focused Work, Meeting Heavy, Administrative, Mixed/Balanced, Planning, Research |
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
      "type": "number",
      "id": "%3ALE%40",
      "config": {
        "format": "number_with_commas"
      },
      "config_formatted": "Format: number_with_commas"
    },
    "Tasks Planned Count": {
      "type": "number",
      "id": "%3DF%7C%7B",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
    },
    "Schedule Adherence %": {
      "type": "number",
      "id": "%3DPlB",
      "config": {
        "format": "percent"
      },
      "config_formatted": "Format: percent"
    },
    "Date": {
      "type": "date",
      "id": "%3Emnq",
      "config": {},
      "config_formatted": "Date field"
    },
    "Task Completion Rate %": {
      "type": "number",
      "id": "%3EoDI",
      "config": {
        "format": "percent"
      },
      "config_formatted": "Format: percent"
    },
    "Time on Unplanned Tasks": {
      "type": "number",
      "id": "%40%3DHu",
      "config": {
        "format": "number_with_commas"
      },
      "config_formatted": "Format: number_with_commas"
    },
    "Day of Week": {
      "type": "formula",
      "id": "GCbN",
      "config": {
        "expression": "formatDate({{notion:block_property:%3Emnq:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"dddd\")"
      },
      "config_formatted": "Formula: `formatDate({{notion:block_property:%3Emnq:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"dddd\")`"
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
    "Cold Tasks Count": {
      "type": "number",
      "id": "RcMh",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
    },
    "Planned Working Hours": {
      "type": "number",
      "id": "Z%5Ekd",
      "config": {
        "format": "number_with_commas"
      },
      "config_formatted": "Format: number_with_commas"
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
      "type": "number",
      "id": "%5C%7BZi",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
    },
    "Planned vs Unplanned %": {
      "type": "formula",
      "id": "%5EYHt",
      "config": {
        "expression": "if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100), 0)"
      },
      "config_formatted": "Formula: `if({{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} > 0, round(({{notion:block_property:mow%3D:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / {{notion:block_property:%3ALE%40:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}) * 100), 0)`"
    },
    "Context Switches": {
      "type": "number",
      "id": "a_jS",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
    },
    "Work Day Type": {
      "type": "select",
      "id": "jLJJ",
      "config": {
        "options": [
          {
            "id": "67b3a935-e5f4-4141-ad03-7a301305f697",
            "name": "Focused Work",
            "color": "green",
            "description": null
          },
          {
            "id": "3e45379a-0f2d-478f-b52a-9cb0171450a7",
            "name": "Meeting Heavy",
            "color": "blue",
            "description": null
          },
          {
            "id": "3deca486-cf5f-4f8d-b2b9-1a2e0791d36e",
            "name": "Administrative",
            "color": "yellow",
            "description": null
          },
          {
            "id": "0482f592-af08-40e0-bbe2-8399d6c92e81",
            "name": "Mixed/Balanced",
            "color": "default",
            "description": null
          },
          {
            "id": "cb23b590-cf05-4733-af8c-bfe83a45079d",
            "name": "Planning",
            "color": "purple",
            "description": null
          },
          {
            "id": "637bf5dc-2c4a-465f-a111-b356343db753",
            "name": "Research",
            "color": "orange",
            "description": null
          }
        ]
      },
      "config_formatted": "Options: Focused Work, Meeting Heavy, Administrative, Mixed/Balanced, Planning, Research"
    },
    "Quality Rating": {
      "type": "select",
      "id": "kv%3Fr",
      "config": {
        "options": [
          {
            "id": "62e38b5b-c50e-475f-a1c6-49b6f670fbc2",
            "name": "Excellent",
            "color": "green",
            "description": null
          },
          {
            "id": "dbef2d83-c43d-4fd1-8d0c-5d72488d201f",
            "name": "Good",
            "color": "blue",
            "description": null
          },
          {
            "id": "231b9f06-16c1-4fde-8fb0-299379aff8fd",
            "name": "Fair",
            "color": "yellow",
            "description": null
          },
          {
            "id": "b172c66d-e262-48dc-a9d7-ec64f3ef7a71",
            "name": "Poor",
            "color": "red",
            "description": null
          },
          {
            "id": "c5dbd755-709c-4a9f-8947-5af01c96ab1a",
            "name": "Not Rated",
            "color": "gray",
            "description": null
          }
        ]
      },
      "config_formatted": "Options: Excellent, Good, Fair, Poor, Not Rated"
    },
    "Time on Planned Tasks": {
      "type": "number",
      "id": "mow%3D",
      "config": {
        "format": "number_with_commas"
      },
      "config_formatted": "Format: number_with_commas"
    },
    "Unplanned Tasks Created": {
      "type": "number",
      "id": "sgDC",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
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
      "type": "number",
      "id": "%7B%3C%3BQ",
      "config": {
        "format": "number"
      },
      "config_formatted": "Format: number"
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
