# TOAD CLI Redesign - Version 0.4.0

## Overview

The TOAD CLI has been redesigned to support flexible date ranges and selective component syncing, making it more efficient for frequent auto-syncing use cases.

## New CLI Structure

### General Sync Command

```bash
# Sync everything for today
toad sync

# Sync everything for a specific date
toad sync 10-12-25

# Sync everything for a date range
toad sync 10-10-25 10-12-25

# Targeted sync for specific component
toad sync --tasks 10-11-25
toad sync --metrics 10-11-25
toad sync --time-blocks 10-11-25

# Or combination
toad sync --tasks --metrics 10-11-25
```

## Key Features

### 1. Flexible Date Formats

The CLI now supports multiple date formats:
- `YYYY-MM-DD` (2025-10-12)
- `MM-DD-YY` (10-12-25)
- `MM/DD/YY` (10/12/25)

### 2. Date Range Support

You can now sync multiple dates at once:
```bash
# Sync task relations for Oct 10-12, 2025
toad sync --tasks 10-10-25 10-12-25
```

This will process all dates in the range inclusively.

### 3. Selective Component Syncing

Three sync flags are available:
- `--tasks` - Sync task relations (date-specific)
- `--metrics` - Sync task performance metrics (all tasks)
- `--time-blocks` - Sync time block sequencing and naming (all blocks)

**Default behavior:** If no flags are specified, all components are synced.

### 4. Component-Specific Behavior

#### Task Relations (`--tasks`)
- **Scope:** Date-specific
- **Action:** For each date, syncs Planned, Active, Worked, and Done task relations
- **Use case:** Daily automation after work sessions

#### Task Metrics (`--metrics`)
- **Scope:** All completed tasks
- **Action:** Calculates and updates Schedule Variance, Estimation Accuracy, Focus Score
- **Use case:** Weekly metrics refresh

#### Time Blocks (`--time-blocks`)
- **Scope:** All time blocks
- **Action:** Sequences blocks, renames them "Task Name (1/3)", updates task planned hours
- **Use case:** After adding/editing time blocks

## Backward Compatibility

The old commands are still available:
```bash
toad update-metrics --completed-only
toad sync-time-blocks --validate-only
toad status 2025-10-12
```

## Examples

### Daily Automation
```bash
# Quick sync of task relations for today
toad sync --tasks

# Or sync everything for today
toad sync
```

### Backfill Missing Data
```bash
# Sync task relations for the past week
toad sync --tasks 10-05-25 10-12-25
```

### Selective Updates
```bash
# Only update metrics (skip task relations and time blocks)
toad sync --metrics

# Update metrics and time blocks, but skip task relations
toad sync --metrics --time-blocks
```

## Future Enhancements

### Incremental Updates (Planned for v0.4.1)

The following optimizations are planned:

#### 1. Last Sync Timestamp Tracking
```python
# Store last sync timestamp in local cache file
~/.toad/last_sync.json
{
  "tasks": "2025-10-12T16:00:00Z",
  "metrics": "2025-10-12T14:00:00Z",
  "time_blocks": "2025-10-12T12:00:00Z"
}
```

#### 2. Incremental Metrics Updates
```python
# Only process tasks modified since last sync
def process_all_tasks(self, filter_completed=False, modified_since=None):
    if modified_since:
        # Add filter to Notion query
        query_filter = {
            "timestamp": "last_edited_time",
            "last_edited_time": {"after": modified_since}
        }
```

#### 3. Incremental Time Block Updates
```python
# Only process time blocks modified since last sync
def sync_time_blocks(self, validate_only=False, modified_since=None):
    # Filter blocks by last_edited_time
```

#### 4. Quick Sync Mode
```bash
# Fast incremental sync (only what changed)
toad sync --quick

# Force full resync
toad sync --full
```

## Performance Considerations

### Current Performance
- **Task relations:** ~2-5 seconds per date
- **Metrics update:** ~30-60 seconds for all tasks (filtered to completed only)
- **Time blocks:** ~15-30 seconds for all blocks

### With Incremental Updates (Estimated)
- **Quick sync (--quick):** ~5-10 seconds total
- **Full sync (--full):** Same as current

### Recommended Automation Schedule
```bash
# Every 10 minutes during work hours (quick mode - future)
*/10 9-17 * * 1-5 cd ~/toad-python && toad sync --quick

# Daily full sync at midnight
0 0 * * * cd ~/toad-python && toad sync --full

# Weekly metrics refresh
0 0 * * 0 cd ~/toad-python && toad sync --metrics
```

## Implementation Details

### Date Parsing
The `parse_date_flexible()` function tries multiple formats:
1. YYYY-MM-DD
2. MM-DD-YY
3. MM/DD/YY

### Date Range Generation
The `parse_date_range()` function:
1. Parses start and end dates
2. Validates end >= start
3. Generates list of all dates in range

### Component Selection Logic
```python
# Determine what to sync
sync_all = not (args.tasks or args.metrics or args.time_blocks)
sync_tasks = sync_all or args.tasks
sync_metrics = sync_all or args.metrics
sync_time_blocks = sync_all or args.time_blocks
```

If no flags are provided, all components are synced.

## Migration Guide

### Old Command → New Command

```bash
# Old: Sync task relations for specific date
toad sync 2025-10-12
# New: Same, but with shorter format
toad sync 10-12-25

# Old: Update metrics for all tasks
toad update-metrics --completed-only
# New: Use sync command
toad sync --metrics

# Old: Sync time blocks
toad sync-time-blocks
# New: Use sync command
toad sync --time-blocks

# Old: Multiple individual commands for full sync
toad sync 2025-10-12
toad update-metrics --completed-only
toad sync-time-blocks
# New: Single command
toad sync 10-12-25
```

## Error Handling

The CLI provides clear error messages:
- Invalid date format
- End date before start date
- Missing database configuration
- Notion API errors

All errors are logged and displayed with context.

## Testing

To test the new CLI:

```bash
# Test help
toad --help
toad sync --help

# Test date parsing
toad sync --tasks 10-12-25      # MM-DD-YY format
toad sync --tasks 10/12/25      # MM/DD/YY format
toad sync --tasks 2025-10-12    # YYYY-MM-DD format

# Test date range
toad sync --tasks 10-10-25 10-12-25

# Test component selection
toad sync --tasks
toad sync --metrics
toad sync --time-blocks
toad sync --tasks --metrics

# Test default (all components)
toad sync
```

## Notes

- The `--dry-run` flag is defined but not yet implemented
- All old commands remain available for backward compatibility
- Date range works only for task relations (metrics and time blocks are always global)
- Default date is today if no date is provided
