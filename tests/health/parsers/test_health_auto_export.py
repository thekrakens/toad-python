"""Tests for HealthAutoExport JSON parser."""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from toad.health.parsers.health_auto_export import HealthAutoExportParser
from toad.health.models import WorkoutData


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "health_auto_export"


class TestHealthAutoExportParser:
    """Tests for HealthAutoExport JSON parser."""

    def test_parse_valid_workouts(self):
        """Test parsing a valid HealthAutoExport JSON file with multiple workouts."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        # Should have 4 workouts
        assert len(workouts) == 4

        # Verify first workout (Climbing)
        # Input: "2026-01-17 10:51:41 -0800" (PST) -> UTC: 18:51:41
        climbing = workouts[0]
        assert climbing.workout_type == "Climb"
        assert climbing.date == datetime(2026, 1, 17, 18, 51, 41, tzinfo=timezone.utc)
        assert climbing.duration_minutes == pytest.approx(249.47, rel=0.01)  # 14968.47 seconds / 60
        assert climbing.calories == pytest.approx(1379.96, rel=0.01)
        assert climbing.avg_heart_rate == pytest.approx(117.82, rel=0.01)
        assert climbing.source == "HealthAutoExport"
        assert climbing.notes is not None
        assert "28842056-B969-46AE-ABEF-4E0421E38B9B" in climbing.notes

        # Verify second workout (Running)
        # Input: "2026-01-15 06:30:00 -0800" (PST) -> UTC: 14:30:00
        running = workouts[1]
        assert running.workout_type == "Run"
        assert running.date == datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        assert running.duration_minutes == pytest.approx(45.5, rel=0.01)  # 2730 seconds / 60
        assert running.distance_miles == pytest.approx(5.2, rel=0.01)
        assert running.calories == 450
        assert running.avg_heart_rate == pytest.approx(145.5, rel=0.01)

        # Verify third workout (Strength Training)
        # Input: "2026-01-16 18:00:00 -0800" (PST) -> UTC: 02:00:00 next day
        strength = workouts[2]
        assert strength.workout_type == "Strength"
        assert strength.date == datetime(2026, 1, 17, 2, 0, 0, tzinfo=timezone.utc)
        assert strength.duration_minutes == 90  # 5400 seconds / 60
        assert strength.calories == 320
        assert strength.avg_heart_rate == pytest.approx(125.3, rel=0.01)
        assert strength.distance_miles is None

        # Verify fourth workout (Hiking)
        # Input: "2026-01-14 08:00:00 -0800" (PST) -> UTC: 16:00:00
        hiking = workouts[3]
        assert hiking.workout_type == "Hike"
        assert hiking.date == datetime(2026, 1, 14, 16, 0, 0, tzinfo=timezone.utc)
        assert hiking.duration_minutes == 120  # 7200 seconds / 60
        assert hiking.distance_miles == pytest.approx(6.5, rel=0.01)
        assert hiking.calories == 650
        assert hiking.avg_heart_rate == pytest.approx(135.7, rel=0.01)

    def test_parse_empty_workouts(self):
        """Test parsing a JSON file with no workouts."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "empty_workouts.json"

        workouts = parser.parse(fixture_path)

        assert workouts == []

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises appropriate error."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "invalid_format.json"

        with pytest.raises(Exception):  # Will be more specific once implemented
            parser.parse(fixture_path)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = HealthAutoExportParser()

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/path/file.json"))

    def test_activity_name_mapping(self):
        """Test that workout names are correctly mapped to TOAD workout names."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)
        workout_types = [w.workout_type for w in workouts]

        # Should have these mapped types
        assert "Climb" in workout_types
        assert "Run" in workout_types
        assert "Strength" in workout_types
        assert "Hike" in workout_types

    def test_duration_conversion(self):
        """Test that duration is correctly converted from seconds to minutes."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        climbing = next(w for w in workouts if w.workout_type == "Climb")
        # 14968.47 seconds = 249.47 minutes
        assert climbing.duration_minutes == pytest.approx(249.47, rel=0.01)

        running = next(w for w in workouts if w.workout_type == "Run")
        # 2730 seconds = 45.5 minutes
        assert running.duration_minutes == pytest.approx(45.5, rel=0.01)

    def test_calories_extraction(self):
        """Test that calories are correctly extracted from activeEnergyBurned."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        climbing = next(w for w in workouts if w.workout_type == "Climb")
        assert climbing.calories == pytest.approx(1379.96, rel=0.01)

        running = next(w for w in workouts if w.workout_type == "Run")
        assert running.calories == 450

    def test_heart_rate_extraction(self):
        """Test that average heart rate is correctly extracted."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        climbing = next(w for w in workouts if w.workout_type == "Climb")
        assert climbing.avg_heart_rate == pytest.approx(117.82, rel=0.01)

        running = next(w for w in workouts if w.workout_type == "Run")
        assert running.avg_heart_rate == pytest.approx(145.5, rel=0.01)

    def test_distance_extraction(self):
        """Test that distance is correctly extracted when present."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        # Workouts with distance
        running = next(w for w in workouts if w.workout_type == "Run")
        assert running.distance_miles == pytest.approx(5.2, rel=0.01)

        hiking = next(w for w in workouts if w.workout_type == "Hike")
        assert hiking.distance_miles == pytest.approx(6.5, rel=0.01)

        # Workouts without distance
        climbing = next(w for w in workouts if w.workout_type == "Climb")
        assert climbing.distance_miles is None

        strength = next(w for w in workouts if w.workout_type == "Strength")
        assert strength.distance_miles is None

    def test_date_parsing(self):
        """Test that workout dates are correctly parsed from start timestamp."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        climbing = next(w for w in workouts if w.workout_type == "Climb")
        # start: "2026-01-17 10:51:41 -0800" -> UTC: 18:51:41
        assert climbing.date == datetime(2026, 1, 17, 18, 51, 41, tzinfo=timezone.utc)
        assert climbing.date.year == 2026
        assert climbing.date.month == 1
        assert climbing.date.day == 17
        assert climbing.date.hour == 18  # UTC hour
        assert climbing.date.minute == 51
        assert climbing.date.tzinfo == timezone.utc

    def test_workout_id_in_notes(self):
        """Test that workout ID is stored in notes for deduplication."""
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        climbing = next(w for w in workouts if w.workout_type == "Climb")
        assert climbing.notes is not None
        assert "28842056-B969-46AE-ABEF-4E0421E38B9B" in climbing.notes
        assert "HealthAutoExport ID:" in climbing.notes

        running = next(w for w in workouts if w.workout_type == "Run")
        assert "ABC12345-1234-5678-ABCD-123456789ABC" in running.notes

    def test_timezone_conversion_to_utc(self):
        """Test that PST times are correctly converted to UTC.

        Input times include timezone offset (e.g., -0800 for PST).
        Parser should convert these to UTC for consistent storage.
        """
        parser = HealthAutoExportParser()
        fixture_path = FIXTURES_DIR / "valid_workouts.json"

        workouts = parser.parse(fixture_path)

        # All workouts should have UTC timezone
        for workout in workouts:
            assert workout.date.tzinfo == timezone.utc

        # Verify specific conversion: 10:51:41 PST = 18:51:41 UTC
        climbing = next(w for w in workouts if w.workout_type == "Climb")
        assert climbing.date.hour == 18  # 10 + 8 = 18

        # Verify: 18:00:00 PST = 02:00:00 UTC (next day)
        strength = next(w for w in workouts if w.workout_type == "Strength")
        assert strength.date.hour == 2
        assert strength.date.day == 17  # Crossed midnight to next day
