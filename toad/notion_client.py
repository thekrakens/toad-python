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
    
    def get_database_pages(self, database_id: Optional[str] = None, page_size: int = 100, 
                          filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all pages from a database with optional filtering.
        
        Args:
            database_id: Database ID to query (uses default if not provided)
            page_size: Number of pages to retrieve per request
            filter_dict: Optional filter to apply to the query
            
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
                
                if filter_dict:
                    query_params["filter"] = filter_dict
                
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

    def get_page_properties(self, page_id: str) -> Dict[str, Any]:
        """
        Get current properties of a page.

        Args:
            page_id: The ID of the page to retrieve.

        Returns:
            Dict containing page properties.
        """
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            return page.get("properties", {})
        except APIResponseError as e:
            logger.error(f"Failed to retrieve page {page_id}: {e}")
            raise

    def _extract_property_value(self, property_data: Dict[str, Any]) -> Any:
        """
        Extract the actual value from a Notion property object.

        Args:
            property_data: The property data from Notion API

        Returns:
            The extracted value (number, string, bool, etc.)
        """
        prop_type = property_data.get("type")

        if prop_type == "number":
            return property_data.get("number")
        elif prop_type == "checkbox":
            return property_data.get("checkbox")
        elif prop_type == "title":
            title_parts = property_data.get("title", [])
            return title_parts[0].get("text", {}).get("content", "") if title_parts else ""
        elif prop_type == "rich_text":
            text_parts = property_data.get("rich_text", [])
            return text_parts[0].get("text", {}).get("content", "") if text_parts else ""
        elif prop_type == "date":
            date_obj = property_data.get("date")
            return date_obj.get("start") if date_obj else None
        elif prop_type == "select":
            select_obj = property_data.get("select")
            return select_obj.get("name") if select_obj else None
        elif prop_type == "relation":
            relations = property_data.get("relation", [])
            return [r.get("id") for r in relations]
        else:
            # For other types, return the raw data
            return property_data.get(prop_type)

    def _properties_differ(self, current_value: Any, new_value: Any) -> bool:
        """
        Check if two property values are different.

        Args:
            current_value: Current value from Notion
            new_value: New value to compare

        Returns:
            True if values differ, False if same
        """
        # Handle None comparisons
        if current_value is None and new_value is None:
            return False
        if current_value is None or new_value is None:
            return True

        # Handle numeric comparisons with tolerance for floating point
        if isinstance(current_value, (int, float)) and isinstance(new_value, (int, float)):
            return abs(current_value - new_value) > 0.0001

        # Handle list comparisons (for relations)
        if isinstance(current_value, list) and isinstance(new_value, list):
            return set(current_value) != set(new_value)

        # Default: direct comparison
        return current_value != new_value

    def update_page_properties_smart(self, page_id: str, new_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update page properties only if values have changed.

        This method:
        1. Fetches current page properties
        2. Compares with new values (property by property)
        3. Updates only changed fields in a single API call
        4. Returns audit trail of what changed

        Args:
            page_id: The ID of the page to update
            new_properties: Dict of properties to update (in Notion API format)

        Returns:
            Dict with:
                - success: bool
                - updated_fields: List of property names that were updated
                - unchanged_fields: List of property names that matched
                - changes: Dict of {property: {old: ..., new: ...}}
        """
        try:
            # Fetch current properties
            current_properties = self.get_page_properties(page_id)

            # Compare and build update dict
            properties_to_update = {}
            updated_fields = []
            unchanged_fields = []
            changes = {}

            for prop_name, new_prop_data in new_properties.items():
                # Get current value
                current_prop_data = current_properties.get(prop_name, {})
                current_value = self._extract_property_value(current_prop_data)

                # Extract new value from the property format
                new_value = self._extract_property_value(new_prop_data)

                # Compare values
                if self._properties_differ(current_value, new_value):
                    properties_to_update[prop_name] = new_prop_data
                    updated_fields.append(prop_name)
                    changes[prop_name] = {"old": current_value, "new": new_value}
                else:
                    unchanged_fields.append(prop_name)

            # If nothing changed, return early
            if not properties_to_update:
                logger.info(f"No changes detected for page {page_id}. Skipping update.")
                return {
                    "success": True,
                    "updated_fields": [],
                    "unchanged_fields": unchanged_fields,
                    "changes": {}
                }

            # Update only changed properties
            self.client.pages.update(
                page_id=page_id,
                properties=properties_to_update
            )

            logger.info(f"Updated page {page_id}: {', '.join(updated_fields)}")

            return {
                "success": True,
                "updated_fields": updated_fields,
                "unchanged_fields": unchanged_fields,
                "changes": changes
            }

        except APIResponseError as e:
            logger.error(f"Failed to smart update page {page_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated_fields": [],
                "unchanged_fields": [],
                "changes": {}
            }

    def get_or_create_page(self, database_id: str, query_property: str,
                          query_value: str, create_properties: Dict[str, Any]) -> Optional[str]:
        """
        Find a page by querying a property, or create it if not found.

        Args:
            database_id: The database to search/create in
            query_property: Property name to query (e.g., "Date")
            query_value: Value to search for (e.g., "2026-01-17")
            create_properties: Properties to use when creating (if not found)

        Returns:
            Page ID (existing or newly created), or None if operation failed
        """
        try:
            # Build filter based on property type
            # Assume date property for now (most common use case)
            filter_dict = {
                "property": query_property,
                "date": {
                    "equals": query_value
                }
            }

            # Query for existing page
            query_result = self.client.databases.query(
                database_id=database_id,
                filter=filter_dict
            )

            if query_result.get("results"):
                # Found existing page
                page_id = query_result["results"][0]["id"]
                logger.debug(f"Found existing page with {query_property}={query_value}: {page_id}")
                return page_id

            # Create new page
            logger.info(f"Creating new page in {database_id} with {query_property}={query_value}")
            new_page = self.client.pages.create(
                parent={"database_id": database_id},
                properties=create_properties
            )

            page_id = new_page["id"]
            logger.info(f"Created new page: {page_id}")
            return page_id

        except APIResponseError as e:
            logger.error(f"Error in get_or_create_page: {e}")
            return None
