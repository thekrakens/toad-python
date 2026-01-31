"""Workout summary formatter for TOAD health module.

Generates formatted workout summaries with performance indicators and progression tracking.
Outputs as markdown text for storage in Activity DB Workout Summary field.
"""

import logging
from typing import List, Dict, Set, Optional
from datetime import datetime

from toad.health.exercise_checker import EnrichedExercise
from toad.health.models import WorkoutData

logger = logging.getLogger(__name__)


class WorkoutSummaryFormatter:
    """Generates formatted workout summaries with progression tracking.

    Creates markdown summaries that include:
    1. Workout metadata (date, duration, calories, HR)
    2. Exercises grouped by section (warmup, main, cooldown, etc.)
    3. Performance indicators (✅ hit target, ⚠️ missed target)
    4. Progression alerts (⬆️ ready to increase weight/reps)
    """

    SECTION_EMOJI = {
        'warmup': '🔶',
        'main': '🏋️',
        'hangboard_warmup': '🧗',
        'hangboard': '🧗',
        'cooldown': '🧘'
    }

    SECTION_NAMES = {
        'warmup': 'Warm-Up',
        'main': 'Core Exercises',
        'hangboard_warmup': 'Hangboard Warmup',
        'hangboard': 'Hangboard',
        'cooldown': 'Cool-Down'
    }

    def generate_summary(
        self,
        workout_data: WorkoutData,
        enriched_exercises: Optional[List[EnrichedExercise]] = None,
        ready_to_increase: Optional[Set[str]] = None
    ) -> str:
        """Generate formatted workout summary as markdown text.

        This is the primary method for generating workout summaries to store
        in the Workout Summary field.

        Args:
            workout_data: WorkoutData from parser
            enriched_exercises: Optional list of exercises with target comparison
            ready_to_increase: Optional set of exercise names ready for progression

        Returns:
            Markdown string suitable for Notion rich_text field
        """
        if ready_to_increase is None:
            ready_to_increase = set()

        lines = []

        # Header with workout metadata
        # For Gymaholic: use notes (e.g., "TOMO A Strength")
        # For HealthAutoExport: use workout_type (NOT notes which contains UUID)
        if workout_data.source == "Gymaholic" and workout_data.notes:
            workout_name = workout_data.notes
        else:
            # Use workout_type and format it nicely (uppercase)
            workout_name = workout_data.workout_type.upper()

        lines.append(f"**{workout_name}**")

        if workout_data.date:
            lines.append(f"📅 {workout_data.date.strftime('%b %d, %Y at %H:%M')}")

        metadata_parts = []
        if workout_data.duration_minutes:
            metadata_parts.append(f"⏱️ {int(workout_data.duration_minutes)} min")
        if workout_data.calories:
            metadata_parts.append(f"🔥 {int(workout_data.calories)} kcal")
        if workout_data.avg_heart_rate:
            metadata_parts.append(f"❤️ {int(workout_data.avg_heart_rate)} bpm avg")
        if workout_data.distance_miles:
            metadata_parts.append(f"📏 {workout_data.distance_miles:.2f} mi")

        if metadata_parts:
            lines.append(" | ".join(metadata_parts))

        # If no exercises (e.g., cardio workout), return header only
        if not enriched_exercises:
            return "\n".join(lines)

        lines.append("")

        # Group exercises by section
        sections = {}
        for ex in enriched_exercises:
            section = ex.section
            if section not in sections:
                sections[section] = []
            sections[section].append(ex)

        # Sort sections by typical workout order
        section_order = ['warmup', 'main', 'hangboard_warmup', 'hangboard', 'cooldown']

        for section_name in section_order:
            if section_name not in sections:
                continue

            emoji = self.SECTION_EMOJI.get(section_name, '•')
            display_name = self.SECTION_NAMES.get(section_name, section_name.title())

            lines.append(f"{emoji} **{display_name}**")

            # Sort exercises by order
            exercises = sorted(sections[section_name], key=lambda x: x.order)

            for ex in exercises:
                exercise_text = self._format_exercise_line(ex, ready_to_increase)
                lines.append(f"  • {exercise_text}")

            lines.append("")

        return "\n".join(lines).strip()

    def _format_exercise_line(
        self,
        ex: EnrichedExercise,
        ready_to_increase: Set[str]
    ) -> str:
        """Format a single exercise as a text line.

        Args:
            ex: EnrichedExercise with performance data
            ready_to_increase: Set of exercises ready for progression

        Returns:
            Formatted exercise line (e.g., "Deadlift: 3×3 @ 165 lbs ✅ ⬆️")
        """
        name = ex.name

        # Build performance string
        perf_parts = []

        # Check if this is a time-based exercise
        if ex.target_time or ex.actual_time:
            # Time-based exercise (e.g., plank, hangboard)
            if ex.actual_sets:
                perf_parts.append(f"{ex.actual_sets} sets")

            if ex.actual_time:
                perf_parts.append(f"{ex.actual_time}s")

            if ex.actual_weight and ex.actual_weight > 0:
                perf_parts.append(f"@ {int(ex.actual_weight)} lbs")

        else:
            # Reps-based exercise
            if ex.actual_sets:
                if ex.actual_reps:
                    perf_parts.append(f"{ex.actual_sets}×{ex.actual_reps}")
                else:
                    perf_parts.append(f"{ex.actual_sets} sets")

            if ex.actual_weight and ex.actual_weight > 0:
                perf_parts.append(f"@ {int(ex.actual_weight)} lbs")

        perf = " ".join(perf_parts) if perf_parts else "completed"

        # Add success indicator if targets exist
        indicators = []
        if ex.has_target:
            if ex.hit_target:
                indicators.append("✅")
            else:
                indicators.append("⚠️")

        # Add progression alert if ready to increase
        if ex.name in ready_to_increase:
            indicators.append("⬆️")

        indicator_str = " ".join(indicators)

        if indicator_str:
            return f"{name}: {perf} {indicator_str}"
        else:
            return f"{name}: {perf}"

    def generate_cardio_summary(self, workout_data: WorkoutData) -> str:
        """Generate summary for cardio workouts (no exercises).

        Args:
            workout_data: WorkoutData from parser

        Returns:
            Formatted summary for cardio/simple workouts
        """
        return self.generate_summary(workout_data, enriched_exercises=None)
