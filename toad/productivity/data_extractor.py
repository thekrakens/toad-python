"""
Data extraction and cleaning for TOAD productivity analytics.
Handles extraction of task data from Notion and conversion to pandas DataFrames.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import numpy as np
from toad.notion_client import TOADNotionClient
from toad.config import Config

logger = logging.getLogger(__name__)

class TaskDataExtractor:
    """Extract and clean task data from Notion for productivity analysis."""
    
    def __init__(self, notion_client: TOADNotionClient):
        """
        Initialize the data extractor.
        
        Args:
            notion_client: Configured TOAD Notion client
        """
        self.client = notion_client
        self._schema_cache = None
        
    def get_database_schema(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get and cache database schema for property mapping.
        
        Args:
            database_id: Database ID (uses default if not provided)
            
        Returns:
            Database schema information
        """
        if self._schema_cache is None:
            self._schema_cache = self.client.analyze_database_schema(database_id)
        return self._schema_cache
    
    def extract_property_value(self, prop_data: Dict[str, Any], prop_name: str) -> Any:
        """
        Extract value from a Notion property based on its type.
        
        Args:
            prop_data: Property data from Notion API
            prop_name: Name of the property
            
        Returns:
            Extracted and cleaned property value
        """
        prop_type = prop_data.get("type")
        
        try:
            if prop_type == "title":
                title_list = prop_data.get("title", [])
                if title_list and len(title_list) > 0:
                    return title_list[0].get("text", {}).get("content", "")
                return ""
                
            elif prop_type == "rich_text":
                rich_text_list = prop_data.get("rich_text", [])
                if rich_text_list and len(rich_text_list) > 0:
                    # Combine all rich text segments
                    return " ".join([
                        segment.get("text", {}).get("content", "")
                        for segment in rich_text_list
                    ])
                return ""
                
            elif prop_type == "select":
                select_obj = prop_data.get("select")
                return select_obj.get("name", "") if select_obj else ""
                
            elif prop_type == "multi_select":
                return [item.get("name", "") for item in prop_data.get("multi_select", [])]
                
            elif prop_type == "date":
                date_obj = prop_data.get("date")
                if date_obj:
                    start_date = date_obj.get("start")
                    end_date = date_obj.get("end")
                    if start_date and end_date:
                        return {"start": start_date, "end": end_date}
                    elif start_date:
                        return start_date
                return None
                
            elif prop_type == "number":
                return prop_data.get("number")
                
            elif prop_type == "checkbox":
                return prop_data.get("checkbox", False)
                
            elif prop_type == "status":
                status_obj = prop_data.get("status")
                return status_obj.get("name", "") if status_obj else ""
                
            elif prop_type == "formula":
                formula_obj = prop_data.get("formula")
                if formula_obj:
                    formula_type = formula_obj.get("type")
                    if formula_type == "number":
                        return formula_obj.get("number")
                    elif formula_type == "string":
                        return formula_obj.get("string", "")
                    elif formula_type == "boolean":
                        return formula_obj.get("boolean", False)
                    elif formula_type == "date":
                        date_obj = formula_obj.get("date")
                        return date_obj.get("start") if date_obj else None
                return None
                
            elif prop_type == "rollup":
                rollup_obj = prop_data.get("rollup")
                if rollup_obj:
                    rollup_type = rollup_obj.get("type")
                    if rollup_type == "number":
                        return rollup_obj.get("number")
                    elif rollup_type == "array":
                        return rollup_obj.get("array", [])
                return None
                
            elif prop_type == "relation":
                relations = prop_data.get("relation", [])
                return [rel.get("id") for rel in relations] if relations else []
                
            elif prop_type == "created_time":
                return prop_data.get("created_time")
                
            elif prop_type == "last_edited_time":
                return prop_data.get("last_edited_time")
                
            elif prop_type == "button":
                return None  # Buttons don't have values
                
            else:
                logger.warning(f"Unknown property type '{prop_type}' for property '{prop_name}'")
                return f"<unsupported:{prop_type}>"
                
        except Exception as e:
            logger.error(f"Error extracting property '{prop_name}' of type '{prop_type}': {e}")
            return None
    
    def extract_tasks_to_dataframe(self, database_id: Optional[str] = None, 
                                  modified_since: Optional[datetime] = None) -> pd.DataFrame:
        """
        Extract all tasks from the database and convert to a pandas DataFrame.
        
        Args:
            database_id: Database ID (uses default if not provided)
            modified_since: If provided, only fetch tasks modified after this timestamp
            
        Returns:
            DataFrame with cleaned task data
        """
        logger.info("Starting task data extraction...")
        
        # Build filter for incremental sync
        filter_dict = None
        if modified_since:
            filter_dict = {
                "timestamp": "last_edited_time",
                "last_edited_time": {
                    "after": modified_since.isoformat()
                }
            }
            logger.info(f"Filtering tasks modified after {modified_since.isoformat()}")
        
        # Get all pages from the database
        pages = self.client.get_database_pages(database_id, filter_dict=filter_dict)
        logger.info(f"Retrieved {len(pages)} pages from database")
        
        # Get schema for reference
        schema = self.get_database_schema(database_id)
        
        # Extract data from each page
        task_records = []
        for page in pages:
            task_record = {
                "page_id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url", "")
            }
            
            # Extract all properties
            for prop_name, prop_data in page.get("properties", {}).items():
                value = self.extract_property_value(prop_data, prop_name)
                task_record[prop_name] = value
            
            task_records.append(task_record)
        
        # Convert to DataFrame
        df = pd.DataFrame(task_records)
        
        # Clean and process the DataFrame
        df = self._clean_dataframe(df)
        
        logger.info(f"Successfully extracted {len(df)} tasks with {len(df.columns)} columns")
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process the extracted DataFrame.
        
        Args:
            df: Raw DataFrame from extraction
            
        Returns:
            Cleaned DataFrame with proper data types
        """
        logger.info("Cleaning and processing DataFrame...")
        
        # Convert datetime columns
        datetime_columns = [
            "created_time", "last_edited_time", "Completed", "Due", 
            "Doing", "Planned Timeline"
        ]
        
        for col in datetime_columns:
            if col in df.columns:
                df[col] = self._parse_datetime_column(df[col])
        
        # Handle special date ranges (like Planned Timeline and Planned)
        if "Planned Timeline" in df.columns:
            df["planned_start"] = df["Planned Timeline"].apply(
                lambda x: self._extract_date_start(x) if pd.notna(x) else None
            )
            df["planned_end"] = df["Planned Timeline"].apply(
                lambda x: self._extract_date_end(x) if pd.notna(x) else None
            )
        elif "Planned" in df.columns:
            # Also handle the "Planned" column if it exists (same format as Planned Timeline)
            df["planned_start"] = df["Planned"].apply(
                lambda x: self._extract_date_start(x) if pd.notna(x) else None
            )
            df["planned_end"] = df["Planned"].apply(
                lambda x: self._extract_date_end(x) if pd.notna(x) else None
            )
        
        # Convert numeric columns
        numeric_columns = [
            "Logged Time", "Planned Hrs.", "Schedule Variance", 
            "Adherence Score", "Task Age", "Context Switches",
            "Est Hours", "Total Planned Block Time (mins)", "Total Planned Block Time (hrs)",
            "Planned Block Count", "Time Estimation Accuracy"
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert boolean columns
        boolean_columns = [
            "Planned Task", "Active Today", "Has Time Blocks"
        ]
        
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool, errors='ignore')
        
        # Clean status and categorical columns
        categorical_columns = ["Status", "Task Type", "Planned Adherence", "Due Adherence"]
        
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype('category', errors='ignore')
        
        # Handle multi-select columns (convert from lists to strings for easier analysis)
        if "Task Type" in df.columns:
            df["task_types_str"] = df["Task Type"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x) if x else ""
            )
        
        # Calculate derived metrics
        df = self._calculate_derived_metrics(df)
        
        return df
    
    def _parse_datetime_column(self, series: pd.Series) -> pd.Series:
        """Parse datetime column with error handling."""
        try:
            # Handle mixed types in the series (some may be dicts, some strings, some None)
            def parse_single_value(val):
                if pd.isna(val) or val is None:
                    return None
                elif isinstance(val, dict):
                    # For date ranges, extract the start date
                    return val.get('start') if val.get('start') else None
                else:
                    return val
            
            # Apply the parsing function to handle mixed types
            cleaned_series = series.apply(parse_single_value)
            return pd.to_datetime(cleaned_series, errors='coerce', utc=True)
        except Exception as e:
            logger.warning(f"Error parsing datetime column: {e}")
            return series
    
    def _extract_date_start(self, date_value: Any) -> Optional[datetime]:
        """Extract start date from a date range or single date."""
        if isinstance(date_value, dict):
            start_date = date_value.get("start")
            return pd.to_datetime(start_date, errors='coerce', utc=True) if start_date else None
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value, errors='coerce', utc=True)
        return None
    
    def _extract_date_end(self, date_value: Any) -> Optional[datetime]:
        """Extract end date from a date range or single date."""
        if isinstance(date_value, dict):
            end_date = date_value.get("end")
            return pd.to_datetime(end_date, errors='coerce', utc=True) if end_date else None
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value, errors='coerce', utc=True)
        return None
    
    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional derived metrics for analysis."""
        
        # Return early if dataframe is empty
        if df.empty:
            return df
        
        # Task completion status
        if "Status" in df.columns:
            df["is_completed"] = df["Status"] == "done"
            df["is_in_progress"] = df["Status"].isin(["doing", "paused"])
            df["is_todo"] = df["Status"] == "todo"
        
        # Time-based metrics
        if "Logged Time" in df.columns and "Planned Hrs." in df.columns:
            df["logged_hours"] = df["Logged Time"] / 60  # Convert minutes to hours
            df["time_variance_hours"] = df["logged_hours"] - df["Planned Hrs."]
            df["time_efficiency"] = np.where(
                df["Planned Hrs."] > 0,
                df["Planned Hrs."] / df["logged_hours"],
                np.nan
            )
        
        # Date-based metrics
        current_time = datetime.now(timezone.utc)
        
        if "Due" in df.columns:
            # Ensure Due column is properly converted to datetime
            due_column = pd.to_datetime(df["Due"], errors='coerce', utc=True)
            df["days_until_due"] = (due_column - current_time).dt.days
            df["is_overdue"] = (due_column < current_time) & (~df["is_completed"])
        
        if "created_time" in df.columns:
            df["days_since_created"] = (current_time - df["created_time"]).dt.days
        
        # Planned timeline metrics
        if "planned_start" in df.columns and "planned_end" in df.columns:
            # Ensure both columns are datetime and not null
            planned_start = pd.to_datetime(df["planned_start"], errors='coerce', utc=True)
            planned_end = pd.to_datetime(df["planned_end"], errors='coerce', utc=True)
            
            # Only calculate duration where both start and end are valid
            valid_mask = planned_start.notna() & planned_end.notna()
            df["planned_duration_hours"] = np.nan
            df.loc[valid_mask, "planned_duration_hours"] = (
                (planned_end[valid_mask] - planned_start[valid_mask]).dt.total_seconds() / 3600
            )
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the extracted data and return quality metrics.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results and data quality metrics
        """
        validation_results = {
            "total_tasks": len(df),
            "columns": list(df.columns),
            "missing_data": {},
            "data_types": {},
            "quality_score": 0.0,
            "issues": []
        }
        
        # Check for missing data
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            validation_results["missing_data"][col] = {
                "count": int(missing_count),
                "percentage": round(missing_pct, 2)
            }
        
        # Check data types
        for col in df.columns:
            validation_results["data_types"][col] = str(df[col].dtype)
        
        # Critical field validation
        critical_fields = ["Name", "Status", "created_time"]
        for field in critical_fields:
            if field not in df.columns:
                validation_results["issues"].append(f"Missing critical field: {field}")
            elif df[field].isna().sum() > 0:
                validation_results["issues"].append(f"Missing values in critical field: {field}")
        
        # Calculate quality score (0-100)
        quality_factors = []
        
        # Completeness factor
        overall_completeness = (1 - df.isna().sum().sum() / (len(df) * len(df.columns))) * 100
        quality_factors.append(overall_completeness)
        
        # Critical fields factor
        critical_completeness = 100
        for field in critical_fields:
            if field in df.columns:
                field_completeness = (1 - df[field].isna().sum() / len(df)) * 100
                critical_completeness = min(critical_completeness, field_completeness)
        quality_factors.append(critical_completeness)
        
        validation_results["quality_score"] = round(sum(quality_factors) / len(quality_factors), 2)
        
        logger.info(f"Data validation complete. Quality score: {validation_results['quality_score']}")
        
        return validation_results

    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the extracted data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "basic_stats": {
                "total_tasks": len(df),
                "completed_tasks": df["is_completed"].sum() if "is_completed" in df.columns else 0,
                "in_progress_tasks": df["is_in_progress"].sum() if "is_in_progress" in df.columns else 0,
                "todo_tasks": df["is_todo"].sum() if "is_todo" in df.columns else 0,
            },
            "date_range": {},
            "time_stats": {},
            "task_types": {}
        }
        
        # Date range analysis
        if "created_time" in df.columns:
            summary["date_range"]["earliest_task"] = df["created_time"].min()
            summary["date_range"]["latest_task"] = df["created_time"].max()
            summary["date_range"]["span_days"] = (
                df["created_time"].max() - df["created_time"].min()
            ).days
        
        # Time statistics
        if "logged_hours" in df.columns:
            logged_hours = df["logged_hours"].dropna()
            if not logged_hours.empty:
                summary["time_stats"]["total_logged_hours"] = round(logged_hours.sum(), 2)
                summary["time_stats"]["avg_hours_per_task"] = round(logged_hours.mean(), 2)
                summary["time_stats"]["median_hours_per_task"] = round(logged_hours.median(), 2)
        
        # Task type distribution
        if "task_types_str" in df.columns:
            task_type_counts = df["task_types_str"].value_counts()
            summary["task_types"] = task_type_counts.head(10).to_dict()
        
        return summary


class TimeBlockExtractor:
    """Extract and clean time block data from Notion for productivity analysis."""
    
    def __init__(self, notion_client: TOADNotionClient):
        """
        Initialize the time block data extractor.
        
        Args:
            notion_client: Configured TOAD Notion client
        """
        self.client = notion_client
        self._schema_cache = None
        
    def get_database_schema(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get and cache database schema for property mapping.
        
        Args:
            database_id: Time blocks database ID (uses config if not provided)
            
        Returns:
            Database schema information
        """
        if self._schema_cache is None:
            db_id = database_id or Config.NOTION_TIME_BLOCKS_DATABASE_ID
            self._schema_cache = self.client.analyze_database_schema(db_id)
        return self._schema_cache
    
    def extract_property_value(self, prop_data: Dict[str, Any], prop_name: str) -> Any:
        """
        Extract value from a Notion property based on its type.
        Uses the same property extraction logic as TaskDataExtractor.
        
        Args:
            prop_data: Property data from Notion API
            prop_name: Name of the property
            
        Returns:
            Extracted and cleaned property value
        """
        # Reuse the same property extraction logic from TaskDataExtractor
        extractor = TaskDataExtractor(self.client)
        return extractor.extract_property_value(prop_data, prop_name)
    
    def extract_time_blocks_to_dataframe(self, database_id: Optional[str] = None) -> pd.DataFrame:
        """
        Extract all time blocks from the database and convert to a pandas DataFrame.
        
        Args:
            database_id: Time blocks database ID (uses config if not provided)
            
        Returns:
            DataFrame with cleaned time block data
        """
        logger.info("Starting time block data extraction...")
        
        # Use configured time blocks database ID if not provided
        db_id = database_id or Config.NOTION_TIME_BLOCKS_DATABASE_ID
        
        if not db_id:
            raise ValueError("Time blocks database ID not configured. Please set NOTION_TIME_BLOCKS_DATABASE_ID in .env")
        
        # Get all pages from the time blocks database
        pages = self.client.get_database_pages(db_id)
        logger.info(f"Retrieved {len(pages)} time block pages from database")
        
        # Get schema for reference
        schema = self.get_database_schema(db_id)
        
        # Extract data from each page
        time_block_records = []
        for page in pages:
            time_block_record = {
                "block_id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url", "")
            }
            
            # Extract all properties
            for prop_name, prop_data in page.get("properties", {}).items():
                value = self.extract_property_value(prop_data, prop_name)
                time_block_record[prop_name] = value
            
            time_block_records.append(time_block_record)
        
        # Convert to DataFrame
        df = pd.DataFrame(time_block_records)
        
        # Clean and process the DataFrame
        df = self._clean_dataframe(df)
        
        logger.info(f"Successfully extracted {len(df)} time blocks with {len(df.columns)} columns")
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process the extracted time blocks DataFrame.
        
        Args:
            df: Raw DataFrame from extraction
            
        Returns:
            Cleaned DataFrame with proper data types
        """
        logger.info("Cleaning and processing time blocks DataFrame...")
        
        # Convert datetime columns
        datetime_columns = [
            "created_time", "last_edited_time", "Block Start", "Block End", 
            "Scheduled Date", "Planned Time Range"
        ]
        
        for col in datetime_columns:
            if col in df.columns:
                df[col] = self._parse_datetime_column(df[col])
        
        # Handle time range columns (extract start and end times)
        if "Planned Time Range" in df.columns:
            df["block_start_time"] = df["Planned Time Range"].apply(
                lambda x: self._extract_date_start(x) if pd.notna(x) else None
            )
            df["block_end_time"] = df["Planned Time Range"].apply(
                lambda x: self._extract_date_end(x) if pd.notna(x) else None
            )
        
        # Convert numeric columns
        numeric_columns = [
            "Duration (minutes)", "Planned Duration", "Actual Duration",
            "Block Size", "Priority Score", "Effort Level"
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert boolean columns
        boolean_columns = [
            "Completed", "Adhered To", "Interrupted", "Productive",
            "Fragmented", "Focus Block"
        ]
        
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool, errors='ignore')
        
        # Clean categorical columns
        categorical_columns = [
            "Block Type", "Status", "Task Category", "Energy Level",
            "Environment", "Block Pattern"
        ]
        
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype('category', errors='ignore')
        
        # Handle relation columns (Task references)
        if "Related Tasks" in df.columns:
            # Convert task relation IDs to a more usable format
            df["related_task_ids"] = df["Related Tasks"].apply(
                lambda x: x if isinstance(x, list) else []
            )
            df["related_task_count"] = df["related_task_ids"].apply(len)
        
        # Calculate derived metrics
        df = self._calculate_derived_metrics(df)
        
        return df
    
    def _parse_datetime_column(self, series: pd.Series) -> pd.Series:
        """Parse datetime column with error handling."""
        try:
            def parse_single_value(val):
                if pd.isna(val) or val is None:
                    return None
                elif isinstance(val, dict):
                    # For date ranges, extract the start date
                    return val.get('start') if val.get('start') else None
                else:
                    return val
            
            cleaned_series = series.apply(parse_single_value)
            return pd.to_datetime(cleaned_series, errors='coerce', utc=True)
        except Exception as e:
            logger.warning(f"Error parsing datetime column: {e}")
            return series
    
    def _extract_date_start(self, date_value: Any) -> Optional[datetime]:
        """Extract start date from a date range or single date."""
        if isinstance(date_value, dict):
            start_date = date_value.get("start")
            return pd.to_datetime(start_date, errors='coerce', utc=True) if start_date else None
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value, errors='coerce', utc=True)
        return None
    
    def _extract_date_end(self, date_value: Any) -> Optional[datetime]:
        """Extract end date from a date range or single date."""
        if isinstance(date_value, dict):
            end_date = date_value.get("end")
            return pd.to_datetime(end_date, errors='coerce', utc=True) if end_date else None
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value, errors='coerce', utc=True)
        return None
    
    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional derived metrics for time block analysis."""
        
        # Block completion status
        if "Completed" in df.columns:
            df["is_completed"] = df["Completed"]
        
        # Block adherence analysis
        if "Adhered To" in df.columns:
            df["is_adhered"] = df["Adhered To"]
        
        # Time-based metrics
        if "block_start_time" in df.columns and "block_end_time" in df.columns:
            # Calculate actual block duration
            start_times = pd.to_datetime(df["block_start_time"], errors='coerce', utc=True)
            end_times = pd.to_datetime(df["block_end_time"], errors='coerce', utc=True)
            
            valid_mask = start_times.notna() & end_times.notna()
            df["calculated_duration_minutes"] = np.nan
            df.loc[valid_mask, "calculated_duration_minutes"] = (
                (end_times[valid_mask] - start_times[valid_mask]).dt.total_seconds() / 60
            )
        
        # Duration variance analysis
        if "Duration (minutes)" in df.columns and "calculated_duration_minutes" in df.columns:
            df["duration_variance_minutes"] = df["calculated_duration_minutes"] - df["Duration (minutes)"]
            df["duration_accuracy"] = np.where(
                df["Duration (minutes)"] > 0,
                1 - (abs(df["duration_variance_minutes"]) / df["Duration (minutes)"]),
                np.nan
            )
        
        # Block efficiency metrics
        if "Productive" in df.columns and "Duration (minutes)" in df.columns:
            productive_mask = df["Productive"] == True
            df["productive_time_minutes"] = np.where(
                productive_mask, 
                df["Duration (minutes)"], 
                0
            )
        
        # Fragmentation analysis
        if "Interrupted" in df.columns:
            df["is_interrupted"] = df["Interrupted"]
        
        # Time of day analysis
        if "block_start_time" in df.columns:
            start_times = pd.to_datetime(df["block_start_time"], errors='coerce', utc=True)
            df["start_hour"] = start_times.dt.hour
            
            # Categorize time periods
            df["time_period"] = pd.cut(
                df["start_hour"], 
                bins=[0, 6, 12, 18, 24], 
                labels=["Night", "Morning", "Afternoon", "Evening"],
                include_lowest=True
            )
        
        # Block size categorization
        if "Duration (minutes)" in df.columns:
            df["block_size_category"] = pd.cut(
                df["Duration (minutes)"],
                bins=[0, 15, 30, 60, 120, float('inf')],
                labels=["Micro", "Short", "Medium", "Long", "Extended"],
                include_lowest=True
            )
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the extracted time block data and return quality metrics.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results and data quality metrics
        """
        validation_results = {
            "total_blocks": len(df),
            "columns": list(df.columns),
            "missing_data": {},
            "data_types": {},
            "quality_score": 0.0,
            "issues": [],
            "time_block_quality": {}
        }
        
        # Check for missing data
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            validation_results["missing_data"][col] = {
                "count": int(missing_count),
                "percentage": round(missing_pct, 2)
            }
        
        # Check data types
        for col in df.columns:
            validation_results["data_types"][col] = str(df[col].dtype)
        
        # Critical field validation for time blocks
        critical_fields = ["Block Name", "Planned Time Range", "Duration (minutes)"]
        for field in critical_fields:
            if field not in df.columns:
                validation_results["issues"].append(f"Missing critical field: {field}")
            elif df[field].isna().sum() > 0:
                validation_results["issues"].append(f"Missing values in critical field: {field}")
        
        # Time block specific quality checks
        quality_checks = {}
        
        # Check for valid time ranges
        if "block_start_time" in df.columns and "block_end_time" in df.columns:
            valid_ranges = (df["block_start_time"] < df["block_end_time"]).sum()
            quality_checks["valid_time_ranges"] = {
                "count": int(valid_ranges),
                "percentage": round((valid_ranges / len(df)) * 100, 2)
            }
        
        # Check for reasonable block durations
        if "Duration (minutes)" in df.columns:
            reasonable_durations = ((df["Duration (minutes)"] >= 5) & 
                                  (df["Duration (minutes)"] <= 480)).sum()  # 5 min to 8 hours
            quality_checks["reasonable_durations"] = {
                "count": int(reasonable_durations),
                "percentage": round((reasonable_durations / len(df)) * 100, 2)
            }
        
        # Check for task relationships
        if "related_task_count" in df.columns:
            blocks_with_tasks = (df["related_task_count"] > 0).sum()
            quality_checks["blocks_with_tasks"] = {
                "count": int(blocks_with_tasks),
                "percentage": round((blocks_with_tasks / len(df)) * 100, 2)
            }
        
        validation_results["time_block_quality"] = quality_checks
        
        # Calculate overall quality score
        quality_factors = []
        
        # Completeness factor
        overall_completeness = (1 - df.isna().sum().sum() / (len(df) * len(df.columns))) * 100
        quality_factors.append(overall_completeness)
        
        # Critical fields factor
        critical_completeness = 100
        for field in critical_fields:
            if field in df.columns:
                field_completeness = (1 - df[field].isna().sum() / len(df)) * 100
                critical_completeness = min(critical_completeness, field_completeness)
        quality_factors.append(critical_completeness)
        
        # Time block specific quality factor
        time_quality = 0
        quality_count = 0
        for check in quality_checks.values():
            if isinstance(check, dict) and "percentage" in check:
                time_quality += check["percentage"]
                quality_count += 1
        
        if quality_count > 0:
            quality_factors.append(time_quality / quality_count)
        
        validation_results["quality_score"] = round(sum(quality_factors) / len(quality_factors), 2)
        
        logger.info(f"Time block validation complete. Quality score: {validation_results['quality_score']}")
        
        return validation_results
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the extracted time block data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "basic_stats": {
                "total_blocks": len(df),
                "completed_blocks": df["is_completed"].sum() if "is_completed" in df.columns else 0,
                "adhered_blocks": df["is_adhered"].sum() if "is_adhered" in df.columns else 0,
                "interrupted_blocks": df["is_interrupted"].sum() if "is_interrupted" in df.columns else 0,
            },
            "time_stats": {},
            "adherence_stats": {},
            "block_patterns": {},
            "productivity_stats": {}
        }
        
        # Time statistics
        if "Duration (minutes)" in df.columns:
            durations = df["Duration (minutes)"].dropna()
            if not durations.empty:
                summary["time_stats"] = {
                    "total_planned_minutes": round(durations.sum(), 2),
                    "total_planned_hours": round(durations.sum() / 60, 2),
                    "avg_block_minutes": round(durations.mean(), 2),
                    "median_block_minutes": round(durations.median(), 2),
                    "min_block_minutes": round(durations.min(), 2),
                    "max_block_minutes": round(durations.max(), 2)
                }
        
        # Adherence statistics
        if "is_adhered" in df.columns:
            total_blocks = len(df)
            adhered_blocks = df["is_adhered"].sum()
            summary["adherence_stats"] = {
                "adherence_rate": round((adhered_blocks / total_blocks) * 100, 2) if total_blocks > 0 else 0,
                "adhered_blocks": int(adhered_blocks),
                "non_adhered_blocks": int(total_blocks - adhered_blocks)
            }
        
        # Block pattern analysis
        if "block_size_category" in df.columns:
            size_distribution = df["block_size_category"].value_counts()
            summary["block_patterns"]["size_distribution"] = size_distribution.to_dict()
        
        if "time_period" in df.columns:
            time_distribution = df["time_period"].value_counts()
            summary["block_patterns"]["time_distribution"] = time_distribution.to_dict()
        
        # Productivity statistics
        if "productive_time_minutes" in df.columns:
            productive_time = df["productive_time_minutes"].sum()
            total_time = df["Duration (minutes)"].sum() if "Duration (minutes)" in df.columns else 0
            summary["productivity_stats"] = {
                "total_productive_minutes": round(productive_time, 2),
                "total_productive_hours": round(productive_time / 60, 2),
                "productivity_rate": round((productive_time / total_time) * 100, 2) if total_time > 0 else 0
            }
        
        return summary
    
    def build_task_relationships(self, time_blocks_df: pd.DataFrame, tasks_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build relationship mapping between time blocks and tasks.
        
        Args:
            time_blocks_df: DataFrame with time block data
            tasks_df: DataFrame with task data
            
        Returns:
            Enhanced time blocks DataFrame with task relationship data
        """
        logger.info("Building task-time block relationships...")
        
        # Create a copy to avoid modifying the original
        enhanced_df = time_blocks_df.copy()
        
        # Initialize relationship columns
        enhanced_df["task_names"] = ""
        enhanced_df["task_statuses"] = ""
        enhanced_df["est_hours_total"] = 0.0
        enhanced_df["logged_hours_total"] = 0.0
        
        if "related_task_ids" not in time_blocks_df.columns:
            logger.warning("No related_task_ids column found in time blocks data")
            return enhanced_df


class TimeEntryExtractor:
    """Extract and clean time entry data from Notion for productivity analysis."""
    
    def __init__(self, notion_client: TOADNotionClient):
        """
        Initialize the time entry data extractor.
        
        Args:
            notion_client: Configured TOAD Notion client
        """
        self.client = notion_client
        self._schema_cache = None
        
    def get_database_schema(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get and cache database schema for property mapping.
        
        Args:
            database_id: Time entries database ID (uses config if not provided)
            
        Returns:
            Database schema information
        """
        if self._schema_cache is None:
            db_id = database_id or Config.NOTION_TIME_ENTRIES_DATABASE_ID
            self._schema_cache = self.client.analyze_database_schema(db_id)
        return self._schema_cache
    
    def extract_property_value(self, prop_data: Dict[str, Any], prop_name: str) -> Any:
        """
        Extract value from a Notion property based on its type.
        Uses the same property extraction logic as TaskDataExtractor.
        
        Args:
            prop_data: Property data from Notion API
            prop_name: Name of the property
            
        Returns:
            Extracted and cleaned property value
        """
        # Reuse the same property extraction logic from TaskDataExtractor
        extractor = TaskDataExtractor(self.client)
        return extractor.extract_property_value(prop_data, prop_name)
    
    def extract_time_entries_to_dataframe(self, database_id: Optional[str] = None,
                                         modified_since: Optional[datetime] = None) -> pd.DataFrame:
        """
        Extract all time entries from the database and convert to a pandas DataFrame.
        
        Args:
            database_id: Time entries database ID (uses config if not provided)
            modified_since: If provided, only fetch entries modified after this timestamp
            
        Returns:
            DataFrame with cleaned time entry data
        """
        logger.info("Starting time entry data extraction...")
        
        # Use configured time entries database ID if not provided
        db_id = database_id or Config.NOTION_TIME_ENTRIES_DATABASE_ID
        
        if not db_id:
            raise ValueError("Time entries database ID not configured. Please set NOTION_TIME_ENTRIES_DATABASE_ID in .env")
        
        # Build filter for incremental sync
        filter_dict = None
        if modified_since:
            filter_dict = {
                "timestamp": "last_edited_time",
                "last_edited_time": {
                    "after": modified_since.isoformat()
                }
            }
            logger.info(f"Filtering time entries modified after {modified_since.isoformat()}")
        
        # Get all pages from the time entries database
        pages = self.client.get_database_pages(db_id, filter_dict=filter_dict)
        logger.info(f"Retrieved {len(pages)} time entry pages from database")
        
        # Get schema for reference
        schema = self.get_database_schema(db_id)
        
        # Extract data from each page
        time_entry_records = []
        for page in pages:
            time_entry_record = {
                "entry_id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url", "")
            }
            
            # Extract all properties
            for prop_name, prop_data in page.get("properties", {}).items():
                value = self.extract_property_value(prop_data, prop_name)
                time_entry_record[prop_name] = value
            
            time_entry_records.append(time_entry_record)
        
        # Convert to DataFrame
        df = pd.DataFrame(time_entry_records)
        
        # Clean and process the DataFrame
        df = self._clean_dataframe(df)
        
        logger.info(f"Successfully extracted {len(df)} time entries with {len(df.columns)} columns")
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process the extracted time entries DataFrame.
        
        Args:
            df: Raw DataFrame from extraction
            
        Returns:
            Cleaned DataFrame with proper data types
        """
        logger.info("Cleaning and processing time entries DataFrame...")
        
        # Convert datetime columns
        datetime_columns = [
            "created_time", "last_edited_time", "Start Time", "Stop Time", 
            "Date", "Time Range"
        ]
        
        for col in datetime_columns:
            if col in df.columns:
                df[col] = self._parse_datetime_column(df[col])
        
        # Handle time range columns (extract start and end times)
        if "Time Range" in df.columns:
            df["entry_start_time"] = df["Time Range"].apply(
                lambda x: self._extract_date_start(x) if pd.notna(x) else None
            )
            df["entry_end_time"] = df["Time Range"].apply(
                lambda x: self._extract_date_end(x) if pd.notna(x) else None
            )
        
        # Use Start Time and Stop Time if available (try different column name variations)
        if "Start Time" in df.columns:
            df["entry_start_time"] = df["Start Time"]
        elif "Start" in df.columns:
            df["entry_start_time"] = df["Start"]
            
        if "Stop Time" in df.columns:
            df["entry_end_time"] = df["Stop Time"]
        elif "End" in df.columns:
            df["entry_end_time"] = df["End"]
        
        # Convert numeric columns
        numeric_columns = [
            "Duration (minutes)", "Duration", "Hours", "Billable Hours"
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert boolean columns
        boolean_columns = [
            "Billable", "Completed", "Approved"
        ]
        
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool, errors='ignore')
        
        # Clean categorical columns
        categorical_columns = [
            "Status", "Entry Type", "Category", "Project"
        ]
        
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype('category', errors='ignore')
        
        # Handle relation columns (Task references)
        if "Related Tasks" in df.columns:
            # Convert task relation IDs to a more usable format
            df["related_task_ids"] = df["Related Tasks"].apply(
                lambda x: x if isinstance(x, list) else []
            )
            df["related_task_count"] = df["related_task_ids"].apply(len)
        
        # Handle Task relation (singular)
        if "Task" in df.columns:
            df["task_ids"] = df["Task"].apply(
                lambda x: x if isinstance(x, list) else []
            )
            if "related_task_ids" not in df.columns:
                df["related_task_ids"] = df["task_ids"]
        
        # Calculate derived metrics
        df = self._calculate_derived_metrics(df)
        
        return df
    
    def _parse_datetime_column(self, series: pd.Series) -> pd.Series:
        """Parse datetime column with error handling."""
        try:
            def parse_single_value(val):
                if pd.isna(val) or val is None:
                    return None
                elif isinstance(val, dict):
                    # For date ranges, extract the start date
                    return val.get('start') if val.get('start') else None
                else:
                    return val
            
            cleaned_series = series.apply(parse_single_value)
            return pd.to_datetime(cleaned_series, errors='coerce', utc=True)
        except Exception as e:
            logger.warning(f"Error parsing datetime column: {e}")
            return series
    
    def _extract_date_start(self, date_value: Any) -> Optional[datetime]:
        """Extract start date from a date range or single date."""
        if isinstance(date_value, dict):
            start_date = date_value.get("start")
            return pd.to_datetime(start_date, errors='coerce', utc=True) if start_date else None
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value, errors='coerce', utc=True)
        return None
    
    def _extract_date_end(self, date_value: Any) -> Optional[datetime]:
        """Extract end date from a date range or single date."""
        if isinstance(date_value, dict):
            end_date = date_value.get("end")
            return pd.to_datetime(end_date, errors='coerce', utc=True) if end_date else None
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value, errors='coerce', utc=True)
        return None
    
    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional derived metrics for time entry analysis."""
        
        # Duration calculations
        if "entry_start_time" in df.columns and "entry_end_time" in df.columns:
            # Calculate actual entry duration
            start_times = pd.to_datetime(df["entry_start_time"], errors='coerce', utc=True)
            end_times = pd.to_datetime(df["entry_end_time"], errors='coerce', utc=True)
            
            valid_mask = start_times.notna() & end_times.notna()
            df["calculated_duration_minutes"] = np.nan
            df.loc[valid_mask, "calculated_duration_minutes"] = (
                (end_times[valid_mask] - start_times[valid_mask]).dt.total_seconds() / 60
            )
        
        # Duration variance analysis
        if "Duration (minutes)" in df.columns and "calculated_duration_minutes" in df.columns:
            df["duration_variance_minutes"] = df["calculated_duration_minutes"] - df["Duration (minutes)"]
        elif "Duration" in df.columns and "calculated_duration_minutes" in df.columns:
            # Convert Duration to minutes if it's in hours
            df["duration_hours"] = df["Duration"]
            df["duration_minutes"] = df["duration_hours"] * 60
            df["duration_variance_minutes"] = df["calculated_duration_minutes"] - df["duration_minutes"]
        
        # Convert hours to minutes for consistency
        if "Hours" in df.columns:
            df["hours_as_minutes"] = df["Hours"] * 60
        
        # Entry date analysis
        if "entry_start_time" in df.columns:
            start_times = pd.to_datetime(df["entry_start_time"], errors='coerce', utc=True)
            df["entry_date"] = start_times.dt.date
            df["entry_hour"] = start_times.dt.hour
            df["entry_day_of_week"] = start_times.dt.day_name()
        
        # Time of day categorization
        if "entry_hour" in df.columns:
            df["time_period"] = pd.cut(
                df["entry_hour"], 
                bins=[0, 6, 12, 18, 24], 
                labels=["Night", "Morning", "Afternoon", "Evening"],
                include_lowest=True
            )
        
        return df
    
    def get_entries_for_date_range(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Filter time entries that fall within a specific date range.
        
        Args:
            df: Time entries DataFrame
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Filtered DataFrame with entries in the date range
        """
        if df.empty or "entry_start_time" not in df.columns:
            return pd.DataFrame()
        
        # Convert to UTC timestamps for comparison
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        # Convert entry start times to UTC timestamps
        start_times = pd.to_datetime(df["entry_start_time"], errors='coerce', utc=True)
        start_timestamps = start_times.astype('int64') // 10**9  # Convert to unix timestamp
        
        # Filter entries within the date range
        mask = (
            start_timestamps.notna() & 
            (start_timestamps >= start_timestamp) & 
            (start_timestamps <= end_timestamp)
        )
        
        return df[mask].copy()
    
    def get_task_ids_with_entries_in_range(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> List[str]:
        """
        Get unique task IDs that have time entries within a specific date range.
        
        Args:
            df: Time entries DataFrame
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            List of unique task IDs that had time entries in the range
        """
        entries_in_range = self.get_entries_for_date_range(df, start_date, end_date)
        
        if entries_in_range.empty or "related_task_ids" not in entries_in_range.columns:
            return []
        
        # Collect all task IDs from entries in range
        task_ids = set()
        for _, entry in entries_in_range.iterrows():
            entry_task_ids = entry.get("related_task_ids", [])
            if isinstance(entry_task_ids, list):
                task_ids.update(entry_task_ids)
        
        return list(task_ids)
