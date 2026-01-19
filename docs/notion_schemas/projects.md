# Projects - Schema

**Database Name:** Projects
**Database ID:** `2042579666bd8147a8ccebe5658fbdda`
**Last Updated:** 2026-01-19 13:24:56

## Description

This simplified database contains only time-tracking features. The 

## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
| Progress | formula | Formula: `lets(
  total,
  {{notion:block_property:qHqi:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} + {{notion:block_property:FGyJ:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},

  fractionClosed,
  if(
    total == 0,
    0,  /* avoid dividing by zero */
    {{notion:block_property:FGyJ:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / total
  ),

  /* Build the bar: '◼' for closed portion, '◻' for the remainder. */
  barClosed,
  substring("◻◻◻◻◻◻◻◻◻◻", 0, round(fractionClosed * 10)),
  barOpen,
  substring("◼◼◼◼◼◼◼◼◼◼", 0, 10 - round(fractionClosed * 10)),

  /* Combine them and add the % figure. */
  barClosed + barOpen + " " + format(round(fractionClosed * 100)) + "%"
)
` |
| Project | title | - |
| Project Time Entries | relation | → Database: 20425796-66bd-8131-b2f9-cbc9f8c78265 |
| Project Type | select | Options: Personal, Work, Project, Resources |
| Status | status | Groups: To-do, In progress, Complete | Options: Planned, Active, Complete |
| Task Hours | rollup | From: Tasks.Time Entries | Function: show_original |
| Tasks | relation | → Database: 20425796-66bd-81bf-87fd-fc4847c70fa5 |
| Tasks V2 | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Timer | button | - |
| Total Hrs. | rollup | From: Project Time Entries.OLD Total Hrs. | Function: sum |
| Total Project Hours | formula | Formula: `{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum().divide(60).multiply(100).round().divide(100)+" hrs"` |
| closed tasks | formula | Formula: `{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}
  .filter(
    current.{{notion:block_property:dR%7Dm:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == "done"
  )
  .length()` |
| open tasks | formula | Formula: `{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}
  .filter(
    current.{{notion:block_property:dR%7Dm:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} != "done"
  )
  .length()` |


## Raw Schema (JSON)

<details>
<summary>Click to expand full schema JSON</summary>

```json
{
  "name": "Projects",
  "database_id": "2042579666bd8147a8ccebe5658fbdda",
  "title": "Projects",
  "description": "This simplified database contains only time-tracking features. The ",
  "properties": {
    "closed tasks": {
      "type": "formula",
      "id": "FGyJ",
      "config": {
        "expression": "{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n  .filter(\n    current.{{notion:block_property:dR%7Dm:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"done\"\n  )\n  .length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n  .filter(\n    current.{{notion:block_property:dR%7Dm:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} == \"done\"\n  )\n  .length()`"
    },
    "Progress": {
      "type": "formula",
      "id": "JfIW",
      "config": {
        "expression": "lets(\n  total,\n  {{notion:block_property:qHqi:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} + {{notion:block_property:FGyJ:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n\n  fractionClosed,\n  if(\n    total == 0,\n    0,  /* avoid dividing by zero */\n    {{notion:block_property:FGyJ:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / total\n  ),\n\n  /* Build the bar: '\u25fc' for closed portion, '\u25fb' for the remainder. */\n  barClosed,\n  substring(\"\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\", 0, round(fractionClosed * 10)),\n  barOpen,\n  substring(\"\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\", 0, 10 - round(fractionClosed * 10)),\n\n  /* Combine them and add the % figure. */\n  barClosed + barOpen + \" \" + format(round(fractionClosed * 100)) + \"%\"\n)\n"
      },
      "config_formatted": "Formula: `lets(\n  total,\n  {{notion:block_property:qHqi:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} + {{notion:block_property:FGyJ:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},\n\n  fractionClosed,\n  if(\n    total == 0,\n    0,  /* avoid dividing by zero */\n    {{notion:block_property:FGyJ:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} / total\n  ),\n\n  /* Build the bar: '\u25fc' for closed portion, '\u25fb' for the remainder. */\n  barClosed,\n  substring(\"\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\u25fb\", 0, round(fractionClosed * 10)),\n  barOpen,\n  substring(\"\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\u25fc\", 0, 10 - round(fractionClosed * 10)),\n\n  /* Combine them and add the % figure. */\n  barClosed + barOpen + \" \" + format(round(fractionClosed * 100)) + \"%\"\n)\n`"
    },
    "Tasks": {
      "type": "relation",
      "id": "JgRZ",
      "config": {
        "database_id": "20425796-66bd-81bf-87fd-fc4847c70fa5",
        "data_source_id": "20425796-66bd-8134-9b41-000b4a999853",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Project",
          "synced_property_id": "i%7D%60_"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81bf-87fd-fc4847c70fa5"
    },
    "Task Hours": {
      "type": "rollup",
      "id": "NbKh",
      "config": {
        "rollup_property_name": "Time Entries",
        "relation_property_name": "Tasks",
        "rollup_property_id": "kb|@",
        "relation_property_id": "JgRZ",
        "function": "show_original"
      },
      "config_formatted": "From: Tasks.Time Entries | Function: show_original"
    },
    "Total Project Hours": {
      "type": "formula",
      "id": "O%3F_t",
      "config": {
        "expression": "{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum().divide(60).multiply(100).round().divide(100)+\" hrs\""
      },
      "config_formatted": "Formula: `{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.map(current.{{notion:block_property:pGr%5E:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}).sum().divide(60).multiply(100).round().divide(100)+\" hrs\"`"
    },
    "Project Time Entries": {
      "type": "relation",
      "id": "PNX%3F",
      "config": {
        "database_id": "20425796-66bd-8131-b2f9-cbc9f8c78265",
        "data_source_id": "20425796-66bd-8167-9b23-000b707c10f5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Project",
          "synced_property_id": "IZu%3D"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-8131-b2f9-cbc9f8c78265"
    },
    "Tasks V2": {
      "type": "relation",
      "id": "%5BDLE",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Projects",
          "synced_property_id": "mc%3Ai"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Status": {
      "type": "status",
      "id": "%5EW~%7B",
      "config": {
        "options": [
          {
            "id": "77f409c2-3408-4a24-8eb2-1286d088420a",
            "name": "Planned",
            "color": "blue",
            "description": null
          },
          {
            "id": "6906cfba-6346-4b21-b058-278eb0f0f6e9",
            "name": "Active",
            "color": "yellow",
            "description": null
          },
          {
            "id": "54f157d3-ad6b-4193-aed4-3f2cfad06b20",
            "name": "Complete",
            "color": "green",
            "description": null
          }
        ],
        "groups": [
          {
            "id": "01b8a77e-8cfe-4065-907b-f598e581203c",
            "name": "To-do",
            "color": "gray",
            "option_ids": [
              "77f409c2-3408-4a24-8eb2-1286d088420a"
            ]
          },
          {
            "id": "e0ff59db-16d9-4a07-b68e-2282423a644c",
            "name": "In progress",
            "color": "blue",
            "option_ids": [
              "6906cfba-6346-4b21-b058-278eb0f0f6e9"
            ]
          },
          {
            "id": "8e12ea55-ae53-4e7f-9557-ce9b587dd97c",
            "name": "Complete",
            "color": "green",
            "option_ids": [
              "54f157d3-ad6b-4193-aed4-3f2cfad06b20"
            ]
          }
        ]
      },
      "config_formatted": "Groups: To-do, In progress, Complete | Options: Planned, Active, Complete"
    },
    "Total Hrs.": {
      "type": "rollup",
      "id": "guDB",
      "config": {
        "rollup_property_name": "OLD Total Hrs.",
        "relation_property_name": "Project Time Entries",
        "rollup_property_id": "lhdn",
        "relation_property_id": "PNX?",
        "function": "sum"
      },
      "config_formatted": "From: Project Time Entries.OLD Total Hrs. | Function: sum"
    },
    "open tasks": {
      "type": "formula",
      "id": "qHqi",
      "config": {
        "expression": "{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n  .filter(\n    current.{{notion:block_property:dR%7Dm:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} != \"done\"\n  )\n  .length()"
      },
      "config_formatted": "Formula: `{{notion:block_property:%5BDLE:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}\n  .filter(\n    current.{{notion:block_property:dR%7Dm:20425796-66bd-81f5-b759-e03fe4eb42f2:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}} != \"done\"\n  )\n  .length()`"
    },
    "Timer": {
      "type": "button",
      "id": "uQDy",
      "config": {},
      "config_formatted": ""
    },
    "Project Type": {
      "type": "select",
      "id": "wYC%60",
      "config": {
        "options": [
          {
            "id": "QA<M",
            "name": "Personal",
            "color": "purple",
            "description": null
          },
          {
            "id": "IgZX",
            "name": "Work",
            "color": "brown",
            "description": null
          },
          {
            "id": "stlM",
            "name": "Project",
            "color": "green",
            "description": null
          },
          {
            "id": "q^mT",
            "name": "Resources",
            "color": "gray",
            "description": null
          }
        ]
      },
      "config_formatted": "Options: Personal, Work, Project, Resources"
    },
    "Project": {
      "type": "title",
      "id": "title",
      "config": {},
      "config_formatted": ""
    }
  }
}
```

</details>
