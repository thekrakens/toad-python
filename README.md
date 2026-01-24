# toad-python

TOAD (Task-Oriented Analytics Dashboard) - A productivity analytics system that syncs with Notion to provide insights on task management, time tracking, and productivity metrics.

## Features

- **Real-time Health Data Sync**: Event-driven daemon watches iCloud directories for new workout/activity files and syncs immediately
- **Daemon Process Management**: Start/stop/status/restart daemon via CLI or install as macOS system service
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

## TOAD Daemon (Recommended)

The TOAD daemon provides real-time sync by watching iCloud directories for new health data files. When a new workout or activity file is detected, it's automatically processed and synced to Notion.

### Quick Start

```bash
# Start the daemon manually
poetry run toad daemon start

# Check daemon status
poetry run toad daemon status

# View daemon logs
tail -f ~/.toad/daemon.log

# Stop the daemon
poetry run toad daemon stop
```

### Install as System Service (macOS)

For automatic startup on boot and crash recovery:

```bash
# Install daemon as launchd service
bash scripts/install_daemon.sh

# Uninstall daemon service
bash scripts/uninstall_daemon.sh
```

The daemon will:
- Start automatically on system boot
- Restart automatically if it crashes
- Watch for new files in configured iCloud directories
- Process and sync data immediately when files are detected
- Log all activity to `~/.toad/daemon.log`

### Daemon Commands

```bash
poetry run toad daemon start     # Start the daemon in background
poetry run toad daemon stop      # Stop the daemon gracefully
poetry run toad daemon restart   # Restart the daemon
poetry run toad daemon status    # Show daemon status (PID, uptime, etc.)
```

### Monitored Directories

The daemon watches these iCloud directories:
- `~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/TOAD_workouts/`
- `~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/TOAD_Activity/`
- `~/Library/Mobile Documents/com~apple~CloudDocs/TOAD/workout_sync/inbox/gymaholic/`

## Auto-Sync (Legacy - 5 Minute Scheduler)

Alternative to the daemon for periodic syncing:

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
