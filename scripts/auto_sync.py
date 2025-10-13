#!/usr/bin/env python3
"""
Auto-sync scheduler for TOAD.
Runs sync command every 5 minutes.
"""

import schedule
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

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

def run_sync():
    """Run the TOAD sync command."""
    try:
        logging.info("Starting sync...")
        
        # Get the script directory and project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        # Run sync command
        result = subprocess.run(
            ["poetry", "run", "toad", "sync"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log output
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logging.info(f"  {line}")
        
        logging.info("✅ Sync completed successfully")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Sync failed with exit code {e.returncode}")
        if e.stderr:
            logging.error(f"Error output: {e.stderr}")
    except FileNotFoundError:
        logging.error("❌ Poetry not found. Make sure Poetry is installed and in PATH")
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")

def main():
    """Main scheduler loop."""
    print("🐸 TOAD Auto-Sync Scheduler")
    print("=" * 40)
    print(f"Log file: {log_file}")
    print("Syncing every 5 minutes...")
    print("Press Ctrl+C to stop")
    print("")
    
    # Schedule sync every 5 minutes
    schedule.every(5).minutes.do(run_sync)
    
    # Run immediately on startup
    logging.info("=" * 60)
    logging.info("🚀 Scheduler started")
    run_sync()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("🛑 Scheduler stopped by user")
        print("\n👋 Scheduler stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
