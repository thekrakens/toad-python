"""
Notion API client for TOAD project.
"""

import logging
from typing import Dict, List, Optional, Any
from notion_client import Client
from notion_client.errors import APIResponseError
from toad.config import Config

logger = logging.getLogger(__name__)

class TOADNotionClient:
    """Enhanced Notion client for TOAD project."""
    
    def __init__(self, token: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize the Notion client.
        
        Args:
            token: Notion API token (uses config default if not provided)
            database_id: Default database ID (uses config default if not provided)
        """
        self.token = token or Config.NOTION_TOKEN
        self.database_id = database_id or Config.NOTION_DATABASE_ID
        
        if not self.token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN in environment or pass to constructor.")
        
        self.client = Client(auth=self.token)
        
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Notion and return user info.
        
        Returns:
            Dict containing user information if successful
        """
        try:
            user_info = self.client.users.me()
            logger.info(f"Successfully connected to Notion as user: {user_info.get('name', 'Unknown')}")
            return user_info
        except APIResponseError as e:
            logger.error(f"Failed to connect to Notion: {e}")
            raise
    
    def get_database_info(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database information including schema.
        
        Args:
            database_id: Database ID to query (uses default if not provided)
            
        Returns:
            Dict containing database information
        """
        db_id = database_id or self.database_id
        if not db_id:
            raise ValueError("Database ID is required")
        
        try:
            database = self.client.databases.retrieve(database_id=db_id)
            return database
        except APIResponseError as e:
            logger.error(f"Failed to retrieve database {db_id}: {e}")
            raise
    
    def get_database_pages(self, database_id: Optional[str] = None, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all pages from a database.
        
        Args:
            database_id: Database ID to query (uses default if not provided)
            page_size: Number of pages to retrieve per request
            
        Returns:
            List of page objects
        """
        db_id = database_id or self.database_id
        if not db_id:
            raise ValueError("Database ID is required")
        
        try:
            pages = []
            has_more = True
            start_cursor = None
            
            while has_more:
                query_params = {
                    "database_id": db_id,
                    "page_size": page_size
                }
                
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                response = self.client.databases.query(**query_params)
                
                pages.extend(response["results"])
                has_more = response["has_more"]
                start_cursor = response.get("next_cursor")
            
            logger.info(f"Retrieved {len(pages)} pages from database {db_id}")
            return pages
            
        except APIResponseError as e:
            logger.error(f"Failed to query database {db_id}: {e}")
            raise
    
    def analyze_database_schema(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the database schema and return a structured summary.
        
        Args:
            database_id: Database ID to analyze (uses default if not provided)
            
        Returns:
            Dict containing schema analysis
        """
        db_info = self.get_database_info(database_id)
        properties = db_info.get("properties", {})
        
        schema_analysis = {
            "database_title": db_info.get("title", [{}])[0].get("text", {}).get("content", "Untitled"),
            "total_properties": len(properties),
            "properties": {},
            "property_types": {}
        }
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "unknown")
            
            schema_analysis["properties"][prop_name] = {
                "type": prop_type,
                "id": prop_info.get("id"),
                "config": prop_info.get(prop_type, {})
            }
            
            if prop_type in schema_analysis["property_types"]:
                schema_analysis["property_types"][prop_type] += 1
            else:
                schema_analysis["property_types"][prop_type] = 1
        
        return schema_analysis
    
    def get_workspace_id(self) -> str:
        """
        Get the workspace (user) ID for creating databases.
        
        Returns:
            The workspace ID
        """
        try:
            user_info = self.client.users.me()
            return user_info["id"]
        except APIResponseError as e:
            logger.error(f"Failed to get workspace ID: {e}")
            raise

    def update_page_properties(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update properties of a specific page.

        Args:
            page_id: The ID of the page to update.
            properties: A dictionary of properties to update.

        Returns:
            The updated page object.
        """
        try:
            updated_page = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"Successfully updated page {page_id}.")
            return updated_page
        except APIResponseError as e:
            logger.error(f"Failed to update page {page_id}: {e}")
            raise
