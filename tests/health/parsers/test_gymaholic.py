"""Tests for Gymaholic CSV parser.

These tests verify parsing of Gymaholic app CSV exports (semicolon-delimited format)
into standardized WorkoutData objects.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from toad.health.parsers.gymaholic import GymaholicParser
from toad.health.models import WorkoutData, ExerciseData


@pytest.fixture
def parser():
    """Create a GymaholicParser instance."""
    return GymaholicParser()


@pytest.fixture
def valid_csv_path():
    """Path to valid test CSV."""
    return Path(__file__).parent.parent.parent / "fixtures" / "gymaholic" / "valid_workout.csv"


@pytest.fixture
def empty_csv_path():
    """Path to empty test CSV."""
    return Path(__file__).parent.parent.parent / "fixtures" / "gymaholic" / "empty.csv"


@pytest.fixture
def malformed_csv_path():
    """Path to malformed test CSV."""
    return Path(__file__).parent.parent.parent / "fixtures" / "gymaholic" / "malformed.csv"


class TestGymaholicParser:
    """Tests for GymaholicParser class."""

    def test_parse_valid_csv(self, parser, valid_csv_path):
        """Test parsing a complete valid Gymaholic CSV."""
        workout = parser.parse(valid_csv_path)

        # Verify it returns a WorkoutData object
        assert isinstance(workout, WorkoutData)

        # Verify workout metadata
        assert workout.workout_type == "Strength"
        assert workout.source == "Gymaholic"
        assert workout.date.month == 1
        assert workout.date.day == 14
        assert workout.duration_minutes == 88  # 1h:28m = 88 minutes
        assert workout.calories == 495
        assert workout.avg_heart_rate == 116

        # Verify exercises were extracted
        assert workout.exercises is not None
        assert len(workout.exercises) == 5  # Side Plank, Military Press, Swings, Inverted Row, Bird Dog

    def test_parse_empty_csv(self, parser, empty_csv_path):
        """Test that empty CSV raises appropriate error."""
        with pytest.raises(ValueError, match="empty|no data"):
            parser.parse(empty_csv_path)

    def test_parse_malformed_csv(self, parser, malformed_csv_path):
        """Test that malformed CSV (missing Date) raises error."""
        with pytest.raises(ValueError, match="Date|required"):
            parser.parse(malformed_csv_path)

    def test_parse_nonexistent_file(self, parser):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.csv"))

    def test_extract_exercises(self, parser, valid_csv_path):
        """Test exercise extraction with various formats."""
        workout = parser.parse(valid_csv_path)

        # Find specific exercises to test different formats
        exercises = {ex.name: ex for ex in workout.exercises}

        # Test 1: Exercise with time only (Side Plank)
        side_plank = exercises.get("Side Plank")
        assert side_plank is not None
        assert side_plank.sets == 3
        # For time-based exercises, we might not track reps/weight the same way

        # Test 2: Exercise with weight and reps, including warmup sets (Standing Military Press)
        military_press = exercises.get("Standing Military Press")
        assert military_press is not None
        assert military_press.sets == 3  # Only working sets, not warmup
        assert len(military_press.reps) == 3
        assert len(military_press.weight) == 3
        assert all(r == 5 for r in military_press.reps)  # All sets are 5 reps
        assert all(w == 95 for w in military_press.weight)  # All sets are 95 lbs

        # Test 3: Exercise with varying reps (Swing Two Hands)
        swings = exercises.get("Swing Two Hands")
        assert swings is not None
        assert swings.sets == 3
        assert swings.reps == [20, 20, 12]
        assert all(w == 35 for w in swings.weight)

        # Test 4: Exercise with just reps, no weight (Inverted Row)
        inverted_row = exercises.get("Inverted Row")
        assert inverted_row is not None
        assert inverted_row.sets == 3
        assert all(r == 8 for r in inverted_row.reps)
        # Weight should be 0 or empty list for bodyweight exercises

    def test_semicolon_delimiter(self, parser, valid_csv_path):
        """Verify parser correctly handles semicolon delimiter."""
        # This is implicitly tested by parse_valid_csv, but we can be explicit
        workout = parser.parse(valid_csv_path)
        assert workout is not None
        # If delimiter was wrong, parsing would fail

    def test_workout_name_extraction(self, parser, valid_csv_path):
        """Test that workout name is extracted from header."""
        workout = parser.parse(valid_csv_path)
        # Workout name should be in notes or we should use it for something
        assert "TOMO B Strength" in (workout.notes or "")

    def test_date_parsing_format(self, parser, valid_csv_path):
        """Test date parsing handles Gymaholic format (e.g., 'Jan 14., 06:04').

        Gymaholic times are device local time (PST), converted to UTC.
        06:04 PST -> 14:04 UTC
        """
        workout = parser.parse(valid_csv_path)
        assert workout.date.month == 1
        assert workout.date.day == 14
        assert workout.date.hour == 14  # UTC hour (6 + 8)
        assert workout.date.minute == 4
        assert workout.date.tzinfo == timezone.utc

    def test_duration_parsing(self, parser, valid_csv_path):
        """Test duration parsing handles format '1h:28m'."""
        workout = parser.parse(valid_csv_path)
        assert workout.duration_minutes == 88  # 1*60 + 28

    def test_raw_file_path_stored(self, parser, valid_csv_path):
        """Test that raw file path is stored in WorkoutData."""
        workout = parser.parse(valid_csv_path)
        assert workout.raw_file_path == str(valid_csv_path)
