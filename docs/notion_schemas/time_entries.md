# Time Entries - Schema

**Database Name:** Time Entries
**Database ID:** `20425796-66bd-8143-b976-eff463de13da`
**Last Updated:** 2026-01-19 13:24:55

## Properties

| Property Name | Type | Configuration |
|---------------|------|---------------|
| Created Today | formula | Formula: `formatDate({{notion:block_property:%60_Hd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, "YYYY-MM-DD") == formatDate(now(), "YYYY-MM-DD")` |
| End | date | Date field |
| Language | select | Options: ABAP, ABC, Agda, Arduino, ASCII Art, Assembly, Bash, BASIC, BNF, C, C#, C++, Clojure, CoffeeScript, Coq, CSS, Dart, Dhall, Diff, Docker, EBNF, Elixir, Elm, Erlang, F#, Flow, Fortran, Gherkin, GLSL, Go, GraphQL, Groovy, Haskell, HCL, HTML, Idris, Java, JavaScript, JSON, Julia, Kotlin, LaTeX, Less, Lisp, LiveScript, LLVM IR, Lua, Makefile, Markdown, Markup, MATLAB, Mathematica, Mermaid, Nix, Notion Formula, Objective-C, OCaml, Pascal, Perl, PHP, Plain Text, PowerShell, Prolog, Protobuf, PureScript, Python, R, Racket, Reason, Ruby, Rust, Sass, Scala, Scheme, Scss, Shell, Smalltalk, Solidity, SQL, Swift, TOML, TypeScript, VB.Net, Verilog, VHDL, Visual Basic, WebAssembly, XML, YAML, Java/C/C++/C#, NotionScript |
| Name | title | - |
| Start | date | Date field |
| Stop Timer | button | - |
| Task | relation | → Database: 20425796-66bd-81f5-b759-e03fe4eb42f2 |
| Timer Status | formula | Formula: `if(
	{{notion:block_property:fY%5Er:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.empty(),
  style(style("⏱️ Timer Running", "green"), "b"),
	style(style( "🛑 Timer Stopped", "red"), "b")
)` |
| comments | rich_text | - |
| mins | formula | Formula: `dateBetween({{notion:block_property:fY%5Er:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},{{notion:block_property:%60_Hd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, "minutes")` |


## Raw Schema (JSON)

<details>
<summary>Click to expand full schema JSON</summary>

```json
{
  "name": "Time Entries",
  "database_id": "20425796-66bd-8143-b976-eff463de13da",
  "title": "Time Entries",
  "description": "",
  "properties": {
    "mins": {
      "type": "formula",
      "id": "CDEJ",
      "config": {
        "expression": "dateBetween({{notion:block_property:fY%5Er:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},{{notion:block_property:%60_Hd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"minutes\")"
      },
      "config_formatted": "Formula: `dateBetween({{notion:block_property:fY%5Er:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}},{{notion:block_property:%60_Hd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"minutes\")`"
    },
    "Created Today": {
      "type": "formula",
      "id": "WZt~",
      "config": {
        "expression": "formatDate({{notion:block_property:%60_Hd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"YYYY-MM-DD\") == formatDate(now(), \"YYYY-MM-DD\")"
      },
      "config_formatted": "Formula: `formatDate({{notion:block_property:%60_Hd:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}, \"YYYY-MM-DD\") == formatDate(now(), \"YYYY-MM-DD\")`"
    },
    "Start": {
      "type": "date",
      "id": "%60_Hd",
      "config": {},
      "config_formatted": "Date field"
    },
    "End": {
      "type": "date",
      "id": "fY%5Er",
      "config": {},
      "config_formatted": "Date field"
    },
    "comments": {
      "type": "rich_text",
      "id": "jFH%3E",
      "config": {},
      "config_formatted": ""
    },
    "Stop Timer": {
      "type": "button",
      "id": "lRAl",
      "config": {},
      "config_formatted": ""
    },
    "Timer Status": {
      "type": "formula",
      "id": "nN%3Ba",
      "config": {
        "expression": "if(\n\t{{notion:block_property:fY%5Er:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.empty(),\n  style(style(\"\u23f1\ufe0f Timer Running\", \"green\"), \"b\"),\n\tstyle(style( \"\ud83d\uded1 Timer Stopped\", \"red\"), \"b\")\n)"
      },
      "config_formatted": "Formula: `if(\n\t{{notion:block_property:fY%5Er:00000000-0000-0000-0000-000000000000:9d802d7a-a3dc-49fb-bb44-062c1e2e23d0}}.empty(),\n  style(style(\"\u23f1\ufe0f Timer Running\", \"green\"), \"b\"),\n\tstyle(style( \"\ud83d\uded1 Timer Stopped\", \"red\"), \"b\")\n)`"
    },
    "Task": {
      "type": "relation",
      "id": "uAj%40",
      "config": {
        "database_id": "20425796-66bd-81f5-b759-e03fe4eb42f2",
        "data_source_id": "20425796-66bd-819c-9134-000b3a96a7b5",
        "type": "dual_property",
        "dual_property": {
          "synced_property_name": "Time Entries",
          "synced_property_id": "tvv%5C"
        }
      },
      "config_formatted": "\u2192 Database: 20425796-66bd-81f5-b759-e03fe4eb42f2"
    },
    "Name": {
      "type": "title",
      "id": "title",
      "config": {},
      "config_formatted": ""
    },
    "Language": {
      "type": "select",
      "id": "7f69c2a8-0ed0-4705-a803-b7ce74d842fb",
      "config": {
        "options": [
          {
            "id": "ABAP",
            "name": "ABAP",
            "color": "green",
            "description": null
          },
          {
            "id": "ABC",
            "name": "ABC",
            "color": "pink",
            "description": null
          },
          {
            "id": "Agda",
            "name": "Agda",
            "color": "default",
            "description": null
          },
          {
            "id": "Arduino",
            "name": "Arduino",
            "color": "yellow",
            "description": null
          },
          {
            "id": "ASCII Art",
            "name": "ASCII Art",
            "color": "gray",
            "description": null
          },
          {
            "id": "Assembly",
            "name": "Assembly",
            "color": "orange",
            "description": null
          },
          {
            "id": "Bash",
            "name": "Bash",
            "color": "red",
            "description": null
          },
          {
            "id": "BASIC",
            "name": "BASIC",
            "color": "blue",
            "description": null
          },
          {
            "id": "BNF",
            "name": "BNF",
            "color": "brown",
            "description": null
          },
          {
            "id": "C",
            "name": "C",
            "color": "purple",
            "description": null
          },
          {
            "id": "C#",
            "name": "C#",
            "color": "brown",
            "description": null
          },
          {
            "id": "C++",
            "name": "C++",
            "color": "red",
            "description": null
          },
          {
            "id": "Clojure",
            "name": "Clojure",
            "color": "orange",
            "description": null
          },
          {
            "id": "CoffeeScript",
            "name": "CoffeeScript",
            "color": "green",
            "description": null
          },
          {
            "id": "Coq",
            "name": "Coq",
            "color": "gray",
            "description": null
          },
          {
            "id": "CSS",
            "name": "CSS",
            "color": "brown",
            "description": null
          },
          {
            "id": "Dart",
            "name": "Dart",
            "color": "default",
            "description": null
          },
          {
            "id": "Dhall",
            "name": "Dhall",
            "color": "purple",
            "description": null
          },
          {
            "id": "Diff",
            "name": "Diff",
            "color": "red",
            "description": null
          },
          {
            "id": "Docker",
            "name": "Docker",
            "color": "red",
            "description": null
          },
          {
            "id": "EBNF",
            "name": "EBNF",
            "color": "pink",
            "description": null
          },
          {
            "id": "Elixir",
            "name": "Elixir",
            "color": "orange",
            "description": null
          },
          {
            "id": "Elm",
            "name": "Elm",
            "color": "brown",
            "description": null
          },
          {
            "id": "Erlang",
            "name": "Erlang",
            "color": "gray",
            "description": null
          },
          {
            "id": "F#",
            "name": "F#",
            "color": "purple",
            "description": null
          },
          {
            "id": "Flow",
            "name": "Flow",
            "color": "default",
            "description": null
          },
          {
            "id": "Fortran",
            "name": "Fortran",
            "color": "yellow",
            "description": null
          },
          {
            "id": "Gherkin",
            "name": "Gherkin",
            "color": "default",
            "description": null
          },
          {
            "id": "GLSL",
            "name": "GLSL",
            "color": "purple",
            "description": null
          },
          {
            "id": "Go",
            "name": "Go",
            "color": "green",
            "description": null
          },
          {
            "id": "GraphQL",
            "name": "GraphQL",
            "color": "green",
            "description": null
          },
          {
            "id": "Groovy",
            "name": "Groovy",
            "color": "red",
            "description": null
          },
          {
            "id": "Haskell",
            "name": "Haskell",
            "color": "pink",
            "description": null
          },
          {
            "id": "HCL",
            "name": "HCL",
            "color": "blue",
            "description": null
          },
          {
            "id": "HTML",
            "name": "HTML",
            "color": "orange",
            "description": null
          },
          {
            "id": "Idris",
            "name": "Idris",
            "color": "orange",
            "description": null
          },
          {
            "id": "Java",
            "name": "Java",
            "color": "red",
            "description": null
          },
          {
            "id": "JavaScript",
            "name": "JavaScript",
            "color": "pink",
            "description": null
          },
          {
            "id": "JSON",
            "name": "JSON",
            "color": "orange",
            "description": null
          },
          {
            "id": "Julia",
            "name": "Julia",
            "color": "gray",
            "description": null
          },
          {
            "id": "Kotlin",
            "name": "Kotlin",
            "color": "default",
            "description": null
          },
          {
            "id": "LaTeX",
            "name": "LaTeX",
            "color": "yellow",
            "description": null
          },
          {
            "id": "Less",
            "name": "Less",
            "color": "pink",
            "description": null
          },
          {
            "id": "Lisp",
            "name": "Lisp",
            "color": "brown",
            "description": null
          },
          {
            "id": "LiveScript",
            "name": "LiveScript",
            "color": "gray",
            "description": null
          },
          {
            "id": "LLVM IR",
            "name": "LLVM IR",
            "color": "orange",
            "description": null
          },
          {
            "id": "Lua",
            "name": "Lua",
            "color": "default",
            "description": null
          },
          {
            "id": "Makefile",
            "name": "Makefile",
            "color": "pink",
            "description": null
          },
          {
            "id": "Markdown",
            "name": "Markdown",
            "color": "gray",
            "description": null
          },
          {
            "id": "Markup",
            "name": "Markup",
            "color": "brown",
            "description": null
          },
          {
            "id": "MATLAB",
            "name": "MATLAB",
            "color": "yellow",
            "description": null
          },
          {
            "id": "Mathematica",
            "name": "Mathematica",
            "color": "gray",
            "description": null
          },
          {
            "id": "Mermaid",
            "name": "Mermaid",
            "color": "green",
            "description": null
          },
          {
            "id": "Nix",
            "name": "Nix",
            "color": "gray",
            "description": null
          },
          {
            "id": "Notion Formula",
            "name": "Notion Formula",
            "color": "red",
            "description": null
          },
          {
            "id": "Objective-C",
            "name": "Objective-C",
            "color": "green",
            "description": null
          },
          {
            "id": "OCaml",
            "name": "OCaml",
            "color": "brown",
            "description": null
          },
          {
            "id": "Pascal",
            "name": "Pascal",
            "color": "red",
            "description": null
          },
          {
            "id": "Perl",
            "name": "Perl",
            "color": "brown",
            "description": null
          },
          {
            "id": "PHP",
            "name": "PHP",
            "color": "purple",
            "description": null
          },
          {
            "id": "Plain Text",
            "name": "Plain Text",
            "color": "default",
            "description": null
          },
          {
            "id": "PowerShell",
            "name": "PowerShell",
            "color": "default",
            "description": null
          },
          {
            "id": "Prolog",
            "name": "Prolog",
            "color": "purple",
            "description": null
          },
          {
            "id": "Protobuf",
            "name": "Protobuf",
            "color": "gray",
            "description": null
          },
          {
            "id": "PureScript",
            "name": "PureScript",
            "color": "pink",
            "description": null
          },
          {
            "id": "Python",
            "name": "Python",
            "color": "gray",
            "description": null
          },
          {
            "id": "R",
            "name": "R",
            "color": "yellow",
            "description": null
          },
          {
            "id": "Racket",
            "name": "Racket",
            "color": "brown",
            "description": null
          },
          {
            "id": "Reason",
            "name": "Reason",
            "color": "green",
            "description": null
          },
          {
            "id": "Ruby",
            "name": "Ruby",
            "color": "brown",
            "description": null
          },
          {
            "id": "Rust",
            "name": "Rust",
            "color": "orange",
            "description": null
          },
          {
            "id": "Sass",
            "name": "Sass",
            "color": "green",
            "description": null
          },
          {
            "id": "Scala",
            "name": "Scala",
            "color": "brown",
            "description": null
          },
          {
            "id": "Scheme",
            "name": "Scheme",
            "color": "orange",
            "description": null
          },
          {
            "id": "Scss",
            "name": "Scss",
            "color": "pink",
            "description": null
          },
          {
            "id": "Shell",
            "name": "Shell",
            "color": "orange",
            "description": null
          },
          {
            "id": "Smalltalk",
            "name": "Smalltalk",
            "color": "orange",
            "description": null
          },
          {
            "id": "Solidity",
            "name": "Solidity",
            "color": "gray",
            "description": null
          },
          {
            "id": "SQL",
            "name": "SQL",
            "color": "blue",
            "description": null
          },
          {
            "id": "Swift",
            "name": "Swift",
            "color": "blue",
            "description": null
          },
          {
            "id": "TOML",
            "name": "TOML",
            "color": "purple",
            "description": null
          },
          {
            "id": "TypeScript",
            "name": "TypeScript",
            "color": "pink",
            "description": null
          },
          {
            "id": "VB.Net",
            "name": "VB.Net",
            "color": "orange",
            "description": null
          },
          {
            "id": "Verilog",
            "name": "Verilog",
            "color": "gray",
            "description": null
          },
          {
            "id": "VHDL",
            "name": "VHDL",
            "color": "yellow",
            "description": null
          },
          {
            "id": "Visual Basic",
            "name": "Visual Basic",
            "color": "purple",
            "description": null
          },
          {
            "id": "WebAssembly",
            "name": "WebAssembly",
            "color": "brown",
            "description": null
          },
          {
            "id": "XML",
            "name": "XML",
            "color": "orange",
            "description": null
          },
          {
            "id": "YAML",
            "name": "YAML",
            "color": "pink",
            "description": null
          },
          {
            "id": "Java/C/C++/C#",
            "name": "Java/C/C++/C#",
            "color": "gray",
            "description": null
          },
          {
            "id": "NotionScript",
            "name": "NotionScript",
            "color": "red",
            "description": null
          }
        ]
      },
      "config_formatted": "Options: ABAP, ABC, Agda, Arduino, ASCII Art, Assembly, Bash, BASIC, BNF, C, C#, C++, Clojure, CoffeeScript, Coq, CSS, Dart, Dhall, Diff, Docker, EBNF, Elixir, Elm, Erlang, F#, Flow, Fortran, Gherkin, GLSL, Go, GraphQL, Groovy, Haskell, HCL, HTML, Idris, Java, JavaScript, JSON, Julia, Kotlin, LaTeX, Less, Lisp, LiveScript, LLVM IR, Lua, Makefile, Markdown, Markup, MATLAB, Mathematica, Mermaid, Nix, Notion Formula, Objective-C, OCaml, Pascal, Perl, PHP, Plain Text, PowerShell, Prolog, Protobuf, PureScript, Python, R, Racket, Reason, Ruby, Rust, Sass, Scala, Scheme, Scss, Shell, Smalltalk, Solidity, SQL, Swift, TOML, TypeScript, VB.Net, Verilog, VHDL, Visual Basic, WebAssembly, XML, YAML, Java/C/C++/C#, NotionScript"
    }
  }
}
```

</details>
