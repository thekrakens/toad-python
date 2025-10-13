# toad-python

TOAD (Task-Oriented Analytics Dashboard) - A productivity analytics system that syncs with Notion to provide insights on task management, time tracking, and productivity metrics.

## Features

- **Simplified Sync CLI**: Three sync modes (incremental, date-specific, full) with intelligent caching
- **Task Relations Management**: Automatically link tasks to daily metrics based on planning, activity, work, and completion
- **Incremental Sync**: Only fetch and process changed data for fast 2-5 second syncs
- **Smart Caching**: Track last sync timestamps to minimize API calls

## Installation

```bash
# Clone the repository
git clone https://github.com/thekrakens/toad-python.git
cd toad-python

# Install dependencies with Poetry
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your Notion API key and database IDs
```

## Usage

### CLI Commands

The CLI has been simplified to a single `sync` command with three modes:

#### Mode 1: Incremental Sync (Default)
```bash
# Sync today only, uses cache for speed (2-5 seconds)
poetry run toad sync
```

#### Mode 2: Date Sync
```bash
# Sync specific date (5-10 seconds)
poetry run toad sync 10-12-25

# Sync date range (5-10 seconds per date)
poetry run toad sync 10-10-25 10-12-25
```

#### Mode 3: Full Sync
```bash
# Sync last 30 days, reset cache (20-30 seconds)
poetry run toad sync --full
```

#### Cache Management
```bash
# Clear sync cache
poetry run toad sync --clear-cache
```

**Supported Date Formats:**
- `YYYY-MM-DD` (2025-10-12)
- `MM-DD-YY` (10-12-25)
- `MM/DD/YY` (10/12/25)

**Performance Targets:**
- Incremental sync: 2-5 seconds
- Date sync: 5-10 seconds per date
- Full sync: 20-30 seconds

See [Incremental Sync Documentation](docs/incremental_sync_design.md) and [Core Baseline](docs/core_baseline.md) for details.

## Documentation

- [Project Overview](docs/context/project_overview.md)
- [CLI Redesign](docs/cli_redesign.md)
- [Property Cleanup](docs/property_cleanup_recommendation.md)
- [Timezone Strategy](docs/timezone_strategy.md)

## Notion Setup

TOAD requires three main Notion databases:

1. **Tasks Database** - Track all tasks with planning, completion, and metrics
2. **Time Entries Database** - Log work sessions with start/end times
3. **Daily Metrics Database** - Store daily task relations and analytics

Required environment variables:
- `NOTION_API_KEY` - Your Notion integration token
- `NOTION_TASKS_DATABASE_ID` - Tasks database ID
- `NOTION_TIME_ENTRIES_DATABASE_ID` - Time entries database ID
- `NOTION_DAILY_METRICS_DATABASE_ID` - Daily metrics database ID
- `NOTION_TIME_BLOCKS_DATABASE_ID` - Time blocks database ID

## Auto-Sync (Run every 5 minutes)

Set up TOAD to automatically sync every 5 minutes:

### macOS Quick Setup

```bash
# Run the setup script
bash scripts/setup_auto_sync.sh
```

This will configure launchd to run `toad sync` every 5 minutes in the background.

### Alternative: Python Scheduler

```bash
# Run Python scheduler in foreground
poetry run python scripts/auto_sync.py

# Or in background
nohup poetry run python scripts/auto_sync.py > /tmp/toad-scheduler.log 2>&1 &
```

**Monitor sync logs:**
```bash
tail -f /tmp/toad-sync.log
```

For complete setup instructions (including Linux and Windows), see [Auto-Sync Setup Guide](docs/auto_sync_setup.md).

## Development

```bash
# Run tests
poetry run pytest

# Run CLI in development
poetry run toad --help

# Format code
poetry run black .
```

## License

MIT
