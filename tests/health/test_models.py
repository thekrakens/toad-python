"""Tests for TOAD Health data models.

These tests verify the basic functionality of WorkoutData, ExerciseData,
and HealthMetric dataclasses.
"""

from datetime import datetime
import pytest
from toad.health.models import WorkoutData, ExerciseData, HealthMetric


class TestWorkoutData:
    """Tests for WorkoutData dataclass."""

    def test_workout_data_creation(self):
        """Test creating a basic WorkoutData instance."""
        workout = WorkoutData(
            date=datetime(2026, 1, 18, 10, 30),
            workout_type="Strength",
            source="Gymaholic"
        )

        assert workout.date == datetime(2026, 1, 18, 10, 30)
        assert workout.workout_type == "Strength"
        assert workout.source == "Gymaholic"
        assert workout.duration_minutes is None
        assert workout.calories is None
        assert workout.avg_heart_rate is None
        assert workout.distance_miles is None
        assert workout.elevation_feet is None
        assert workout.notes is None
        assert workout.raw_file_path is None
        assert workout.exercises is None

    def test_workout_data_with_optional_fields(self):
        """Test creating WorkoutData with all optional fields populated."""
        workout = WorkoutData(
            date=datetime(2026, 1, 18, 10, 30),
            workout_type="Run",
            source="Apple Health Export",
            duration_minutes=45,
            calories=350,
            avg_heart_rate=155,
            distance_miles=4.2,
            elevation_feet=250,
            notes="Morning run, felt great",
            raw_file_path="/path/to/export.xml"
        )

        assert workout.duration_minutes == 45
        assert workout.calories == 350
        assert workout.avg_heart_rate == 155
        assert workout.distance_miles == 4.2
        assert workout.elevation_feet == 250
        assert workout.notes == "Morning run, felt great"
        assert workout.raw_file_path == "/path/to/export.xml"

    def test_workout_data_with_exercises(self):
        """Test creating WorkoutData with exercise list."""
        exercises = [
            ExerciseData(
                name="Bench Press",
                sets=3,
                reps=[10, 8, 6],
                weight=[135, 155, 175]
            )
        ]

        workout = WorkoutData(
            date=datetime(2026, 1, 18, 10, 30),
            workout_type="Strength",
            source="Gymaholic",
            exercises=exercises
        )

        assert workout.exercises is not None
        assert len(workout.exercises) == 1
        assert workout.exercises[0].name == "Bench Press"


class TestExerciseData:
    """Tests for ExerciseData dataclass."""

    def test_exercise_data_creation(self):
        """Test creating a basic ExerciseData instance."""
        exercise = ExerciseData(
            name="Squat",
            sets=3,
            reps=[8, 8, 8],
            weight=[185, 185, 185]
        )

        assert exercise.name == "Squat"
        assert exercise.sets == 3
        assert exercise.reps == [8, 8, 8]
        assert exercise.weight == [185, 185, 185]
        assert exercise.notes is None

    def test_exercise_data_with_notes(self):
        """Test creating ExerciseData with notes."""
        exercise = ExerciseData(
            name="Deadlift",
            sets=3,
            reps=[5, 5, 5],
            weight=[225, 245, 265],
            notes="Focus on form, controlled descent"
        )

        assert exercise.notes == "Focus on form, controlled descent"

    def test_exercise_data_varying_reps_and_weights(self):
        """Test ExerciseData with different reps/weights per set."""
        exercise = ExerciseData(
            name="Overhead Press",
            sets=4,
            reps=[10, 8, 6, 4],
            weight=[65, 75, 85, 95]
        )

        assert len(exercise.reps) == 4
        assert len(exercise.weight) == 4
        assert exercise.reps == [10, 8, 6, 4]
        assert exercise.weight == [65, 75, 85, 95]


class TestHealthMetric:
    """Tests for HealthMetric dataclass."""

    def test_health_metric_creation(self):
        """Test creating a basic HealthMetric instance."""
        metric = HealthMetric(
            date=datetime(2026, 1, 18),
            tag="lbs",
            value=175.0
        )

        assert metric.date == datetime(2026, 1, 18)
        assert metric.tag == "lbs"
        assert metric.value == 175.0

    def test_health_metric_all_tags(self):
        """Test creating HealthMetric instances for all tag types."""
        metrics = [
            HealthMetric(date=datetime(2026, 1, 18), tag="lbs", value=175.0),
            HealthMetric(date=datetime(2026, 1, 18), tag="bf", value=15.5),
            HealthMetric(date=datetime(2026, 1, 18), tag="cals_in", value=2200.0),
            HealthMetric(date=datetime(2026, 1, 18), tag="cals_out", value=2800.0),
        ]

        assert len(metrics) == 4
        assert metrics[0].tag == "lbs"
        assert metrics[1].tag == "bf"
        assert metrics[2].tag == "cals_in"
        assert metrics[3].tag == "cals_out"

    def test_health_metric_float_values(self):
        """Test that HealthMetric handles both int and float values."""
        metric_int = HealthMetric(date=datetime(2026, 1, 18), tag="lbs", value=175)
        metric_float = HealthMetric(date=datetime(2026, 1, 18), tag="bf", value=15.5)

        assert metric_int.value == 175.0
        assert metric_float.value == 15.5
