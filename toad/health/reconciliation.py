"""Workout reconciliation engine.

Matches and merges workouts from different sources (Gymaholic + HealthAutoExport)
even when they arrive at different times (e.g., late Gymaholic export).
"""

import logging
from datetime import datetime, timezone
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

    def __init__(self, tolerance_seconds: int = 5):
        """
        Initialize reconciler.

        Args:
            tolerance_seconds: Time window for matching workouts (default 5 seconds)
        """
        self.tolerance_seconds = tolerance_seconds

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
        3. DateTime within ±5 seconds

        Args:
            new_workout: New workout data
            existing_workout: Existing Notion workout page

        Returns:
            True if match, False otherwise
        """
        # Extract existing workout properties
        try:
            existing_type = self._extract_property(existing_workout, "Type", "select")

            # Try Workout Time property first (more precise), fall back to Date
            existing_datetime_prop = self._extract_property(existing_workout, "Workout Time", "date")

            if not existing_type:
                return False

            # Get existing workout datetime
            existing_dt = None
            if existing_datetime_prop:
                # Workout Time property exists (ISO 8601 with time)
                existing_start = existing_datetime_prop.get("start")
                if existing_start:
                    existing_dt = datetime.fromisoformat(existing_start.replace("Z", "+00:00"))

            # If no DateTime property, try Date property (legacy)
            if not existing_dt:
                existing_date_prop = self._extract_property(existing_workout, "Date", "date")
                if existing_date_prop:
                    existing_start = existing_date_prop.get("start")
                    if existing_start:
                        existing_dt = datetime.fromisoformat(existing_start.replace("Z", "+00:00"))

            if not existing_dt:
                return False

            # Check date match (same calendar day)
            if not self._same_date(new_workout.date, existing_dt):
                return False

            # Check type compatibility
            if not self._compatible_types(new_workout.workout_type, existing_type):
                return False

            # Check DateTime within ±5 seconds
            if not self._time_overlap(new_workout, existing_workout, existing_dt):
                return False

            return True

        except Exception as e:
            logger.warning(f"[RECONCILIATION] Error checking match: {e}")
            return False

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (assumes UTC if naive)."""
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

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
        Check if workouts have same DateTime within ±5 seconds.

        Duplicates from the same source (Gymaholic + HealthAutoExport)
        have identical DateTime values.

        Args:
            new_workout: New workout data
            existing_workout: Existing Notion workout page
            existing_start: Existing workout start time

        Returns:
            True if DateTime within ±5 seconds
        """
        # Ensure both datetimes are timezone-aware before comparison
        new_start = self._ensure_timezone_aware(new_workout.date)
        existing_start = self._ensure_timezone_aware(existing_start)

        # Calculate time difference in seconds
        time_diff_seconds = abs((new_start - existing_start).total_seconds())

        # Match if within ±5 seconds
        return time_diff_seconds <= self.tolerance_seconds

    def merge_workouts(
        self,
        new_workout: WorkoutData,
        existing_workout: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge new workout data into existing workout.

        Priority-based merging strategy:
        - Gymaholic has priority (detailed exercise data)
        - If Gymaholic arrives first → HealthAutoExport only fills missing data
        - If HealthAutoExport arrives first → Gymaholic replaces all properties

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

        # Case 1: Gymaholic arrives first, HealthAutoExport arrives second
        # → HealthAutoExport only fills missing data (don't overwrite Gymaholic)
        if existing_source == "Gymaholic" and new_source == "Health Auto Export":
            logger.info(
                f"[RECONCILIATION] Gymaholic first - filling missing data from HealthAutoExport"
            )

            # Check existing values and only fill if missing
            existing_calories = self._extract_property(existing_workout, "Calories", "number")
            existing_hr = self._extract_property(existing_workout, "Avg HR", "number")
            existing_duration = self._extract_property(existing_workout, "Duration", "number")

            # Only add HealthAutoExport data if Gymaholic didn't have it
            if not existing_calories and new_workout.calories:
                updated_properties["Calories"] = {"number": new_workout.calories}
                logger.info(f"[RECONCILIATION] Added missing Calories: {new_workout.calories}")

            if not existing_hr and new_workout.avg_heart_rate:
                updated_properties["Avg HR"] = {"number": new_workout.avg_heart_rate}
                logger.info(f"[RECONCILIATION] Added missing Avg HR: {new_workout.avg_heart_rate}")

            if not existing_duration and new_workout.duration_minutes:
                updated_properties["Duration"] = {"number": new_workout.duration_minutes}
                logger.info(f"[RECONCILIATION] Added missing Duration: {new_workout.duration_minutes}")

            # Update source to indicate merged data (only if we added anything)
            if updated_properties:
                updated_properties["Source"] = {
                    "select": {"name": "Gymaholic + Health Auto Export"}
                }

        # Case 2: HealthAutoExport arrives first, Gymaholic arrives second
        # → Gymaholic replaces all properties it has values for (Gymaholic priority)
        elif existing_source == "Health Auto Export" and new_source == "Gymaholic":
            logger.info(
                f"[RECONCILIATION] HealthAutoExport first - Gymaholic replaces Name, Type, Source"
            )

            # Gymaholic replaces Name, Type, and Source
            # (The handler will provide these from the staging data's notion_properties)
            # We need to return them here to tell the handler what to update

            # Preserve HealthAutoExport measured data if Gymaholic doesn't have it
            existing_calories = self._extract_property(existing_workout, "Calories", "number")
            existing_hr = self._extract_property(existing_workout, "Avg HR", "number")
            existing_distance = self._extract_property(existing_workout, "Distance", "number")

            # If HealthAutoExport had these values and Gymaholic doesn't, preserve them
            if existing_calories and not new_workout.calories:
                updated_properties["Calories"] = {"number": existing_calories}
                logger.info(f"[RECONCILIATION] Preserving HealthAutoExport Calories: {existing_calories}")

            if existing_hr and not new_workout.avg_heart_rate:
                updated_properties["Avg HR"] = {"number": existing_hr}
                logger.info(f"[RECONCILIATION] Preserving HealthAutoExport Avg HR: {existing_hr}")

            if existing_distance and not new_workout.distance_miles:
                updated_properties["Distance"] = {"number": existing_distance}
                logger.info(f"[RECONCILIATION] Preserving HealthAutoExport Distance: {existing_distance}")

            # Update source to indicate merged data
            updated_properties["Source"] = {
                "select": {"name": "Gymaholic + Health Auto Export"}
            }

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
