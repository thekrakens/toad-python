"""
Unit and integration tests for TOAD CLI.
Tests the simplified sync command with 3 modes.
"""

import pytest
import argparse
import sys
from datetime import date, datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO

from toad.cli import (
    parse_date_flexible,
    parse_date_range,
    cmd_sync,
    main
)


class TestDateParsing:
    """Test date parsing utilities."""
    
    def test_parse_date_flexible_yyyy_mm_dd(self):
        """Test parsing YYYY-MM-DD format."""
        result = parse_date_flexible("2025-10-12")
        assert result == date(2025, 10, 12)
    
    def test_parse_date_flexible_mm_dd_yy(self):
        """Test parsing MM-DD-YY format."""
        result = parse_date_flexible("10-12-25")
        assert result == date(2025, 10, 12)
    
    def test_parse_date_flexible_mm_slash_dd_slash_yy(self):
        """Test parsing MM/DD/YY format."""
        result = parse_date_flexible("10/12/25")
        assert result == date(2025, 10, 12)
    
    def test_parse_date_flexible_invalid_format(self):
        """Test parsing with invalid format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_date_flexible("invalid-date")
        
        assert "Invalid date format" in str(exc_info.value)
    
    def test_parse_date_range_empty(self):
        """Test parse_date_range with no arguments returns today."""
        result = parse_date_range([])
        assert result == [date.today()]
    
    def test_parse_date_range_single_date(self):
        """Test parse_date_range with single date."""
        result = parse_date_range(["10-12-25"])
        assert result == [date(2025, 10, 12)]
    
    def test_parse_date_range_two_dates(self):
        """Test parse_date_range with date range."""
        result = parse_date_range(["10-10-25", "10-12-25"])
        expected = [
            date(2025, 10, 10),
            date(2025, 10, 11),
            date(2025, 10, 12)
        ]
        assert result == expected
    
    def test_parse_date_range_end_before_start(self):
        """Test parse_date_range raises error when end date before start."""
        with pytest.raises(ValueError) as exc_info:
            parse_date_range(["10-12-25", "10-10-25"])
        
        assert "before start date" in str(exc_info.value)
    
    def test_parse_date_range_too_many_args(self):
        """Test parse_date_range raises error with too many arguments."""
        with pytest.raises(ValueError) as exc_info:
            parse_date_range(["10-10-25", "10-11-25", "10-12-25"])
        
        assert "Too many date arguments" in str(exc_info.value)


class TestCLICacheClear:
    """Test CLI cache clearing functionality."""
    
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_clear_cache_flag(self, mock_print, mock_client, mock_get_cache):
        """Test --clear-cache flag clears the cache and exits."""
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        
        # Create mock args
        args = Mock()
        args.clear_cache = True
        args.full = False
        args.dates = None
        
        # Execute command
        cmd_sync(args)
        
        # Verify cache was cleared
        mock_cache.clear_all.assert_called_once()
        
        # Verify success message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Cache cleared successfully" in str(call) for call in print_calls)


class TestCLIIncrementalSync:
    """Test Mode 1: Incremental Sync (Default)."""
    
    @patch('toad.cli.TaskRelationsManager')
    @patch('toad.cli.TimeEntryExtractor')
    @patch('toad.cli.TaskDataExtractor')
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_incremental_sync_with_cache(self, mock_print, mock_client, 
                                         mock_get_cache, mock_task_extractor_class,
                                         mock_time_extractor_class, mock_relations_class):
        """Test incremental sync uses cache timestamps."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        
        # Mock cache returning timestamps
        last_sync = datetime(2025, 10, 12, 10, 0, 0)
        mock_cache.get_last_sync_time.side_effect = lambda component: last_sync
        
        # Mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = Mock(
            __len__=lambda self: 10
        )
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = Mock(
            __len__=lambda self: 5
        )
        
        # Mock relations manager
        mock_relations = Mock()
        mock_relations_class.return_value = mock_relations
        mock_relations.process_daily_task_relations_with_data.return_value = {
            'planned': {'success': True, 'task_count': 2},
            'active': {'success': True, 'task_count': 3},
            'worked': {'success': True, 'task_count': 1},
            'done': {'success': True, 'task_count': 1}
        }
        
        # Create args for incremental sync (no dates, no flags)
        args = Mock()
        args.clear_cache = False
        args.full = False
        args.dates = None
        
        # Execute
        cmd_sync(args)
        
        # Verify cache was checked
        assert mock_cache.get_last_sync_time.call_count == 2
        mock_cache.get_last_sync_time.assert_any_call('tasks')
        mock_cache.get_last_sync_time.assert_any_call('time_entries')
        
        # Verify extractors were called with modified_since
        mock_task_extractor.extract_tasks_to_dataframe.assert_called_once_with(
            modified_since=last_sync
        )
        mock_time_extractor.extract_time_entries_to_dataframe.assert_called_once_with(
            modified_since=last_sync
        )
        
        # Verify only today was synced
        assert mock_relations.process_daily_task_relations_with_data.call_count == 1
        
        # Verify cache was updated
        assert mock_cache.update_last_sync_time.call_count == 2
    
    @patch('toad.cli.TaskRelationsManager')
    @patch('toad.cli.TimeEntryExtractor')
    @patch('toad.cli.TaskDataExtractor')
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_incremental_sync_no_cache(self, mock_print, mock_client,
                                       mock_get_cache, mock_task_extractor_class,
                                       mock_time_extractor_class, mock_relations_class):
        """Test incremental sync without cache fetches all data."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        
        # Mock cache returning None (no previous sync)
        mock_cache.get_last_sync_time.return_value = None
        
        # Mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = Mock(
            __len__=lambda self: 50
        )
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = Mock(
            __len__=lambda self: 25
        )
        
        # Mock relations manager
        mock_relations = Mock()
        mock_relations_class.return_value = mock_relations
        mock_relations.process_daily_task_relations_with_data.return_value = {
            'planned': {'success': True, 'task_count': 5},
            'active': {'success': True, 'task_count': 8},
            'worked': {'success': True, 'task_count': 3},
            'done': {'success': True, 'task_count': 2}
        }
        
        # Create args
        args = Mock()
        args.clear_cache = False
        args.full = False
        args.dates = None
        
        # Execute
        cmd_sync(args)
        
        # Verify extractors were called WITHOUT modified_since
        mock_task_extractor.extract_tasks_to_dataframe.assert_called_once_with(
            modified_since=None
        )
        mock_time_extractor.extract_time_entries_to_dataframe.assert_called_once_with(
            modified_since=None
        )


class TestCLIDateSync:
    """Test Mode 2: Date Sync."""
    
    @patch('toad.cli.TaskRelationsManager')
    @patch('toad.cli.TimeEntryExtractor')
    @patch('toad.cli.TaskDataExtractor')
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_single_date_sync(self, mock_print, mock_client,
                             mock_get_cache, mock_task_extractor_class,
                             mock_time_extractor_class, mock_relations_class):
        """Test syncing a single specific date."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get_last_sync_time.return_value = datetime(2025, 10, 12, 10, 0, 0)
        
        # Mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = Mock(
            __len__=lambda self: 10
        )
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = Mock(
            __len__=lambda self: 5
        )
        
        # Mock relations manager
        mock_relations = Mock()
        mock_relations_class.return_value = mock_relations
        mock_relations.process_daily_task_relations_with_data.return_value = {
            'planned': {'success': True, 'task_count': 3},
            'active': {'success': True, 'task_count': 4},
            'worked': {'success': True, 'task_count': 2},
            'done': {'success': True, 'task_count': 1}
        }
        
        # Create args for specific date
        args = Mock()
        args.clear_cache = False
        args.full = False
        args.dates = ["10-10-25"]
        
        # Execute
        cmd_sync(args)
        
        # Verify only one date was processed
        assert mock_relations.process_daily_task_relations_with_data.call_count == 1
        
        # Verify the correct date was used
        call_args = mock_relations.process_daily_task_relations_with_data.call_args
        assert call_args[0][0] == date(2025, 10, 10)
    
    @patch('toad.cli.TaskRelationsManager')
    @patch('toad.cli.TimeEntryExtractor')
    @patch('toad.cli.TaskDataExtractor')
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_date_range_sync(self, mock_print, mock_client,
                            mock_get_cache, mock_task_extractor_class,
                            mock_time_extractor_class, mock_relations_class):
        """Test syncing a date range."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get_last_sync_time.return_value = datetime(2025, 10, 12, 10, 0, 0)
        
        # Mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = Mock(
            __len__=lambda self: 10
        )
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = Mock(
            __len__=lambda self: 5
        )
        
        # Mock relations manager
        mock_relations = Mock()
        mock_relations_class.return_value = mock_relations
        mock_relations.process_daily_task_relations_with_data.return_value = {
            'planned': {'success': True, 'task_count': 2},
            'active': {'success': True, 'task_count': 3},
            'worked': {'success': True, 'task_count': 1},
            'done': {'success': True, 'task_count': 1}
        }
        
        # Create args for date range (3 days)
        args = Mock()
        args.clear_cache = False
        args.full = False
        args.dates = ["10-10-25", "10-12-25"]
        
        # Execute
        cmd_sync(args)
        
        # Verify three dates were processed
        assert mock_relations.process_daily_task_relations_with_data.call_count == 3
        
        # Verify the correct dates were used
        call_dates = [
            call[0][0] for call in 
            mock_relations.process_daily_task_relations_with_data.call_args_list
        ]
        assert date(2025, 10, 10) in call_dates
        assert date(2025, 10, 11) in call_dates
        assert date(2025, 10, 12) in call_dates


class TestCLIFullSync:
    """Test Mode 3: Full Sync."""
    
    @patch('toad.cli.TaskRelationsManager')
    @patch('toad.cli.TimeEntryExtractor')
    @patch('toad.cli.TaskDataExtractor')
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_full_sync(self, mock_print, mock_client,
                      mock_get_cache, mock_task_extractor_class,
                      mock_time_extractor_class, mock_relations_class):
        """Test full sync mode syncs last 30 days and resets cache."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        
        # Mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = Mock(
            __len__=lambda self: 100
        )
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = Mock(
            __len__=lambda self: 50
        )
        
        # Mock relations manager
        mock_relations = Mock()
        mock_relations_class.return_value = mock_relations
        mock_relations.process_daily_task_relations_with_data.return_value = {
            'planned': {'success': True, 'task_count': 5},
            'active': {'success': True, 'task_count': 8},
            'worked': {'success': True, 'task_count': 3},
            'done': {'success': True, 'task_count': 2}
        }
        
        # Create args for full sync
        args = Mock()
        args.clear_cache = False
        args.full = True
        args.dates = None
        
        # Execute
        cmd_sync(args)
        
        # Verify 30 dates were processed
        assert mock_relations.process_daily_task_relations_with_data.call_count == 30
        
        # Verify extractors were called WITHOUT modified_since (ignoring cache)
        mock_task_extractor.extract_tasks_to_dataframe.assert_called_once()
        mock_time_extractor.extract_time_entries_to_dataframe.assert_called_once()
        
        # Verify cache was updated (reset)
        assert mock_cache.update_last_sync_time.call_count == 2


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    @patch('toad.cli.TaskRelationsManager')
    @patch('toad.cli.TimeEntryExtractor')
    @patch('toad.cli.TaskDataExtractor')
    @patch('toad.cli.get_sync_cache')
    @patch('toad.cli.TOADNotionClient')
    @patch('builtins.print')
    def test_sync_with_error(self, mock_print, mock_client,
                            mock_get_cache, mock_task_extractor_class,
                            mock_time_extractor_class, mock_relations_class):
        """Test sync handles errors gracefully."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get_last_sync_time.return_value = None
        
        # Mock extractors
        mock_task_extractor = Mock()
        mock_time_extractor = Mock()
        mock_task_extractor_class.return_value = mock_task_extractor
        mock_time_extractor_class.return_value = mock_time_extractor
        
        mock_task_extractor.extract_tasks_to_dataframe.return_value = Mock(
            __len__=lambda self: 10
        )
        mock_time_extractor.extract_time_entries_to_dataframe.return_value = Mock(
            __len__=lambda self: 5
        )
        
        # Mock relations manager to return an error
        mock_relations = Mock()
        mock_relations_class.return_value = mock_relations
        mock_relations.process_daily_task_relations_with_data.return_value = {
            'error': 'Failed to update relations'
        }
        
        # Create args
        args = Mock()
        args.clear_cache = False
        args.full = False
        args.dates = None
        
        # Execute
        cmd_sync(args)
        
        # Verify error was handled (cache should NOT be updated)
        mock_cache.update_last_sync_time.assert_not_called()
        
        # Verify error message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("error" in str(call).lower() for call in print_calls)
    
    @patch('builtins.print')
    @patch('sys.exit')
    def test_invalid_date_format(self, mock_exit, mock_print):
        """Test invalid date format exits with error."""
        args = Mock()
        args.clear_cache = False
        args.full = False
        args.dates = ["invalid-date"]
        
        # Execute (should exit with error)
        cmd_sync(args)
        
        # Verify exit was called
        mock_exit.assert_called_once_with(1)


class TestMainFunction:
    """Test main CLI entry point."""
    
    @patch('toad.cli.cmd_sync')
    @patch('sys.argv', ['toad.cli', 'sync'])
    def test_main_default_sync(self, mock_cmd_sync):
        """Test main function with default sync command."""
        main()
        
        # Verify cmd_sync was called
        mock_cmd_sync.assert_called_once()
    
    @patch('toad.cli.cmd_sync')
    @patch('sys.argv', ['toad.cli', 'sync', '10-12-25'])
    def test_main_date_sync(self, mock_cmd_sync):
        """Test main function with date argument."""
        main()
        
        # Verify cmd_sync was called with date in args
        args = mock_cmd_sync.call_args[0][0]
        assert args.dates == ['10-12-25']
    
    @patch('toad.cli.cmd_sync')
    @patch('sys.argv', ['toad.cli', 'sync', '--full'])
    def test_main_full_sync(self, mock_cmd_sync):
        """Test main function with full flag."""
        main()
        
        # Verify cmd_sync was called with full flag
        args = mock_cmd_sync.call_args[0][0]
        assert args.full is True
    
    @patch('builtins.print')
    @patch('sys.exit')
    @patch('sys.argv', ['toad.cli', 'invalid'])
    def test_main_invalid_command(self, mock_exit, mock_print):
        """Test main function with invalid command."""
        main()
        
        # Verify error was printed and exit was called
        mock_exit.assert_called_once_with(1)
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Unknown command" in str(call) for call in print_calls)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
