# Productivity Charts - High-Level Planning

**Created:** 2026-01-19
**Status:** Planning
**Principle:** All data lives in Notion. TOAD only does ETL for tasks Notion can't handle natively.

---

## Current Database Analysis

### What We Have

**Tasks** (`20425796-66bd-81f5-b759-e03fe4eb42f2`):
- ✅ Task Type (multi_select): coding, fixing, Meeting, planning, etc.
- ✅ Feature (multi_select): health, productivity, bttc, etc.
- ✅ Projects (relation)
- ✅ Time Entries (relation)
- ✅ Planned Hrs. (formula) - from Planned date range
- ✅ Logged Hrs. (formula) - sum of Time Entries
- ✅ Status (status): todo, doing, paused, done
- ✅ Dates: Planned, Doing, Done, Due

**Time Entries** (`20425796-66bd-8143-b976-eff463de13da`):
- ✅ Start (date with time)
- ✅ End (date with time)
- ✅ Task (relation)
- ✅ mins (formula) - calculated duration

**Daily Productivity Metrics** (`23525796-66bd-8017-a464-c1a7d32d35c4`):
- ✅ Date
- ✅ Relations: Planned, Active, Worked, Done (to Tasks)
- ⚠️  Numeric fields (currently empty - need ETL):
  - Effective Hours Worked
  - Planned Working Hours
  - Time on Planned Tasks
  - Time on Unplanned Tasks
  - Tasks Planned Count, Tasks Active Count
  - Productivity Score, etc.

**Planned Time Blocks** (`2282579666bd803db27de8b6b6938b26`):
- ✅ Start Time (date with time)
- ✅ End Time (date with time)
- ✅ Task (relation)

**Projects** (`2042579666bd8147a8ccebe5658fbdda`):
- ✅ Tasks V2 (relation)
- ✅ Total Project Hours (formula)

---

## Chart Requirements

### 1. Hours Worked Per Day

**Dimensions to break down by:**
- Project (from Tasks.Projects)
- Feature (from Tasks.Feature)
- Task Type (from Tasks.Task Type)
- Planned vs. Actual

**Time slices:**
- Per day
- Per week (Sun-Fri)
- Per month (Jan, Feb, etc.)

**Chart types:**
- Stacked bar chart (hours by task type per day)
- Line chart (planned vs actual hours over time)
- Area chart (hours by project over weeks)

### 2. Tasks Per Day

**Dimensions:**
- Project
- Feature
- Task Type
- Status (planned, active, worked on, completed, backlog)

**Metrics:**
- Count of tasks in each status
- Breakdown by project/feature/type

**Chart types:**
- Stacked bar (task counts by status per day)
- Multi-line chart (tasks planned vs completed over time)

### 3. Timeline Visualization (Planned vs Actual)

**Goal:** Show throughout a single day:
- Planned time blocks (from Planned Time Blocks)
- Actual time entries (from Time Entries)
- Overlay them to see adherence

**Challenge:** Notion doesn't have Gantt/timeline chart
**Options:**
- Use Notion table view with timeline layout
- OR create hourly rollup data for bar chart approximation
- OR external visualization (but goes against principle)

### 4. Consolidated Productivity Metric

**Single number per day that combines:**
- Task completion rate
- Planned vs actual adherence
- Focus time (uninterrupted blocks)
- Efficiency (output per hour)

**Formula approach:**
```
Productivity Score = (
  0.4 * Task Completion Rate +
  0.3 * Schedule Adherence +
  0.2 * Planned/Actual Ratio +
  0.1 * Focus Score
)
```

---

## Approach: Notion-First Design

### What Notion CAN Do Natively

✅ **Daily aggregate metrics via rollups:**
- Daily Productivity Metrics can rollup from Tasks relations
- Example: `Planned.Planned Hrs.` → sum of planned hours
- Example: `Worked.Logged Hrs.` → sum of logged hours

✅ **Charts on Daily Productivity Metrics:**
- X-axis: Date
- Y-axis: Effective Hours Worked, Planned Working Hours
- Group by: (only one dimension at a time)

✅ **Formulas for calculated metrics:**
- Planned vs Actual % (already exists)
- Can add more formulas for productivity score

### What Notion CANNOT Do Natively

❌ **Multi-dimensional breakdown in one chart:**
- Can't show "Hours by Task Type AND Project" in one chart
- Charts limited to one grouping dimension

❌ **Weekly/Monthly aggregation:**
- Charts plot by date
- No native "group by week" or "group by month"

❌ **Time-series transformations:**
- Can't reshape data from wide to long format
- Can't pivot task types into separate series

---

## Proposed Solution: Two-Tier Approach

### Tier 1: Enhanced Daily Productivity Metrics (Notion Formulas/Rollups)

**Populate existing numeric fields using Notion formulas:**

```
Daily Productivity Metrics for 2026-01-18:
├─ Planned (relation) → [Task A, Task B, Task C]
├─ Worked (relation) → [Task A, Task D]
├─ Done (relation) → [Task B]
│
├─ Tasks Planned Count = Planned.count()
├─ Effective Hours Worked = Worked.Logged Hrs.sum()
├─ Planned Working Hours = Planned.Planned Hrs.sum()
├─ Time on Planned Tasks = Worked.filter(is in Planned).Logged Hrs.sum()
├─ Task Completion Rate % = Done.count() / Planned.count()
├─ Productivity Score = custom formula
```

**TOAD's role:** Maintain the relations (already doing this!)
**Notion's role:** Calculate aggregates via formulas/rollups

**Charts we can make:**
- ✅ Total hours per day (line chart)
- ✅ Planned vs Actual hours (multi-line chart)
- ✅ Task completion rate (line chart)
- ✅ Productivity score trend (line chart)
- ✅ Filtered views for specific projects (filter chart view)

### Tier 2: Productivity Stats Database (ETL for Multi-Dimensional Charts)

**Create new database:** `Productivity Stats`

**Schema (time-series format):**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| title | Title | Auto: "{metric} - {dimension_value} - {date}" | "hours_worked - coding - 2026-01-18" |
| date | Date | Date of metric | 2026-01-18 |
| week | Formula | ISO week (YYYY-Www) | 2026-W03 |
| month | Formula | Month (YYYY-MM) | 2026-01 |
| metric_type | Select | Type of metric | hours_worked, tasks_completed |
| dimension | Select | What it's grouped by | task_type, project, feature, overall |
| dimension_value | Text | Specific value | "coding", "TOAD v0.2.0", "health" |
| value | Number | The metric value | 8.5 |

**Select options:**
```
metric_type:
- hours_worked
- hours_planned
- tasks_completed
- tasks_planned
- tasks_active

dimension:
- task_type
- project
- feature
- overall
- status
```

**ETL Process (similar to Health Stats):**

```
EXTRACT:
- Query Tasks for date range
- Query Time Entries for date range
- Join on Task.Time Entries relation

TRANSFORM:
For each date:
  For each Task Type:
    → Row: hours_worked | task_type | "coding" | 8.5
    → Row: tasks_completed | task_type | "coding" | 3

  For each Project:
    → Row: hours_worked | project | "TOAD v0.2.0" | 12.3

  For each Feature:
    → Row: hours_worked | feature | "health" | 10.2

  Overall:
    → Row: hours_worked | overall | "all" | 28.5
    → Row: hours_planned | overall | "all" | 32.0

LOAD:
- Upsert to Productivity Stats
- Match on (date + metric_type + dimension + dimension_value)
```

**Charts we can make with Productivity Stats:**

✅ **Hours by Task Type per Week:**
- Chart type: Stacked bar
- X-axis: week
- Y-axis: value (sum)
- Group by: dimension_value
- Filter: metric_type = "hours_worked" AND dimension = "task_type"

✅ **Hours by Project per Month:**
- Chart type: Stacked area
- X-axis: month
- Y-axis: value (sum)
- Group by: dimension_value
- Filter: metric_type = "hours_worked" AND dimension = "project"

✅ **Planned vs Actual by Task Type:**
- Chart type: Grouped bar
- X-axis: dimension_value
- Y-axis: value (sum)
- Group by: metric_type
- Filter: dimension = "task_type" AND week = "2026-W03"

---

## Implementation Strategy

### Phase 1: Enhance Daily Productivity Metrics (Notion-Only)

**No TOAD changes needed!** Just update Notion formulas.

**Add/update these formula properties:**

1. **Tasks Planned Count** (formula):
   ```
   prop("Planned").length()
   ```

2. **Tasks Completed Count** (formula):
   ```
   prop("Done").length()
   ```

3. **Tasks Worked Count** (formula):
   ```
   prop("Worked").length()
   ```

4. **Effective Hours Worked** (rollup):
   ```
   Rollup: Worked → Logged Hrs. → sum
   ```

5. **Planned Working Hours** (rollup):
   ```
   Rollup: Planned → Planned Hrs. → sum
   ```

6. **Logged Hours on Planned Tasks** (formula):
   ```
   prop("Worked")
     .filter(current in prop("Planned"))
     .map(current.prop("Logged Hrs."))
     .sum()
   ```

7. **Task Completion Rate %** (formula):
   ```
   if(prop("Tasks Planned Count") > 0,
     prop("Tasks Completed Count") / prop("Tasks Planned Count") * 100,
     0
   )
   ```

8. **Schedule Adherence %** (formula):
   ```
   if(prop("Planned Working Hours") > 0,
     min(prop("Effective Hours Worked") / prop("Planned Working Hours") * 100, 100),
     0
   )
   ```

9. **Productivity Score** (formula):
   ```
   (
     prop("Task Completion Rate %") * 0.4 +
     prop("Schedule Adherence %") * 0.3 +
     prop("Planned vs Unplanned %") * 0.2 +
     (prop("Quality Rating") == "Excellent" ? 100 :
      prop("Quality Rating") == "Good" ? 75 :
      prop("Quality Rating") == "Fair" ? 50 : 25) * 0.1
   )
   ```

**Create Chart Views:**

📊 **Chart 1: Weekly Hours Trend**
- View type: Line chart
- X-axis: Date
- Y-axis: Effective Hours Worked, Planned Working Hours
- Filter: Date > relativeDate("lastWeek")

📊 **Chart 2: Task Completion Rate**
- View type: Line chart
- X-axis: Date
- Y-axis: Task Completion Rate %
- Filter: Date > relativeDate("lastMonth")

📊 **Chart 3: Productivity Score**
- View type: Line chart
- X-axis: Date
- Y-axis: Productivity Score
- Filter: Date > relativeDate("lastMonth")

**Benefits:**
- ✅ Zero TOAD development needed
- ✅ Real-time updates (formulas auto-calculate)
- ✅ Covers basic time tracking needs
- ✅ Establishes baseline metrics

**Limitations:**
- ❌ Can't break down by project/task type in charts
- ❌ No weekly/monthly aggregation
- ❌ Single dimension per chart

### Phase 2: Productivity Stats ETL (TOAD Implementation)

**Only implement if Phase 1 charts are insufficient!**

**TOAD files to create/modify:**
```
toad/productivity/
├─ productivity_stats_sync.py   [NEW]
│  └─ Extract/transform/load for Productivity Stats
│
└─ productivity_orchestrator.py [MODIFY]
   └─ Call stats ETL after task sync
```

**ETL methods (similar to Health Stats):**
```python
class ProductivityNotionSync:

    def sync_productivity_stats_for_date_range(self, start_date, end_date):
        """Main ETL orchestrator."""
        # 1. Extract
        task_data = self._extract_task_metrics(start_date, end_date)

        # 2. Transform
        time_series = self._transform_to_time_series(task_data)

        # 3. Load
        for entry in time_series:
            self._load_productivity_stat(entry)

    def _extract_task_metrics(self, start_date, end_date):
        """Query Tasks + Time Entries."""
        # Query tasks modified in date range
        # Get related time entries
        # Return structured data

    def _transform_to_time_series(self, task_data):
        """Wide → Long format."""
        # One row per task → Many rows per metric
        # Example: Task with 3 types → 3 stat rows

    def _load_productivity_stat(self, entry):
        """Upsert to Productivity Stats."""
        # Find by (date + metric_type + dimension + dimension_value)
        # Update if exists, create if not
```

**Configuration:**
```bash
# .env
NOTION_PRODUCTIVITY_STATS_DATABASE_ID=your_stats_db_id
```

**Integration with auto-sync:**
```python
# Already runs every 5 minutes!
# Just add ETL call to productivity sync
def run_productivity_sync():
    sync.sync_tasks()  # Existing
    sync.sync_productivity_stats()  # New
```

---

## Recommendation: Phased Approach

### Start with Phase 1 (Notion-Only)

**Why:**
1. Zero development effort
2. Immediate results
3. Validates metrics are useful
4. TOAD already maintains relations

**Action items:**
1. Update Daily Productivity Metrics formulas (15 min)
2. Create 3-4 chart views (10 min)
3. Use for 1-2 weeks to validate

### Evaluate if Phase 2 is needed

**Indicators that Phase 2 is necessary:**
- Need to compare projects side-by-side in one chart
- Need weekly/monthly aggregation instead of daily
- Want to slice by multiple dimensions (project + task type)
- Need historical reporting by feature

**If Phase 2 is needed:**
- Implement Productivity Stats database
- Follow Health Stats ETL pattern (proven approach)
- Estimated effort: 2-3 days

---

## Timeline Chart (Requirement #3)

**Problem:** Notion doesn't have Gantt/timeline charts

**Options:**

### Option A: Timeline Database View (Notion Native)

Create a view that combines Planned Time Blocks + Time Entries:

```
Timeline View Settings:
- Layout: Timeline
- Start: Start Time / Start
- End: End Time / End
- Color by: "Planned" vs "Actual" (need union table)
```

**Challenge:** Can't combine two databases in one view
**Workaround:** Create union table or use database filter

### Option B: Hourly Breakdown Chart (ETL Approximation)

Create `Hourly Productivity` database:

```
| date | hour | planned_tasks | actual_tasks | planned_mins | actual_mins |
|------|------|---------------|--------------|--------------|-------------|
| 2026-01-18 | 9 | Task A, B | Task A | 60 | 45 |
| 2026-01-18 | 10 | Task A, B | Task D | 60 | 30 |
```

Chart as stacked bar (one bar per hour).

**ETL logic:**
- For each hour in day:
  - Find Planned Time Blocks overlapping that hour
  - Find Time Entries overlapping that hour
  - Calculate planned vs actual minutes

### Option C: Deferred to External Tool

**Recommendation:** Use Notion's native Timeline view for now
- Good enough for visual inspection
- No ETL needed
- Can enhance later if critical

---

## Summary: What to Build

### Immediate (Notion-only):
1. ✅ Update Daily Productivity Metrics formulas
2. ✅ Create basic chart views (hours, completion rate, productivity score)
3. ✅ Use Timeline view for planned vs actual visualization

### Future (if needed):
1. 🔮 Productivity Stats database + ETL
2. 🔮 Multi-dimensional charts (by project, task type, feature)
3. 🔮 Weekly/monthly aggregation
4. 🔮 Hourly breakdown for timeline approximation

### Never (against principle):
1. ❌ External charting tools
2. ❌ Data export to other systems
3. ❌ Duplicate data storage outside Notion

---

## Next Steps

1. **User decision:** Start with Phase 1 (Notion formulas)?
2. **If yes:** Provide exact formulas to add to Daily Productivity Metrics
3. **If want Phase 2:** Create Productivity Stats database schema first
4. **Timeline chart:** Test Timeline view or decide on hourly breakdown approach

**Key question for user:**
> Do the existing Daily Productivity Metrics relations (Planned, Active, Worked, Done) accurately capture what you want to measure? Or do we need to modify the task categorization logic?
