# Health Module

Syncs workout and health data from mobile apps to Notion.

## Data Flow

```
[Data Sources]                    [Parsing]                      [Processing]                [Output]

Gymaholic CSV ──────────────► GymaholicParser ─────┐
                                                   ├──► WorkoutMerger ──► HealthNotionSync ──► Notion Workouts DB
HealthAutoExport JSON ──────► HealthAutoExportParser ─┘       │                │
                                                              │                └──► Habit Tracker (checkboxes)
HealthAutoExport JSON ──────► HealthAutoExportMetricsParser ──┴──────────────────► Habit Tracker (metrics)
```

## Components

### Entry Point
- **`sync_orchestrator.py`** - Coordinates all sync operations. Called by the daemon.

### Parsers (`parsers/`)
| Parser | Input | Output |
|--------|-------|--------|
| `GymaholicParser` | CSV (semicolon-delimited) | `WorkoutData` with exercises |
| `HealthAutoExportParser` | JSON with workout array | `WorkoutData` with heart rate/calories |
| `HealthAutoExportMetricsParser` | JSON with daily metrics | `DailyActivityMetrics` (steps, weight, etc.) |

### Processing
- **`workout_merger.py`** - Merges same-day workouts from different sources (Gymaholic exercises + Apple Health heart rate)
- **`reconciliation.py`** - Detects and skips duplicate workouts already in Notion

### Notion Sync
- **`notion_sync.py`** - Creates/updates Notion pages in Workouts DB and Habit Tracker

### Models
- **`models.py`** - Data classes: `WorkoutData`, `ExerciseData`, `DailyActivityMetrics`, `HealthMetric`

## Timezone Handling

All parsers convert to UTC for storage:
- **HealthAutoExport**: Parses timezone offset from data (e.g., `-0800`) and converts to UTC
- **Gymaholic**: Assumes device local time (PST) and converts to UTC
