"""Exercise target checker for TOAD health module.

Compares actual exercise performance against targets to determine success.
"""

import logging
from typing import Dict, List, Optional
from toad.health.models import ExerciseData

logger = logging.getLogger(__name__)


class EnrichedExercise:
    """Exercise with target comparison results."""

    def __init__(
        self,
        name: str,
        section: str,
        order: int,
        actual_sets: int,
        actual_reps: Optional[int],
        actual_weight: Optional[float],
        actual_time: Optional[int],
        target_reps: Optional[int],
        target_weight: Optional[float],
        target_time: Optional[int],
        warmup_sets: int,
        hit_target: bool,
        has_target: bool
    ):
        self.name = name
        self.section = section
        self.order = order
        self.actual_sets = actual_sets
        self.actual_reps = actual_reps
        self.actual_weight = actual_weight
        self.actual_time = actual_time
        self.target_reps = target_reps
        self.target_weight = target_weight
        self.target_time = target_time
        self.warmup_sets = warmup_sets
        self.hit_target = hit_target
        self.has_target = has_target


class ExerciseTargetChecker:
    """Checks if exercise performance meets targets."""

    def check_exercise(
        self,
        exercise: ExerciseData,
        target_info: Optional[Dict]
    ) -> EnrichedExercise:
        """Check if an exercise met its target.

        Args:
            exercise: ExerciseData from parser
            target_info: Target info from WorkoutTargetsFetcher (or None)

        Returns:
            EnrichedExercise with comparison results
        """
        # Extract actual values
        actual_sets = exercise.sets
        actual_reps = max(exercise.reps) if exercise.reps else None
        actual_weight = max(exercise.weight) if exercise.weight else None
        actual_time = None  # Not available in current parser

        # Extract target values
        if target_info:
            target_reps = target_info.get('target_reps')
            target_weight = target_info.get('target_weight')
            target_time = target_info.get('target_time')
            warmup_sets = target_info.get('warmup_sets', 0)
            section = target_info.get('section', 'main')
            order = target_info.get('order', 999)
            has_target = True
        else:
            target_reps = None
            target_weight = None
            target_time = None
            warmup_sets = 0
            section = 'main'
            order = 999
            has_target = False

        # Determine if target was hit
        hit_target = self._check_target_hit(
            actual_reps, actual_weight, actual_time,
            target_reps, target_weight, target_time
        )

        return EnrichedExercise(
            name=exercise.name,
            section=section,
            order=order,
            actual_sets=actual_sets,
            actual_reps=actual_reps,
            actual_weight=actual_weight,
            actual_time=actual_time,
            target_reps=target_reps,
            target_weight=target_weight,
            target_time=target_time,
            warmup_sets=warmup_sets,
            hit_target=hit_target,
            has_target=has_target
        )

    def _check_target_hit(
        self,
        actual_reps: Optional[int],
        actual_weight: Optional[float],
        actual_time: Optional[int],
        target_reps: Optional[int],
        target_weight: Optional[float],
        target_time: Optional[int]
    ) -> bool:
        """Determine if target was hit based on actual vs target values.

        Logic:
        - If no target exists, return False (no target to hit)
        - For reps-based: actual_reps >= target_reps AND actual_weight >= target_weight
        - For time-based: actual_time >= target_time AND actual_weight >= target_weight
        - Must meet ALL applicable criteria

        Args:
            actual_reps: Actual reps performed (max across sets)
            actual_weight: Actual weight used (max across sets)
            actual_time: Actual time held (not currently available)
            target_reps: Target reps
            target_weight: Target weight
            target_time: Target time

        Returns:
            True if target was hit, False otherwise
        """
        # No target = can't hit target
        if not target_reps and not target_time:
            return False

        hit = True

        # Check reps target (if exists)
        if target_reps is not None:
            if actual_reps is None or actual_reps < target_reps:
                hit = False

        # Check weight target (if exists)
        if target_weight is not None:
            if actual_weight is None or actual_weight < target_weight:
                hit = False

        # Check time target (if exists)
        if target_time is not None:
            if actual_time is None or actual_time < target_time:
                # For now, assume success if exercise was completed
                # (since we don't have actual_time from parser yet)
                pass

        return hit

    def enrich_exercises(
        self,
        exercises: List[ExerciseData],
        targets: Dict[str, Dict]
    ) -> List[EnrichedExercise]:
        """Check all exercises against their targets.

        Args:
            exercises: List of ExerciseData from parser
            targets: Dictionary of targets from WorkoutTargetsFetcher

        Returns:
            List of EnrichedExercise objects with hit/miss info
        """
        enriched = []

        for exercise in exercises:
            target_info = targets.get(exercise.name)

            if not target_info:
                logger.debug(f"No targets found for: {exercise.name}")

            enriched_exercise = self.check_exercise(exercise, target_info)
            enriched.append(enriched_exercise)

        return enriched
