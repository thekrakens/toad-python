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
