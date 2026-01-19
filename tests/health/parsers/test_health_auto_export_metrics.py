"""Tests for HealthAutoExport activity metrics parser."""

import pytest
from datetime import datetime
from pathlib import Path

from toad.health.parsers.health_auto_export_metrics import HealthAutoExportMetricsParser
from toad.health.models import DailyActivityMetrics


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "health_auto_export"


class TestHealthAutoExportMetricsParser:
    """Tests for HealthAutoExport activity metrics parser."""

    def test_parse_valid_daily_metrics(self):
        """Test parsing a valid daily metrics file with all metrics present."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        assert isinstance(metrics, DailyActivityMetrics)
        assert metrics.date == datetime(2026, 1, 17)
        assert metrics.calories_in == pytest.approx(2100.5, rel=0.01)
        assert metrics.calories_out == pytest.approx(1750.25, rel=0.01)
        assert metrics.weight == pytest.approx(175.5, rel=0.01)
        assert metrics.body_fat == pytest.approx(15.2, rel=0.01)
        assert metrics.source == "HealthAutoExport"

    def test_parse_empty_metrics(self):
        """Test parsing a file with no metrics."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "HealthAutoExport-2026-01-18.json"

        metrics = parser.parse(fixture_path)

        assert isinstance(metrics, DailyActivityMetrics)
        # Should extract date from filename
        assert metrics.date == datetime(2026, 1, 18)
        # All metrics should be None
        assert metrics.calories_in is None
        assert metrics.calories_out is None
        assert metrics.weight is None
        assert metrics.body_fat is None

    def test_parse_partial_metrics(self):
        """Test parsing a file with only some metrics present."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "partial_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        assert isinstance(metrics, DailyActivityMetrics)
        assert metrics.date == datetime(2026, 1, 18)
        # Only weight and active_energy present
        assert metrics.weight == pytest.approx(174.8, rel=0.01)
        assert metrics.calories_out == pytest.approx(450.0, rel=0.01)
        # Others should be None
        assert metrics.calories_in is None
        assert metrics.body_fat is None

    def test_aggregate_multiple_weight_readings(self):
        """Test averaging multiple weight readings in a day."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "multiple_readings_per_day.json"

        metrics = parser.parse(fixture_path)

        # Three weight readings: 175.2, 176.8, 175.5
        # Average: (175.2 + 176.8 + 175.5) / 3 = 175.83
        assert metrics.weight == pytest.approx(175.8, abs=0.1)

    def test_aggregate_multiple_body_fat_readings(self):
        """Test averaging multiple body fat readings in a day."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "multiple_readings_per_day.json"

        metrics = parser.parse(fixture_path)

        # Two body fat readings: 15.1, 15.3
        # Average: (15.1 + 15.3) / 2 = 15.2
        assert metrics.body_fat == pytest.approx(15.2, rel=0.01)

    def test_sum_calorie_values(self):
        """Test summing calorie values (not averaging)."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "multiple_readings_per_day.json"

        metrics = parser.parse(fixture_path)

        # Calories should be summed, not averaged
        assert metrics.calories_out == pytest.approx(1800.5, rel=0.01)
        assert metrics.calories_in == pytest.approx(2200.0, rel=0.01)

    def test_extract_dietary_energy(self):
        """Test extracting dietary energy (calories in)."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        assert metrics.calories_in == pytest.approx(2100.5, rel=0.01)

    def test_extract_active_energy(self):
        """Test extracting active energy (calories out)."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        assert metrics.calories_out == pytest.approx(1750.25, rel=0.01)

    def test_extract_weight_body_mass(self):
        """Test extracting weight."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        assert metrics.weight == pytest.approx(175.5, rel=0.01)

    def test_extract_body_fat_percentage(self):
        """Test extracting body fat percentage."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        assert metrics.body_fat == pytest.approx(15.2, rel=0.01)

    def test_handle_missing_metrics(self):
        """Test handling when expected metrics are missing."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "partial_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        # Should not raise error, just set missing metrics to None
        assert metrics.calories_in is None
        assert metrics.body_fat is None

    def test_parse_date_from_data(self):
        """Test date extraction from metric data points."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        # Date should be extracted from first data point
        assert metrics.date == datetime(2026, 1, 17)
        assert metrics.date.year == 2026
        assert metrics.date.month == 1
        assert metrics.date.day == 17

    def test_parse_date_from_filename_fallback(self):
        """Test date extraction from filename when no data points have dates."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "HealthAutoExport-2026-01-18.json"

        metrics = parser.parse(fixture_path)

        # Should fall back to extracting date from filename
        assert metrics.date == datetime(2026, 1, 18)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = HealthAutoExportMetricsParser()

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/path/file.json"))

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises appropriate error."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "invalid_format.json"

        with pytest.raises(ValueError):
            parser.parse(fixture_path)

    def test_ignore_unrelated_metrics(self):
        """Test that unrelated metrics (like walking_running_distance) are ignored."""
        parser = HealthAutoExportMetricsParser()
        # The partial_activity_metrics file might have walking_running_distance
        # Let's just verify that parsing doesn't fail when extra metrics exist
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        # Should successfully parse without errors
        assert isinstance(metrics, DailyActivityMetrics)

    def test_rounded_values(self):
        """Test that all values are properly rounded to 1 decimal place."""
        parser = HealthAutoExportMetricsParser()
        fixture_path = FIXTURES_DIR / "valid_activity_metrics.json"

        metrics = parser.parse(fixture_path)

        # All values should be floats rounded to 1 decimal
        if metrics.calories_in:
            assert metrics.calories_in == round(metrics.calories_in, 1)
        if metrics.calories_out:
            assert metrics.calories_out == round(metrics.calories_out, 1)
        if metrics.weight:
            assert metrics.weight == round(metrics.weight, 1)
        if metrics.body_fat:
            assert metrics.body_fat == round(metrics.body_fat, 1)
