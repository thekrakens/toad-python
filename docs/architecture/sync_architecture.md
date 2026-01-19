# TOAD Sync Architecture

**Last Updated:** 2026-01-19
**Version:** v0.2.0

---

## Overview

TOAD uses a modular sync architecture with separate flows for **Productivity** and **Health** data. Both modules share common infrastructure (`notion_client.py`, `sync_cache.py`) but have module-specific orchestrators and logic.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI Entry Point                            │
│                   toad/cli.py                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Commands:                                                       │
│  • toad sync productivity [dates] [--dry-run]                   │
│  • toad sync health [dates] [--dry-run] [--full]                │
│  • toad sync all                                                 │
│                                                                  │
└───────────┬──────────────────────────┬──────────────────────────┘
            │                          │
            ↓                          ↓
┌───────────────────────┐   ┌──────────────────────────┐
│ PRODUCTIVITY MODULE   │   │   HEALTH MODULE          │
│ toad/productivity/    │   │   toad/health/           │
└───────────────────────┘   └──────────────────────────┘
```

---

## Common Infrastructure

### 1. TOADNotionClient (`toad/notion_client.py`)

**Purpose:** Centralized Notion API wrapper with smart update capabilities

**Key Methods:**
```python
# Read operations
query_database(database_id, filter, sorts)
get_page(page_id)
get_page_property(page_id, property_id)

# Write operations
update_page_properties_smart(page_id, properties)  # Only updates changed fields
get_or_create_page(database_id, query_property, query_value, create_properties)

# Block operations
get_blocks(page_id)
append_blocks(page_id, blocks)
```

**Smart Batching:**
- Compares existing vs new properties
- Only updates fields that changed
- Returns audit trail (updated_fields, unchanged_fields, changes)

---

### 2. SyncCache (`toad/sync_cache.py`)

**Purpose:** Track last sync times for incremental syncing

**Storage:** `~/.toad/sync_cache.json`

**Structure:**
```json
{
  "tasks": "2026-01-19T00:13:14.687030",
  "time_entries": "2026-01-19T00:13:14.690356",
  "health_workouts": "2026-01-18T23:45:00.000000"
}
```

**Usage:**
```python
# Get last sync time
last_sync = cache.get_last_sync('tasks')

# Update after successful sync
cache.update_last_sync('tasks')
```

---

## Productivity Module Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Productivity Sync Flow                          │
└─────────────────────────────────────────────────────────────────┘

CLI: toad sync productivity [date]
  │
  ↓
┌──────────────────────────────────────────────────┐
│ 1. Data Extraction                               │
│    toad/productivity/data_extractor.py           │
├──────────────────────────────────────────────────┤
│                                                   │
│ extract_task_data(last_modified_since)           │
│   → Query Tasks database                         │
│   → Filter by last_modified > cache timestamp    │
│   → Return DataFrame with task properties        │
│                                                   │
│ extract_time_entry_data(last_modified_since)     │
│   → Query Time Entries database                  │
│   → Filter by last_modified > cache timestamp    │
│   → Return DataFrame with time entry properties  │
│                                                   │
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 2. Relation Processing                           │
│    toad/productivity/task_relations.py           │
├──────────────────────────────────────────────────┤
│                                                   │
│ For each date:                                   │
│   categorize_tasks(tasks_df, date)               │
│     → Planned: task.Planned == date              │
│     → Active: task.Doing == date                 │
│     → Worked: task has TimeEntry on date         │
│     → Done: task.Done == date                    │
│                                                   │
│   update_daily_metrics(date, task_lists)         │
│     → Find/create Daily Metrics entry            │
│     → Update Planned relation                    │
│     → Update Active relation                     │
│     → Update Worked relation                     │
│     → Update Done relation                       │
│                                                   │
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 3. Notion Update (via TOADNotionClient)          │
├──────────────────────────────────────────────────┤
│                                                   │
│ • Create Daily Metrics page if doesn't exist     │
│ • Update task relations (smart batching)         │
│ • Cache updated with new sync timestamp          │
│                                                   │
└──────────────────────────────────────────────────┘
```

### Module Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `data_extractor.py` | Pull task & time entry data from Notion | `extract_task_data()`, `extract_time_entry_data()` |
| `task_relations.py` | Categorize tasks and update Daily Metrics | `categorize_tasks()`, `update_daily_metrics()` |

**No Orchestrator:** Productivity sync is simple enough to be called directly from CLI.

---

## Health Module Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Health Sync Flow                             │
└─────────────────────────────────────────────────────────────────┘

CLI: toad sync health [dates] [--dry-run] [--full]
  │
  ↓
┌──────────────────────────────────────────────────────────────┐
│ 1. Orchestration Layer                                       │
│    toad/health/sync_orchestrator.py                          │
│    HealthSyncOrchestrator                                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ sync_date_range(start_date, end_date):                       │
│                                                               │
│   For each date in range:                                    │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 1: Parse Gymaholic CSVs                        │  │
│   │   - Scan inbox/gymaholic/*.csv                      │  │
│   │   - Filter by date range                            │  │
│   │   - Parse with GymaholicParser                      │  │
│   │   → List[WorkoutData] with exercises                │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 2: Parse HealthAutoExport Activity             │  │
│   │   - Read TOAD_Activity/HealthAutoExport-{date}.json │  │
│   │   - Parse with HealthAutoExportMetricsParser        │  │
│   │   → DailyActivityMetrics (cals, weight, bf%)        │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 3: Parse HealthAutoExport Workouts             │  │
│   │   - Read TOAD_workouts/HealthAutoExport-{date}.json │  │
│   │   - Parse with HealthAutoExportParser               │  │
│   │   → List[WorkoutData] (cardio, with IDs)            │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 4: Merge Workouts                              │  │
│   │   - WorkoutMerger.merge_workouts_for_day()          │  │
│   │   - Match Gymaholic + HealthAutoExport by:          │  │
│   │     • Same date (±30min window)                     │  │
│   │     • Same/equivalent type                          │  │
│   │   - Gymaholic = primary (exercises)                 │  │
│   │   - HealthAutoExport = enrich (HR, cals)            │  │
│   │   → List[WorkoutData] merged                        │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 5: Sync to Notion                              │  │
│   │   - _sync_activity_metrics()                        │  │
│   │   - _sync_merged_workouts()                         │  │
│   │     → Calls HealthNotionSync methods                │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 6: Move Processed Files                        │  │
│   │   - Move Gymaholic CSVs to processed/gymaholic/     │  │
│   │   - HealthAutoExport files stay (tracked by ID)     │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
│ After all dates processed:                                   │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ Step 7: Health Stats ETL                            │  │
│   │   - sync_health_stats_for_date_range()              │  │
│   │     → Calls HealthNotionSync ETL methods            │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────┬──────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. Notion Sync Layer                                         │
│    toad/health/notion_sync.py                                │
│    HealthNotionSync                                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Activity Metrics:                                            │
│   update_habit_tracker_metrics(metrics)                      │
│     → Find/create Habit Tracker page for date               │
│     → Update CaloriesIn, CaloriesOut, Weight, BodyFat       │
│     → Smart batching (only changed fields)                   │
│                                                               │
│ Workouts:                                                    │
│   sync_workout(workout)                                      │
│     → Check for duplicates (by ID or attributes)            │
│     → Generate workout summary                               │
│     → Create/update Workouts DB entry                        │
│     → Update Habit Tracker checkboxes                        │
│     → Update Habit Tracker page icon                         │
│     → Update Habit Tracker page content (exercises)          │
│                                                               │
│ Health Stats ETL:                                            │
│   sync_health_stats_for_date_range(start, end)              │
│     → Extract: Query Habit Tracker for metrics              │
│     → Transform: Wide format → time-series                   │
│     → Load: Upsert to Health Stats DB                        │
│                                                               │
│ Duplicate Detection:                                         │
│   is_workout_duplicate(workout)                              │
│     → Strategy 1: HealthAutoExport by UUID in notes         │
│     → Strategy 2: Gymaholic by date+type+source             │
│                                                               │
│ Workout Summary:                                             │
│   generate_workout_summary(workout)                          │
│     → Gymaholic: Use notes (e.g., "TOMO A Strength")        │
│     → Cardio: Format with distance/duration/HR              │
│     → Strength: List exercises                               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Module Files

| File | Purpose | Key Functions | Status |
|------|---------|---------------|--------|
| `sync_orchestrator.py` | **Main coordinator** - Orchestrates entire sync flow | `sync_date_range()` | ✅ Active |
| `notion_sync.py` | **Notion API integration** - All Notion write operations | `sync_workout()`, `update_habit_tracker_metrics()`, `sync_health_stats_for_date_range()` | ✅ Active |
| `workout_merger.py` | Merge Gymaholic + HealthAutoExport workouts | `merge_workouts_for_day()` | ✅ Active |
| `parsers/gymaholic.py` | Parse Gymaholic CSV files | `parse()` | ✅ Active |
| `parsers/health_auto_export.py` | Parse HealthAutoExport workout JSON | `parse()` | ✅ Active |
| `parsers/health_auto_export_metrics.py` | Parse HealthAutoExport activity JSON | `parse()` | ✅ Active |
| `workout_sync.py` | **DEAD CODE** - Never implemented | N/A | ❌ Unused |

---

## Key Differences: Productivity vs Health

| Aspect | Productivity | Health |
|--------|-------------|--------|
| **Orchestrator** | No orchestrator (simple flow) | `HealthSyncOrchestrator` coordinates complex flow |
| **Data Source** | Notion only | File system + Notion |
| **Parsing** | None (data already in Notion) | 3 parsers (Gymaholic, HealthAutoExport workouts/metrics) |
| **Merging** | None | `WorkoutMerger` combines sources |
| **ETL** | None (yet - planned for v0.3.0) | Health Stats ETL (extract/transform/load) |
| **Caching** | Incremental by modified timestamp | Full date range scan |
| **Dry Run** | Not supported | Supported (`--dry-run` flag) |

---

## Redundancy Analysis

### ❌ Dead Code Identified

**File:** `toad/health/workout_sync.py`
- **Status:** Skeleton with `NotImplementedError` stubs
- **Reason:** Functionality implemented in `sync_orchestrator.py` instead
- **Action:** Can be safely deleted

### ✅ No Other Redundancy Found

All other modules serve distinct purposes:
- `sync_orchestrator.py` - Orchestrates multi-step flow
- `notion_sync.py` - Notion API operations (single responsibility)
- `workout_merger.py` - Workout matching logic
- Parsers - Each handles specific file format

**Separation of Concerns:**
- Orchestrator = "what to do and when"
- Notion sync = "how to write to Notion"
- Parsers = "how to read source data"
- Merger = "how to combine data"

---

## Auto-Sync Daemon Flow

```
┌──────────────────────────────────────────────────────────────┐
│                  scripts/auto_sync.py                         │
│                  Auto-Sync Scheduler                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Schedule:                                                     │
│   • Every 5 min:  run_productivity_sync()                    │
│   • Every 30 min: run_health_sync()                          │
│                                                               │
│ Execution:                                                    │
│   • Uses threading.Lock for sequential execution             │
│   • When syncs align at t=30min, runs sequentially:          │
│     1. Productivity sync completes                           │
│     2. Then health sync starts                               │
│                                                               │
│ Commands:                                                     │
│   • Productivity: poetry run toad sync productivity          │
│   • Health: poetry run toad sync health --full               │
│                                                               │
│ Logging:                                                      │
│   • All output → ~/.toad/auto_sync.log                       │
│   • Markers: 🔄 (productivity), 💪 (health)                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Error Handling Patterns

### Productivity Module

```python
# Graceful degradation
try:
    extract_task_data()
except Exception as e:
    logger.error(f"Failed to extract tasks: {e}")
    # Continue with empty data
    tasks_df = pd.DataFrame()
```

### Health Module

```python
# Per-item error handling with summary
summary = {
    'metrics_processed': 0,
    'workouts_processed': 0,
    'errors': []
}

for date in date_range:
    try:
        sync_for_date(date)
        summary['metrics_processed'] += 1
    except Exception as e:
        summary['errors'].append(f"{date}: {str(e)}")

return summary  # Report all errors at end
```

---

## Data Persistence

### Notion Databases

**Productivity:**
- Tasks (`NOTION_DATABASE_ID`)
- Time Entries (`NOTION_TIME_ENTRIES_DATABASE_ID`)
- Daily Productivity Metrics (`NOTION_DAILY_METRICS_DATABASE_ID`)

**Health:**
- Habit Tracker (`NOTION_HABITS_DATABASE_ID`)
- Workouts (`NOTION_WORKOUTS_DATABASE_ID`)
- Health Stats (`NOTION_HEALTH_STATS_DATABASE_ID`)

### Local Files

**Cache:**
- `~/.toad/sync_cache.json` - Last sync timestamps

**Logs:**
- `~/.toad/auto_sync.log` - Auto-sync daemon logs
- Console output - CLI sync logs

**Source Files:**
- `~/iCloud/TOAD/workout_sync/inbox/gymaholic/*.csv` - Pending
- `~/iCloud/TOAD/workout_sync/processed/gymaholic/*.csv` - Processed
- HealthAutoExport files stay in place (tracked by workout ID in notes)

---

## Configuration

### Environment Variables

```bash
# Notion API
NOTION_TOKEN=secret_xxx

# Productivity Databases
NOTION_DATABASE_ID=xxx           # Tasks
NOTION_TIME_ENTRIES_DATABASE_ID=xxx
NOTION_DAILY_METRICS_DATABASE_ID=xxx

# Health Databases
NOTION_HABITS_DATABASE_ID=xxx
NOTION_WORKOUTS_DATABASE_ID=xxx
NOTION_HEALTH_STATS_DATABASE_ID=xxx

# Health Sync Paths
WORKOUT_SYNC_INBOX_PATH=/path/to/inbox
WORKOUT_SYNC_PROCESSED_PATH=/path/to/processed
HEALTH_AUTO_EXPORT_WORKOUTS_PATH=/path/to/TOAD_workouts
HEALTH_AUTO_EXPORT_ACTIVITY_PATH=/path/to/TOAD_Activity

# Sync Intervals (minutes)
PRODUCTIVITY_SYNC_INTERVAL=5
HEALTH_SYNC_INTERVAL=30
```

---

## Future Enhancements

### v0.3.0: Productivity Analytics

**New Components:**
- `productivity/productivity_stats_sync.py` - ETL for time-series data
- `productivity/report_generator.py` - LLM-powered weekly reports

**Pattern:** Follow Health Stats ETL architecture
- Extract from Tasks/Time Entries
- Transform to time-series format
- Load to Productivity Stats DB

### Potential Refactoring

**Option 1: Base Orchestrator Class**
```python
class BaseSyncOrchestrator:
    """Common sync patterns for all modules."""

    def sync_date_range(self, start, end):
        """Template method pattern."""
        for date in date_range:
            self.extract_for_date(date)    # Abstract
            self.transform_data(data)       # Abstract
            self.sync_to_notion(data)      # Abstract
```

**Option 2: Unified ETL Framework**
```python
# Common ETL pattern used by both:
# - Health Stats ETL (implemented)
# - Productivity Stats ETL (planned v0.3.0)
```

---

## Recommendations

### 1. Remove Dead Code ✅
Delete `toad/health/workout_sync.py` - never implemented, functionality in orchestrator

### 2. Add Module README Files
- `toad/productivity/README.md` - Explain data extractor + task relations
- `toad/health/README.md` - Explain orchestrator → notion_sync flow

### 3. Document Notion Database Schemas
Create `docs/notion_schemas/` with:
- `tasks.md`
- `daily_metrics.md`
- `habit_tracker.md`
- `workouts.md`
- `health_stats.md`

### 4. API Usage Monitoring
Add logging for Notion API call counts per sync to track against rate limits

### 5. Consider Unifying Cache Strategy
Both modules could use same incremental sync approach (health currently scans full date range)

---

## Questions & Answers

**Q: Why does health have an orchestrator but productivity doesn't?**
A: Health sync is multi-step (parse files → merge → sync → ETL) with multiple data sources. Productivity is simple (query Notion → categorize → update relations).

**Q: Is `workout_sync.py` used anywhere?**
A: No, it's dead code. Can be safely deleted.

**Q: Why do Gymaholic files move but HealthAutoExport files stay?**
A: Gymaholic CSVs are discrete (one per export). HealthAutoExport files are updated in place daily, so we track processed workout IDs in the notes field instead.

**Q: How does incremental sync work?**
A: Productivity uses `sync_cache.json` to store last sync time, then queries Notion for `last_modified > cache_time`. Health scans files for date range (could be optimized).

---

## References

- Main sync flow: `toad/cli.py` (`sync_command()`)
- Productivity: `toad/productivity/data_extractor.py`, `task_relations.py`
- Health: `toad/health/sync_orchestrator.py`, `notion_sync.py`
- Common: `toad/notion_client.py`, `toad/sync_cache.py`
- Daemon: `scripts/auto_sync.py`
