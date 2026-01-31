"""Workout targets fetcher for TOAD health module.

Fetches exercise targets from the Notion Workouts database.
"""

import logging
import os
from typing import Dict, Optional
from pathlib import Path

from toad.notion_client import TOADNotionClient

logger = logging.getLogger(__name__)


class WorkoutTargetsFetcher:
    """Fetches exercise targets from Notion Workouts database.

    The Workouts database has one row per exercise with structure:
    - Workout (select): "TOMO A Strength", "TOMO B Strength", etc.
    - Exercise (rich_text): Exercise name
    - Section (select): warmup, main, hangboard_warmup, hangboard, cooldown
    - Order (number): For sorting
    - Target Reps (number)
    - Target Weight (number)
    - Target Time (number)
    - Warmup Sets (number)
    """

    def __init__(self, client: TOADNotionClient):
        """Initialize the targets fetcher.

        Args:
            client: Configured TOAD Notion client
        """
        self.client = client
        self.db_id = os.getenv('NOTION_WORKOUT_TEMPLATES_DB_ID', '').replace("-", "")
        self._cache: Dict[str, Dict[str, Dict]] = {}  # {workout_name: {exercise_name: targets}}

    def fetch_targets(self, workout_name: str) -> Dict[str, Dict]:
        """Fetch all exercise targets for a workout.

        Args:
            workout_name: Name of the workout (e.g., "TOMO A Strength")

        Returns:
            Dictionary mapping exercise names to their targets/metadata:
            {
                "Deadlift": {
                    "target_reps": 3,
                    "target_weight": 165,
                    "target_time": None,
                    "warmup_sets": 5,
                    "section": "main",
                    "order": 3
                },
                ...
            }
        """
        # Check cache first
        if workout_name in self._cache:
            logger.debug(f"Using cached targets for: {workout_name}")
            return self._cache[workout_name]

        if not self.db_id:
            logger.error("NOTION_WORKOUT_TEMPLATES_DB_ID not configured")
            return {}

        logger.info(f"Fetching targets from Notion for: {workout_name}")

        try:
            # Query all exercises for this workout
            filter_dict = {
                "property": "Workout",
                "select": {"equals": workout_name}
            }

            results = self.client.get_database_pages(self.db_id, filter_dict=filter_dict)

            targets = {}
            for page in results:
                props = page['properties']

                # Extract exercise name
                exercise_name = None
                if 'Exercise' in props and props['Exercise']['rich_text']:
                    exercise_name = props['Exercise']['rich_text'][0]['plain_text']

                if not exercise_name:
                    continue

                # Extract targets and metadata
                targets[exercise_name] = {
                    'target_reps': props.get('Target Reps', {}).get('number'),
                    'target_weight': props.get('Target Weight', {}).get('number'),
                    'target_time': props.get('Target Time', {}).get('number'),
                    'warmup_sets': props.get('Warmup Sets', {}).get('number', 0),
                    'section': props.get('Section', {}).get('select', {}).get('name', 'main'),
                    'order': props.get('Order', {}).get('number', 999)
                }

            logger.info(f"Found targets for {len(targets)} exercises")

            # Cache for future use
            self._cache[workout_name] = targets
            return targets

        except Exception as e:
            logger.error(f"Failed to fetch targets for {workout_name}: {e}")
            return {}

    def get_exercise_target(self, workout_name: str, exercise_name: str) -> Optional[Dict]:
        """Get target for a specific exercise in a workout.

        Args:
            workout_name: Name of the workout
            exercise_name: Name of the exercise

        Returns:
            Dictionary with target info, or None if not found
        """
        targets = self.fetch_targets(workout_name)
        return targets.get(exercise_name)

    def clear_cache(self):
        """Clear the targets cache."""
        self._cache.clear()
        logger.debug("Cleared targets cache")
