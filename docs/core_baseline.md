# TOAD Core Baseline - Back to Fundamentals

## Problem Statement

We've built too much complexity. Need to establish a **solid baseline** focused on:
1. **Task Relations to Daily Metrics** (primary goal)
2. Time entries tracking
3. Time blocks management (no sequencing - future feature)
4. Fast, incremental syncing (1-5 minute intervals)

## Final Task Properties (Cleaned Up!)

### ✅ Core Properties (KEEP)

**BASIC INFO:**
- `Name` (title) - Task name
- `Status` (select/status) - Current status (todo, doing, done)
- `Projects` (relation) - Project categorization
- `Task Type` (multi-select) - Type categorization
- `Logged Hrs.` (rollup/number) - Total time from time entries

**PLANNING:**
- `Planned` (date range) - When task is planned (Start and End Date)
- `Done` (datetime) - Completion timestamp
- `Due` (date) - Due date
- `Doing` (date) - When work started

**RELATIONS:**
- `Time Blocks` (relation) - Link to time blocks
- `Time Entries` (relation) - Link to time entries
- `Daily Metrics` (relation) - Link to daily metrics
- `Related to Daily Productivity Metrics (Planned Tasks)` - From Daily Metrics
- `Related to Daily Productivity Metrics (Active Tasks)` - From Daily Metrics
- `Related to Daily Productivity Metrics (Worked On Tasks)` - From Daily Metrics
- `Related to Daily Productivity Metrics (Completed Tasks)` - From Daily Metrics

### 📊 Formula Helpers (Simplified)

**ONE unified planned hours field:**
- `Planned Hrs.` (formula) - **Smart calculation:**
  - If `Planned` date range exists → (Planned End - Planned Start) in hours
  - Else if `Time Blocks` exist → sum of Time Block durations
  - Else → 0

**Time block rollup:**
- `Total Block Duration (hrs)` (rollup) - Sum of time block durations in hours
- `Planned Block Count` (rollup) - Count of time blocks

### ❌ Deleted Properties

- ~~`Planned Task`~~ - Redundant checkbox
- ~~`Has Time Blocks`~~ - Redundant checkbox
- ~~`Context Switches`~~ - Not needed
- ~~`Estimated Hrs.`~~ - Replaced by unified `Planned Hrs.`
- ~~`Total Block Duration (mins)`~~ - Keeping only hours version

## Planned Hrs. Formula Recommendation

Your `Planned Hrs.` formula should be:

```
if(prop("Planned"), dateBetween(prop("Planned").end, prop("Planned").start, "hours"), prop("Total Block Duration (hrs)"))
```

**Explanation:**
- If `Planned` date range exists → Calculate hours between end and start
- Otherwise → Use sum of time block durations
- Gives you ONE unified metric that works whether you plan by date range, time blocks, or both

**Breaking it down:**
- `prop("Planned")` - Check if Planned date range is set
- `prop("Planned").start` - Start of date range
- `prop("Planned").end` - End of date range  
- `dateBetween(end, start, "hours")` - Calculate hours between them
- `prop("Total Block Duration (hrs)")` - Fallback to time blocks sum

## Simplified Task Relations Logic

### What Gets Synced to Daily Metrics

**For a given date (e.g., 2025-10-12):**

1. **Planned Tasks**: Tasks where `Planned` date range overlaps with target date
2. **Active Tasks**: Tasks that are either:
   - Planned for this date, OR
   - Worked on this date, OR
   - Planned earlier but not yet done
3. **Worked Tasks**: Tasks with time entries on this date
4. **Done Tasks**: Tasks with `Done` datetime on this date

### Update Process

1. Fetch tasks and time entries (incremental if using cache)
2. Calculate which tasks belong in each category for the date
3. Update Daily Metrics entry relations:
   - `Related to Daily Productivity Metrics (Planned Tasks)`
   - `Related to Daily Productivity Metrics (Active Tasks)`
   - `Related to Daily Productivity Metrics (Worked On Tasks)`
   - `Related to Daily Productivity Metrics (Completed Tasks)`
4. Done!

**No metrics calculations. Just relations.**

## Daily Metrics Database

Your Daily Metrics should have these properties:

**Essential:**
- `Name` (title) - "Daily Metrics - YYYY-MM-DD"
- `Date` (date) - The date this entry represents

**Relations to Tasks:**
- `Planned Tasks` (relation to Tasks)
- `Active Tasks` (relation to Tasks)
- `Worked On Tasks` (relation to Tasks)
- `Completed Tasks` (relation to Tasks)

**Rollup Properties (calculated from relations):**
- `Planned Count` (rollup count of Planned Tasks)
- `Active Count` (rollup count of Active Tasks)
- `Worked Count` (rollup count of Worked On Tasks)
- `Done Count` (rollup count of Completed Tasks)
- `Total Planned Hours` (rollup sum from Tasks → Planned Hrs.)
- `Total Logged Hours` (rollup sum from Tasks → Logged Hrs.)

## TOAD Code Structure

### Core Modules (Keep & Simplify)

```
toad/
├── cli.py                          # CLI with 3 sync modes
├── config.py                       # Configuration
├── notion_client.py                # Notion API wrapper (with filters)
├── sync_cache.py                   # Timestamp caching for incremental sync
└── productivity/
    ├── data_extractor.py           # Extract tasks/entries/blocks (with incremental)
    └── task_relations.py           # Update Daily Metrics relations
```

### Modules to REMOVE/ARCHIVE:
- ❌ `task_metrics.py` - Delete (no more calculated metrics)
- ❌ `daily_metrics.py` - Delete (daily metrics are just relations now)
- ❌ `time_block_manager.py` - Delete (no sequencing in baseline)

## Three Sync Modes

### Mode 1: Default Sync (Incremental)
```bash
toad sync
```
- **Uses sync cache** to track last update
- Only fetches tasks/entries **modified since last sync**
- Syncs only **TODAY's** relations
- **Target: 2-5 seconds**
- Run every 1-5 minutes via cron

**How it works:**
1. Check cache for last sync timestamp
2. Fetch only tasks/entries modified since then
3. Process only today's date
4. Update Daily Metrics for today
5. Update cache timestamp

### Mode 2: Date Sync
```bash
toad sync 10-12-25                  # Single date
toad sync 10-10-25 10-12-25        # Date range
```
- Fetches tasks/entries (uses cache if available)
- Syncs **specified date(s)** only
- **Target: 5-10 seconds per date**
- Manual or weekly use

**How it works:**
1. Check cache for last sync timestamp
2. Fetch tasks/entries modified since cache OR all if no cache
3. Process specified date(s)
4. Update Daily Metrics for those dates
5. Update cache timestamp

### Mode 3: Full Sync
```bash
toad sync --full
```
- Fetches **ALL** tasks/entries (ignores cache)
- Syncs **last 30 days**
- Rebuilds cache
- **Target: 20-30 seconds**
- Weekly or after major changes

**How it works:**
1. Ignore cache
2. Fetch ALL tasks and time entries
3. Process last 30 days
4. Update Daily Metrics for all dates
5. Reset cache timestamp

### Additional Commands
```bash
toad sync --clear-cache            # Clear cache, next sync will be full
```

## Command Structure Summary

| Command | Tasks Fetched | Entries Fetched | Dates Synced | Speed | Use Case |
|---------|---------------|-----------------|--------------|-------|----------|
| `toad sync` | Modified since cache | Modified since cache | Today | 2-5s | Auto-sync (every 1-5 min) |
| `toad sync 10-12-25` | Modified since cache | Modified since cache | That date | 5-10s | Manual date sync |
| `toad sync 10-10-25 10-12-25` | Modified since cache | Modified since cache | Date range | 5-10s/date | Manual range sync |
| `toad sync --full` | ALL | ALL | Last 30 days | 20-30s | Weekly full rebuild |

## Implementation Roadmap

### Phase 1: Property Cleanup ✅ (DONE!)
1. ✅ Deleted `Planned Task` flag
2. ✅ Deleted `Has Time Blocks` flag
3. ✅ Deleted `Context Switches`
4. ✅ Deleted `Estimated Hrs.` (replaced by unified `Planned Hrs.`)
5. ✅ Deleted `Total Block Duration (mins)` (keeping only hours)

### Phase 2: Code Simplification (IN PROGRESS)
1. ✅ Sync cache system (DONE)
2. ✅ Incremental filters in extractors (DONE)
3. ✅ Filter support in notion_client (DONE)
4. ⏳ Update CLI with three modes (NEXT)
5. ⏳ Remove task_metrics.py, daily_metrics.py, time_block_manager.py

### Phase 3: Testing & Validation
1. Test full sync mode (baseline)
2. Test date sync mode
3. Test incremental sync mode
4. Verify cache works correctly
5. Measure performance

### Phase 4: Production Deployment
1. Set up cron job for default sync (every 5 minutes)
2. Monitor performance and errors
3. Adjust timing if needed (could go to 1 minute)

## Success Criteria

✅ **Baseline established when:**
1. Task relations update correctly for any date
2. Default sync runs in < 5 seconds
3. Date sync runs in < 10 seconds per date
4. Full sync runs in < 30 seconds
5. Auto-sync runs every 1-5 minutes without issues

✅ **Daily Metrics show:**
- Planned tasks for the day
- Active tasks (planned + in-progress)
- Worked tasks (with time entries)
- Done tasks (completed that day)

✅ **Rollup properties calculate:**
- Task counts for each category
- Total planned hours (unified metric)
- Total logged hours

## Property Mapping for TOAD Code

The code needs to map to your actual property names:

```python
# Current mapping (update task_relations.py to use these)
PROPERTY_NAMES = {
    'name': 'Name',
    'status': 'Status',
    'planned': 'Planned',                   # Date range (Start and End)
    'done': 'Done',                         # DateTime
    'due': 'Due',                           # Date
    'doing': 'Doing',                       # Date
    'logged_hours': 'Logged Hrs.',          # Rollup from time entries
    'planned_hours': 'Planned Hrs.',        # Unified formula
    'time_blocks': 'Time Blocks',           # Relation
    'time_entries': 'Time Entries',         # Relation
}

# Daily Metrics relation property names
DAILY_METRICS_RELATIONS = {
    'planned': 'Related to Daily Productivity Metrics (Planned Tasks)',
    'active': 'Related to Daily Productivity Metrics (Active Tasks)',
    'worked': 'Related to Daily Productivity Metrics (Worked On Tasks)',
    'done': 'Related to Daily Productivity Metrics (Completed Tasks)',
}
```

## Next Actions

1. ✅ **YOU:** Clean up properties in Notion (DONE!)
2. ⏳ **ME:** Simplify CLI to 3 modes + cache integration
3. ⏳ **ME:** Remove unused modules (task_metrics, time_block_manager)
4. ⏳ **YOU:** Test each sync mode
5. ⏳ **ME:** Fix any issues
6. ⏳ **YOU:** Set up cron job for auto-sync
7. ⏳ **BOTH:** Celebrate solid baseline! 🎉

---

## Final Property Summary

**Tasks Database - Final List:**
- Name (title)
- Status (select/status)
- Projects (relation)
- Task Type (multi-select)
- Planned (date range) ← Used for planned hours calculation
- Done (datetime)
- Due (date)
- Doing (date)
- Planned Hrs. (formula) ← Unified metric
- Logged Hrs. (rollup)
- Total Block Duration (hrs) (rollup)
- Planned Block Count (rollup)
- Time Blocks (relation)
- Time Entries (relation)
- Daily Metrics (relation)
- 4x Relations from Daily Metrics

**Deleted:**
- ~~Planned Task~~ (redundant)
- ~~Has Time Blocks~~ (redundant)
- ~~Context Switches~~ (unused)
- ~~Estimated Hrs.~~ (replaced by Planned Hrs.)
- ~~Total Block Duration (mins)~~ (using hours only)
