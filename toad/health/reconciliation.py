"""Workout reconciliation engine.

Matches and merges workouts from different sources (Gymaholic + HealthAutoExport)
even when they arrive at different times (e.g., late Gymaholic export).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from toad.health.models import WorkoutData

logger = logging.getLogger(__name__)

# Type equivalents for workout matching
TYPE_EQUIVALENTS = {
    "Functional Training": [
        "Functional Strength Training",
        "Cross Training",
        "Climbing",  # Gymaholic functional → subsequent cardio
        "Running",
        "Hiking"
    ],
    "Traditional Strength Training": [
        "Traditional Strength Training",
        "Strength Training",
        "Strength",
        "Weightlifting"
    ],
    "Yoga": ["Yoga", "Stretching"],
    "Running": ["Running", "Outdoor Run", "Indoor Run", "Treadmill Running"],
    "Climbing": ["Climbing", "Rock Climbing", "Bouldering"],
    "Hiking": ["Hiking", "Hill Walking"],
    "Walking": ["Walking", "Indoor Walk", "Outdoor Walk"],
}


class WorkoutReconciler:
    """Reconciles workouts from multiple sources."""

    def __init__(self, tolerance_minutes: int = 30):
        """
        Initialize reconciler.

        Args:
            tolerance_minutes: Time window for matching workouts (default 30 min)
        """
        self.tolerance_minutes = tolerance_minutes

    def match_workout(
        self,
        new_workout: WorkoutData,
        existing_workouts: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find existing workout that matches the new workout.

        Args:
            new_workout: New workout to match
            existing_workouts: List of existing Notion workout pages

        Returns:
            Matching workout dict, or None if no match found
        """
        for existing in existing_workouts:
            if self._is_match(new_workout, existing):
                logger.info(
                    f"[RECONCILIATION] Found match: {new_workout.workout_type} @ "
                    f"{new_workout.date.strftime('%Y-%m-%d %H:%M')} matches "
                    f"existing workout {existing['id']}"
                )
                return existing

        logger.info(
            f"[RECONCILIATION] No match found for {new_workout.workout_type} @ "
            f"{new_workout.date.strftime('%Y-%m-%d %H:%M')}"
        )
        return None

    def _is_match(
        self,
        new_workout: WorkoutData,
        existing_workout: Dict[str, Any]
    ) -> bool:
        """
        Check if new workout matches existing workout.

        Criteria (ALL must match):
        1. Same date (YYYY-MM-DD)
        2. Compatible workout type
        3. Time overlap (within tolerance window)

        Args:
            new_workout: New workout data
            existing_workout: Existing Notion workout page

        Returns:
            True if match, False otherwise
        """
        # Extract existing workout properties
        try:
            existing_type = self._extract_property(existing_workout, "Type", "select")
            existing_date_prop = self._extract_property(existing_workout, "Date", "date")

            if not existing_type or not existing_date_prop:
                return False

            # Parse existing workout date
            existing_start = existing_date_prop.get("start")
            if not existing_start:
                return False

            existing_dt = datetime.fromisoformat(existing_start.replace("Z", "+00:00"))

            # Check date match (same calendar day)
            if not self._same_date(new_workout.date, existing_dt):
                return False

            # Check type compatibility
            if not self._compatible_types(new_workout.workout_type, existing_type):
                return False

            # Check time overlap
            if not self._time_overlap(new_workout, existing_workout, existing_dt):
                return False

            return True

        except Exception as e:
            logger.warning(f"[RECONCILIATION] Error checking match: {e}")
            return False

    def _same_date(self, date1: datetime, date2: datetime) -> bool:
        """Check if two datetimes are on the same calendar day."""
        return (date1.year == date2.year and
                date1.month == date2.month and
                date1.day == date2.day)

    def _compatible_types(self, type1: str, type2: str) -> bool:
        """
        Check if two workout types are compatible for merging.

        Args:
            type1: First workout type
            type2: Second workout type

        Returns:
            True if types are compatible
        """
        # Direct match
        if type1 == type2:
            return True

        # Check equivalents
        for primary, equivalents in TYPE_EQUIVALENTS.items():
            expanded = [primary] + equivalents
            if type1 in expanded and type2 in expanded:
                return True

        return False

    def _time_overlap(
        self,
        new_workout: WorkoutData,
        existing_workout: Dict[str, Any],
        existing_start: datetime
    ) -> bool:
        """
        Check if workouts overlap in time within tolerance.

        Args:
            new_workout: New workout data
            existing_workout: Existing Notion workout page
            existing_start: Existing workout start time

        Returns:
            True if time overlaps within tolerance
        """
        # Calculate time difference between start times
        time_diff_minutes = abs((new_workout.date - existing_start).total_seconds() / 60)

        if time_diff_minutes <= self.tolerance_minutes:
            return True

        # Also check if workout durations overlap
        if new_workout.duration_minutes and "Duration" in existing_workout.get("properties", {}):
            existing_duration = self._extract_property(existing_workout, "Duration", "number")

            if existing_duration:
                new_end = new_workout.date + timedelta(minutes=new_workout.duration_minutes)
                existing_end = existing_start + timedelta(minutes=existing_duration)

                # Check if time ranges overlap
                if (new_workout.date <= existing_end and
                    new_end >= existing_start):
                    return True

        return False

    def merge_workouts(
        self,
        new_workout: WorkoutData,
        existing_workout: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge new workout data into existing workout.

        Strategy:
        - Keep HealthAutoExport timestamp (more accurate from Apple Watch)
        - Keep HealthAutoExport calories, HR, duration (measured data)
        - Add Gymaholic exercise details (sets, reps, weight)
        - Update summary/notes with exercise list

        Args:
            new_workout: New workout to merge
            existing_workout: Existing Notion workout page

        Returns:
            Updated properties dict for Notion API
        """
        updated_properties = {}

        # Determine primary source
        existing_source = self._extract_property(existing_workout, "Source", "select")
        new_source = new_workout.source

        logger.info(
            f"[RECONCILIATION] Merging: {new_source} → {existing_source} workout"
        )

        # If new is Gymaholic and existing is HealthAutoExport
        if new_source == "Gymaholic" and existing_source == "Health Auto Export":
            # Add exercise details (Gymaholic is primary for exercises)
            if new_workout.exercises:
                # Update source to indicate merged data
                updated_properties["Source"] = {
                    "select": {"name": "Gymaholic + Health Auto Export"}
                }

                # Keep HealthAutoExport measured data (calories, HR, duration)
                # but add notes about exercises
                notes = self._format_exercise_summary(new_workout.exercises)
                updated_properties["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }

                logger.info(
                    f"[RECONCILIATION] Added {len(new_workout.exercises)} exercises "
                    f"to existing workout"
                )

        # If new is HealthAutoExport and existing is Gymaholic
        elif new_source == "Health Auto Export" and existing_source == "Gymaholic":
            # Update measured data from HealthAutoExport
            if new_workout.calories:
                updated_properties["Calories"] = {"number": new_workout.calories}

            if new_workout.avg_heart_rate:
                updated_properties["Avg HR"] = {"number": new_workout.avg_heart_rate}

            if new_workout.duration_minutes:
                updated_properties["Duration"] = {"number": new_workout.duration_minutes}

            # Update source to indicate merged data
            updated_properties["Source"] = {
                "select": {"name": "Gymaholic + Health Auto Export"}
            }

            logger.info(
                f"[RECONCILIATION] Updated measured data from HealthAutoExport"
            )

        return updated_properties

    def _extract_property(
        self,
        page: Dict[str, Any],
        property_name: str,
        property_type: str
    ) -> Optional[Any]:
        """
        Extract property value from Notion page.

        Args:
            page: Notion page dict
            property_name: Property name to extract
            property_type: Property type (select, date, number, etc.)

        Returns:
            Property value, or None if not found
        """
        try:
            properties = page.get("properties", {})
            prop = properties.get(property_name, {})

            if property_type == "select":
                return prop.get("select", {}).get("name")
            elif property_type == "date":
                return prop.get("date")
            elif property_type == "number":
                return prop.get("number")
            elif property_type == "rich_text":
                text_array = prop.get("rich_text", [])
                if text_array:
                    return text_array[0].get("text", {}).get("content")
                return None

            return None

        except Exception:
            return None

    def _format_exercise_summary(self, exercises) -> str:
        """
        Format exercise list for Notion notes field.

        Args:
            exercises: List of ExerciseData objects

        Returns:
            Formatted exercise summary string
        """
        lines = ["Exercises:"]

        for exercise in exercises:
            # Format sets/reps/weight
            if exercise.weight and any(w > 0 for w in exercise.weight):
                # Weight exercises
                set_details = []
                for i in range(exercise.sets):
                    reps = exercise.reps[i] if i < len(exercise.reps) else "?"
                    weight = exercise.weight[i] if i < len(exercise.weight) else "?"
                    set_details.append(f"{weight} lbs x {reps}")
                lines.append(f"• {exercise.name}: {', '.join(set_details)}")
            elif exercise.reps:
                # Bodyweight exercises
                reps_str = ", ".join(str(r) for r in exercise.reps)
                lines.append(f"• {exercise.name}: {exercise.sets} sets x {reps_str} reps")
            else:
                # Time-based or unknown
                lines.append(f"• {exercise.name}: {exercise.sets} sets")

        return "\n".join(lines)
