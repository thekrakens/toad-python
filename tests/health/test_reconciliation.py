"""Tests for workout reconciliation engine."""

import pytest
from datetime import datetime, timedelta, timezone

from toad.health.models import WorkoutData, ExerciseData
from toad.health.reconciliation import WorkoutReconciler


@pytest.fixture
def reconciler():
    """Create WorkoutReconciler with 30-min tolerance."""
    return WorkoutReconciler(tolerance_minutes=30)


@pytest.fixture
def sample_gymaholic_workout():
    """Sample Gymaholic workout with exercises."""
    return WorkoutData(
        date=datetime(2026, 1, 21, 18, 30, tzinfo=timezone.utc),
        workout_type="Functional Training",
        source="Gymaholic",
        duration_minutes=88,
        calories=495,
        avg_heart_rate=116,
        exercises=[
            ExerciseData(
                name="Barbell Squat",
                sets=3,
                reps=[5, 5, 5],
                weight=[225, 225, 225]
            ),
            ExerciseData(
                name="Bench Press",
                sets=3,
                reps=[8, 8, 7],
                weight=[185, 185, 185]
            ),
        ]
    )


@pytest.fixture
def sample_healthautoexport_workout():
    """Sample HealthAutoExport workout (no exercises)."""
    return WorkoutData(
        date=datetime(2026, 1, 21, 18, 25, tzinfo=timezone.utc),  # 5 min earlier
        workout_type="Cross Training",
        source="Health Auto Export",
        duration_minutes=92,
        calories=510,
        avg_heart_rate=118,
    )


@pytest.fixture
def existing_notion_workout():
    """Sample existing Notion workout page."""
    return {
        "id": "workout-123",
        "properties": {
            "Type": {
                "select": {"name": "Cross Training"}
            },
            "Date": {
                "date": {"start": "2026-01-21T18:25:00+00:00"}
            },
            "Duration": {
                "number": 92
            },
            "Calories": {
                "number": 510
            },
            "Avg HR": {
                "number": 118
            },
            "Source": {
                "select": {"name": "Health Auto Export"}
            }
        }
    }


class TestWorkoutMatching:
    """Tests for workout matching logic."""

    def test_match_same_time(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test matching workouts at same time."""
        # Adjust gymaholic to exact same time
        sample_gymaholic_workout.date = datetime(2026, 1, 21, 18, 25, tzinfo=timezone.utc)

        result = reconciler.match_workout(sample_gymaholic_workout, [existing_notion_workout])

        assert result is not None
        assert result["id"] == "workout-123"

    def test_match_within_tolerance(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test matching workouts within 30-min tolerance."""
        # Gymaholic is 5 min later (within tolerance)
        result = reconciler.match_workout(sample_gymaholic_workout, [existing_notion_workout])

        assert result is not None
        assert result["id"] == "workout-123"

    def test_no_match_outside_tolerance(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test no match when time difference exceeds tolerance."""
        # Set gymaholic 2 hours later (no duration overlap either)
        sample_gymaholic_workout.date = datetime(2026, 1, 21, 20, 30, tzinfo=timezone.utc)

        result = reconciler.match_workout(sample_gymaholic_workout, [existing_notion_workout])

        assert result is None

    def test_no_match_different_date(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test no match when on different calendar day."""
        # Set gymaholic to next day
        sample_gymaholic_workout.date = datetime(2026, 1, 22, 18, 25, tzinfo=timezone.utc)

        result = reconciler.match_workout(sample_gymaholic_workout, [existing_notion_workout])

        assert result is None

    def test_no_match_different_type(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test no match when workout types incompatible."""
        # Change gymaholic to running (not compatible with cross training)
        sample_gymaholic_workout.workout_type = "Running"

        result = reconciler.match_workout(sample_gymaholic_workout, [existing_notion_workout])

        # Should still match because Running is in Functional Training equivalents
        # Let's test with a truly incompatible type
        sample_gymaholic_workout.workout_type = "Yoga"

        result = reconciler.match_workout(sample_gymaholic_workout, [existing_notion_workout])

        assert result is None

    def test_match_multiple_candidates(self, reconciler, sample_gymaholic_workout):
        """Test matching returns first valid match from multiple candidates."""
        # Create two potential matches
        workout1 = {
            "id": "workout-1",
            "properties": {
                "Type": {"select": {"name": "Cross Training"}},
                "Date": {"date": {"start": "2026-01-21T18:20:00+00:00"}},
                "Duration": {"number": 90},
                "Source": {"select": {"name": "Health Auto Export"}}
            }
        }

        workout2 = {
            "id": "workout-2",
            "properties": {
                "Type": {"select": {"name": "Functional Strength Training"}},
                "Date": {"date": {"start": "2026-01-21T18:35:00+00:00"}},
                "Duration": {"number": 85},
                "Source": {"select": {"name": "Health Auto Export"}}
            }
        }

        result = reconciler.match_workout(sample_gymaholic_workout, [workout1, workout2])

        # Should return first match
        assert result is not None
        assert result["id"] == "workout-1"


class TestTypeCompatibility:
    """Tests for workout type compatibility."""

    def test_exact_type_match(self, reconciler):
        """Test exact type match."""
        assert reconciler._compatible_types("Running", "Running")
        assert reconciler._compatible_types("Yoga", "Yoga")

    def test_functional_training_equivalents(self, reconciler):
        """Test Functional Training type equivalents."""
        assert reconciler._compatible_types("Functional Training", "Cross Training")
        assert reconciler._compatible_types("Functional Training", "Functional Strength Training")
        assert reconciler._compatible_types("Cross Training", "Functional Strength Training")

    def test_strength_training_equivalents(self, reconciler):
        """Test strength training type equivalents."""
        assert reconciler._compatible_types("Traditional Strength Training", "Strength Training")
        assert reconciler._compatible_types("Traditional Strength Training", "Weightlifting")

    def test_running_equivalents(self, reconciler):
        """Test running type equivalents."""
        assert reconciler._compatible_types("Running", "Outdoor Run")
        assert reconciler._compatible_types("Running", "Indoor Run")
        assert reconciler._compatible_types("Outdoor Run", "Indoor Run")

    def test_incompatible_types(self, reconciler):
        """Test incompatible workout types."""
        assert not reconciler._compatible_types("Running", "Yoga")
        assert not reconciler._compatible_types("Climbing", "Swimming")
        assert not reconciler._compatible_types("Yoga", "Weightlifting")


class TestTimeOverlap:
    """Tests for time overlap detection."""

    def test_start_times_within_tolerance(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test matching when start times are within tolerance."""
        # Gymaholic 5 min later (within 30-min tolerance)
        existing_start = datetime(2026, 1, 21, 18, 25, tzinfo=timezone.utc)

        assert reconciler._time_overlap(
            sample_gymaholic_workout,
            existing_notion_workout,
            existing_start
        )

    def test_start_times_outside_tolerance(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test no match when start times exceed tolerance and no duration overlap."""
        # Gymaholic 2 hours later (way outside tolerance, no overlap)
        sample_gymaholic_workout.date = datetime(2026, 1, 21, 20, 30, tzinfo=timezone.utc)
        existing_start = datetime(2026, 1, 21, 18, 25, tzinfo=timezone.utc)

        assert not reconciler._time_overlap(
            sample_gymaholic_workout,
            existing_notion_workout,
            existing_start
        )

    def test_duration_overlap_detection(self, reconciler, sample_gymaholic_workout, existing_notion_workout):
        """Test matching when workout durations overlap."""
        # Set gymaholic 40 min later (outside start time tolerance)
        # But durations should overlap:
        # Existing: 18:25 - 19:57 (92 min)
        # Gymaholic: 19:05 - 20:33 (88 min)
        # Overlap: 19:05 - 19:57
        sample_gymaholic_workout.date = datetime(2026, 1, 21, 19, 5, tzinfo=timezone.utc)
        existing_start = datetime(2026, 1, 21, 18, 25, tzinfo=timezone.utc)

        assert reconciler._time_overlap(
            sample_gymaholic_workout,
            existing_notion_workout,
            existing_start
        )


class TestWorkoutMerging:
    """Tests for workout merging logic."""

    def test_merge_gymaholic_into_healthautoexport(
        self,
        reconciler,
        sample_gymaholic_workout,
        existing_notion_workout
    ):
        """Test merging Gymaholic workout into HealthAutoExport workout."""
        updated = reconciler.merge_workouts(
            sample_gymaholic_workout,
            existing_notion_workout
        )

        # Should update source
        assert updated["Source"]["select"]["name"] == "Gymaholic + Health Auto Export"

        # Should add exercise notes
        assert "Notes" in updated
        notes = updated["Notes"]["rich_text"][0]["text"]["content"]
        assert "Barbell Squat" in notes
        assert "Bench Press" in notes
        assert "225 lbs x 5" in notes

    def test_merge_healthautoexport_into_gymaholic(self, reconciler, sample_healthautoexport_workout):
        """Test merging HealthAutoExport data into Gymaholic workout."""
        existing_gymaholic = {
            "id": "workout-456",
            "properties": {
                "Type": {"select": {"name": "Functional Training"}},
                "Date": {"date": {"start": "2026-01-21T18:30:00+00:00"}},
                "Duration": {"number": 88},
                "Source": {"select": {"name": "Gymaholic"}},
                "Notes": {
                    "rich_text": [{"text": {"content": "TOMO B Strength"}}]
                }
            }
        }

        updated = reconciler.merge_workouts(
            sample_healthautoexport_workout,
            existing_gymaholic
        )

        # Should update measured data
        assert updated["Calories"]["number"] == 510
        assert updated["Avg HR"]["number"] == 118
        assert updated["Duration"]["number"] == 92

        # Should update source
        assert updated["Source"]["select"]["name"] == "Gymaholic + Health Auto Export"

    def test_merge_preserves_exercise_details(
        self,
        reconciler,
        sample_gymaholic_workout,
        existing_notion_workout
    ):
        """Test that exercise details are formatted correctly."""
        updated = reconciler.merge_workouts(
            sample_gymaholic_workout,
            existing_notion_workout
        )

        notes = updated["Notes"]["rich_text"][0]["text"]["content"]

        # Check exercise formatting
        assert "Exercises:" in notes
        assert "• Barbell Squat: 225 lbs x 5, 225 lbs x 5, 225 lbs x 5" in notes
        assert "• Bench Press: 185 lbs x 8, 185 lbs x 8, 185 lbs x 7" in notes


class TestExerciseSummaryFormatting:
    """Tests for exercise summary formatting."""

    def test_format_weight_exercises(self, reconciler):
        """Test formatting exercises with weights."""
        exercises = [
            ExerciseData(
                name="Deadlift",
                sets=3,
                reps=[5, 5, 5],
                weight=[315, 315, 315]
            )
        ]

        summary = reconciler._format_exercise_summary(exercises)

        assert "Deadlift: 315 lbs x 5, 315 lbs x 5, 315 lbs x 5" in summary

    def test_format_bodyweight_exercises(self, reconciler):
        """Test formatting bodyweight exercises."""
        exercises = [
            ExerciseData(
                name="Pull-ups",
                sets=3,
                reps=[8, 7, 6],
                weight=[]
            )
        ]

        summary = reconciler._format_exercise_summary(exercises)

        assert "Pull-ups: 3 sets x 8, 7, 6 reps" in summary

    def test_format_multiple_exercises(self, reconciler):
        """Test formatting multiple exercises."""
        exercises = [
            ExerciseData(name="Squat", sets=3, reps=[5, 5, 5], weight=[225, 225, 225]),
            ExerciseData(name="Bench Press", sets=3, reps=[8, 8, 7], weight=[185, 185, 185]),
            ExerciseData(name="Rows", sets=3, reps=[10, 10, 9], weight=[135, 135, 135]),
        ]

        summary = reconciler._format_exercise_summary(exercises)

        assert "Exercises:" in summary
        assert "Squat" in summary
        assert "Bench Press" in summary
        assert "Rows" in summary
