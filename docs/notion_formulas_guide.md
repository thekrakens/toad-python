# Daily Productivity Metrics - Notion Formulas Guide

**Database:** Daily Productivity Metrics (`23525796-66bd-8017-a464-c1a7d32d35c4`)
**Last Updated:** 2026-01-19
**Status:** Ready to implement

---

## Overview

This guide provides exact formulas to populate the Daily Productivity Metrics database using **only Notion's native formulas and rollups**. No TOAD code changes needed!

TOAD already maintains the relations (Planned, Active, Worked, Done) via the productivity sync that runs every 5 minutes. These formulas will automatically calculate metrics based on those relations.

---

## Step-by-Step Implementation

### 1. Tasks Planned Count

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
prop("Planned").length()
```

**What it does:** Counts how many tasks are in the Planned relation (tasks with Planned date = this date)

---

### 2. Tasks Active Count

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
prop("Active").length()
```

**What it does:** Counts how many tasks are in the Active relation (tasks with Doing date = this date)

---

### 3. Tasks Completed Count

**Current:** None (need to add new property)
**Add as:** Formula property named "Tasks Completed Count"

**Formula:**
```
prop("Done").length()
```

**What it does:** Counts how many tasks are in the Done relation (tasks with Done date = this date)

---

### 4. Tasks Worked Count

**Current:** None (need to add new property)
**Add as:** Formula property named "Tasks Worked Count"

**Formula:**
```
prop("Worked").length()
```

**What it does:** Counts how many tasks are in the Worked relation (tasks with time entries on this date)

---

### 5. Effective Hours Worked

**Current:** Number property (likely empty)
**Change to:** Rollup

**Rollup configuration:**
- Relation: `Worked`
- Property: `Logged Hrs.`
- Calculate: `Sum`

**Alternative (if you want formula):**
```
prop("Worked").map(current.prop("Logged Hrs.")).sum()
```

**What it does:** Sums up the logged hours from all tasks that were worked on this date

---

### 6. Planned Working Hours

**Current:** Number property (likely empty)
**Change to:** Rollup

**Rollup configuration:**
- Relation: `Planned`
- Property: `Planned Hrs.`
- Calculate: `Sum`

**Alternative (if you want formula):**
```
prop("Planned").map(current.prop("Planned Hrs.")).sum()
```

**What it does:** Sums up the planned hours from all tasks planned for this date

---

### 7. Time on Planned Tasks

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
prop("Worked").filter(current.id().inside(prop("Planned").map(current.id()))).map(current.prop("Logged Hrs.")).sum()
```

**Simplified explanation:**
- Get all Worked tasks
- Filter to only those that are also in Planned
- Sum their Logged Hrs

**What it does:** Calculates how many hours were spent on tasks that were actually planned (not ad-hoc work)

---

### 8. Time on Unplanned Tasks

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
prop("Effective Hours Worked") - prop("Time on Planned Tasks")
```

**What it does:** Calculates hours spent on unplanned/ad-hoc tasks (total worked - planned)

---

### 9. Task Completion Rate %

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
if(prop("Tasks Planned Count") > 0, round(prop("Done").length() / prop("Tasks Planned Count") * 100), 0)
```

**What it does:** Percentage of planned tasks that were completed on this date

---

### 10. Schedule Adherence %

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
if(prop("Planned Working Hours") > 0, round(min(prop("Effective Hours Worked") / prop("Planned Working Hours"), 1) * 100), 0)
```

**What it does:** How closely actual hours matched planned hours (capped at 100%)

---

### 11. Planned vs Unplanned %

**Current:** Formula (already exists)
**Verify it matches:**

**Formula:**
```
if(prop("Effective Hours Worked") > 0, round((prop("Time on Planned Tasks") / prop("Effective Hours Worked")) * 100), 0)
```

**What it does:** Percentage of work time spent on planned vs unplanned tasks

---

### 12. Productivity Score

**Current:** Number property (likely empty or manual)
**Change to:** Formula

**Formula:**
```
lets(
  completionScore, if(prop("Tasks Planned Count") > 0, prop("Done").length() / prop("Tasks Planned Count") * 100, 0),
  adherenceScore, if(prop("Planned Working Hours") > 0, min(prop("Effective Hours Worked") / prop("Planned Working Hours"), 1) * 100, 0),
  plannedRatio, if(prop("Effective Hours Worked") > 0, (prop("Time on Planned Tasks") / prop("Effective Hours Worked")) * 100, 0),
  qualityScore, if(prop("Quality Rating") == "Excellent", 100, if(prop("Quality Rating") == "Good", 75, if(prop("Quality Rating") == "Fair", 50, if(prop("Quality Rating") == "Poor", 25, 50)))),

  round(
    completionScore * 0.4 +
    adherenceScore * 0.3 +
    plannedRatio * 0.2 +
    qualityScore * 0.1
  )
)
```

**Weights:**
- 40% Task completion rate
- 30% Schedule adherence
- 20% Planned work ratio
- 10% Quality rating

**What it does:** Consolidated productivity metric (0-100)

---

### 13. Unplanned Tasks Created

**Current:** Number property (likely empty)
**Change to:** Formula

**Formula:**
```
prop("Worked").filter(not current.id().inside(prop("Planned").map(current.id()))).length()
```

**What it does:** Counts how many tasks were worked on that weren't originally planned for this date

---

### 14. Context Switches (Advanced)

**Current:** Number property (likely manual)
**Keep as:** Number (manual entry for now)

**Why:** Requires analyzing time entry sequence, which is complex in Notion formulas. Can ETL later if needed.

**Workaround for now:** Manually estimate or leave empty

---

### 15. Cold Tasks Count (Optional)

**Current:** Number property
**Keep as:** Number (manual entry or custom definition)

**Note:** "Cold tasks" needs definition - tasks not touched in X days? Can add formula once definition is clear.

---

## Properties Summary

| Property | Type | Change Required | Complexity |
|----------|------|----------------|------------|
| Tasks Planned Count | Number → Formula | ✅ Update | Easy |
| Tasks Active Count | Number → Formula | ✅ Update | Easy |
| Tasks Completed Count | ➕ Add new | ✅ Add | Easy |
| Tasks Worked Count | ➕ Add new | ✅ Add | Easy |
| Effective Hours Worked | Number → Rollup | ✅ Update | Easy |
| Planned Working Hours | Number → Rollup | ✅ Update | Easy |
| Time on Planned Tasks | Number → Formula | ✅ Update | Medium |
| Time on Unplanned Tasks | Number → Formula | ✅ Update | Easy |
| Task Completion Rate % | Number → Formula | ✅ Update | Easy |
| Schedule Adherence % | Number → Formula | ✅ Update | Easy |
| Planned vs Unplanned % | Formula | ✅ Verify | Easy |
| Productivity Score | Number → Formula | ✅ Update | Medium |
| Unplanned Tasks Created | Number → Formula | ✅ Update | Medium |
| Context Switches | Number | ⏸️  Keep manual | - |
| Cold Tasks Count | Number | ⏸️  Keep manual | - |

---

## Implementation Order

**Phase 1 (Start here - 10 min):**
1. Tasks Planned Count (formula)
2. Tasks Completed Count (new formula)
3. Tasks Worked Count (new formula)
4. Effective Hours Worked (rollup)
5. Planned Working Hours (rollup)

**Phase 2 (Add next - 10 min):**
6. Task Completion Rate % (formula)
7. Schedule Adherence % (formula)
8. Time on Planned Tasks (formula)
9. Time on Unplanned Tasks (formula)

**Phase 3 (Finalize - 5 min):**
10. Productivity Score (formula)
11. Unplanned Tasks Created (formula)
12. Verify Planned vs Unplanned % (existing formula)

---

## Chart Views to Create

Once formulas are in place, create these chart views:

### Chart 1: Daily Hours Trend

**View name:** "Hours: Daily Trend"
**Chart type:** Line chart
**Configuration:**
- X-axis: Date
- Y-axis (multi-line):
  - Effective Hours Worked
  - Planned Working Hours
- Filter: Date is within "Last 30 days"
- Sort: Date (ascending)

**What it shows:** Planned vs actual hours over the last month

---

### Chart 2: Task Completion Rate

**View name:** "Tasks: Completion Rate"
**Chart type:** Line chart
**Configuration:**
- X-axis: Date
- Y-axis: Task Completion Rate %
- Filter: Date is within "Last 30 days"
- Sort: Date (ascending)

**What it shows:** Percentage of planned tasks completed each day

---

### Chart 3: Productivity Score Trend

**View name:** "Productivity Score"
**Chart type:** Line chart
**Configuration:**
- X-axis: Date
- Y-axis: Productivity Score
- Filter: Date is within "Last 30 days"
- Sort: Date (ascending)

**What it shows:** Overall productivity trend (0-100 scale)

---

### Chart 4: Planned vs Unplanned Work

**View name:** "Work: Planned vs Unplanned"
**Chart type:** Stacked bar chart
**Configuration:**
- X-axis: Date
- Y-axis (stacked):
  - Time on Planned Tasks
  - Time on Unplanned Tasks
- Filter: Date is within "Last 14 days"
- Sort: Date (ascending)

**What it shows:** How much time spent on planned vs ad-hoc work

---

### Chart 5: Weekly Summary Table

**View name:** "Weekly Summary"
**View type:** Table (not chart)
**Configuration:**
- Group by: Week (use Day of Week to identify weeks)
- Show:
  - Date
  - Effective Hours Worked
  - Tasks Completed Count
  - Productivity Score
- Filter: Date is within "Last 8 weeks"

**What it shows:** Week-by-week productivity summary

---

## Testing the Formulas

After adding formulas, test with a recent date that has data:

**Example: 2026-01-18**

Expected results (adjust based on your data):
```
Date: 2026-01-18
Planned: [Task A, Task B, Task C] (3 tasks)
Worked: [Task A, Task D] (2 tasks)
Done: [Task B] (1 task)

Calculated:
✅ Tasks Planned Count = 3
✅ Tasks Completed Count = 1
✅ Tasks Worked Count = 2
✅ Task Completion Rate % = 33 (1/3 * 100)
✅ Effective Hours Worked = (sum of Task A + Task D logged hours)
✅ Planned Working Hours = (sum of Task A + Task B + Task C planned hours)
✅ Time on Planned Tasks = (Task A logged hours only)
✅ Time on Unplanned Tasks = (Task D logged hours)
```

---

## Troubleshooting

### Formula shows "Error"
- Check property names match exactly (case-sensitive)
- Ensure relations are properly synced by TOAD
- Verify referenced properties exist

### Values show as 0 when should have data
- Check that TOAD sync has run recently (should run every 5 min)
- Verify task relations are populated (check a Daily Metrics entry)
- Ensure tasks have Planned/Done dates set

### "prop() not found" error
- Use exact property names from your database
- Check if property was renamed
- Try refreshing the database

### Rollup not working
- Ensure relation property has data
- Check that target property exists in related database
- Verify rollup function is set correctly (Sum, Count, etc.)

---

## Expected Outcomes

**After Phase 1:**
- ✅ See task counts auto-populate
- ✅ See hours calculations working
- ✅ Can create basic line charts

**After Phase 2:**
- ✅ See percentage metrics (completion, adherence)
- ✅ Understand planned vs unplanned work split
- ✅ Can create comparison charts

**After Phase 3:**
- ✅ See overall productivity score
- ✅ Identify productivity patterns
- ✅ Can track improvements over time

**What you can answer:**
- "How many hours did I work this week?"
- "What's my task completion rate trend?"
- "Am I spending too much time on unplanned work?"
- "Which days am I most productive?"
- "Is my productivity improving?"

---

## Next Steps

1. **Open Daily Productivity Metrics database**
2. **Start with Phase 1 formulas** (5 properties, ~10 min)
3. **Test with recent dates** that have task data
4. **Create Chart 1 and Chart 2** to visualize
5. **Review after 1 week** - are these charts useful?
6. **Add Phase 2 formulas** if Phase 1 is working well
7. **Report back** - do we need Tier 2 (ETL) or is this sufficient?

---

## When to Consider Tier 2 (ETL)

You'll know you need the Productivity Stats ETL if:

❌ "I need to see hours by task type across all projects"
❌ "I want weekly aggregation, not daily data points"
❌ "I need to compare Feature X vs Feature Y hours"
❌ "I want to filter by project AND task type in same chart"

✅ If current charts answer your questions, stick with Notion formulas!

---

## Support

**TOAD's role:**
- Maintains task relations every 5 minutes ✅
- No code changes needed for this phase ✅

**Your role:**
- Add formulas to Notion database
- Create chart views
- Test and validate

**Questions?**
- Check formula syntax matches property names exactly
- Verify TOAD sync is running (check auto_sync.log)
- Test with dates that have known task data
