"""Progression tracker for TOAD health module.

Tracks exercise progression across multiple workouts to determine when to increase weight/reps.
"""

import logging
import os
from typing import Dict, Set, Optional, List
from datetime import datetime, date

from toad.notion_client import TOADNotionClient

logger = logging.getLogger(__name__)


class ProgressionTracker:
    """Tracks exercise progression across workouts.

    Queries Activity DB to check if an exercise has hit its target
    in the last N consecutive workouts of the same type.
    """

    def __init__(self, client: TOADNotionClient, required_hits: int = 3):
        """Initialize the progression tracker.

        Args:
            client: Configured TOAD Notion client
            required_hits: Number of consecutive hits required to trigger "increase" alert
        """
        self.client = client
        self.required_hits = required_hits
        self.db_id = os.getenv('NOTION_WORKOUTS_DATABASE_ID', '').replace("-", "")

    def check_ready_to_increase(
        self,
        workout_name: str,
        exercise_name: str,
        current_date: date,
        exclude_current: bool = True
    ) -> bool:
        """Check if an exercise is ready for weight/rep increase.

        Queries the last N workouts of the same type and checks if this
        exercise hit its target in all of them.

        Args:
            workout_name: Name of workout (e.g., "TOMO A Strength")
            exercise_name: Name of exercise (e.g., "Deadlift")
            current_date: Date of current workout (to exclude or include)
            exclude_current: If True, check previous N workouts (not including today)

        Returns:
            True if exercise hit target in last N consecutive workouts
        """
        if not self.db_id:
            logger.error("NOTION_WORKOUTS_DATABASE_ID not configured")
            return False

        try:
            # Query Activity DB for recent workouts of this type
            # We need to fetch page content blocks to check for checkmarks
            recent_workouts = self._fetch_recent_workouts(
                workout_name,
                current_date,
                limit=self.required_hits + (1 if exclude_current else 0)
            )

            if not recent_workouts:
                logger.debug(f"No previous workouts found for {workout_name}")
                return False

            # Filter out current workout if requested
            if exclude_current:
                recent_workouts = [
                    w for w in recent_workouts
                    if w['date'] != current_date
                ]

            # Only keep the last N workouts
            recent_workouts = recent_workouts[:self.required_hits]

            if len(recent_workouts) < self.required_hits:
                logger.debug(
                    f"Only {len(recent_workouts)} previous workouts found, "
                    f"need {self.required_hits}"
                )
                return False

            # Check if exercise hit target in all N workouts
            all_hit = True
            for workout in recent_workouts:
                if not self._did_exercise_hit_target(workout['page_id'], exercise_name):
                    all_hit = False
                    break

            if all_hit:
                logger.info(
                    f"🎯 {exercise_name} hit target in last {self.required_hits} "
                    f"{workout_name} sessions - READY TO INCREASE!"
                )

            return all_hit

        except Exception as e:
            logger.error(f"Failed to check progression for {exercise_name}: {e}")
            return False

    def check_all_exercises(
        self,
        workout_name: str,
        exercise_names: List[str],
        current_date: date
    ) -> Set[str]:
        """Check which exercises are ready to increase.

        Args:
            workout_name: Name of workout
            exercise_names: List of exercise names to check
            current_date: Date of current workout

        Returns:
            Set of exercise names that are ready to increase
        """
        ready_to_increase = set()

        for exercise_name in exercise_names:
            if self.check_ready_to_increase(workout_name, exercise_name, current_date):
                ready_to_increase.add(exercise_name)

        return ready_to_increase

    def _fetch_recent_workouts(
        self,
        workout_name: str,
        current_date: date,
        limit: int
    ) -> List[Dict]:
        """Fetch recent workouts of a specific type.

        Args:
            workout_name: Name of workout to filter by
            current_date: Reference date (to get workouts before this)
            limit: Max number of workouts to fetch

        Returns:
            List of dicts with page_id and date, sorted newest first
        """
        try:
            # Query Activity DB for this workout type, sorted by date descending
            # We filter by Name containing the workout name
            response = self.client.client.databases.query(
                database_id=self.db_id,
                filter={
                    "property": "Name",
                    "title": {
                        "contains": workout_name
                    }
                },
                sorts=[
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ],
                page_size=limit + 5  # Fetch a few extra in case some are invalid
            )

            workouts = []
            for page in response['results']:
                props = page['properties']

                # Extract date
                date_prop = props.get('Date', {}).get('date', {})
                if not date_prop:
                    continue

                workout_date = datetime.strptime(date_prop['start'], '%Y-%m-%d').date()

                workouts.append({
                    'page_id': page['id'],
                    'date': workout_date
                })

            # Sort by date descending (newest first)
            workouts.sort(key=lambda x: x['date'], reverse=True)

            return workouts[:limit]

        except Exception as e:
            logger.error(f"Failed to fetch recent workouts: {e}")
            return []

    def _did_exercise_hit_target(self, page_id: str, exercise_name: str) -> bool:
        """Check if an exercise hit its target in a specific workout.

        Fetches page content blocks and looks for the exercise with a checkmark (✅).

        Args:
            page_id: Notion page ID of the workout
            exercise_name: Name of exercise to check

        Returns:
            True if exercise has checkmark, False otherwise
        """
        try:
            # Fetch page content blocks
            blocks_response = self.client.client.blocks.children.list(page_id)
            blocks = blocks_response.get('results', [])

            # Look for bullet items containing the exercise name
            for block in blocks:
                if block.get('type') != 'bulleted_list_item':
                    continue

                # Extract text from bullet
                rich_text = block.get('bulleted_list_item', {}).get('rich_text', [])
                text = ''.join([rt.get('text', {}).get('content', '') for rt in rich_text])

                # Check if this bullet is for our exercise and has checkmark
                if exercise_name in text and '✅' in text:
                    logger.debug(f"Found ✅ for {exercise_name} in workout {page_id}")
                    return True

            logger.debug(f"No ✅ found for {exercise_name} in workout {page_id}")
            return False

        except Exception as e:
            logger.error(f"Failed to check exercise target in page {page_id}: {e}")
            return False
