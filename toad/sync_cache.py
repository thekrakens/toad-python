"""
Sync Cache Manager for TOAD productivity system.
Stores timestamps of last successful syncs to enable incremental updates.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Cache file location
CACHE_DIR = Path.home() / ".toad"
CACHE_FILE = CACHE_DIR / "sync_cache.json"


class SyncCache:
    """Manage sync timestamp cache for incremental updates."""
    
    def __init__(self, cache_file: Path = CACHE_FILE):
        """
        Initialize the sync cache.
        
        Args:
            cache_file: Path to the cache file
        """
        self.cache_file = cache_file
        self._ensure_cache_dir()
        self._cache_data = self._load_cache()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self) -> Dict:
        """
        Load cache from file.
        
        Returns:
            Dictionary with cache data
        """
        if not self.cache_file.exists():
            return {"last_sync": {}}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load sync cache: {e}. Starting fresh.")
            return {"last_sync": {}}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sync cache: {e}")
    
    def get_last_sync_time(self, component: str) -> Optional[datetime]:
        """
        Get the last sync timestamp for a component.
        
        Args:
            component: Component name (e.g., 'tasks', 'time_entries', 'time_blocks')
            
        Returns:
            Last sync datetime, or None if never synced
        """
        timestamp_str = self._cache_data.get("last_sync", {}).get(component)
        
        if not timestamp_str:
            return None
        
        try:
            return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.warning(f"Invalid timestamp for {component}: {e}")
            return None
    
    def update_last_sync_time(self, component: str, timestamp: Optional[datetime] = None):
        """
        Update the last sync timestamp for a component.
        
        Args:
            component: Component name (e.g., 'tasks', 'time_entries', 'time_blocks')
            timestamp: Timestamp to store (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Ensure last_sync dict exists
        if "last_sync" not in self._cache_data:
            self._cache_data["last_sync"] = {}
        
        # Store as ISO format string
        self._cache_data["last_sync"][component] = timestamp.isoformat()
        
        self._save_cache()
        logger.info(f"Updated {component} last sync time to {timestamp}")
    
    def clear_component(self, component: str):
        """
        Clear the last sync time for a component.
        
        Args:
            component: Component name to clear
        """
        if "last_sync" in self._cache_data and component in self._cache_data["last_sync"]:
            del self._cache_data["last_sync"][component]
            self._save_cache()
            logger.info(f"Cleared {component} last sync time")
    
    def clear_all(self):
        """Clear all sync timestamps (force full sync next time)."""
        self._cache_data = {"last_sync": {}}
        self._save_cache()
        logger.info("Cleared all sync cache")
    
    def get_all_sync_times(self) -> Dict[str, datetime]:
        """
        Get all sync timestamps.
        
        Returns:
            Dictionary mapping component names to last sync times
        """
        result = {}
        for component, timestamp_str in self._cache_data.get("last_sync", {}).items():
            try:
                result[component] = datetime.fromisoformat(timestamp_str)
            except Exception as e:
                logger.warning(f"Invalid timestamp for {component}: {e}")
        
        return result


# Global cache instance
_cache_instance = None


def get_sync_cache() -> SyncCache:
    """
    Get the global sync cache instance.
    
    Returns:
        SyncCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SyncCache()
    return _cache_instance
