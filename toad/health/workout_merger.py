"""Workout merging logic for TOAD health module.

Handles matching and merging workouts from multiple sources:
- Gymaholic (primary): Provides exercise details, workout name
- HealthAutoExport (enrichment): Provides HR, calories, distance
"""

from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from toad.health.models import WorkoutData

logger = logging.getLogger(__name__)


class WorkoutMerger:
    """Handles matching and merging workouts from multiple sources."""

    # Time window for matching workouts (minutes)
    MATCH_TIME_WINDOW_MINUTES = 30

    # Type mappings for matching
    TYPE_EQUIVALENTS = {
        "Strength": ["Strength", "Traditional Strength Training", "Functional Strength Training"],
        "Run": ["Run", "Running", "Outdoor Run", "Indoor Run"],
        "Climb": ["Climb", "Climbing", "Rock Climbing"],
        "Hike": ["Hike", "Hiking"],
        "Walk": ["Walk", "Walking", "Indoor Walk", "Outdoor Walk"],
        "Bike": ["Bike", "Cycling", "Indoor Cycling", "Outdoor Cycling"],
    }

    def merge_workouts_for_day(
        self,
        gymaholic_workouts: List[WorkoutData],
        healthautoexport_workouts: List[WorkoutData]
    ) -> List[WorkoutData]:
        """Merge workouts from both sources for a single day.

        Matching strategy:
        - Same or equivalent workout type
        - Within time window (30 minutes)
        - Gymaholic is primary source, HealthAutoExport enriches

        Args:
            gymaholic_workouts: List of Gymaholic workouts for the day
            healthautoexport_workouts: List of HealthAutoExport workouts for the day

        Returns:
            List of merged workouts (Gymaholic enriched + unmatched HealthAutoExport)
        """
        merged_workouts = []
        matched_healthautoexport_indices = set()

        # Process each Gymaholic workout (primary)
        for gymaholic in gymaholic_workouts:
            # Try to find matching HealthAutoExport workout
            match_idx, match = self._find_matching_workout(
                gymaholic,
                healthautoexport_workouts,
                matched_healthautoexport_indices
            )

            if match:
                # Merge: Gymaholic primary, enrich with HealthAutoExport data
                merged = self._merge_workouts(gymaholic, match)
                merged_workouts.append(merged)
                matched_healthautoexport_indices.add(match_idx)
                logger.info(
                    f"Merged Gymaholic '{gymaholic.notes}' with HealthAutoExport "
                    f"'{match.workout_type}' at {gymaholic.date.strftime('%H:%M')}"
                )
            else:
                # No match, keep Gymaholic workout as-is
                merged_workouts.append(gymaholic)

        # Add unmatched HealthAutoExport workouts
        for idx, healthautoexport in enumerate(healthautoexport_workouts):
            if idx not in matched_healthautoexport_indices:
                merged_workouts.append(healthautoexport)

        return merged_workouts

    def _find_matching_workout(
        self,
        primary: WorkoutData,
        candidates: List[WorkoutData],
        exclude_indices: set
    ) -> Tuple[Optional[int], Optional[WorkoutData]]:
        """Find a matching workout from candidates.

        Args:
            primary: Primary workout to match against
            candidates: List of candidate workouts
            exclude_indices: Indices to skip (already matched)

        Returns:
            Tuple of (index, workout) or (None, None) if no match
        """
        for idx, candidate in enumerate(candidates):
            if idx in exclude_indices:
                continue

            # Check if types match
            if not self._types_match(primary.workout_type, candidate.workout_type):
                continue

            # Check if times are within window
            if not self._times_match(primary.date, candidate.date):
                continue

            return idx, candidate

        return None, None

    def _types_match(self, type1: str, type2: str) -> bool:
        """Check if two workout types are equivalent.

        Args:
            type1: First workout type
            type2: Second workout type

        Returns:
            True if types match or are equivalent
        """
        # Exact match
        if type1 == type2:
            return True

        # Check equivalents
        for base_type, equivalents in self.TYPE_EQUIVALENTS.items():
            if type1 in equivalents and type2 in equivalents:
                return True

        return False

    def _times_match(self, time1: datetime, time2: datetime) -> bool:
        """Check if two workout times are within the matching window.

        Args:
            time1: First workout time
            time2: Second workout time

        Returns:
            True if within MATCH_TIME_WINDOW_MINUTES
        """
        time_diff = abs((time1 - time2).total_seconds() / 60)
        return time_diff <= self.MATCH_TIME_WINDOW_MINUTES

    def _merge_workouts(
        self,
        gymaholic: WorkoutData,
        healthautoexport: WorkoutData
    ) -> WorkoutData:
        """Merge two workouts, with Gymaholic as primary.

        Strategy:
        - Keep Gymaholic: name (notes), exercises, type, source
        - Enrich from HealthAutoExport: HR, calories, distance (if Gymaholic doesn't have)
        - Use HealthAutoExport time if available (more accurate from Apple Watch)

        Args:
            gymaholic: Primary workout (Gymaholic)
            healthautoexport: Enrichment workout (HealthAutoExport)

        Returns:
            Merged WorkoutData
        """
        # Start with Gymaholic as base
        merged = WorkoutData(
            date=healthautoexport.date,  # Use HealthAutoExport time (more accurate)
            workout_type=gymaholic.workout_type,
            source=gymaholic.source,  # Keep as "Gymaholic"
            duration_minutes=gymaholic.duration_minutes or healthautoexport.duration_minutes,
            calories=gymaholic.calories or healthautoexport.calories,
            avg_heart_rate=gymaholic.avg_heart_rate or healthautoexport.avg_heart_rate,
            distance_miles=gymaholic.distance_miles or healthautoexport.distance_miles,
            elevation_feet=gymaholic.elevation_feet or healthautoexport.elevation_feet,
            notes=gymaholic.notes,  # Keep Gymaholic notes (e.g., "TOMO A Strength")
            raw_file_path=gymaholic.raw_file_path,
            exercises=gymaholic.exercises  # Keep Gymaholic exercises
        )

        return merged
