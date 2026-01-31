# CORRECT FILE FLOW ARCHITECTURE

## Current (WRONG) Flow ❌

```
1. Raw file arrives in inbox/
2. Handler moves it to staging/ (RAW FILE) ❌ WRONG
3. Handler processes from staging/ ❌ WRONG
4. Handler moves to processed/ ❌ WRONG
```

**Problems:**
- Staging contains RAW files, not Notion-ready data
- Cannot replay/review what was sent to Notion
- Archive is not being used
- File flow is backwards

---

## CORRECT Flow ✅

```
1. Raw file arrives in inbox/ (Gymaholic CSV or HealthAutoExport JSON)
   └─> Watcher detects new file

2. Handler processes ENTIRELY IN MEMORY:
   ├─> Parse file (CSV → WorkoutData or JSON → WorkoutData)
   ├─> Generate Notion properties (including Summary with progression)
   ├─> Check for duplicates/reconciliation
   └─> Build staging data (JSON with Notion properties + metadata)

3. Handler writes staging file:
   └─> staging/{date}/{source}/workout_{timestamp}.json
       Contains: {
         "notion_properties": {...},  # Ready for Notion API
         "metadata": {
           "source_file": "...",
           "parsed_at": "...",
           "workout_date": "...",
           "reconciliation_action": "create|merge|skip"
         }
       }

4. Handler moves RAW file to archive:
   └─> archive/{date}/{source}/original_{timestamp}.{ext}
       (Preserves raw export for replay/debugging)

5. Handler syncs to Notion using staging data:
   └─> Read staging JSON
   └─> Call Notion API with properties
   └─> Record result in staging JSON

6. Handler moves staging file to processed/:
   └─> processed/{date}/{source}/workout_{timestamp}.json
       (Contains full audit trail: what was synced, when, result)
```

---

## Directory Structure

```
~/.toad/
└─> inbox/
    ├─> gymaholic/           # Watched by daemon
    └─> health/              # Not used (files come from iCloud)

~/icloud/HealthExport/
├─> TOAD_workouts/           # Watched by daemon (HealthAutoExport JSONs)
└─> TOAD_Activity/           # Watched by daemon (Activity metrics CSVs)

~/icloud/TOAD/
├─> staging/                 # Notion-ready JSON files (delta/changes)
│   └─> {YYYY-MM-DD}/
│       ├─> gymaholic/
│       │   └─> workout_20260129_123456.json
│       └─> health/
│           ├─> workout_20260129_123456.json
│           └─> activity_20260129_123456.json
│
├─> archive/                 # Raw files (replay/debug)
│   └─> {YYYY-MM-DD}/
│       ├─> gymaholic/
│       │   └─> TOMO_A_Strength_20260129_123456.csv
│       └─> health/
│           ├─> HealthAutoExport-2026-01-29_20260129_123456.json
│           └─> Activity-2026-01-29_20260129_123456.csv
│
└─> processed/               # Staging files after successful sync
    └─> {YYYY-MM-DD}/
        ├─> gymaholic/
        │   └─> workout_20260129_123456.json  # Same as staging, with result
        └─> health/
            ├─> workout_20260129_123456.json
            └─> activity_20260129_123456.json
```

---

## Staging File Format

```json
{
  "version": "1.0",
  "type": "workout",
  "source_file": {
    "path": "/path/to/original.csv",
    "filename": "TOMO A Strength.csv",
    "source": "Gymaholic"
  },
  "parsed_at": "2026-01-29T12:34:56.000Z",
  "workout_data": {
    "date": "2026-01-28T10:45:00.000Z",
    "workout_type": "Strength",
    "notes": "TOMO A Strength",
    "duration_minutes": 98,
    "calories": 555,
    "exercises": [...]
  },
  "notion_properties": {
    "Name": {"title": [{"text": {"content": "TOMO A Strength"}}]},
    "Date": {"date": {"start": "2026-01-28"}},
    "DateTime": {"date": {"start": "2026-01-28T10:45:00.000Z"}},
    "Type": {"select": {"name": "Strength"}},
    "Source": {"select": {"name": "Gymaholic"}},
    "Summary": {"rich_text": [{"text": {"content": "**TOMO A STRENGTH**\n..."}}]},
    ...
  },
  "reconciliation": {
    "action": "merge",  # create | merge | skip
    "matched_page_id": "notion-page-id-if-merge",
    "reason": "Found existing workout within 30min tolerance"
  },
  "sync_result": {
    "success": true,
    "notion_page_id": "...",
    "synced_at": "2026-01-29T12:35:10.000Z",
    "error": null
  }
}
```

---

## Handler Refactor

### New Method: `process_file_in_memory()`

```python
def process_file_in_memory(self, file_path: Path, file_type: str) -> Dict[str, Any]:
    """Process file entirely in memory.

    Returns:
        {
            "workout_data": WorkoutData,
            "notion_properties": Dict,
            "reconciliation": Dict,
            "staging_data": Dict  # Complete staging JSON
        }
    """
    # 1. Parse file
    workout = self.parse_file(file_path, file_type)

    # 2. Generate Notion properties (including Summary)
    properties = self.notion_sync.generate_properties(workout)

    # 3. Check reconciliation
    reconciliation = self.check_reconciliation(workout)

    # 4. Build staging data
    staging_data = {
        "version": "1.0",
        "source_file": {...},
        "workout_data": workout.to_dict(),
        "notion_properties": properties,
        "reconciliation": reconciliation
    }

    return staging_data
```

### New Method: `write_staging_file()`

```python
def write_staging_file(self, staging_data: Dict, workout_date: date) -> Path:
    """Write staging JSON to staging directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source = staging_data["source_file"]["source"].lower()
    date_str = workout_date.strftime("%Y-%m-%d")

    staging_dir = STAGING_DIR / date_str / source
    staging_dir.mkdir(parents=True, exist_ok=True)

    staging_file = staging_dir / f"workout_{timestamp}.json"
    staging_file.write_text(json.dumps(staging_data, indent=2))

    return staging_file
```

### New Method: `archive_raw_file()`

```python
def archive_raw_file(self, file_path: Path, workout_date: date) -> Path:
    """Move raw file to archive directory."""
    date_str = workout_date.strftime("%Y-%m-%d")
    source = self.detect_source(file_path)

    archive_dir = ARCHIVE_DIR / date_str / source
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = archive_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

    shutil.move(file_path, archive_file)
    return archive_file
```

---

## Benefits of Correct Flow

1. **Staging shows what's going to Notion** (not raw exports)
2. **Archive preserves raw files** for replay/debugging
3. **Processed has audit trail** (what was synced, when, result)
4. **Can replay** by reading archive + regenerating staging
5. **Can review** staging before Notion sync (for debugging)
6. **Clear separation** between raw data and Notion-ready data

---

## Implementation Plan

1. Create archive directory structure
2. Add `write_staging_file()` method
3. Add `archive_raw_file()` method
4. Refactor `handle_file()` to:
   - Process in memory
   - Write staging JSON
   - Archive raw file
   - Sync from staging
   - Move staging to processed
5. Update file_manager to support archive operations
6. Test end-to-end with real files

---

## Reconciliation Fix

**Problem:** Gymaholic and HealthAutoExport aren't merging properly.

**Root Cause:** Need to investigate reconciliation logic and timing.

**Possible Issues:**
1. HealthAutoExport arrives first → creates workout
2. Gymaholic arrives later → should find and merge, but doesn't
3. OR: Reconciliation tolerance is too strict
4. OR: Workout type matching is failing

**Fix:**
- Add detailed logging to reconciliation
- Check if tolerance (30 min) is sufficient
- Verify workout type matching logic
- Consider: Should we skip certain HealthAutoExport workouts?
  (e.g., auto-detected cardio that will be overwritten by Gymaholic?)
