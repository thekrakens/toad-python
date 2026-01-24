# Tasks - Schema

**Database Name:** Tasks
**Database ID:** `20425796-66bd-81f5-b759-e03fe4eb42f2`
**Last Updated:** 2026-01-19 19:31:55

## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
| Archived Date | date | Date field |
| Backlog Date | date | Date field |
| Create Entry | button | - |
| Created time | created_time | - |
| Daily Metrics | relation | → Database: 20425796-66bd-8171-92ad-da80f18fdf02 |
| Doing | date | Date field |
| Done | formula | Formula: `if(
  empty({{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}),
  {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},
  if(
    empty({{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}),
    {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},
    if(
      dateBetween({{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, "hours") >= 2,
      {{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},
      {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}
    )
  )
)` |
| Due | date | Date field |
| Feature | multi_select | Options: auto calibration, beta customer engagement, bttc, habits, health, productivity, streamlit app |
| Logged Time (hrs) | formula | Formula: `{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:CDEJ:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum() / 60` |
| Logged Time (mins) | formula | Formula: `{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:CDEJ:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()` |
| Name | title | - |
| Parent item | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Planned | date | Date field |
| Planned Hrs. | formula | Formula: `if({{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, dateBetween({{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.dateEnd(), {{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.dateStart(), "hours"), {{notion:block_property:axej:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}})` |
| Planned Time (hrs) | formula | Formula: `{{notion:block_property:tfgh:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / 60` |
| Planned Time (mins) | rollup | From: Time Blocks.Duration (mins) | Function: sum |
| Projects | relation | → Database: 20425796-66bd-8147-a8cc-ebe5658fbdda |
| Related to Daily Productivity Metrics (Active Tasks) | relation | → Database: 23525796-66bd-8017-a464-c1a7d32d35c4 |
| Related to Daily Productivity Metrics (Archived) | relation | → Database: 23525796-66bd-8017-a464-c1a7d32d35c4 |
| Related to Daily Productivity Metrics (Backlog) | relation | → Database: 23525796-66bd-8017-a464-c1a7d32d35c4 |
| Related to Daily Productivity Metrics (Completed Tasks) | relation | → Database: 23525796-66bd-8017-a464-c1a7d32d35c4 |
| Related to Daily Productivity Metrics (Planned Tasks) | relation | → Database: 23525796-66bd-8017-a464-c1a7d32d35c4 |
| Related to Daily Productivity Metrics (Worked On Tasks) | relation | → Database: 23525796-66bd-8017-a464-c1a7d32d35c4 |
| Status | status | Groups: To-do, In progress, Complete | Options: todo, backlog, doing, paused, done, archived |
| Sub-item | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Task Type | multi_select | Options: Meeting, R&D, coding, fixing, analysis, tests, planning, personal, documentation, deploy, cleanup |
| Time Blocks | relation | → Database: 22825796-66bd-803d-b27d-e8b6b6938b26 |
| Time Entries | relation | → Database: 20425796-66bd-8143-b976-eff463de13da |
| lastTimeEntryEnd | formula | Formula: `{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}
    .sort(current.{{notion:block_property:fY%5Er:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}})
    .last()
    .{{notion:block_property:fY%5Er:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} ` |
| setToDoneTime | date | Date field |
| ⏰ PLANNING ⏰ | rich_text | - |
| 🏴‍☠️ FLAGS🏴‍☠️  | rich_text | - |
| 📊 AUTO METRICS 📊  | rich_text | - |
| 📝 BASIC INFO 📝 | rich_text | - |
| 🔧  FORMULA HELPERS 🔧  | rich_text | - |
| 🤖 SYSTEM 🤖  | rich_text | - |
| 🧮 RELATIONS 🧮 | rich_text | - |


## Raw Schema (JSON)

<details>
<summary>Click to expand full schema JSON</summary>

```json
{
  "name": "Tasks",
  "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
  "title": "Tasks",
  "description": "",
  "properties": {
    "Related to Daily Productivity Metrics (Completed Tasks)": {
      "type": "relation",
      "id": "%3ADWM",
      "config": {
        "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
        "data_source_id": "23525796-66bd-80bb-9d91-000b89804e1c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Done",
          "synced_property_id": "%7Dna%7D"
        }
      },
      "config_formatted": "\u2192 Database: 23525796-66bd-8017-a464-c1a7d32d35c4"
    },
    "Planned": {
      "type": "date",
      "id": "%3AP%3Fv",
      "config": {},
      "config_formatted": "Date field"
    },
    "Backlog Date": {
      "type": "date",
      "id": "%3Az%3EI",
      "config": {},
      "config_formatted": "Date field"
    },
    "Related to Daily Productivity Metrics (Worked On Tasks)": {
      "type": "relation",
      "id": "%3BIPk",
      "config": {
        "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
        "data_source_id": "23525796-66bd-80bb-9d91-000b89804e1c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Worked",
          "synced_property_id": "uz_a"
        }
      },
      "config_formatted": "\u2192 Database: 23525796-66bd-8017-a464-c1a7d32d35c4"
    },
    "Done": {
      "type": "formula",
      "id": "%3By%5Em",
      "config": {
        "expression": "if(\n  empty({{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}),\n  {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n  if(\n    empty({{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}),\n    {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n    if(\n      dateBetween({{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"hours\") >= 2,\n      {{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n      {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n    )\n  )\n)"
      },
      "config_formatted": "Formula: `if(\n  empty({{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}),\n  {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n  if(\n    empty({{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}),\n    {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n    if(\n      dateBetween({{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"hours\") >= 2,\n      {{notion:block_property:vUD%5E:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n      {{notion:block_property:%3DT%5Bb:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n    )\n  )\n)`"
    },
    "setToDoneTime": {
      "type": "date",
      "id": "%3DT%5Bb",
      "config": {},
      "config_formatted": "Date field"
    },
    "Doing": {
      "type": "date",
      "id": "%3E%3CYb",
      "config": {},
      "config_formatted": "Date field"
    },
    "Parent item": {
      "type": "relation",
      "id": "%3FIHk",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Sub-item",
          "synced_property_id": "Pevu"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "\ud83e\uddee RELATIONS \ud83e\uddee": {
      "type": "rich_text",
      "id": "CXXp",
      "config": {},
      "config_formatted": ""
    },
    "Daily Metrics": {
      "type": "relation",
      "id": "IfLX",
      "config": {
        "database_id": "20425796-66bd-8171-92ad-da80f18fdf02",
        "data_source_id": "20425796-66bd-8174-b736-000b6b3508b0",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Tasks",
          "synced_property_id": "t%3BB%40"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-8171-92ad-da80f18fdf02"
    },
    "Task Type": {
      "type": "multi_select",
      "id": "JUdC",
      "config": {
        "options": [
          {
            "id": "12e4a2de-ef6e-4556-8577-b5453cc9a657",
            "name": "Meeting",
            "color": "blue",
            "description": null
          },
          {
            "id": "6e5f017a-4875-48a3-8b9d-2e6035548554",
            "name": "R&D",
            "color": "default",
            "description": null
          },
          {
            "id": "64f475ca-1d9a-4ed2-a22b-dda1c18ab327",
            "name": "coding",
            "color": "green",
            "description": null
          },
          {
            "id": "754647ad-521d-49e4-831b-4262f103d875",
            "name": "fixing",
            "color": "orange",
            "description": null
          },
          {
            "id": "98c694b3-6bd9-4199-82ff-267babfa257d",
            "name": "analysis",
            "color": "pink",
            "description": null
          },
          {
            "id": "97d36f43-2c53-4abb-b438-7381f1d10229",
            "name": "tests",
            "color": "purple",
            "description": null
          },
          {
            "id": "f208a29c-ac45-46b9-8634-1c41294b43bd",
            "name": "planning",
            "color": "brown",
            "description": null
          },
          {
            "id": "f113fa46-d69f-4778-aa60-925f9ef40d77",
            "name": "personal",
            "color": "red",
            "description": null
          },
          {
            "id": "4786712c-cf6e-449c-8c8c-f9c9772baf77",
            "name": "documentation",
            "color": "yellow",
            "description": null
          },
          {
            "id": "ffd1a0f0-b37a-4ddd-9c53-372e789b697b",
            "name": "deploy",
            "color": "purple",
            "description": null
          },
          {
            "id": "33e61c45-2c77-482a-8cef-cb4fc419bc01",
            "name": "cleanup",
            "color": "red",
            "description": null
          }
        ]
      },
      "config_formatted": "Options: Meeting, R&D, coding, fixing, analysis, tests, planning, personal, documentation, deploy, cleanup"
    },
    "Feature": {
      "type": "multi_select",
      "id": "KNjL",
      "config": {
        "options": [
          {
            "id": "6cd3eaf8-cc82-4b95-86c6-6780c5c3f2a8",
            "name": "auto calibration",
            "color": "red",
            "description": null
          },
          {
            "id": "4fe52da0-da45-40fd-8db1-93d6b70e30f4",
            "name": "beta customer engagement",
            "color": "default",
            "description": null
          },
          {
            "id": "ec0f01fb-6a69-4467-b120-3700982dcd88",
            "name": "bttc",
            "color": "green",
            "description": null
          },
          {
            "id": "d86dba78-2fd5-409f-9264-fd30cc690b21",
            "name": "habits",
            "color": "brown",
            "description": null
          },
          {
            "id": "7d87bc1a-3126-4c01-87d3-06fef5baa602",
            "name": "health",
            "color": "blue",
            "description": null
          },
          {
            "id": "b18f705b-f689-4d41-ae25-0ef62b697c0e",
            "name": "productivity",
            "color": "yellow",
            "description": null
          },
          {
            "id": "f9ec676a-d9f9-4720-99c8-d5370fe9b270",
            "name": "streamlit app",
            "color": "pink",
            "description": null
          }
        ]
      },
      "config_formatted": "Options: auto calibration, beta customer engagement, bttc, habits, health, productivity, streamlit app"
    },
    "\ud83c\udff4\u200d\u2620\ufe0f FLAGS\ud83c\udff4\u200d\u2620\ufe0f ": {
      "type": "rich_text",
      "id": "Kyet",
      "config": {},
      "config_formatted": ""
    },
    "\ud83e\udd16 SYSTEM \ud83e\udd16 ": {
      "type": "rich_text",
      "id": "M%3AOB",
      "config": {},
      "config_formatted": ""
    },
    "Related to Daily Productivity Metrics (Active Tasks)": {
      "type": "relation",
      "id": "N_v%3A",
      "config": {
        "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
        "data_source_id": "23525796-66bd-80bb-9d91-000b89804e1c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Active",
          "synced_property_id": "%5Bn~k"
        }
      },
      "config_formatted": "\u2192 Database: 23525796-66bd-8017-a464-c1a7d32d35c4"
    },
    "Sub-item": {
      "type": "relation",
      "id": "Pevu",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Parent item",
          "synced_property_id": "%3FIHk"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Related to Daily Productivity Metrics (Backlog)": {
      "type": "relation",
      "id": "UeWq",
      "config": {
        "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
        "data_source_id": "23525796-66bd-80bb-9d91-000b89804e1c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Backlog",
          "synced_property_id": "%5Ex%5Ey"
        }
      },
      "config_formatted": "\u2192 Database: 23525796-66bd-8017-a464-c1a7d32d35c4"
    },
    "Created time": {
      "type": "created_time",
      "id": "Yefl",
      "config": {},
      "config_formatted": ""
    },
    "\ud83d\udd27  FORMULA HELPERS \ud83d\udd27 ": {
      "type": "rich_text",
      "id": "%60Nwb",
      "config": {},
      "config_formatted": ""
    },
    "Planned Time (hrs)": {
      "type": "formula",
      "id": "axej",
      "config": {
        "expression": "{{notion:block_property:tfgh:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / 60"
      },
      "config_formatted": "Formula: `{{notion:block_property:tfgh:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / 60`"
    },
    "Planned Hrs.": {
      "type": "formula",
      "id": "ben%3A",
      "config": {
        "expression": "if({{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, dateBetween({{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.dateEnd(), {{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.dateStart(), \"hours\"), {{notion:block_property:axej:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}})"
      },
      "config_formatted": "Formula: `if({{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, dateBetween({{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.dateEnd(), {{notion:block_property:%3AP%3Fv:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.dateStart(), \"hours\"), {{notion:block_property:axej:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}})`"
    },
    "Archived Date": {
      "type": "date",
      "id": "cqf%3F",
      "config": {},
      "config_formatted": "Date field"
    },
    "Status": {
      "type": "status",
      "id": "dR%7Dm",
      "config": {
        "options": [
          {
            "id": "a53b3d91-1655-4589-9e85-10f3bf7c6ad2",
            "name": "todo",
            "color": "default",
            "description": null
          },
          {
            "id": "]gcF",
            "name": "backlog",
            "color": "brown",
            "description": null
          },
          {
            "id": "7e935533-c1e8-4542-ad4c-bd1375eaf0cc",
            "name": "doing",
            "color": "yellow",
            "description": null
          },
          {
            "id": "`M;A",
            "name": "paused",
            "color": "orange",
            "description": null
          },
          {
            "id": "0cbe2e97-0d37-4e8a-9585-fe7b34363b9f",
            "name": "done",
            "color": "green",
            "description": null
          },
          {
            "id": "PkoR",
            "name": "archived",
            "color": "red",
            "description": null
          }
        ],
        "groups": [
          {
            "id": "a3695232-9ba2-4e8c-9b4b-bde6123924ef",
            "name": "To-do",
            "color": "gray",
            "option_ids": [
              "]gcF",
              "a53b3d91-1655-4589-9e85-10f3bf7c6ad2"
            ]
          },
          {
            "id": "9a09caca-f1b9-463b-afb2-61e36be73083",
            "name": "In progress",
            "color": "blue",
            "option_ids": [
              "7e935533-c1e8-4542-ad4c-bd1375eaf0cc",
              "`M;A"
            ]
          },
          {
            "id": "18c917be-57a0-4d5d-9a42-80933e81c6a3",
            "name": "Complete",
            "color": "green",
            "option_ids": [
              "0cbe2e97-0d37-4e8a-9585-fe7b34363b9f",
              "PkoR"
            ]
          }
        ]
      },
      "config_formatted": "Groups: To-do, In progress, Complete | Options: todo, backlog, doing, paused, done, archived"
    },
    "Related to Daily Productivity Metrics (Archived)": {
      "type": "relation",
      "id": "fSjg",
      "config": {
        "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
        "data_source_id": "23525796-66bd-80bb-9d91-000b89804e1c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Archived",
          "synced_property_id": "KGI%3E"
        }
      },
      "config_formatted": "\u2192 Database: 23525796-66bd-8017-a464-c1a7d32d35c4"
    },
    "Create Entry": {
      "type": "button",
      "id": "hKX%3A",
      "config": {},
      "config_formatted": ""
    },
    "Projects": {
      "type": "relation",
      "id": "mc%3Ai",
      "config": {
        "database_id": "20425796-66bd-8147-a8cc-ebe5658fbdda",
        "data_source_id": "20425796-66bd-81ed-93bc-000bb7605825",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Tasks V2",
          "synced_property_id": "%5BDLE"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-8147-a8cc-ebe5658fbdda"
    },
    "Time Blocks": {
      "type": "relation",
      "id": "nDsi",
      "config": {
        "database_id": "22825796-66bd-803d-b27d-e8b6b6938b26",
        "data_source_id": "22825796-66bd-8009-92e6-000ba8763a5c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Task",
          "synced_property_id": "guM%5E"
        }
      },
      "config_formatted": "\u2192 Database: 22825796-66bd-803d-b27d-e8b6b6938b26"
    },
    "Logged Time (hrs)": {
      "type": "formula",
      "id": "pGr%5E",
      "config": {
        "expression": "{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:CDEJ:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum() / 60"
      },
      "config_formatted": "Formula: `{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:CDEJ:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum() / 60`"
    },
    "Related to Daily Productivity Metrics (Planned Tasks)": {
      "type": "relation",
      "id": "si%5E%3C",
      "config": {
        "database_id": "23525796-66bd-8017-a464-c1a7d32d35c4",
        "data_source_id": "23525796-66bd-80bb-9d91-000b89804e1c",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Planned",
          "synced_property_id": "M~KU"
        }
      },
      "config_formatted": "\u2192 Database: 23525796-66bd-8017-a464-c1a7d32d35c4"
    },
    "Planned Time (mins)": {
      "type": "rollup",
      "id": "tfgh",
      "config": {
        "rollup_property_name": "Duration (mins)",
        "relation_property_name": "Time Blocks",
        "rollup_property_id": "CtF^",
        "relation_property_id": "nDsi",
        "function": "sum"
      },
      "config_formatted": "From: Time Blocks.Duration (mins) | Function: sum"
    },
    "Time Entries": {
      "type": "relation",
      "id": "tvv%5C",
      "config": {
        "database_id": "20425796-66bd-8143-b976-eff463de13da",
        "data_source_id": "20425796-66bd-8106-903f-000b75285f6d",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Task",
          "synced_property_id": "uAj%40"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-8143-b976-eff463de13da"
    },
    "lastTimeEntryEnd": {
      "type": "formula",
      "id": "vUD%5E",
      "config": {
        "expression": "{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n    .sort(current.{{notion:block_property:fY%5Er:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}})\n    .last()\n    .{{notion:block_property:fY%5Er:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} "
      },
      "config_formatted": "Formula: `{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n    .sort(current.{{notion:block_property:fY%5Er:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}})\n    .last()\n    .{{notion:block_property:fY%5Er:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} `"
    },
    "Due": {
      "type": "date",
      "id": "y%3B%3EJ",
      "config": {},
      "config_formatted": "Date field"
    },
    "\u23f0 PLANNING \u23f0": {
      "type": "rich_text",
      "id": "yM%5Cd",
      "config": {},
      "config_formatted": ""
    },
    "Logged Time (mins)": {
      "type": "formula",
      "id": "yXe%5B",
      "config": {
        "expression": "{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:CDEJ:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()"
      },
      "config_formatted": "Formula: `{{notion:block_property:tvv%5C:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:CDEJ:20425796-66bd-8143-b976-eff463de13da:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum()`"
    },
    "\ud83d\udcdd BASIC INFO \ud83d\udcdd": {
      "type": "rich_text",
      "id": "ywLB",
      "config": {},
      "config_formatted": ""
    },
    "\ud83d\udcca AUTO METRICS \ud83d\udcca ": {
      "type": "rich_text",
      "id": "%7CoLE",
      "config": {},
      "config_formatted": ""
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
