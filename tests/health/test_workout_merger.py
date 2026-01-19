"""Tests for workout merger."""

import pytest
from datetime import datetime, timedelta

from toad.health.workout_merger import WorkoutMerger
from toad.health.models import WorkoutData, ExerciseData


class TestWorkoutMerger:
    """Tests for WorkoutMerger class."""

    def test_match_workouts_by_date_window(self):
        """Test matching workouts within time window."""
        merger = WorkoutMerger()

        # Gymaholic at 6:04am
        gymaholic = WorkoutData(
            date=datetime(2026, 1, 16, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO A Strength",
            exercises=[ExerciseData(name="Bench Press", sets=3, reps=[10, 8, 6], weight=[135, 155, 175])]
        )

        # HealthAutoExport at 6:05am (1 minute apart)
        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 6, 5),
            workout_type="Strength",
            source="HealthAutoExport",
            avg_heart_rate=117,
            calories=412
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        # Should result in 1 merged workout
        assert len(merged) == 1
        assert merged[0].notes == "TOMO A Strength"
        assert merged[0].avg_heart_rate == 117
        assert merged[0].calories == 412
        assert merged[0].exercises is not None

    def test_merge_gymaholic_primary(self):
        """Test that Gymaholic data takes priority in merge."""
        merger = WorkoutMerger()

        gymaholic = WorkoutData(
            date=datetime(2026, 1, 16, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO A Strength",
            duration_minutes=88,
            calories=400,
            exercises=[ExerciseData(name="Squat", sets=4, reps=[8, 8, 8, 8], weight=[185, 185, 185, 185])]
        )

        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 6, 5),
            workout_type="Strength",
            source="HealthAutoExport",
            duration_minutes=90,
            calories=412,
            avg_heart_rate=117
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        assert len(merged) == 1
        result = merged[0]

        # Gymaholic data takes priority
        assert result.notes == "TOMO A Strength"
        assert result.workout_type == "Strength"
        assert result.source == "Gymaholic"
        assert result.exercises is not None
        assert result.duration_minutes == 88  # Gymaholic has value
        assert result.calories == 400  # Gymaholic has value

        # HealthAutoExport enriches missing data
        assert result.avg_heart_rate == 117  # Gymaholic didn't have this
        assert result.date == healthautoexport.date  # Use HealthAutoExport time (more accurate)

    def test_enrich_with_apple_health_data(self):
        """Test enriching Gymaholic with HealthAutoExport HR/calories."""
        merger = WorkoutMerger()

        # Gymaholic missing HR and calories
        gymaholic = WorkoutData(
            date=datetime(2026, 1, 16, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO B Strength",
            duration_minutes=70,
            exercises=[ExerciseData(name="Deadlift", sets=3, reps=[5, 5, 5], weight=[225, 245, 265])]
        )

        # HealthAutoExport has HR and calories
        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 6, 10),
            workout_type="Strength",
            source="HealthAutoExport",
            avg_heart_rate=120,
            calories=380
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        assert len(merged) == 1
        result = merged[0]

        # Should have enriched data
        assert result.avg_heart_rate == 120
        assert result.calories == 380
        assert result.notes == "TOMO B Strength"
        assert result.exercises is not None

    def test_no_match_creates_separate_workouts(self):
        """Test that unmatched workouts remain separate."""
        merger = WorkoutMerger()

        # Morning Gymaholic strength
        gymaholic = WorkoutData(
            date=datetime(2026, 1, 16, 6, 4),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO A Strength"
        )

        # Afternoon run (different type, different time)
        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 15, 30),
            workout_type="Run",
            source="HealthAutoExport",
            distance_miles=5.2,
            duration_minutes=45
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        # Should have 2 separate workouts
        assert len(merged) == 2
        assert merged[0].workout_type == "Strength"
        assert merged[1].workout_type == "Run"

    def test_match_equivalent_types(self):
        """Test matching workouts with equivalent type names."""
        merger = WorkoutMerger()

        gymaholic = WorkoutData(
            date=datetime(2026, 1, 17, 10, 0),
            workout_type="Walk",
            source="Gymaholic",
            notes="Recovery Walk"
        )

        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 17, 10, 5),
            workout_type="Indoor Walk",  # Equivalent to "Walk"
            source="HealthAutoExport",
            distance_miles=2.8,
            avg_heart_rate=101
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        # Should merge because Walk and Indoor Walk are equivalent
        assert len(merged) == 1
        assert merged[0].notes == "Recovery Walk"
        assert merged[0].distance_miles == 2.8
        assert merged[0].avg_heart_rate == 101

    def test_time_window_too_far_no_match(self):
        """Test that workouts outside time window don't match."""
        merger = WorkoutMerger()

        # 6:00am
        gymaholic = WorkoutData(
            date=datetime(2026, 1, 16, 6, 0),
            workout_type="Strength",
            source="Gymaholic",
            notes="Morning Strength"
        )

        # 7:00am (60 minutes apart, outside 30min window)
        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 7, 0),
            workout_type="Strength",
            source="HealthAutoExport",
            avg_heart_rate=120
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        # Should keep separate (outside time window)
        assert len(merged) == 2

    def test_multiple_workouts_same_day(self):
        """Test handling multiple workouts on same day."""
        merger = WorkoutMerger()

        # Morning strength
        gymaholic1 = WorkoutData(
            date=datetime(2026, 1, 16, 6, 0),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO A Strength"
        )

        # Evening strength
        gymaholic2 = WorkoutData(
            date=datetime(2026, 1, 16, 18, 0),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO B Strength"
        )

        # HealthAutoExport for morning
        health1 = WorkoutData(
            date=datetime(2026, 1, 16, 6, 5),
            workout_type="Strength",
            source="HealthAutoExport",
            avg_heart_rate=115
        )

        # HealthAutoExport for evening
        health2 = WorkoutData(
            date=datetime(2026, 1, 16, 18, 5),
            workout_type="Strength",
            source="HealthAutoExport",
            avg_heart_rate=120
        )

        merged = merger.merge_workouts_for_day([gymaholic1, gymaholic2], [health1, health2])

        # Should have 2 merged workouts
        assert len(merged) == 2

        # Check morning workout
        morning = next(w for w in merged if w.notes == "TOMO A Strength")
        assert morning.avg_heart_rate == 115

        # Check evening workout
        evening = next(w for w in merged if w.notes == "TOMO B Strength")
        assert evening.avg_heart_rate == 120

    def test_multiple_gymaholic_one_healthautoexport(self):
        """Test when multiple Gymaholic but only one HealthAutoExport."""
        merger = WorkoutMerger()

        gymaholic1 = WorkoutData(
            date=datetime(2026, 1, 16, 6, 0),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO A"
        )

        gymaholic2 = WorkoutData(
            date=datetime(2026, 1, 16, 7, 0),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO B"
        )

        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 6, 5),
            workout_type="Strength",
            source="HealthAutoExport",
            avg_heart_rate=115
        )

        merged = merger.merge_workouts_for_day([gymaholic1, gymaholic2], [healthautoexport])

        # Should merge with first (closest time), keep second separate
        assert len(merged) == 2

        # First should be merged
        first = next(w for w in merged if w.notes == "TOMO A")
        assert first.avg_heart_rate == 115

        # Second should be standalone
        second = next(w for w in merged if w.notes == "TOMO B")
        assert second.avg_heart_rate is None

    def test_only_gymaholic_workouts(self):
        """Test handling only Gymaholic workouts (no HealthAutoExport)."""
        merger = WorkoutMerger()

        gymaholic = WorkoutData(
            date=datetime(2026, 1, 16, 6, 0),
            workout_type="Strength",
            source="Gymaholic",
            notes="TOMO A Strength"
        )

        merged = merger.merge_workouts_for_day([gymaholic], [])

        assert len(merged) == 1
        assert merged[0].notes == "TOMO A Strength"

    def test_only_healthautoexport_workouts(self):
        """Test handling only HealthAutoExport workouts (no Gymaholic)."""
        merger = WorkoutMerger()

        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 16, 15, 0),
            workout_type="Run",
            source="HealthAutoExport",
            distance_miles=5.2
        )

        merged = merger.merge_workouts_for_day([], [healthautoexport])

        assert len(merged) == 1
        assert merged[0].distance_miles == 5.2

    def test_empty_lists(self):
        """Test handling empty workout lists."""
        merger = WorkoutMerger()

        merged = merger.merge_workouts_for_day([], [])

        assert len(merged) == 0

    def test_enrich_distance_for_cardio(self):
        """Test enriching cardio workout with distance data."""
        merger = WorkoutMerger()

        gymaholic = WorkoutData(
            date=datetime(2026, 1, 17, 10, 0),
            workout_type="Run",
            source="Gymaholic",
            notes="Morning Run",
            duration_minutes=45
        )

        healthautoexport = WorkoutData(
            date=datetime(2026, 1, 17, 10, 2),
            workout_type="Run",
            source="HealthAutoExport",
            distance_miles=5.2,
            avg_heart_rate=155
        )

        merged = merger.merge_workouts_for_day([gymaholic], [healthautoexport])

        assert len(merged) == 1
        result = merged[0]
        assert result.notes == "Morning Run"
        assert result.distance_miles == 5.2
        assert result.avg_heart_rate == 155
        assert result.duration_minutes == 45
