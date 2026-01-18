# Incremental Sync Design

## Problem

Current sync fetches ALL data every time:
- 510 tasks (takes ~5-7 seconds)
- 1397 time entries (takes ~13-15 seconds)
- **Total: ~20-25 seconds** just to fetch data

For 1-5 minute auto-sync, this is too slow and inefficient.

## Solution: Incremental Sync with Timestamp Caching

### Core Concept

1. **Store last sync timestamp** in a local cache file
2. **Query Notion with `last_edited_time` filter** to only get changed records
3. **Update cache timestamp** after successful sync

### Architecture

```
~/.toad/sync_cache.json
{
  "last_sync": {
    "tasks": "2025-10-12T16:42:30Z",
    "time_entries": "2025-10-12T16:42:30Z",
    "time_blocks": "2025-10-12T16:42:30Z"
  }
}
```

### Notion API Filter Example

```python
# Only fetch tasks edited since last sync
filter = {
    "timestamp": "last_edited_time",
    "last_edited_time": {
        "after": "2025-10-12T16:42:30Z"
    }
}
```

## Implementation Plan

### Phase 1: Cache System (v0.4.1)

1. Create `toad/sync_cache.py`:
   - `get_last_sync_time(component)` - Read from cache
   - `update_last_sync_time(component, timestamp)` - Write to cache
   - Cache location: `~/.toad/sync_cache.json`

2. Modify data extractors to support incremental fetching:
   - `extract_tasks_to_dataframe(modified_since=None)`
   - `extract_time_entries_to_dataframe(modified_since=None)`
   - `extract_time_blocks_to_dataframe(modified_since=None)`

### Phase 2: Incremental Task Relations (v0.4.1)

**Problem:** Task relations need ALL tasks to determine which ones are planned/active/worked/done for a date.

**Solution:**
- For **full sync**: Fetch all tasks
- For **incremental sync**: 
  - Fetch only modified tasks
  - Merge with previously cached complete dataset
  - Process relations from merged dataset

**Alternative (simpler):**
- Task relations are date-specific
- For auto-sync, likely only syncing "today"
- Can fetch ALL tasks for today's sync (since it's one date)
- But use incremental for time entries

### Phase 3: Incremental Time Blocks (v0.4.1)

Time blocks are independent - can be updated incrementally:
- Fetch only modified time blocks
- Update their names/sequences
- Update affected task planned hours

## CLI Modes

### Quick Sync (Default for auto-sync)
```bash
toad sync --quick
```
- Uses incremental fetch
- Only syncs today's task relations
- Only updates modified time blocks
- **Target: < 5 seconds**

### Full Sync (Weekly/on-demand)
```bash
toad sync --full
```
- Fetches everything
- Syncs all dates if range provided
- Rebuilds cache
- **Time: 20-30 seconds** (current behavior)

## Performance Estimates

### Current (Full Sync)
- Fetch 510 tasks: ~7 seconds
- Fetch 1397 time entries: ~15 seconds
- Process & update: ~3-5 seconds
- **Total: ~25-30 seconds**

### With Incremental Sync (5-minute intervals)
Assuming 1-5 tasks and 5-10 time entries modified:
- Fetch 5 tasks: ~1 second
- Fetch 10 time entries: ~1 second
- Process & update: ~2 seconds
- **Total: ~4-5 seconds ✨**

## Migration Strategy

1. Keep existing sync as `--full` mode (default for now)
2. Implement incremental as `--quick` mode (opt-in)
3. Test incremental thoroughly
4. Make incremental the default, full becomes `--full`

## Focus Areas (Immediate)

### Keep:
- ✅ Task relations (Planned, Active, Worked, Done)
- ✅ Time block sequencing and naming
- ✅ Time block → Task planned hours rollup

### Remove (for now):
- ❌ Task metrics calculations
- ❌ Metrics properties (delete from Notion)

### Add:
- 🆕 Incremental sync with timestamp caching
- 🆕 Quick sync mode for auto-sync
- 🆕 Full sync mode for manual/weekly runs

## Auto-Sync Setup (Future)

### Cron Job (macOS/Linux)
```bash
# Every 5 minutes during work hours
*/5 9-17 * * 1-5 cd ~/toad-python && poetry run toad sync --quick
```

### Notion Webhook (Advanced)
- Set up Notion webhook to trigger on database changes
- Run sync immediately when user modifies tasks/time entries
- **Target: Real-time sync within 10 seconds**

## Next Steps

1. ✅ Simplified CLI (done)
2. 🔄 Implement sync cache system
3. 🔄 Add incremental filters to data extractors
4. 🔄 Create `--quick` sync mode
5. 🔄 Test with real data
6. 🔄 Set up auto-sync cron job
