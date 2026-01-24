#!/usr/bin/env python3
"""
Auto-sync scheduler for TOAD.

Runs multiple sync jobs at different intervals:
- Productivity sync (default: every 5 minutes)
- Health sync (default: every 30 minutes, includes Health Stats ETL)

When multiple jobs align at the same time, they run sequentially.
"""

import schedule
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
from threading import Lock

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from toad.config import Config

# Setup logging
log_file = Path.home() / ".toad" / "auto_sync.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Lock to prevent concurrent execution
sync_lock = Lock()


def run_productivity_sync():
    """Run productivity sync."""
    with sync_lock:
        try:
            logging.info("🔄 Starting productivity sync...")

            # Get project root
            project_root = Path(__file__).parent.parent

            # Run productivity sync command
            result = subprocess.run(
                ["poetry", "run", "toad", "sync", "productivity"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )

            # Log output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():  # Skip empty lines
                        logging.info(f"  {line}")

            logging.info("✅ Productivity sync completed")

        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Productivity sync failed with exit code {e.returncode}")
            if e.stderr:
                logging.error(f"Error output: {e.stderr}")
        except subprocess.TimeoutExpired:
            logging.error("❌ Productivity sync timed out (5 minutes)")
        except FileNotFoundError:
            logging.error("❌ Poetry not found. Make sure Poetry is installed and in PATH")
        except Exception as e:
            logging.error(f"❌ Unexpected error in productivity sync: {e}")


def run_health_sync():
    """Run health sync (includes Health Stats ETL)."""
    with sync_lock:
        try:
            logging.info("💪 Starting health sync...")

            # Get project root
            project_root = Path(__file__).parent.parent

            # Run health sync for last 30 days (to catch any backfill)
            result = subprocess.run(
                ["poetry", "run", "toad", "sync", "health", "--full"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minute timeout
            )

            # Log output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():  # Skip empty lines
                        logging.info(f"  {line}")

            logging.info("✅ Health sync completed (includes Health Stats ETL)")

        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Health sync failed with exit code {e.returncode}")
            if e.stderr:
                logging.error(f"Error output: {e.stderr}")
        except subprocess.TimeoutExpired:
            logging.error("❌ Health sync timed out (10 minutes)")
        except FileNotFoundError:
            logging.error("❌ Poetry not found. Make sure Poetry is installed and in PATH")
        except Exception as e:
            logging.error(f"❌ Unexpected error in health sync: {e}")


def main():
    """Main scheduler loop."""
    # Load intervals from config
    productivity_interval = Config.PRODUCTIVITY_SYNC_INTERVAL
    health_interval = Config.HEALTH_SYNC_INTERVAL

    print("🐸 TOAD Auto-Sync Scheduler")
    print("=" * 60)
    print(f"📁 Log file: {log_file}")
    print(f"⏱️  Sync Intervals:")
    print(f"   • Productivity: every {productivity_interval} minutes")
    print(f"   • Health:       every {health_interval} minutes (includes ETL)")
    print()
    print("📝 Note: When multiple syncs align, they run sequentially")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)
    print("")

    # Schedule syncs
    schedule.every(productivity_interval).minutes.do(run_productivity_sync)
    schedule.every(health_interval).minutes.do(run_health_sync)

    # Log startup
    logging.info("=" * 60)
    logging.info("🚀 Scheduler started")
    logging.info(f"   Productivity sync: every {productivity_interval} minutes")
    logging.info(f"   Health sync: every {health_interval} minutes")

    # Run both immediately on startup
    logging.info("🔄 Running initial sync...")
    run_productivity_sync()
    run_health_sync()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("=" * 60)
        logging.info("🛑 Scheduler stopped by user")
        print("\n👋 Scheduler stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
