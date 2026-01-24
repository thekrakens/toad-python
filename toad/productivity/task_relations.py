"""
Task Relations Manager for TOAD productivity system.
Manages the linking of tasks to Daily Metrics entries based on task activity.
"""

import logging
import pandas as pd
from typing import Dict, List, Any
from datetime import date, datetime, timezone, timedelta
import pytz

from toad.notion_client import TOADNotionClient
from toad.productivity.data_extractor import TaskDataExtractor, TimeEntryExtractor
from toad.config import Config

logger = logging.getLogger(__name__)

class TaskRelationsManager:
    """Manage task relations to Daily Metrics entries."""
    
    def __init__(self, notion_client: TOADNotionClient):
        """
        Initialize the task relations manager.
        
        Args:
            notion_client: Configured TOAD Notion client
        """
        self.client = notion_client
        self.task_extractor = TaskDataExtractor(notion_client)
        self.time_entry_extractor = TimeEntryExtractor(notion_client)
        
    def _get_pst_day_boundaries_utc(self, target_date: date) -> tuple[int, int]:
        """
        Convert PST date to UTC unix timestamp boundaries (start and end of day).
        
        Args:
            target_date: Date to convert (date object)
            
        Returns:
            Tuple of (utc_start_timestamp, utc_end_timestamp)
        """
        pst = pytz.timezone('America/Los_Angeles')
        
        # Create PST start of day (00:00:00 PST)
        pst_start = pst.localize(datetime.combine(target_date, datetime.min.time()))
        # Create PST end of day (23:59:59.999999 PST)
        pst_end = pst.localize(datetime.combine(target_date, datetime.max.time()))
        
        # Convert to UTC unix timestamps
        utc_start = int(pst_start.timestamp())
        utc_end = int(pst_end.timestamp())
        
        return utc_start, utc_end
    
    def _get_planned_tasks(self, tasks_df: pd.DataFrame, target_date: date) -> List[str]:
        """
        Get task IDs for tasks that were planned for the target date.
        A task is considered planned if the target date falls within its planned date range.
        
        Args:
            tasks_df: DataFrame with task data
            target_date: Target date (date object)
            
        Returns:
            List of task IDs (page_id values)
        """
        if tasks_df.empty or 'page_id' not in tasks_df.columns:
            return []
        
        planned_task_ids = []
        
        # Get PST day boundaries as UTC unix timestamps for the target date
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)
        
        # Convert to timestamp for easier comparison
        target_timestamp = utc_start  # Start of the target day in PST (as UTC timestamp)
        
        # Check if we have planned_start and planned_end columns (extracted date ranges)
        if 'planned_start' in tasks_df.columns and 'planned_end' in tasks_df.columns:
            # Use the extracted start/end columns
            planned_start_times = pd.to_datetime(tasks_df['planned_start'], errors='coerce', utc=True)
            planned_end_times = pd.to_datetime(tasks_df['planned_end'], errors='coerce', utc=True)
            
            planned_start_timestamps = (planned_start_times.astype('int64') // 10**9).fillna(0).astype(int)
            planned_end_timestamps = (planned_end_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Task is planned for target_date if the range overlaps with the target day
            planned_mask = (
                (planned_start_timestamps > 0) &  # Has a valid start
                (planned_start_timestamps <= utc_end) &  # Starts before or during target day
                (planned_end_timestamps >= utc_start)  # Ends during or after target day
            )
            
            planned_task_ids = tasks_df[planned_mask]['page_id'].tolist()
        
        # Check for "Planned" column with single dates
        elif 'Planned' in tasks_df.columns:
            planned_times = pd.to_datetime(tasks_df['Planned'], errors='coerce', utc=True)
            planned_timestamps = (planned_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Check if the planned date falls within the target day
            planned_mask = (
                (planned_timestamps >= utc_start) & 
                (planned_timestamps <= utc_end)
            )
            
            planned_task_ids = tasks_df[planned_mask]['page_id'].tolist()
        
        # Alternative: Check for "Planned Timeline" column
        elif 'Planned Timeline' in tasks_df.columns:
            planned_times = pd.to_datetime(tasks_df['Planned Timeline'], errors='coerce', utc=True)
            planned_timestamps = (planned_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            planned_mask = (
                (planned_timestamps >= utc_start) & 
                (planned_timestamps <= utc_end)
            )
            
            planned_task_ids = tasks_df[planned_mask]['page_id'].tolist()
        
        return planned_task_ids
    
    def _get_worked_tasks(self, time_entries_df: pd.DataFrame, target_date: date) -> List[str]:
        """
        Get task IDs for tasks that had work done on the target date.
        
        Args:
            time_entries_df: DataFrame with time entry data
            target_date: Target date (date object)
            
        Returns:
            List of task IDs
        """
        if time_entries_df.empty or 'related_task_ids' not in time_entries_df.columns:
            return []
        
        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)
        
        # Filter time entries for the target date
        if 'entry_start_time' in time_entries_df.columns:
            entry_times = pd.to_datetime(time_entries_df['entry_start_time'], errors='coerce', utc=True)
            entry_timestamps = (entry_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Filter entries within the PST day (in UTC)
            today_mask = (
                (entry_timestamps >= utc_start) & 
                (entry_timestamps <= utc_end)
            )
            
            today_entries = time_entries_df[today_mask]
            
            # Collect task IDs from these entries
            worked_on_ids = set()
            for ids in today_entries['related_task_ids']:
                if ids and isinstance(ids, list):
                    worked_on_ids.update(ids)
            
            return list(worked_on_ids)
        
        return []
    
    def _get_done_tasks(self, tasks_df: pd.DataFrame, target_date: date) -> List[str]:
        """
        Get task IDs for tasks that were completed on the target date.
        
        Args:
            tasks_df: DataFrame with task data
            target_date: Target date (date object)
            
        Returns:
            List of task IDs (page_id values)
        """
        if tasks_df.empty or 'page_id' not in tasks_df.columns:
            return []
        
        done_task_ids = []
        
        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)
        
        # Check for "Done" column (preferred)
        if 'Done' in tasks_df.columns:
            done_times = pd.to_datetime(tasks_df['Done'], errors='coerce', utc=True)
            done_timestamps = (done_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Filter tasks completed within the PST day (in UTC)
            done_mask = (
                (done_timestamps >= utc_start) & 
                (done_timestamps <= utc_end)
            )
            
            done_task_ids = tasks_df[done_mask]['page_id'].tolist()
        
        # Alternative: Check for "Completed" column
        elif 'Completed' in tasks_df.columns:
            completed_times = pd.to_datetime(tasks_df['Completed'], errors='coerce', utc=True)
            completed_timestamps = (completed_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            completed_mask = (
                (completed_timestamps >= utc_start) & 
                (completed_timestamps <= utc_end)
            )
            
            done_task_ids = tasks_df[completed_mask]['page_id'].tolist()
        
        return done_task_ids
    
    def _get_active_tasks(self, tasks_df: pd.DataFrame, time_entries_df: pd.DataFrame, target_date: date) -> List[str]:
        """
        Get task IDs for tasks that were active on the target date.
        Active tasks are those that were planned OR worked on OR have earlier planning that's not done.

        Args:
            tasks_df: DataFrame with task data
            time_entries_df: DataFrame with time entry data
            target_date: Target date (date object)

        Returns:
            List of task IDs (page_id values)
        """
        active_tasks = set()

        # Add planned tasks
        planned_tasks = self._get_planned_tasks(tasks_df, target_date)
        active_tasks.update(planned_tasks)

        # Add worked tasks
        worked_tasks = self._get_worked_tasks(time_entries_df, target_date)
        active_tasks.update(worked_tasks)

        # Add tasks with earlier planning that aren't done yet
        if not tasks_df.empty and 'page_id' in tasks_df.columns:
            # Get PST day boundaries
            utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)

            # Check for tasks planned before today that aren't completed
            if 'Planned Timeline' in tasks_df.columns:
                planned_times = pd.to_datetime(tasks_df['Planned Timeline'], errors='coerce', utc=True)
                planned_timestamps = (planned_times.astype('int64') // 10**9).fillna(0).astype(int)

                # Tasks planned before today
                earlier_planned_mask = (planned_timestamps > 0) & (planned_timestamps < utc_start)

                # Check if not completed
                if 'Done' in tasks_df.columns:
                    done_times = pd.to_datetime(tasks_df['Done'], errors='coerce', utc=True)
                    not_done_mask = done_times.isna()
                    earlier_planned_mask = earlier_planned_mask & not_done_mask
                elif 'Completed' in tasks_df.columns:
                    completed_times = pd.to_datetime(tasks_df['Completed'], errors='coerce', utc=True)
                    not_completed_mask = completed_times.isna()
                    earlier_planned_mask = earlier_planned_mask & not_completed_mask
                elif 'Status' in tasks_df.columns:
                    # Check if status is not "done" or "completed"
                    not_done_status = ~tasks_df['Status'].str.lower().isin(['done', 'completed'])
                    earlier_planned_mask = earlier_planned_mask & not_done_status

                earlier_planned_ids = tasks_df[earlier_planned_mask]['page_id'].tolist()
                active_tasks.update(earlier_planned_ids)

        return list(active_tasks)

    def _get_backlog_tasks(self, tasks_df: pd.DataFrame, target_date: date) -> List[str]:
        """
        Get task IDs for tasks that were moved to backlog on the target date.

        Args:
            tasks_df: DataFrame with task data
            target_date: Target date (date object)

        Returns:
            List of task IDs (page_id values)
        """
        if tasks_df.empty or 'page_id' not in tasks_df.columns:
            return []

        backlog_task_ids = []

        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)

        # Check for "Backlog Date" column
        if 'Backlog Date' in tasks_df.columns:
            backlog_times = pd.to_datetime(tasks_df['Backlog Date'], errors='coerce', utc=True)
            backlog_timestamps = (backlog_times.astype('int64') // 10**9).fillna(0).astype(int)

            # Filter tasks backlogged within the PST day (in UTC)
            backlog_mask = (
                (backlog_timestamps >= utc_start) &
                (backlog_timestamps <= utc_end)
            )

            backlog_task_ids = tasks_df[backlog_mask]['page_id'].tolist()

        return backlog_task_ids

    def _get_archived_tasks(self, tasks_df: pd.DataFrame, target_date: date) -> List[str]:
        """
        Get task IDs for tasks that were archived on the target date.

        Args:
            tasks_df: DataFrame with task data
            target_date: Target date (date object)

        Returns:
            List of task IDs (page_id values)
        """
        if tasks_df.empty or 'page_id' not in tasks_df.columns:
            return []

        archived_task_ids = []

        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)

        # Check for "Archived Date" column
        if 'Archived Date' in tasks_df.columns:
            archived_times = pd.to_datetime(tasks_df['Archived Date'], errors='coerce', utc=True)
            archived_timestamps = (archived_times.astype('int64') // 10**9).fillna(0).astype(int)

            # Filter tasks archived within the PST day (in UTC)
            archived_mask = (
                (archived_timestamps >= utc_start) &
                (archived_timestamps <= utc_end)
            )

            archived_task_ids = tasks_df[archived_mask]['page_id'].tolist()

        return archived_task_ids
    
    def process_daily_task_relations(self, target_date: date) -> Dict[str, Any]:
        """
        Process task relations for a specific date and update the Daily Metrics entry.

        Args:
            target_date: Date to process relations for

        Returns:
            Dict with results of the operation
        """
        logger.info(f"Processing task relations for {target_date}")

        try:
            # Build filters for efficient querying
            task_filter = self._build_date_filter_for_tasks(target_date)
            time_entry_filter = self._build_date_filter_for_time_entries(target_date)

            logger.info(f"Querying tasks relevant to {target_date} (filtered at Notion API level)")

            # Extract data with filters - only gets relevant tasks!
            tasks_df = self._extract_filtered_tasks(task_filter)
            time_entries_df = self._extract_filtered_time_entries(time_entry_filter)

            logger.info(f"Extracted {len(tasks_df)} relevant tasks and {len(time_entries_df)} time entries")

            return self._process_relations_with_data(target_date, tasks_df, time_entries_df)

        except Exception as e:
            logger.error(f"Error processing task relations: {e}")
            return {
                "error": str(e),
                "target_date": str(target_date)
            }
    
    def process_daily_task_relations_with_data(self, target_date: date, 
                                              tasks_df: pd.DataFrame, 
                                              time_entries_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process task relations for a specific date using pre-loaded data.
        This is more efficient when processing multiple dates.
        
        Args:
            target_date: Date to process relations for
            tasks_df: Pre-loaded tasks DataFrame
            time_entries_df: Pre-loaded time entries DataFrame
            
        Returns:
            Dict with results of the operation
        """
        logger.info(f"Processing task relations for {target_date} (with cached data)")
        
        try:
            return self._process_relations_with_data(target_date, tasks_df, time_entries_df)
        except Exception as e:
            logger.error(f"Error processing task relations: {e}")
            return {
                "error": str(e),
                "target_date": str(target_date)
            }
    
    def _process_relations_with_data(self, target_date: date,
                                    tasks_df: pd.DataFrame,
                                    time_entries_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Internal method to process relations with provided data.

        Args:
            target_date: Date to process relations for
            tasks_df: Tasks DataFrame
            time_entries_df: Time entries DataFrame

        Returns:
            Dict with results of the operation
        """
        # Get task IDs for each relation type
        planned_ids = self._get_planned_tasks(tasks_df, target_date)
        active_ids = self._get_active_tasks(tasks_df, time_entries_df, target_date)
        worked_ids = self._get_worked_tasks(time_entries_df, target_date)
        done_ids = self._get_done_tasks(tasks_df, target_date)
        backlog_ids = self._get_backlog_tasks(tasks_df, target_date)
        archived_ids = self._get_archived_tasks(tasks_df, target_date)

        logger.info(f"Found: {len(planned_ids)} planned, {len(active_ids)} active, {len(worked_ids)} worked, {len(done_ids)} done, {len(backlog_ids)} backlog, {len(archived_ids)} archived")

        # Find or create Daily Metrics entry for this date
        metrics_entry_id = self._find_or_create_daily_metrics_entry(target_date)

        if not metrics_entry_id:
            return {
                "error": "Failed to find or create Daily Metrics entry",
                "target_date": str(target_date)
            }

        # Update relations
        result = {
            "target_date": str(target_date),
            "metrics_entry_id": metrics_entry_id,
            "planned": self._update_relation(metrics_entry_id, "Planned", planned_ids),
            "active": self._update_relation(metrics_entry_id, "Active", active_ids),
            "worked": self._update_relation(metrics_entry_id, "Worked", worked_ids),
            "done": self._update_relation(metrics_entry_id, "Done", done_ids),
            "backlog": self._update_relation(metrics_entry_id, "Backlog", backlog_ids),
            "archived": self._update_relation(metrics_entry_id, "Archived", archived_ids)
        }

        return result
    
    def _find_or_create_daily_metrics_entry(self, target_date: date) -> str:
        """
        Find or create a Daily Metrics entry for the given date.
        
        Args:
            target_date: Date for the metrics entry
            
        Returns:
            Page ID of the metrics entry
        """
        database_id = Config.NOTION_DAILY_METRICS_DATABASE_ID
        
        if not database_id:
            raise ValueError("NOTION_DAILY_METRICS_DATABASE_ID not configured")
        
        # Search for existing entry
        date_str = target_date.strftime('%Y-%m-%d')
        
        try:
            query_result = self.client.client.databases.query(
                database_id=database_id,
                filter={
                    "property": "Date",
                    "date": {
                        "equals": date_str
                    }
                }
            )
            
            if query_result.get("results"):
                # Found existing entry
                return query_result["results"][0]["id"]
            
            # Create new entry
            logger.info(f"Creating new Daily Metrics entry for {date_str}")
            new_page = self.client.client.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Name": {
                        "title": [{"text": {"content": f"Daily Metrics - {date_str}"}}]
                    },
                    "Date": {
                        "date": {"start": date_str}
                    }
                }
            )
            
            return new_page["id"]
            
        except Exception as e:
            logger.error(f"Error finding/creating Daily Metrics entry: {e}")
            raise
    
    def _update_relation(self, page_id: str, relation_name: str, task_ids: List[str]) -> Dict[str, Any]:
        """
        Update a relation property on a page by ADDING new task IDs to existing relations.

        This ensures that:
        - Tasks planned across multiple days appear in all relevant Daily Metrics
        - Tasks with time entries across multiple days keep all "Worked" relations

        Args:
            page_id: ID of the page to update
            relation_name: Name of the relation property
            task_ids: List of task IDs to ADD to the relation

        Returns:
            Dict with success status and details
        """
        try:
            # First, fetch current relations
            current_page = self.client.client.pages.retrieve(page_id=page_id)
            current_relations = current_page.get("properties", {}).get(relation_name, {}).get("relation", [])

            # Extract existing task IDs
            existing_ids = set(rel["id"] for rel in current_relations)

            # Merge with new task IDs (union, no duplicates)
            all_task_ids = existing_ids.union(set(task_ids))

            # Build merged relation array
            relation_data = [{"id": task_id} for task_id in all_task_ids]

            # Update the page with merged relations
            self.client.client.pages.update(
                page_id=page_id,
                properties={
                    relation_name: {
                        "relation": relation_data
                    }
                }
            )

            added_count = len(all_task_ids) - len(existing_ids)
            logger.info(f"Updated {relation_name}: {len(existing_ids)} existing + {added_count} new = {len(all_task_ids)} total")

            return {
                "success": True,
                "task_count": len(all_task_ids),
                "added_count": added_count,
                "existing_count": len(existing_ids),
                "relation_name": relation_name
            }

        except Exception as e:
            logger.error(f"Error updating {relation_name} relation: {e}")
            return {
                "success": False,
                "error": str(e),
                "relation_name": relation_name
            }
    
    def _build_date_filter_for_tasks(self, target_date: date) -> dict:
        """
        Build a Notion filter to query only tasks relevant to the target date.

        Fetches tasks where Planned, Done, Doing, Backlog Date, or Archived Date matches target_date.
        Also includes tasks planned before target_date that aren't done (for "Active").

        Args:
            target_date: Date to filter for

        Returns:
            Notion API filter dict
        """
        date_str = target_date.strftime('%Y-%m-%d')

        # Query tasks where Planned OR Done OR Doing OR Backlog Date OR Archived Date equals target date
        # OR tasks planned before today that aren't done
        return {
            "or": [
                {
                    "property": "Planned",
                    "date": {"equals": date_str}
                },
                {
                    "property": "Done",
                    "date": {"equals": date_str}
                },
                {
                    "property": "Doing",
                    "date": {"equals": date_str}
                },
                {
                    "property": "Backlog Date",
                    "date": {"equals": date_str}
                },
                {
                    "property": "Archived Date",
                    "date": {"equals": date_str}
                },
                # Include tasks planned before target date that might still be active
                {
                    "and": [
                        {
                            "property": "Planned",
                            "date": {"on_or_before": date_str}
                        },
                        {
                            "property": "Done",
                            "date": {"is_empty": True}
                        }
                    ]
                }
            ]
        }

    def _build_date_filter_for_time_entries(self, target_date: date) -> dict:
        """
        Build a Notion filter to query only time entries for the target date.

        Args:
            target_date: Date to filter for

        Returns:
            Notion API filter dict
        """
        date_str = target_date.strftime('%Y-%m-%d')

        # Query time entries where Start date equals target date
        return {
            "property": "Start",
            "date": {"equals": date_str}
        }

    def get_relation_summary(self, target_date: date) -> Dict[str, Any]:
        """
        Get a summary of task relations for a specific date without updating.

        Args:
            target_date: Date to get summary for

        Returns:
            Dict with relation counts
        """
        try:
            # Build filters for efficient querying
            task_filter = self._build_date_filter_for_tasks(target_date)
            time_entry_filter = self._build_date_filter_for_time_entries(target_date)

            logger.info(f"Querying tasks relevant to {target_date} (filtered at Notion API level)")

            # Extract data with filters - only gets relevant tasks!
            tasks_df = self._extract_filtered_tasks(task_filter)
            time_entries_df = self._extract_filtered_time_entries(time_entry_filter)

            logger.info(f"Extracted {len(tasks_df)} relevant tasks and {len(time_entries_df)} time entries")

            # Get task IDs for each relation type
            planned_ids = self._get_planned_tasks(tasks_df, target_date)
            active_ids = self._get_active_tasks(tasks_df, time_entries_df, target_date)
            worked_ids = self._get_worked_tasks(time_entries_df, target_date)
            done_ids = self._get_done_tasks(tasks_df, target_date)
            backlog_ids = self._get_backlog_tasks(tasks_df, target_date)
            archived_ids = self._get_archived_tasks(tasks_df, target_date)

            return {
                "target_date": str(target_date),
                "planned_count": len(planned_ids),
                "active_count": len(active_ids),
                "worked_count": len(worked_ids),
                "done_count": len(done_ids),
                "backlog_count": len(backlog_ids),
                "archived_count": len(archived_ids),
                "planned_ids": planned_ids,
                "active_ids": active_ids,
                "worked_ids": worked_ids,
                "done_ids": done_ids,
                "backlog_ids": backlog_ids,
                "archived_ids": archived_ids
            }

        except Exception as e:
            logger.error(f"Error getting relation summary: {e}")
            return {
                "error": str(e),
                "target_date": str(target_date)
            }

    def _extract_filtered_tasks(self, filter_dict: dict) -> pd.DataFrame:
        """Extract tasks with a Notion API filter."""
        from toad.config import Config

        database_id = Config.NOTION_DATABASE_ID
        pages = self.client.get_database_pages(database_id, filter_dict=filter_dict)

        # Reuse the extractor's parsing logic
        task_records = []
        for page in pages:
            task_record = {
                "page_id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url", "")
            }

            for prop_name, prop_data in page.get("properties", {}).items():
                value = self.task_extractor.extract_property_value(prop_data, prop_name)
                task_record[prop_name] = value

            task_records.append(task_record)

        df = pd.DataFrame(task_records)
        if not df.empty:
            df = self.task_extractor._clean_dataframe(df)

        return df

    def _extract_filtered_time_entries(self, filter_dict: dict) -> pd.DataFrame:
        """Extract time entries with a Notion API filter."""
        from toad.config import Config

        database_id = Config.NOTION_TIME_ENTRIES_DATABASE_ID
        pages = self.client.get_database_pages(database_id, filter_dict=filter_dict)

        # Reuse the extractor's parsing logic
        entry_records = []
        for page in pages:
            entry_record = {
                "entry_id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url", "")
            }

            for prop_name, prop_data in page.get("properties", {}).items():
                value = self.time_entry_extractor.extract_property_value(prop_data, prop_name)
                entry_record[prop_name] = value

            entry_records.append(entry_record)

        df = pd.DataFrame(entry_records)
        if not df.empty:
            df = self.time_entry_extractor._clean_dataframe(df)

        return df
