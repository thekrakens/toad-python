# Phase 2: Property Review & Chart Requirements Analysis

**Date:** 2026-01-19
**Status:** Planning

---

## Chart Requirements Summary

### Chart 1: Hours Worked Per Day
**Breakdowns:**
- Project
- Feature
- Task Type
- Planned vs. Actual

**Time Slices:**
- Daily
- Weekly (Sun-Fri)
- Monthly (Jan, Feb, Mar)

**Can Notion Do This?**
- ❌ **No** - Requires multi-dimensional aggregation
- Notion rollups can't filter by multiple dimensions (e.g., "hours for Feature X in Project Y")

**Solution:** Productivity Stats ETL database

---

### Chart 2: Tasks Per Day
**Breakdowns:**
- Project
- Feature
- Task Type
- Planned vs. Actual
- Status (Planned, Completed, Worked On, Active, Backlog)

**Time Slices:**
- Daily
- Weekly
- Monthly

**Can Notion Do This?**
- ⚠️ **Partial**
  - ✅ Status counts work (Planned, Done, Backlog, etc.)
  - ❌ Project/Feature/Task Type breakdowns need ETL

**Solution:**
- Use Daily Metrics for status counts (works now)
- Add Productivity Stats ETL for dimensional breakdowns

---

### Chart 3: Timeline Visualization
**Show:** Planned task spans vs. actual time entry spans hour-by-hour

**Can Notion Do This?**
- ❌ **No** - Notion can't render timeline/Gantt visualizations

**Solution:** External tool (Google Sheets, Tableau, custom viz)

---

### Chart 4: Consolidated Productivity Score
**Show:** Single metric rolled up by day/week/month

**Can Notion Do This?**
- ✅ **Yes** - Works with Productivity Score formula in Daily Metrics

**Solution:** Use Notion native (already in formulas guide)

---

## Current Property Audit

### Tasks Database (20425796-66bd-81f5-b759-e03fe4eb42f2)

#### ✅ Keep - Core Properties
| Property | Type | Why |
|----------|------|-----|
| Name | Title | Required |
| Status | Status | Needed for task state tracking |
| Projects | Relation | Required for Chart 1 & 2 dimensional breakdowns |
| Feature | Multi-select | Required for Chart 1 & 2 dimensional breakdowns |
| Task Type | Multi-select | Required for Chart 1 & 2 dimensional breakdowns |

#### ✅ Keep - Date Properties
| Property | Type | Why |
|----------|------|-----|
| Planned | Date | Primary planning date, used in Daily Metrics relations |
| Doing | Date | Tracks when task became active |
| Done | Date | Completion tracking, used in Daily Metrics relations |
| Due | Date | Useful for tracking overdue tasks |

#### ✅ Keep - Time Tracking
| Property | Type | Why |
|----------|------|-----|
| Logged Hrs. | Formula | Sum of time entries, needed for actual hours |
| Planned Hrs. | Formula | Uses Time Blocks or Planned date range |
| Total Block Duration (hrs) | Formula | Sums time block durations |

#### ✅ Keep - Relations
| Property | Type | Why |
|----------|------|-----|
| Time Entries | Relation | Required for time tracking |
| Time Blocks | Relation | Required for planning |
| Parent item / Sub-item | Relation | Task hierarchy |
| Related to Daily Productivity Metrics (Planned/Active/Worked/Done) | Relations | Auto-synced by TOAD |

#### 🤔 Review - Potentially Redundant
| Property | Type | Issue | Recommendation |
|----------|------|-------|----------------|
| Daily Metrics | Relation | Database ID `20425796-66bd-8171-92ad-da80f18fdf02` doesn't match current Daily Productivity Metrics (`23525796-66bd-8017-a464-c1a7d32d35c4`) | Remove if orphaned |

#### 📝 Keep - Organizational
| Property | Type | Why |
|----------|------|-----|
| Create Entry | Button | UX helper |
| Created time | System | Useful for analysis |
| Section dividers (🤖 SYSTEM, 📝 BASIC INFO, etc.) | Rich text | Organization |

---

### Daily Productivity Metrics Database (23525796-66bd-8017-a464-c1a7d32d35c4)

#### ✅ Keep - Core Properties
| Property | Type | Why |
|----------|------|-----|
| Name | Title | Required |
| Date | Date | Primary key |
| Day of Week | Formula | Useful for weekly grouping |

#### ✅ Keep - Relations (TOAD-synced)
| Property | Type | Why |
|----------|------|-----|
| Planned | Relation | Tasks planned for this date |
| Active | Relation | Tasks active on this date |
| Worked | Relation | Tasks worked on this date |
| Done | Relation | Tasks completed this date |
| **Backlog** | Relation | **NEW** - Tasks backlogged this date |
| **Archived** | Relation | **NEW** - Tasks archived this date |

#### ⚠️ Convert to Formulas - Metrics
These are currently Number properties but should be formulas/rollups:

| Property | Current | Change To | Formula |
|----------|---------|-----------|---------|
| Tasks Planned Count | Number | Formula | `prop("Planned").length()` |
| Tasks Active Count | Number | Formula | `prop("Active").length()` |
| Effective Hours Worked | Number | Rollup | Worked → Logged Hrs. → Sum |
| Planned Working Hours | Number | Rollup | Planned → Planned Hrs. → Sum |
| Time on Planned Tasks | Number | Formula | See formulas guide |
| Time on Unplanned Tasks | Number | Formula | `prop("Effective Hours Worked") - prop("Time on Planned Tasks")` |
| Task Completion Rate % | Number | Formula | See formulas guide |
| Schedule Adherence % | Number | Formula | See formulas guide |
| Productivity Score | Number | Formula | See formulas guide |
| Unplanned Tasks Created | Number | Formula | See formulas guide |

#### ✅ Keep - Manual Input
| Property | Type | Why |
|----------|------|-----|
| Quality Rating | Select | Manual reflection on work quality |
| Work Day Type | Select | Manual categorization of day type |
| Notes | Rich text | Daily journal |

#### ⏸️ Keep - Manual (For Now)
| Property | Type | Why |
|----------|------|-----|
| Context Switches | Number | Complex to calculate, manual for now |
| Cold Tasks Count | Number | Needs definition, manual for now |

#### ✅ Keep - Formulas
| Property | Type | Status |
|----------|------|--------|
| Planned vs Unplanned % | Formula | Already working |

---

## What Charts Can We Build Now?

### Tier 1: Notion Native (Available Now)

**Charts you can build with current setup + formulas:**

1. ✅ **Daily Hours Trend**
   - Effective Hours Worked over time
   - Planned vs Actual (totals only, no breakdowns)
   - Line chart, grouped by week/month

2. ✅ **Task Status Counts**
   - Planned, Active, Worked, Done, Backlog, Archived counts per day
   - Stacked bar chart
   - Can group by week/month

3. ✅ **Productivity Score Trend**
   - Single line showing score over time
   - Grouped by week/month

4. ✅ **Completion Metrics**
   - Task Completion Rate %
   - Schedule Adherence %
   - Planned vs Unplanned %

5. ✅ **Planned vs Unplanned Hours**
   - Total hours breakdown (not by project/feature)
   - Stacked bar or pie chart

---

## What Charts Need ETL?

### Tier 2: Productivity Stats ETL Database

For multi-dimensional analysis, create new database: **Productivity Stats**

**Structure:**
```
{
  date: Date,
  project: Relation → Projects,
  feature: Multi-select,
  task_type: Multi-select,
  planned_hours: Number,
  actual_hours: Number,
  planned_tasks: Number,
  completed_tasks: Number,
  active_tasks: Number,
  backlog_tasks: Number
}
```

**This enables:**
1. ✅ Hours by Project (Chart 1a)
2. ✅ Hours by Feature (Chart 1a)
3. ✅ Hours by Task Type (Chart 1a)
4. ✅ Tasks by Project (Chart 2a)
5. ✅ Tasks by Feature (Chart 2a)
6. ✅ Tasks by Task Type (Chart 2a)
7. ✅ Cross-dimensional queries ("Feature X in Project Y")

**TOAD would ETL this daily by:**
- Querying all tasks worked on each date
- Grouping by {date, project, feature, task_type}
- Aggregating hours and counts

---

## Decision Framework

### Start with Tier 1 (Recommended)

**Reasons:**
1. ✅ Zero development - just add formulas in Notion
2. ✅ Answers core questions:
   - "How many hours did I work this week?"
   - "What's my task completion rate?"
   - "Am I spending too much time on unplanned work?"
3. ✅ Validates if charts are actually useful
4. ✅ Can add Tier 2 later if needed

**Do This:**
1. Implement formulas from formulas guide (Phase 1, 2, 3)
2. Create 5 charts listed above
3. Use for 1-2 weeks
4. Evaluate if Project/Feature breakdowns are critical

### Add Tier 2 If Needed

**You'll know you need Tier 2 when:**
- ❌ "I need to see hours by project to understand where time is going"
- ❌ "I want to compare Feature X vs Feature Y productivity"
- ❌ "I need to break down Task Types within each Project"

**If these questions don't come up in 2 weeks → stick with Tier 1!**

---

## Next Steps

**Immediate (This Week):**
1. ✅ Add Backlog and Archived properties (Done!)
2. ✅ Test backlog/archived sync (Done!)
3. ⬜ Convert Daily Metrics properties to formulas (use formulas guide)
4. ⬜ Create 5 Tier 1 charts in Notion
5. ⬜ Test with real data

**Evaluate (In 2 Weeks):**
- Are Tier 1 charts answering your questions?
- Do you find yourself wanting Project/Feature breakdowns?
- Decide: Tier 2 ETL or stick with Tier 1?

**Future (If Needed):**
- Implement Productivity Stats ETL database
- Add TOAD job to populate daily
- Create dimensional charts

---

## Property Naming Conventions

### Recommended Standardization

**Current naming is inconsistent:**
- Some use "Tasks Planned Count" (descriptive)
- Some use "Worked" (short relation name)
- Some use emoji dividers

**Proposed convention:**
- Relations: Short names (Planned, Active, Worked, Done, Backlog, Archived)
- Counts: "{Relation} Tasks Count" (e.g., "Planned Tasks Count")
- Hours: "{Context} Hours" (e.g., "Effective Hours Worked", "Planned Working Hours")
- Percentages: "{Metric} %" (e.g., "Task Completion %", "Schedule Adherence %")
- Formulas: Descriptive (e.g., "Productivity Score", "Day of Week")

**Should we standardize during this phase?** (Optional - can defer)

---

## Questions for User

Before finalizing property changes:

1. **Do you want to implement Tier 1 first and evaluate before building Tier 2 ETL?**
   - My recommendation: Yes (faster value, less risk)

2. **Are there any current properties you know you don't use?**
   - e.g., Work Day Type, Quality Rating, Context Switches

3. **Should we clean up the orphaned "Daily Metrics" relation in Tasks?**
   - (Appears to point to old database)

4. **Do you want to standardize property names now or later?**

---

## Summary

**What we have:**
- ✅ Solid foundation with relations synced by TOAD
- ✅ Can build 5 useful charts with Notion native
- ✅ All status tracking works (Planned, Done, Backlog, Archived)

**What we're missing:**
- ❌ Multi-dimensional breakdowns (Project × Feature × Task Type)
- ❌ Timeline visualization

**Recommendation:**
1. ✅ Implement Tier 1 charts (this week)
2. 🔄 Use for 2 weeks, gather feedback
3. 🤔 Evaluate if Tier 2 ETL is worth building
4. 📊 Add dimensional analysis only if clearly needed

**This gets you 80% of value with 20% of effort!**
