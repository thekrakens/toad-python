"""
Daily productivity metrics calculator specifically for Notion sync.
Extends existing TOAD analytics with user-requested metrics.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import pytz

from toad.productivity.data_extractor import TaskDataExtractor, TimeEntryExtractor

logger = logging.getLogger(__name__)

@dataclass
class DailyMetrics:
    """Container for daily productivity metrics."""
    date: datetime
    
    # Core user-requested metrics
    planned_working_hours: float
    effective_hours_worked: float
    time_on_planned_tasks: float
    time_on_unplanned_tasks: float
    planned_vs_unplanned_pct: float
    tasks_planned_count: int
    tasks_active_count: int
    unplanned_tasks_created: int
    cold_tasks_count: int
    
    # Enhanced context metrics
    productivity_score: float
    schedule_adherence_pct: float
    task_completion_rate_pct: float
    context_switches: int
    
    # Task relation tracking for better daily metrics
    active_task_ids: List[str] = None
    planned_task_ids: List[str] = None
    worked_on_task_ids: List[str] = None
    completed_task_ids: List[str] = None
    
    # Optional fields for manual input
    work_day_type: Optional[str] = None
    quality_rating: Optional[str] = None
    notes: Optional[str] = None

class DailyMetricsCalculator:
    """Calculate daily productivity metrics for Notion sync."""
    
    def __init__(self, tasks_df: pd.DataFrame, time_blocks_df: pd.DataFrame = None, time_entries_df: pd.DataFrame = None):
        """
        Initialize with task and time block data.

        Args:
            tasks_df: DataFrame with task data
            time_blocks_df: Optional DataFrame with time block data
            time_entries_df: Optional DataFrame with time entry data
        """
        self.tasks_df = tasks_df.copy() if not tasks_df.empty else pd.DataFrame()
        self.time_blocks_df = time_blocks_df.copy() if time_blocks_df is not None and not time_blocks_df.empty else pd.DataFrame()
        self.time_entries_df = time_entries_df.copy() if time_entries_df is not None and not time_entries_df.empty else pd.DataFrame()
        self.logger = logging.getLogger(__name__)
        
    def calculate_metrics_for_date(self, target_date: datetime) -> DailyMetrics:
        """
        Calculate all daily metrics for a specific date.
        
        Args:
            target_date: Date to calculate metrics for
            
        Returns:
            DailyMetrics object with all calculated values
        """
        self.logger.info(f"Calculating daily metrics for {target_date.date()}")
        
        # Filter data for the target date
        daily_tasks = self._filter_tasks_by_date(target_date)
        daily_blocks = self._filter_time_blocks_by_date(target_date)
        
        # Calculate core metrics
        planned_hours = self._calculate_planned_working_hours(daily_tasks, daily_blocks, target_date)
        effective_hours = self._calculate_effective_hours_worked(daily_tasks, target_date)
        planned_time, unplanned_time = self._calculate_planned_vs_unplanned_time(daily_tasks, target_date)
        planned_vs_unplanned_pct = self._calculate_planned_vs_unplanned_percentage(planned_time, effective_hours)
        
        # Calculate task counts
        tasks_planned = self._calculate_tasks_planned_count(daily_tasks, target_date)
        tasks_active = self._calculate_tasks_active_count(daily_tasks, target_date)
        unplanned_created = self._calculate_unplanned_tasks_created(target_date)
        cold_tasks = self._calculate_cold_tasks_count(target_date)
        
        # Calculate enhanced metrics
        productivity_score = self._calculate_productivity_score(daily_tasks, daily_blocks, target_date)
        schedule_adherence = self._calculate_schedule_adherence(daily_blocks)
        completion_rate = self._calculate_task_completion_rate(daily_tasks)
        context_switches = self._calculate_context_switches(daily_tasks)
        
        # Collect task IDs for relations
        active_task_ids = self._collect_active_task_ids(target_date)
        planned_task_ids = self._collect_planned_task_ids(target_date)
        worked_on_task_ids = self._collect_worked_on_task_ids(target_date)
        completed_task_ids = self._collect_completed_task_ids(target_date)
        
        return DailyMetrics(
            date=target_date,
            planned_working_hours=planned_hours,
            effective_hours_worked=effective_hours,
            time_on_planned_tasks=planned_time,
            time_on_unplanned_tasks=unplanned_time,
            planned_vs_unplanned_pct=planned_vs_unplanned_pct,
            tasks_planned_count=tasks_planned,
            tasks_active_count=tasks_active,
            unplanned_tasks_created=unplanned_created,
            cold_tasks_count=cold_tasks,
            productivity_score=productivity_score,
            schedule_adherence_pct=schedule_adherence,
            task_completion_rate_pct=completion_rate,
            context_switches=context_switches,
            active_task_ids=active_task_ids,
            planned_task_ids=planned_task_ids,
            worked_on_task_ids=worked_on_task_ids,
            completed_task_ids=completed_task_ids
        )
    
    def _filter_tasks_by_date(self, target_date: datetime) -> pd.DataFrame:
        """Filter tasks relevant to the target date (handling PST timezone)."""
        if self.tasks_df.empty:
            return pd.DataFrame()
        
        # Convert target date to PST for comparison
        pst = pytz.timezone('America/Los_Angeles')
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
        target_date_pst = target_date.astimezone(pst).date()
        
        date_filters = []
        
        # Tasks completed on this date (convert to PST)
        if 'Completed' in self.tasks_df.columns:
            completed_times = pd.to_datetime(self.tasks_df['Completed'], errors='coerce')
            # Convert to PST and extract date
            completed_dates_pst = completed_times.dt.tz_convert(pst).dt.date
            completed_filter = completed_dates_pst == target_date_pst
            date_filters.append(completed_filter)
        
        # Tasks with planned timeline including this date
        if 'Planned Timeline' in self.tasks_df.columns:
            planned_times = pd.to_datetime(self.tasks_df['Planned Timeline'], errors='coerce')
            planned_dates_pst = planned_times.dt.tz_convert(pst).dt.date
            planned_filter = (planned_dates_pst == target_date_pst) & planned_dates_pst.notna()
            date_filters.append(planned_filter)
        
        # Tasks with time entries today - this is the key filter for actual work
        if 'Time Entries Today' in self.tasks_df.columns:
            today_entries_filter = self.tasks_df['Time Entries Today'] > 0
            date_filters.append(today_entries_filter)
        
        # Tasks with "doing" status set on this date (convert to PST)
        if 'Doing' in self.tasks_df.columns:
            doing_times = pd.to_datetime(self.tasks_df['Doing'], errors='coerce')
            doing_dates_pst = doing_times.dt.tz_convert(pst).dt.date
            doing_filter = doing_dates_pst == target_date_pst
            date_filters.append(doing_filter)

        # Tasks created on this date
        if 'created_time' in self.tasks_df.columns:
            created_times = pd.to_datetime(self.tasks_df['created_time'], errors='coerce')
            created_dates_pst = created_times.dt.tz_convert(pst).dt.date
            created_filter = created_dates_pst == target_date_pst
            date_filters.append(created_filter)
        
        if date_filters:
            combined_filter = date_filters[0]
            for f in date_filters[1:]:
                combined_filter = combined_filter | f
            return self.tasks_df[combined_filter].copy()
        
        return pd.DataFrame()
    
    def _filter_time_blocks_by_date(self, target_date: datetime) -> pd.DataFrame:
        """Filter time blocks for the target date."""
        if self.time_blocks_df.empty or 'block_start_time' not in self.time_blocks_df.columns:
            return pd.DataFrame()
        
        block_dates = pd.to_datetime(self.time_blocks_df['block_start_time'], errors='coerce').dt.date
        return self.time_blocks_df[block_dates == target_date.date()].copy()

    def _filter_time_entries_by_date(self, time_entries_df: pd.DataFrame, target_date: datetime) -> pd.DataFrame:
        """Filter time entries for the target date."""
        if time_entries_df.empty or 'entry_start_time' not in time_entries_df.columns:
            return pd.DataFrame()

        entry_dates = pd.to_datetime(time_entries_df['entry_start_time'], errors='coerce', utc=True).dt.date
        return time_entries_df[entry_dates == target_date.date()].copy()
    
    def _calculate_planned_working_hours(self, daily_tasks: pd.DataFrame, daily_blocks: pd.DataFrame, target_date: datetime = None) -> float:
        """Calculate planned working hours for the day."""
        planned_hours = 0.0
        
        # Prefer time blocks if available
        if not daily_blocks.empty and 'Duration (minutes)' in daily_blocks.columns:
            total_minutes = daily_blocks['Duration (minutes)'].sum()
            planned_hours = total_minutes / 60
        
        # Use Effective Planned Hours but only for tasks marked as planned
        elif not daily_tasks.empty and 'Effective Planned Hours' in daily_tasks.columns:
            # Simple approach: only sum Effective Planned Hours for tasks marked as Planned Task = True
            planned_tasks_mask = daily_tasks.get('Planned Task', False) == True
            planned_tasks = daily_tasks[planned_tasks_mask]
            
            if not planned_tasks.empty and 'Effective Planned Hours' in planned_tasks.columns:
                # If we have a target date, filter tasks to only those planned for that specific date
                if target_date is not None and 'Planned Timeline' in planned_tasks.columns:
                    # Convert target date to the same format for comparison
                    target_date_only = target_date.date() if hasattr(target_date, 'date') else target_date
                    
                    # Convert planned timeline to date and filter
                    planned_dates = pd.to_datetime(planned_tasks['Planned Timeline'], errors='coerce').dt.date
                    date_match_mask = (planned_dates == target_date_only)
                    
                    final_planned_tasks = planned_tasks[date_match_mask]
                    if not final_planned_tasks.empty:
                        planned_hours = final_planned_tasks['Effective Planned Hours'].sum()
                else:
                    # No target date provided, sum all planned tasks
                    planned_hours = planned_tasks['Effective Planned Hours'].sum()
        
        # Fallback to planned timeline duration if available
        elif not daily_tasks.empty and 'planned_duration_hours' in daily_tasks.columns:
            planned_hours = daily_tasks['planned_duration_hours'].sum()
        
        return round(planned_hours, 2)
    
    def _calculate_effective_hours_worked(self, daily_tasks: pd.DataFrame, target_date: datetime) -> float:
        """Calculate effective hours worked based on time entries logged today."""
        if self.time_entries_df.empty:
            return 0.0

        today_entries = self._filter_time_entries_by_date(self.time_entries_df, target_date)
        if today_entries.empty:
            return 0.0

        return round(today_entries['calculated_duration_minutes'].sum() / 60, 2)
    
    def _calculate_planned_vs_unplanned_time(self, daily_tasks: pd.DataFrame, target_date: datetime) -> Tuple[float, float]:
        """Calculate time spent on planned vs unplanned tasks (only for tasks with time entries today)."""
        if self.time_entries_df.empty:
            return 0.0, 0.0

        today_entries = self._filter_time_entries_by_date(self.time_entries_df, target_date)
        if today_entries.empty:
            return 0.0, 0.0

        planned_time = 0.0
        unplanned_time = 0.0

        for _, entry in today_entries.iterrows():
            task_ids = entry.get('related_task_ids', [])
            if not task_ids:
                unplanned_time += entry['calculated_duration_minutes']
                continue

            task_id = task_ids[0]
            if task_id in self.tasks_df.index:
                task = self.tasks_df.loc[task_id]
                if task.get('Planned Task', False):
                    planned_time += entry['calculated_duration_minutes']
                else:
                    unplanned_time += entry['calculated_duration_minutes']
            else:
                unplanned_time += entry['calculated_duration_minutes']

        return round(planned_time / 60, 2), round(unplanned_time / 60, 2)
    
    def _calculate_planned_vs_unplanned_percentage(self, planned_time: float, total_time: float) -> float:
        """Calculate percentage of time spent on planned tasks."""
        if total_time == 0:
            return 0.0
        
        percentage = (planned_time / total_time) * 100
        return round(percentage, 1)
    
    def _calculate_tasks_planned_count(self, daily_tasks: pd.DataFrame, target_date: datetime) -> int:
        """Calculate number of tasks planned for this day."""
        if daily_tasks.empty:
            return 0
        
        planned_count = 0
        
        # Count tasks with Planned Task = True
        if 'Planned Task' in daily_tasks.columns:
            planned_count = daily_tasks['Planned Task'].sum()
        
        # Alternative: count tasks with planned timeline including this date
        elif 'planned_start' in daily_tasks.columns and 'planned_end' in daily_tasks.columns:
            target_date_only = target_date.date()
            planned_start = pd.to_datetime(daily_tasks['planned_start'], errors='coerce').dt.date
            planned_end = pd.to_datetime(daily_tasks['planned_end'], errors='coerce').dt.date
            
            planned_filter = (
                (planned_start <= target_date_only) & 
                (planned_end >= target_date_only) &
                planned_start.notna() & 
                planned_end.notna()
            )
            planned_count = planned_filter.sum()
        
        return int(planned_count)
    
    def _calculate_tasks_active_count(self, daily_tasks: pd.DataFrame, target_date: datetime) -> int:
        """
        Calculate number of tasks active for this day using complex logic:
        - Planned that day (Planned Timeline includes date), OR
        - Worked on that day (time entries logged), OR  
        - Status set to "doing" that day (last_edited_time + status change)
        """
        if daily_tasks.empty:
            return 0
        
        active_tasks = set()
        target_date_only = target_date.date()
        
        # Method 1: Tasks planned for this day
        if 'Planned Timeline' in daily_tasks.columns:
            planned_dates = pd.to_datetime(daily_tasks['Planned Timeline'], errors='coerce').dt.date
            planned_mask = (planned_dates == target_date_only) & planned_dates.notna()
            
            planned_task_ids = daily_tasks[planned_mask].index.tolist()
            active_tasks.update(planned_task_ids)
        
        # Method 2: Tasks worked on this day (with logged time)
        if 'last_edited_time' in daily_tasks.columns and 'logged_hours' in daily_tasks.columns:
            edited_dates = pd.to_datetime(daily_tasks['last_edited_time'], errors='coerce').dt.date
            has_logged_time = daily_tasks['logged_hours'] > 0
            
            worked_mask = (edited_dates == target_date_only) & has_logged_time
            worked_task_ids = daily_tasks[worked_mask].index.tolist()
            active_tasks.update(worked_task_ids)
        
        # Method 3: Tasks with "doing" status set on this day
        if 'Doing' in daily_tasks.columns:
            doing_dates = pd.to_datetime(daily_tasks['Doing'], errors='coerce').dt.date
            doing_mask = doing_dates == target_date_only
            
            doing_task_ids = daily_tasks[doing_mask].index.tolist()
            active_tasks.update(doing_task_ids)

        # Method 4: Tasks created on this day
        if 'created_time' in daily_tasks.columns:
            created_dates = pd.to_datetime(daily_tasks['created_time'], errors='coerce').dt.date
            created_mask = (created_dates == target_date_only) & created_dates.notna()
            
            created_task_ids = daily_tasks[created_mask].index.tolist()
            active_tasks.update(created_task_ids)
        
        return len(active_tasks)
    
    def _calculate_unplanned_tasks_created(self, target_date: datetime) -> int:
        """Calculate number of unplanned tasks created on this day."""
        if self.tasks_df.empty:
            return 0
        
        target_date_only = target_date.date()
        unplanned_count = 0
        
        if 'created_time' in self.tasks_df.columns and 'Planned Task' in self.tasks_df.columns:
            created_dates = pd.to_datetime(self.tasks_df['created_time'], errors='coerce').dt.date
            is_unplanned = self.tasks_df['Planned Task'] == False
            
            created_today_mask = created_dates == target_date_only
            unplanned_created_mask = created_today_mask & is_unplanned
            
            unplanned_count = unplanned_created_mask.sum()
        
        return int(unplanned_count)
    
    def _calculate_cold_tasks_count(self, target_date: datetime, cold_days_threshold: int = 7) -> int:
        """
        Calculate number of cold tasks (no recent activity).
        
        Args:
            target_date: Reference date
            cold_days_threshold: Days without activity to consider "cold"
        """
        if self.tasks_df.empty:
            return 0
        
        cutoff_date = target_date.date() - timedelta(days=cold_days_threshold)
        cold_count = 0
        
        if 'last_edited_time' in self.tasks_df.columns:
            last_edited_dates = pd.to_datetime(self.tasks_df['last_edited_time'], errors='coerce').dt.date
            
            # Tasks that haven't been edited recently and aren't completed
            cold_mask = (
                (last_edited_dates < cutoff_date) & 
                last_edited_dates.notna() &
                (self.tasks_df.get('is_completed', False) == False)
            )
            
            cold_count = cold_mask.sum()
        
        return int(cold_count)
    
    def _calculate_productivity_score(self, daily_tasks: pd.DataFrame, daily_blocks: pd.DataFrame, target_date: datetime) -> float:
        """Calculate composite productivity score (0-100)."""
        score_factors = []
        weights = []
        
        # Task completion factor (30% weight)
        completion_rate = self._calculate_task_completion_rate(daily_tasks)
        if completion_rate > 0:
            score_factors.append(completion_rate)
            weights.append(0.30)
        
        # Time efficiency factor (25% weight)
        effective_hours = self._calculate_effective_hours_worked(daily_tasks, target_date)
        if effective_hours > 0:
            # Normalize to 8-hour workday
            efficiency_score = min(100, (effective_hours / 8.0) * 100)
            score_factors.append(efficiency_score)
            weights.append(0.25)
        
        # Schedule adherence factor (20% weight)
        adherence = self._calculate_schedule_adherence(daily_blocks)
        if adherence > 0:
            score_factors.append(adherence)
            weights.append(0.20)
        
        # Planned vs unplanned balance factor (15% weight)
        planned_time, _ = self._calculate_planned_vs_unplanned_time(daily_tasks, target_date)
        planned_pct = self._calculate_planned_vs_unplanned_percentage(planned_time, effective_hours)
        if planned_pct > 0:
            # Optimal is around 70-80% planned work
            balance_score = max(0, 100 - abs(75 - planned_pct) * 2)
            score_factors.append(balance_score)
            weights.append(0.15)
        
        # Activity level factor (10% weight)
        if not daily_tasks.empty:
            activity_score = min(100, len(daily_tasks) * 10)  # 10 points per task, max 100
            score_factors.append(activity_score)
            weights.append(0.10)
        
        if not score_factors:
            return 0.0
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        productivity_score = sum(f * w for f, w in zip(score_factors, weights))
        return round(productivity_score, 1)
    
    def _calculate_schedule_adherence(self, daily_blocks: pd.DataFrame) -> float:
        """Calculate schedule adherence percentage."""
        if daily_blocks.empty or 'is_adhered' not in daily_blocks.columns:
            return 0.0
        
        adhered_blocks = daily_blocks['is_adhered'].sum()
        total_blocks = len(daily_blocks)
        adherence_pct = (adhered_blocks / total_blocks) * 100 if total_blocks > 0 else 0.0
        
        return round(adherence_pct, 1)
    
    def _calculate_task_completion_rate(self, daily_tasks: pd.DataFrame) -> float:
        """Calculate task completion rate percentage."""
        if daily_tasks.empty or 'is_completed' not in daily_tasks.columns:
            return 0.0
        
        completed_tasks = daily_tasks['is_completed'].sum()
        total_tasks = len(daily_tasks)
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0.0
        
        return round(completion_rate, 1)
    
    def _calculate_context_switches(self, daily_tasks: pd.DataFrame) -> int:
        """Calculate context switching count."""
        if daily_tasks.empty or 'Context Switches' not in daily_tasks.columns:
            return 0
        
        return int(daily_tasks['Context Switches'].sum())
    
    def _collect_active_task_ids(self, target_date: datetime) -> List[str]:
        """Collect all task IDs that were active on the target date."""
        if self.tasks_df.empty:
            return []
        
        active_task_ids = set()
        
        # Get all task IDs from the specific relation methods using Unix timestamps
        planned_ids = set(self._collect_planned_task_ids(target_date))
        worked_ids = set(self._collect_worked_on_task_ids(target_date))
        completed_ids = set(self._collect_completed_task_ids(target_date))
        doing_ids = set(self._collect_doing_task_ids(target_date))
        
        # Combine all activity types
        active_task_ids.update(planned_ids)
        active_task_ids.update(worked_ids)
        active_task_ids.update(completed_ids)
        active_task_ids.update(doing_ids)
        
        return list(active_task_ids)
    
    def _get_pst_day_boundaries_utc(self, target_date: datetime) -> Tuple[int, int]:
        """Convert PST date to UTC unix timestamp boundaries (start and end of day)."""
        pst = pytz.timezone('America/Los_Angeles')
        
        # If target_date has no timezone, assume it's already the desired PST date
        if target_date.tzinfo is None:
            target_date_naive = target_date.date()
        else:
            # Convert to PST to get the date
            target_date_naive = target_date.astimezone(pst).date()
        
        # Create PST start of day (00:00:00 PST)
        pst_start = pst.localize(datetime.combine(target_date_naive, datetime.min.time()))
        # Create PST end of day (23:59:59.999999 PST)
        pst_end = pst.localize(datetime.combine(target_date_naive, datetime.max.time()))
        
        # Convert to UTC unix timestamps
        utc_start = int(pst_start.timestamp())
        utc_end = int(pst_end.timestamp())
        
        return utc_start, utc_end
    
    def _collect_planned_task_ids(self, target_date: datetime) -> List[str]:
        """Collect task IDs for tasks that were planned for the target date."""
        if self.tasks_df.empty or 'page_id' not in self.tasks_df.columns:
            return []
        
        planned_task_ids = []
        
        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)
        
        # Tasks with planned timeline within this PST day (converted to UTC range)
        if 'Planned Timeline' in self.tasks_df.columns:
            planned_times = pd.to_datetime(self.tasks_df['Planned Timeline'], errors='coerce', utc=True)
            planned_timestamps = (planned_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Filter tasks whose planned timeline falls within the PST day (in UTC)
            planned_mask = (
                (planned_timestamps >= utc_start) & 
                (planned_timestamps <= utc_end)
            )
            
            planned_task_ids = self.tasks_df[planned_mask]['page_id'].tolist()
        
        return planned_task_ids
    
    def _collect_worked_on_task_ids(self, target_date: datetime) -> List[str]:
        """Collect task IDs for tasks that had work done on the target date."""
        if self.time_entries_df.empty or 'related_task_ids' not in self.time_entries_df.columns:
            return []

        today_entries = self._filter_time_entries_by_date(self.time_entries_df, target_date)
        if today_entries.empty:
            return []

        worked_on_ids = set()
        for ids in today_entries['related_task_ids']:
            if ids:
                worked_on_ids.update(ids)
        
        return list(worked_on_ids)
    
    def _collect_completed_task_ids(self, target_date: datetime) -> List[str]:
        """Collect task IDs for tasks that were completed on the target date."""
        if self.tasks_df.empty or 'page_id' not in self.tasks_df.columns:
            return []
        
        completed_task_ids = []
        
        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)
        
        # Tasks completed within this PST day (converted to UTC range)
        if 'Completed' in self.tasks_df.columns:
            completed_times = pd.to_datetime(self.tasks_df['Completed'], errors='coerce', utc=True)
            completed_timestamps = (completed_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Filter tasks whose completion time falls within the PST day (in UTC)
            completed_mask = (
                (completed_timestamps >= utc_start) & 
                (completed_timestamps <= utc_end)
            )
            
            completed_task_ids = self.tasks_df[completed_mask]['page_id'].tolist()
        
        return completed_task_ids
    
    def _collect_doing_task_ids(self, target_date: datetime) -> List[str]:
        """Collect task IDs for tasks that had 'Doing' status set on the target date."""
        if self.tasks_df.empty or 'page_id' not in self.tasks_df.columns:
            return []
        
        doing_task_ids = []
        
        # Get PST day boundaries as UTC unix timestamps
        utc_start, utc_end = self._get_pst_day_boundaries_utc(target_date)
        
        # Tasks with 'Doing' status set within this PST day (converted to UTC range)
        if 'Doing' in self.tasks_df.columns:
            doing_times = pd.to_datetime(self.tasks_df['Doing'], errors='coerce', utc=True)
            doing_timestamps = (doing_times.astype('int64') // 10**9).fillna(0).astype(int)
            
            # Filter tasks whose 'Doing' status was set within the PST day (in UTC)
            doing_mask = (
                (doing_timestamps >= utc_start) & 
                (doing_timestamps <= utc_end)
            )
            
            doing_task_ids = self.tasks_df[doing_mask]['page_id'].tolist()
        
        return doing_task_ids
    
    def to_notion_record(self, metrics: DailyMetrics, database_id: str) -> Dict[str, Any]:
        """
        Convert DailyMetrics to Notion database record format.
        
        Args:
            metrics: DailyMetrics object
            database_id: Target Notion database ID
            
        Returns:
            Dict formatted for Notion pages.create()
        """
        record = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"📊 Daily Metrics - {metrics.date.strftime('%Y-%m-%d')}"}}]
                },
                "Date": {
                    "date": {"start": metrics.date.strftime('%Y-%m-%d')}
                },
                "Planned Working Hours": {"number": metrics.planned_working_hours},
                "Effective Hours Worked": {"number": metrics.effective_hours_worked},
                "Time on Planned Tasks": {"number": metrics.time_on_planned_tasks},
                "Time on Unplanned Tasks": {"number": metrics.time_on_unplanned_tasks},
                "Tasks Planned Count": {"number": metrics.tasks_planned_count},
                "Tasks Active Count": {"number": metrics.tasks_active_count},
                "Unplanned Tasks Created": {"number": metrics.unplanned_tasks_created},
                "Cold Tasks Count": {"number": metrics.cold_tasks_count},
                "Productivity Score": {"number": metrics.productivity_score},
                "Schedule Adherence %": {"number": metrics.schedule_adherence_pct / 100},
                "Task Completion Rate %": {"number": metrics.task_completion_rate_pct / 100},
                "Context Switches": {"number": metrics.context_switches}
            }
        }
        
        # Add task relations if they exist
        if metrics.active_task_ids:
            record["properties"]["Active Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.active_task_ids]
            }
        
        if metrics.planned_task_ids:
            record["properties"]["Planned Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.planned_task_ids]
            }
        
        if metrics.worked_on_task_ids:
            record["properties"]["Worked On Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.worked_on_task_ids]
            }
        
        if metrics.completed_task_ids:
            record["properties"]["Completed Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.completed_task_ids]
            }
        
        # Add optional fields if provided
        if metrics.work_day_type:
            record["properties"]["Work Day Type"] = {"select": {"name": metrics.work_day_type}}
        
        if metrics.quality_rating:
            record["properties"]["Quality Rating"] = {"select": {"name": metrics.quality_rating}}
        
        if metrics.notes:
            record["properties"]["Notes"] = {"rich_text": [{"text": {"content": metrics.notes}}]}
        
        return record
    
    def to_notion_update_properties(self, metrics: DailyMetrics) -> Dict[str, Any]:
        """
        Convert DailyMetrics to Notion update properties format (for pages.update()).
        
        Args:
            metrics: DailyMetrics object
            
        Returns:
            Dict formatted for Notion pages.update() properties
        """
        properties = {
            "Planned Working Hours": {"number": metrics.planned_working_hours},
            "Effective Hours Worked": {"number": metrics.effective_hours_worked},
            "Time on Planned Tasks": {"number": metrics.time_on_planned_tasks},
            "Time on Unplanned Tasks": {"number": metrics.time_on_unplanned_tasks},
            "Tasks Planned Count": {"number": metrics.tasks_planned_count},
            "Tasks Active Count": {"number": metrics.tasks_active_count},
            "Unplanned Tasks Created": {"number": metrics.unplanned_tasks_created},
            "Cold Tasks Count": {"number": metrics.cold_tasks_count},
            "Productivity Score": {"number": metrics.productivity_score},
            "Schedule Adherence %": {"number": metrics.schedule_adherence_pct / 100},
            "Task Completion Rate %": {"number": metrics.task_completion_rate_pct / 100},
            "Context Switches": {"number": metrics.context_switches}
        }
        
        # Add task relations if they exist
        if metrics.active_task_ids:
            properties["Active Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.active_task_ids]
            }
        
        if metrics.planned_task_ids:
            properties["Planned Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.planned_task_ids]
            }
        
        if metrics.worked_on_task_ids:
            properties["Worked On Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.worked_on_task_ids]
            }
        
        if metrics.completed_task_ids:
            properties["Completed Tasks"] = {
                "relation": [{"id": task_id} for task_id in metrics.completed_task_ids]
            }
        
        # Add optional fields if provided
        if metrics.work_day_type:
            properties["Work Day Type"] = {"select": {"name": metrics.work_day_type}}
        
        if metrics.quality_rating:
            properties["Quality Rating"] = {"select": {"name": metrics.quality_rating}}
        
        if metrics.notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": metrics.notes}}]}
        
        return properties

    def find_existing_metrics_page(self, database_id: str, target_date: datetime, notion_client) -> Optional[str]:
        """
        Find existing metrics page for the given date.
        
        Args:
            database_id: Notion database ID
            target_date: Date to search for
            notion_client: Notion client instance
            
        Returns:
            Page ID if found, None otherwise
        """
        try:
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Query database for entries with matching date
            query_result = notion_client.client.databases.query(
                database_id=database_id,
                filter={
                    "property": "Date",
                    "date": {
                        "equals": date_str
                    }
                }
            )
            
            if query_result.get("results"):
                # Return the first matching page ID
                return query_result["results"][0]["id"]
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find existing metrics page: {e}")
            return None

    def upsert_metrics_to_notion(self, metrics: DailyMetrics, database_id: str, notion_client) -> Dict[str, str]:
        """
        Insert or update daily metrics in Notion database.
        
        Args:
            metrics: DailyMetrics object
            database_id: Target Notion database ID
            notion_client: Notion client instance
            
        Returns:
            Dict with page_id, url, and action (created/updated)
        """
        # Check if entry already exists for this date
        existing_page_id = self.find_existing_metrics_page(database_id, metrics.date, notion_client)
        
        if existing_page_id:
            # Update existing page
            logger.info(f"Updating existing metrics page for {metrics.date.date()}")
            update_properties = self.to_notion_update_properties(metrics)
            
            response = notion_client.client.pages.update(
                page_id=existing_page_id,
                properties=update_properties
            )
            
            return {
                "page_id": response["id"],
                "url": response["url"],
                "action": "updated"
            }
        else:
            # Create new page
            logger.info(f"Creating new metrics page for {metrics.date.date()}")
            create_record = self.to_notion_record(metrics, database_id)
            
            response = notion_client.client.pages.create(**create_record)
            
            return {
                "page_id": response["id"],
                "url": response["url"],
                "action": "created"
            }
