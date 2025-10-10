"""
Unit tests for task relations functionality.
Tests the TaskRelationsManager and related timezone handling.
"""

import pytest
import pandas as pd
from datetime import date, datetime, timezone
import pytz
from unittest.mock import Mock, MagicMock, patch

from toad.productivity.task_relations import TaskRelationsManager
from toad.notion_client import TOADNotionClient


class TestTimezoneHandling:
    """Test timezone conversion and day boundary calculations."""
    
    def test_pst_day_boundaries_utc_summer(self):
        """Test PST day boundaries during summer (PDT)."""
        # Create a mock client
        mock_client = Mock(spec=TOADNotionClient)
        manager = TaskRelationsManager(mock_client)
        
        # Test date in summer (PDT - UTC-7)
        target_date = date(2025, 7, 10)
        utc_start, utc_end = manager._get_pst_day_boundaries_utc(target_date)
        
        # Expected: 2025-07-10 00:00:00 PDT = 2025-07-10 07:00:00 UTC
        # Expected: 2025-07-10 23:59:59.999999 PDT ≈ 2025-07-11 06:59:59 UTC
        pst = pytz.timezone('America/Los_Angeles')
        expected_start = pst.localize(datetime.combine(target_date, datetime.min.time()))
        expected_end = pst.localize(datetime.combine(target_date, datetime.max.time()))
        
        assert utc_start == int(expected_start.timestamp())
        assert utc_end == int(expected_end.timestamp())
    
    def test_pst_day_boundaries_utc_winter(self):
        """Test PST day boundaries during winter (PST - UTC-8)."""
        mock_client = Mock(spec=TOADNotionClient)
        manager = TaskRelationsManager(mock_client)
        
        # Test date in winter (PST - UTC-8)
        target_date = date(2025, 1, 10)
        utc_start, utc_end = manager._get_pst_day_boundaries_utc(target_date)
        
        # Expected: 2025-01-10 00:00:00 PST = 2025-01-10 08:00:00 UTC
        pst = pytz.timezone('America/Los_Angeles')
        expected_start = pst.localize(datetime.combine(target_date, datetime.min.time()))
        expected_end = pst.localize(datetime.combine(target_date, datetime.max.time()))
        
        assert utc_start == int(expected_start.timestamp())
        assert utc_end == int(expected_end.timestamp())


class TestPlannedTasks:
    """Test planned task identification logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=TOADNotionClient)
        self.manager = TaskRelationsManager(self.mock_client)
    
    def test_get_planned_tasks_with_date_range(self):
        """Test planned tasks with date ranges that include target date."""
        # Create test data
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2', 'task3'],
            'Name': ['Task 1', 'Task 2', 'Task 3'],
            'planned_start': [
                pd.Timestamp('2025-10-10 08:00:00', tz='UTC'),
                pd.Timestamp('2025-10-09 08:00:00', tz='UTC'),
                pd.Timestamp('2025-10-11 08:00:00', tz='UTC'),
            ],
            'planned_end': [
                pd.Timestamp('2025-10-10 10:00:00', tz='UTC'),
                pd.Timestamp('2025-10-09 10:00:00', tz='UTC'),
                pd.Timestamp('2025-10-11 10:00:00', tz='UTC'),
            ]
        })
        
        target_date = date(2025, 10, 10)
        planned_ids = self.manager._get_planned_tasks(tasks_df, target_date)
        
        # Should only include task1 (planned on 10/10)
        assert len(planned_ids) == 1
        assert 'task1' in planned_ids
    
    def test_get_planned_tasks_multi_day_range(self):
        """Test planned tasks spanning multiple days."""
        # Create test data with a multi-day task
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2', 'task3'],
            'Name': ['Multi-day Task', 'Task 2', 'Task 3'],
            'planned_start': [
                pd.Timestamp('2025-10-09 08:00:00', tz='UTC'),  # Starts Oct 9
                pd.Timestamp('2025-10-10 08:00:00', tz='UTC'),
                pd.Timestamp('2025-10-08 08:00:00', tz='UTC'),
            ],
            'planned_end': [
                pd.Timestamp('2025-10-11 17:00:00', tz='UTC'),  # Ends Oct 11
                pd.Timestamp('2025-10-10 10:00:00', tz='UTC'),
                pd.Timestamp('2025-10-08 10:00:00', tz='UTC'),
            ]
        })
        
        # Test Oct 9, 10, 11 - multi-day task should appear in all
        for test_date in [date(2025, 10, 9), date(2025, 10, 10), date(2025, 10, 11)]:
            planned_ids = self.manager._get_planned_tasks(tasks_df, test_date)
            assert 'task1' in planned_ids, f"Multi-day task should be in {test_date}"
        
        # Test Oct 8 and Oct 12 - multi-day task should NOT appear
        planned_ids_before = self.manager._get_planned_tasks(tasks_df, date(2025, 10, 8))
        assert 'task1' not in planned_ids_before
        
        planned_ids_after = self.manager._get_planned_tasks(tasks_df, date(2025, 10, 12))
        assert 'task1' not in planned_ids_after
    
    def test_get_planned_tasks_empty_dataframe(self):
        """Test behavior with empty dataframe."""
        tasks_df = pd.DataFrame()
        target_date = date(2025, 10, 10)
        
        planned_ids = self.manager._get_planned_tasks(tasks_df, target_date)
        
        assert planned_ids == []
    
    def test_get_planned_tasks_no_planned_column(self):
        """Test behavior when neither Planned nor Planned Timeline columns exist."""
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2'],
            'Name': ['Task 1', 'Task 2']
        })
        target_date = date(2025, 10, 10)
        
        planned_ids = self.manager._get_planned_tasks(tasks_df, target_date)
        
        assert planned_ids == []


class TestWorkedTasks:
    """Test worked task identification logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=TOADNotionClient)
        self.manager = TaskRelationsManager(self.mock_client)
    
    def test_get_worked_tasks_single_entry(self):
        """Test worked tasks with a single time entry on target date."""
        time_entries_df = pd.DataFrame({
            'entry_id': ['entry1', 'entry2', 'entry3'],
            'entry_start_time': [
                pd.Timestamp('2025-10-10 09:00:00', tz='UTC'),
                pd.Timestamp('2025-10-09 09:00:00', tz='UTC'),
                pd.Timestamp('2025-10-11 09:00:00', tz='UTC'),
            ],
            'related_task_ids': [
                ['task1'],
                ['task2'],
                ['task3'],
            ]
        })
        
        target_date = date(2025, 10, 10)
        worked_ids = self.manager._get_worked_tasks(time_entries_df, target_date)
        
        # Should only include task1 (worked on 10/10)
        assert len(worked_ids) == 1
        assert 'task1' in worked_ids
    
    def test_get_worked_tasks_multiple_entries_same_task(self):
        """Test worked tasks when multiple entries for same task on same day."""
        time_entries_df = pd.DataFrame({
            'entry_id': ['entry1', 'entry2', 'entry3'],
            'entry_start_time': [
                pd.Timestamp('2025-10-10 09:00:00', tz='UTC'),
                pd.Timestamp('2025-10-10 13:00:00', tz='UTC'),
                pd.Timestamp('2025-10-10 15:00:00', tz='UTC'),
            ],
            'related_task_ids': [
                ['task1'],
                ['task1'],  # Same task, different entry
                ['task2'],
            ]
        })
        
        target_date = date(2025, 10, 10)
        worked_ids = self.manager._get_worked_tasks(time_entries_df, target_date)
        
        # Should include both task1 and task2 (deduplicated)
        assert len(worked_ids) == 2
        assert 'task1' in worked_ids
        assert 'task2' in worked_ids
    
    def test_get_worked_tasks_empty_dataframe(self):
        """Test behavior with empty dataframe."""
        time_entries_df = pd.DataFrame()
        target_date = date(2025, 10, 10)
        
        worked_ids = self.manager._get_worked_tasks(time_entries_df, target_date)
        
        assert worked_ids == []


class TestDoneTasks:
    """Test completed task identification logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=TOADNotionClient)
        self.manager = TaskRelationsManager(self.mock_client)
    
    def test_get_done_tasks_with_done_column(self):
        """Test done tasks using 'Done' column."""
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2', 'task3'],
            'Name': ['Task 1', 'Task 2', 'Task 3'],
            'Done': [
                pd.Timestamp('2025-10-10 14:00:00', tz='UTC'),
                pd.Timestamp('2025-10-09 14:00:00', tz='UTC'),
                pd.NaT,  # Not done
            ]
        })
        
        target_date = date(2025, 10, 10)
        done_ids = self.manager._get_done_tasks(tasks_df, target_date)
        
        # Should only include task1 (done on 10/10)
        assert len(done_ids) == 1
        assert 'task1' in done_ids
    
    def test_get_done_tasks_timezone_boundary(self):
        """Test done tasks respecting PST day boundaries."""
        # This tests a task completed late at night PST
        # which might be the next day in UTC
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2'],
            'Name': ['Late Task', 'Early Task'],
            'Done': [
                # Oct 10, 2025 23:00:00 PST = Oct 11, 2025 06:00:00 UTC
                pd.Timestamp('2025-10-11 06:00:00', tz='UTC'),
                # Oct 11, 2025 01:00:00 PST = Oct 11, 2025 08:00:00 UTC
                pd.Timestamp('2025-10-11 08:00:00', tz='UTC'),
            ]
        })
        
        # Task completed at 23:00 PST on Oct 10 should be in Oct 10's done list
        target_date = date(2025, 10, 10)
        done_ids = self.manager._get_done_tasks(tasks_df, target_date)
        
        assert 'task1' in done_ids
        assert 'task2' not in done_ids  # This is Oct 11 PST


class TestActiveTasks:
    """Test active task identification logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=TOADNotionClient)
        self.manager = TaskRelationsManager(self.mock_client)
    
    def test_get_active_tasks_planned_only(self):
        """Test active tasks that are only planned."""
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2'],
            'Name': ['Planned Task', 'Other Task'],
            'planned_start': [
                pd.Timestamp('2025-10-10 08:00:00', tz='UTC'),
                pd.Timestamp('2025-10-09 08:00:00', tz='UTC'),
            ],
            'planned_end': [
                pd.Timestamp('2025-10-10 10:00:00', tz='UTC'),
                pd.Timestamp('2025-10-09 10:00:00', tz='UTC'),
            ]
        })
        
        time_entries_df = pd.DataFrame()  # No time entries
        
        target_date = date(2025, 10, 10)
        active_ids = self.manager._get_active_tasks(tasks_df, time_entries_df, target_date)
        
        # Should include task1 (planned for today)
        assert 'task1' in active_ids
        assert 'task2' not in active_ids
    
    def test_get_active_tasks_worked_only(self):
        """Test active tasks that are only worked on (not planned)."""
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2'],
            'Name': ['Worked Task', 'Other Task']
        })
        
        time_entries_df = pd.DataFrame({
            'entry_id': ['entry1'],
            'entry_start_time': [
                pd.Timestamp('2025-10-10 09:00:00', tz='UTC'),
            ],
            'related_task_ids': [
                ['task1'],
            ]
        })
        
        target_date = date(2025, 10, 10)
        active_ids = self.manager._get_active_tasks(tasks_df, time_entries_df, target_date)
        
        # Should include task1 (worked on today)
        assert 'task1' in active_ids
        assert 'task2' not in active_ids
    
    def test_get_active_tasks_combined(self):
        """Test active tasks combining planned and worked."""
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2', 'task3'],
            'Name': ['Planned and Worked', 'Only Planned', 'Only Worked'],
            'planned_start': [
                pd.Timestamp('2025-10-10 08:00:00', tz='UTC'),
                pd.Timestamp('2025-10-10 09:00:00', tz='UTC'),
                pd.NaT,
            ],
            'planned_end': [
                pd.Timestamp('2025-10-10 10:00:00', tz='UTC'),
                pd.Timestamp('2025-10-10 11:00:00', tz='UTC'),
                pd.NaT,
            ]
        })
        
        time_entries_df = pd.DataFrame({
            'entry_id': ['entry1', 'entry2'],
            'entry_start_time': [
                pd.Timestamp('2025-10-10 09:00:00', tz='UTC'),
                pd.Timestamp('2025-10-10 13:00:00', tz='UTC'),
            ],
            'related_task_ids': [
                ['task1'],
                ['task3'],
            ]
        })
        
        target_date = date(2025, 10, 10)
        active_ids = self.manager._get_active_tasks(tasks_df, time_entries_df, target_date)
        
        # Should include all three tasks
        assert len(active_ids) == 3
        assert 'task1' in active_ids  # Both planned and worked
        assert 'task2' in active_ids  # Only planned
        assert 'task3' in active_ids  # Only worked


class TestIntegration:
    """Integration tests for the full workflow."""
    
    @patch('toad.productivity.task_relations.TaskDataExtractor')
    @patch('toad.productivity.task_relations.TimeEntryExtractor')
    def test_get_relation_summary(self, mock_time_extractor_class, mock_task_extractor_class):
        """Test getting a summary of all relations for a date."""
        # Set up mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        # Mock task data
        tasks_df = pd.DataFrame({
            'page_id': ['task1', 'task2', 'task3'],
            'Name': ['Task 1', 'Task 2', 'Task 3'],
            'planned_start': [
                pd.Timestamp('2025-10-10 08:00:00', tz='UTC'),
                pd.NaT,
                pd.NaT,
            ],
            'planned_end': [
                pd.Timestamp('2025-10-10 10:00:00', tz='UTC'),
                pd.NaT,
                pd.NaT,
            ],
            'Done': [
                pd.NaT,
                pd.Timestamp('2025-10-10 14:00:00', tz='UTC'),
                pd.NaT,
            ]
        })
        
        # Mock time entry data
        time_entries_df = pd.DataFrame({
            'entry_id': ['entry1', 'entry2'],
            'entry_start_time': [
                pd.Timestamp('2025-10-10 09:00:00', tz='UTC'),
                pd.Timestamp('2025-10-10 13:00:00', tz='UTC'),
            ],
            'related_task_ids': [
                ['task1'],
                ['task3'],
            ]
        })
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = tasks_df
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = time_entries_df
        
        # Create manager and get summary
        mock_client = Mock(spec=TOADNotionClient)
        manager = TaskRelationsManager(mock_client)
        
        target_date = date(2025, 10, 10)
        summary = manager.get_relation_summary(target_date)
        
        # Verify summary
        assert summary['target_date'] == '2025-10-10'
        assert summary['planned_count'] == 1  # task1
        assert summary['done_count'] == 1  # task2
        assert summary['worked_count'] == 2  # task1, task3
        assert summary['active_count'] >= 2  # At least task1 and task3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
