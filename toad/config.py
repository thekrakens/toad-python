"""
Configuration management for TOAD project.
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for TOAD project."""
    
    # Notion Configuration
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")
    NOTION_TIME_BLOCKS_DATABASE_ID: str = os.getenv("NOTION_TIME_BLOCKS_DATABASE_ID", "")
    NOTION_DAILY_METRICS_DATABASE_ID: str = os.getenv("NOTION_DAILY_METRICS_DATABASE_ID", "")
    NOTION_TIME_ENTRIES_DATABASE_ID: str = os.getenv("NOTION_TIME_ENTRIES_DATABASE_ID", "")

    # Health Module Databases
    NOTION_HABITS_DATABASE_ID: str = os.getenv("NOTION_HABITS_DATABASE_ID", "")
    NOTION_WORKOUTS_DATABASE_ID: str = os.getenv("NOTION_WORKOUTS_DATABASE_ID", "")
    NOTION_HEALTH_STATS_DATABASE_ID: str = os.getenv("NOTION_HEALTH_STATS_DATABASE_ID", "")

    # Workout Sync Paths (iCloud Drive)
    WORKOUT_SYNC_INBOX_PATH: str = os.getenv("WORKOUT_SYNC_INBOX_PATH", "")
    WORKOUT_SYNC_PROCESSED_PATH: str = os.getenv("WORKOUT_SYNC_PROCESSED_PATH", "")
    WORKOUT_SYNC_FAILED_PATH: str = os.getenv("WORKOUT_SYNC_FAILED_PATH", "")

    # HealthAutoExport Paths
    HEALTH_AUTO_EXPORT_WORKOUTS_PATH: str = os.getenv("HEALTH_AUTO_EXPORT_WORKOUTS_PATH", "")
    HEALTH_AUTO_EXPORT_ACTIVITY_PATH: str = os.getenv("HEALTH_AUTO_EXPORT_ACTIVITY_PATH", "")

    # Sync Intervals (in minutes)
    PRODUCTIVITY_SYNC_INTERVAL: int = int(os.getenv("PRODUCTIVITY_SYNC_INTERVAL", "5"))
    HEALTH_SYNC_INTERVAL: int = int(os.getenv("HEALTH_SYNC_INTERVAL", "30"))

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    @classmethod
    def validate_notion_config(cls) -> bool:
        """Validate that required Notion configuration is present."""
        return bool(cls.NOTION_TOKEN and cls.NOTION_DATABASE_ID)
    
    @classmethod
    def validate_time_blocks_config(cls) -> bool:
        """Validate that Time Blocks database configuration is present."""
        return bool(cls.NOTION_TOKEN and cls.NOTION_TIME_BLOCKS_DATABASE_ID)

    @classmethod
    def validate_time_entries_config(cls) -> bool:
        """Validate that Time Entries database configuration is present."""
        return bool(cls.NOTION_TOKEN and cls.NOTION_TIME_ENTRIES_DATABASE_ID)

    @classmethod
    def validate_health_config(cls) -> bool:
        """Validate that Health module configuration is present."""
        return bool(
            cls.NOTION_TOKEN
            and cls.NOTION_HABITS_DATABASE_ID
            and cls.NOTION_WORKOUTS_DATABASE_ID
            and cls.NOTION_HEALTH_STATS_DATABASE_ID
        )

    @classmethod
    def validate_workout_sync_paths(cls) -> bool:
        """Validate that workout sync paths are configured."""
        return bool(
            cls.WORKOUT_SYNC_INBOX_PATH
            and cls.WORKOUT_SYNC_PROCESSED_PATH
            and cls.WORKOUT_SYNC_FAILED_PATH
        )

    @classmethod
    def validate_health_auto_export_paths(cls) -> bool:
        """Validate that HealthAutoExport paths are configured."""
        return bool(
            cls.HEALTH_AUTO_EXPORT_WORKOUTS_PATH
            and cls.HEALTH_AUTO_EXPORT_ACTIVITY_PATH
        )

    @classmethod
    def get_available_llm_providers(cls) -> list[str]:
        """Get list of available LLM providers based on configured API keys."""
        providers = []
        
        if cls.OPENAI_API_KEY:
            providers.append("openai")
        if cls.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if cls.GOOGLE_API_KEY:
            providers.append("google")
        
        # Always include ollama as it's local
        providers.append("ollama")
        
        return providers
