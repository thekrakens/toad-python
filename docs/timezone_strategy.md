# Timezone Handling in TOAD

## Overview

TOAD uses **PST (Pacific Standard Time / America/Los_Angeles)** as the primary timezone for all date-based operations. This document explains how timezones are handled throughout the system.

## Why PST?

The system is configured to use PST because:
1. The user's local timezone is PST
2. All "day" boundaries should align with PST midnight, not UTC midnight
3. Notion stores all dates/times in UTC, so we need to convert properly

## How It Works

### 1. Date Boundaries

When we process a date like `2025-10-10`, we need to know exactly when that day starts and ends in PST, then convert those boundaries to UTC for comparison with Notion's UTC timestamps.

**Example:**
- Target Date: `2025-10-10` (October 10, 2025)
- PST Start: `2025-10-10 00:00:00 PST` → converts to `2025-10-10 07:00:00 UTC`
- PST End: `2025-10-10 23:59:59.999999 PST` → converts to `2025-10-11 06:59:59.999999 UTC`

### 2. The Conversion Function

```python
def _get_pst_day_boundaries_utc(self, target_date: date) -> tuple[int, int]:
    """
    Convert PST date to UTC unix timestamp boundaries (start and end of day).
    
    Args:
        target_date: Date to convert (date object)
        
    Returns:
        Tuple of (utc_start_timestamp, utc_end_timestamp)
    """
    pst = pytz.timezone('America/Los_Angeles')
    
    # Create PST start of day (00:00:00 PST)
    pst_start = pst.localize(datetime.combine(target_date, datetime.min.time()))
    # Create PST end of day (23:59:59.999999 PST)
    pst_end = pst.localize(datetime.combine(target_date, datetime.max.time()))
    
    # Convert to UTC unix timestamps
    utc_start = int(pst_start.timestamp())
    utc_end = int(pst_end.timestamp())
    
    return utc_start, utc_end
```

### 3. Planned Tasks - Date Range Matching

For the **Planned** relation, we check if the target date falls **within** the planned date range:

```python
# Task is planned for target_date if the range overlaps with the target day
planned_mask = (
    (planned_start_timestamps > 0) &  # Has a valid start
    (planned_start_timestamps <= utc_end) &  # Starts before or during target day
    (planned_end_timestamps >= utc_start)  # Ends during or after target day
)
```

**Example:**
- Task planned: `2025-10-10 09:00 PST` to `2025-10-10 17:00 PST`
- Target date: `2025-10-10`
- Result: ✅ Task is included (falls within the day)

**Multi-day task example:**
- Task planned: `2025-10-10 09:00 PST` to `2025-10-12 17:00 PST`
- Target date: `2025-10-10` → ✅ Included
- Target date: `2025-10-11` → ✅ Included
- Target date: `2025-10-12` → ✅ Included
- Target date: `2025-10-13` → ❌ Not included

### 4. Worked Tasks - Time Entry Matching

For the **Worked** relation, we check if time entries were logged during the target date:

```python
# Filter entries within the PST day (in UTC)
today_mask = (
    (entry_timestamps >= utc_start) & 
    (entry_timestamps <= utc_end)
)
```

**Example:**
- Time entry logged: `2025-10-10 14:30 PST` (which is `2025-10-10 21:30 UTC`)
- Target date: `2025-10-10`
- PST boundaries: `2025-10-10 07:00 UTC` to `2025-10-11 06:59:59 UTC`
- Result: ✅ Entry is included

### 5. Done Tasks - Completion Date Matching

For the **Done** relation, we check if tasks were completed during the target date:

```python
# Filter tasks completed within the PST day (in UTC)
done_mask = (
    (done_timestamps >= utc_start) & 
    (done_timestamps <= utc_end)
)
```

### 6. Active Tasks - Combination Logic

Active tasks combine multiple criteria:
1. Tasks planned for that day (using date range matching)
2. Tasks worked on that day (using time entry matching)
3. Tasks with earlier planning that aren't done yet

## Data Flow

```
User Input (PST date)
    ↓
Convert to PST day boundaries (00:00:00 to 23:59:59 PST)
    ↓
Convert PST boundaries to UTC timestamps
    ↓
Compare Notion's UTC timestamps against UTC boundaries
    ↓
Return matching tasks
```

## Important Notes

1. **All Notion dates are stored in UTC** - This is how Notion works internally
2. **We always convert to PST for "day" calculations** - This ensures the user's day boundaries are correct
3. **Unix timestamps are used for comparison** - This avoids timezone confusion in pandas operations
4. **Date ranges are inclusive** - A task planned from 9am-5pm on Oct 10 is included in Oct 10's metrics

## Testing Timezone Logic

You can test the timezone logic with specific examples:

```bash
# Test for a specific date
poetry run python test_task_relations_logic.py 2025-10-10

# Debug the planned field structure
poetry run python debug_planned_field.py
```

## Potential Edge Cases

### Daylight Saving Time (DST)

PST observes DST, becoming PDT (Pacific Daylight Time) in summer:
- PST: UTC-8 (winter)
- PDT: UTC-7 (summer)

The `pytz` library automatically handles DST transitions, so:
- Winter date: `2025-01-10 00:00 PST` = `2025-01-10 08:00 UTC`
- Summer date: `2025-07-10 00:00 PDT` = `2025-07-10 07:00 UTC`

### Late Night Tasks

A task worked on at `2025-10-10 23:55 PST` is correctly attributed to Oct 10, not Oct 11, even though it's `2025-10-11 06:55 UTC`.

### Multi-day Tasks

A task planned from `2025-10-10 09:00 PST` to `2025-10-12 17:00 PST` will appear in the Planned relation for all three days: Oct 10, Oct 11, and Oct 12.

## Troubleshooting

If tasks aren't appearing in the correct day's relations:

1. **Check the Notion date format** - Ensure dates are stored with timezone info
2. **Verify the PST timezone** - Confirm your system timezone matches expectations
3. **Use the debug script** - `python debug_planned_field.py` shows the raw date values
4. **Check the test script** - `python test_task_relations_logic.py <date>` shows what would be matched

## Summary

✅ **All "day" boundaries use PST timezone**
✅ **Notion's UTC timestamps are converted to PST for comparison**
✅ **Date ranges are properly handled (tasks can span multiple days)**
✅ **DST transitions are automatically handled by pytz**
✅ **Unix timestamps ensure consistent comparisons**
