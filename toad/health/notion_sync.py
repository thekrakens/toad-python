"""
Notion sync module for TOAD health data.

Handles syncing health data (activity metrics, workouts) to Notion databases.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import date, datetime

from toad.notion_client import TOADNotionClient
from toad.health.models import DailyActivityMetrics, WorkoutData
from toad.config import Config

logger = logging.getLogger(__name__)


class HealthNotionSync:
    """Handles syncing health data to Notion databases."""

    def __init__(self, notion_client: TOADNotionClient):
        """
        Initialize the health Notion sync handler.

        Args:
            notion_client: Configured TOAD Notion client
        """
        self.client = notion_client

    def update_habit_tracker_metrics(self, metrics: DailyActivityMetrics) -> Dict[str, Any]:
        """
        Update Habit Tracker with activity metrics using smart batching.

        Updates CaloriesIn, CaloriesOut, Weight, and BodyFat fields in the Habit Tracker
        for the given date. Creates a new entry if one doesn't exist.

        Uses smart update to:
        - Only update fields that have changed
        - Batch all changes into a single API call
        - Return audit trail of what changed

        Args:
            metrics: DailyActivityMetrics object with data to sync

        Returns:
            Dict with success status and details:
                - success: bool
                - date: str
                - page_id: str
                - updated_fields: List of fields that were updated
                - unchanged_fields: List of fields that didn't change
                - changes: Dict of old vs new values
        """
        # Extract date from metrics (convert datetime to date if needed)
        target_date = metrics.date.date() if hasattr(metrics.date, 'date') else metrics.date
        date_str = target_date.strftime('%Y-%m-%d')

        # Get database ID
        database_id = Config.NOTION_HABITS_DATABASE_ID
        if not database_id:
            logger.error("NOTION_HABITS_DATABASE_ID not configured")
            return {
                "success": False,
                "error": "NOTION_HABITS_DATABASE_ID not configured",
                "date": date_str
            }

        # Find or create habit entry using centralized method
        page_id = self.client.get_or_create_page(
            database_id=database_id,
            query_property="Date",
            query_value=date_str,
            create_properties={
                "Name": {
                    "title": [{"text": {"content": date_str}}]
                },
                "Date": {
                    "date": {"start": date_str}
                }
            }
        )

        if not page_id:
            return {
                "success": False,
                "error": "Failed to find or create Habit Tracker entry",
                "date": date_str
            }

        # Build properties dict with only non-None values (in Notion API format)
        properties = {}

        if metrics.calories_in is not None:
            properties["CaloriesIn"] = {"type": "number", "number": metrics.calories_in}

        if metrics.calories_out is not None:
            properties["CaloriesOut"] = {"type": "number", "number": metrics.calories_out}

        if metrics.weight is not None:
            properties["Weight"] = {"type": "number", "number": metrics.weight}

        if metrics.body_fat is not None:
            properties["BodyFat"] = {"type": "number", "number": metrics.body_fat}

        # If no properties to update, return early
        if not properties:
            logger.info(f"No metrics to update for {date_str}")
            return {
                "success": True,
                "date": date_str,
                "page_id": page_id,
                "updated_fields": [],
                "unchanged_fields": [],
                "changes": {}
            }

        # Use smart update - only updates changed fields
        result = self.client.update_page_properties_smart(page_id, properties)

        # Enhance result with our metadata
        result["date"] = date_str
        result["page_id"] = page_id

        if result["success"]:
            if result["updated_fields"]:
                logger.info(f"Updated Habit Tracker for {date_str}: {', '.join(result['updated_fields'])}")
            else:
                logger.info(f"No changes needed for Habit Tracker {date_str}")

        return result

    def find_workout_by_healthautoexport_id(self, workout_id: str) -> Optional[str]:
        """Find a workout in Notion by HealthAutoExport ID.

        Searches the Workouts database for a workout with the given ID
        in its notes field (format: "HealthAutoExport ID: {uuid}").

        Args:
            workout_id: UUID from HealthAutoExport workout

        Returns:
            Notion page ID if found, None otherwise
        """
        database_id = Config.NOTION_WORKOUTS_DATABASE_ID
        if not database_id:
            logger.error("NOTION_WORKOUTS_DATABASE_ID not configured")
            return None

        try:
            # Query for workouts with this ID in the notes
            # Note: Notion doesn't support regex in filters, so we need to fetch
            # all workouts and check notes manually (or use a more specific query)
            response = self.client.client.databases.query(
                database_id=database_id,
                filter={
                    "property": "Notes",
                    "rich_text": {
                        "contains": f"HealthAutoExport ID: {workout_id}"
                    }
                }
            )

            if response["results"]:
                # Return the first match (should be unique)
                return response["results"][0]["id"]

            return None

        except Exception as e:
            logger.error(f"Error querying for workout ID {workout_id}: {e}")
            return None

    def find_workout_by_attributes(
        self,
        workout_date: datetime,
        workout_type: str,
        source: str
    ) -> Optional[str]:
        """Find a workout in Notion by date, type, and source.

        Used for Gymaholic workouts which don't have IDs.
        Searches for exact matches on date, type, and source.

        Args:
            workout_date: Workout datetime
            workout_type: Type of workout (Strength, Run, etc.)
            source: Source system (Gymaholic, etc.)

        Returns:
            Notion page ID if found, None otherwise
        """
        database_id = Config.NOTION_WORKOUTS_DATABASE_ID
        if not database_id:
            logger.error("NOTION_WORKOUTS_DATABASE_ID not configured")
            return None

        try:
            # Format date for Notion query
            date_str = workout_date.strftime("%Y-%m-%d")

            # Query with compound filter
            response = self.client.client.databases.query(
                database_id=database_id,
                filter={
                    "and": [
                        {
                            "property": "Date",
                            "date": {
                                "equals": date_str
                            }
                        },
                        {
                            "property": "Type",
                            "select": {
                                "equals": workout_type
                            }
                        },
                        {
                            "property": "Source",
                            "select": {
                                "equals": source
                            }
                        }
                    ]
                }
            )

            if response["results"]:
                # Return the first match (should be unique for Gymaholic)
                return response["results"][0]["id"]

            return None

        except Exception as e:
            logger.error(f"Error querying for workout {workout_type} on {date_str}: {e}")
            return None

    def is_workout_duplicate(self, workout: WorkoutData) -> Optional[str]:
        """Check if a workout already exists in Notion.

        Determines duplicate detection strategy based on workout source:
        - HealthAutoExport: Check by UUID in notes
        - Gymaholic: Check by date + type + source

        Args:
            workout: WorkoutData object to check

        Returns:
            Notion page ID if duplicate found, None otherwise
        """
        # Strategy 1: HealthAutoExport workouts have UUIDs in notes
        if workout.source == "HealthAutoExport" and workout.notes:
            # Extract ID from notes: "HealthAutoExport ID: {uuid}"
            match = re.search(r"HealthAutoExport ID: ([a-f0-9-]+)", workout.notes)
            if match:
                workout_id = match.group(1)
                page_id = self.find_workout_by_healthautoexport_id(workout_id)
                if page_id:
                    logger.debug(f"Found duplicate HealthAutoExport workout: {workout_id}")
                    return page_id

        # Strategy 2: Gymaholic and other sources - match by attributes
        page_id = self.find_workout_by_attributes(
            workout.date,
            workout.workout_type,
            workout.source
        )
        if page_id:
            logger.debug(
                f"Found duplicate {workout.source} workout: "
                f"{workout.workout_type} on {workout.date.strftime('%Y-%m-%d')}"
            )
            return page_id

        return None

    def generate_workout_summary(self, workout: WorkoutData) -> str:
        """Generate a summary string for a workout.

        Creates a concise summary of the workout for the Notion Name field:
        - For Gymaholic with notes (e.g., "TOMO A Strength"): Use notes
        - For strength workouts with exercises: List exercises with set counts
        - For cardio workouts: Include distance/duration if available
        - Fallback to workout type

        Args:
            workout: WorkoutData object to summarize

        Returns:
            Summary string suitable for Notion Name field
        """
        # Strategy 1: Gymaholic workouts with notes (e.g., "TOMO A Strength")
        if workout.source == "Gymaholic" and workout.notes:
            return workout.notes

        # Strategy 2: Strength workouts with exercise details
        if workout.exercises and len(workout.exercises) > 0:
            exercise_summaries = []
            for exercise in workout.exercises:
                # Format: "Exercise Name (X sets)"
                exercise_summaries.append(f"{exercise.name} ({exercise.sets} sets)")

            return ", ".join(exercise_summaries)

        # Strategy 3: Cardio workouts with distance/duration
        # Check if workout type contains cardio keywords
        cardio_keywords = ["Run", "Climb", "Hike", "Walk", "Bike", "Swim"]
        is_cardio = any(keyword.lower() in workout.workout_type.lower() for keyword in cardio_keywords)

        if is_cardio:
            parts = [workout.workout_type]

            if workout.distance_miles:
                parts.append(f"{workout.distance_miles:.1f}mi")

            if workout.duration_minutes:
                hours = int(workout.duration_minutes // 60)
                mins = int(workout.duration_minutes % 60)
                if hours > 0:
                    parts.append(f"{hours}h{mins}m")
                else:
                    parts.append(f"{mins}m")

            if workout.avg_heart_rate:
                parts.append(f"{int(workout.avg_heart_rate)}bpm avg")

            return " - ".join(parts)

        # Strategy 4: Fallback to workout type (avoid showing UUIDs)
        return workout.workout_type

    def sync_workout(self, workout: WorkoutData) -> Dict[str, Any]:
        """Sync a workout to the Workouts database.

        Creates a new workout entry or updates an existing one if it's a duplicate.
        Also updates relevant checkboxes in the Habit Tracker.

        Args:
            workout: WorkoutData object to sync

        Returns:
            Dict with sync result:
                - success: bool
                - workout_page_id: str (Notion page ID)
                - is_duplicate: bool
                - updated_fields: List of fields updated
                - habit_tracker_updated: bool
        """
        database_id = Config.NOTION_WORKOUTS_DATABASE_ID
        if not database_id:
            logger.error("NOTION_WORKOUTS_DATABASE_ID not configured")
            return {
                "success": False,
                "error": "NOTION_WORKOUTS_DATABASE_ID not configured"
            }

        # Check for duplicates
        existing_page_id = self.is_workout_duplicate(workout)

        # Generate summary
        summary = self.generate_workout_summary(workout)

        # Build Notion properties (no relation needed)
        properties = self._build_workout_properties(workout, summary)

        # Create or update workout entry
        if existing_page_id:
            # Update existing workout
            logger.info(f"Updating existing workout: {existing_page_id}")
            result = self.client.update_page_properties_smart(existing_page_id, properties)
            result["workout_page_id"] = existing_page_id
            result["is_duplicate"] = True
        else:
            # Create new workout entry
            logger.info(f"Creating new workout: {workout.workout_type} on {workout.date}")
            try:
                response = self.client.client.pages.create(
                    parent={"database_id": database_id},
                    properties=properties
                )
                result = {
                    "success": True,
                    "workout_page_id": response["id"],
                    "is_duplicate": False,
                    "updated_fields": list(properties.keys()),
                    "unchanged_fields": [],
                    "changes": {}
                }
            except Exception as e:
                logger.error(f"Failed to create workout: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

        # Update Habit Tracker checkboxes
        if result["success"]:
            habit_result = self._update_habit_tracker_checkboxes(workout)
            result["habit_tracker_updated"] = habit_result["success"]

        return result

    def _build_workout_properties(self, workout: WorkoutData, summary: str) -> Dict[str, Any]:
        """Build Notion properties dict for a workout.

        Args:
            workout: WorkoutData object
            summary: Pre-generated summary string

        Returns:
            Dict of Notion properties in API format
        """
        # Format date for Notion
        date_str = workout.date.strftime("%Y-%m-%d")

        properties = {
            "Name": {
                "title": [{"text": {"content": summary}}]
            },
            "Date": {
                "date": {"start": date_str}
            },
            "Type": {
                "select": {"name": workout.workout_type}
            },
            "Source": {
                "select": {"name": workout.source}
            }
        }

        # Add optional fields
        if workout.duration_minutes is not None:
            properties["Duration"] = {"number": workout.duration_minutes}

        if workout.calories is not None:
            properties["Calories"] = {"number": workout.calories}

        if workout.avg_heart_rate is not None:
            properties["Avg HR"] = {"number": workout.avg_heart_rate}

        if workout.distance_miles is not None:
            properties["Distance"] = {"number": workout.distance_miles}

        if workout.elevation_feet is not None:
            properties["Elevation"] = {"number": workout.elevation_feet}

        if workout.notes:
            properties["Notes"] = {
                "rich_text": [{"text": {"content": workout.notes}}]
            }

        return properties

    def _update_habit_tracker_checkboxes(self, workout: WorkoutData) -> Dict[str, Any]:
        """Update checkboxes in Habit Tracker based on workout type.

        Maps workout types to checkbox fields:
        - Run/Walk (>1.5mi) → Runs checkbox
        - Strength → WeightTraining checkbox
        - Climbing → Climbing checkbox
        - Yoga → Yoga checkbox

        Args:
            workout: WorkoutData object

        Returns:
            Dict with success status
        """
        database_id = Config.NOTION_HABITS_DATABASE_ID
        if not database_id:
            return {"success": False, "error": "NOTION_HABITS_DATABASE_ID not configured"}

        # Extract date
        target_date = workout.date.date() if hasattr(workout.date, 'date') else workout.date
        date_str = target_date.strftime('%Y-%m-%d')

        # Find habit tracker entry
        page_id = self.client.get_or_create_page(
            database_id=database_id,
            query_property="Date",
            query_value=date_str,
            create_properties={
                "Name": {"title": [{"text": {"content": date_str}}]},
                "Date": {"date": {"start": date_str}}
            }
        )

        if not page_id:
            return {"success": False, "error": "Failed to find or create Habit Tracker entry"}

        # Determine which checkbox to update
        checkbox_properties = {}

        # Check workout type (case-insensitive matching)
        workout_type_lower = workout.workout_type.lower()

        # Runs/Walks over 1.5mi -> Run checkbox
        if "run" in workout_type_lower or "walk" in workout_type_lower:
            if workout.distance_miles and workout.distance_miles > 1.5:
                checkbox_properties["Run"] = {"checkbox": True}

        # Strength workouts -> Weightlifting checkbox
        elif "strength" in workout_type_lower:
            checkbox_properties["Weightlifting"] = {"checkbox": True}

        # Climbing -> Climb checkbox
        elif "climb" in workout_type_lower:
            checkbox_properties["Climb"] = {"checkbox": True}

        # Yoga -> Yoga checkbox
        elif "yoga" in workout_type_lower:
            checkbox_properties["Yoga"] = {"checkbox": True}

        if not checkbox_properties:
            logger.debug(f"No checkboxes to update for workout type: {workout.workout_type}")
            return {"success": True, "message": "No checkboxes to update"}

        # Update checkboxes using smart update
        result = self.client.update_page_properties_smart(page_id, checkbox_properties)

        # Update page icon based on workout types
        if result.get("success"):
            self._update_habit_tracker_icon(page_id, checkbox_properties)

        return result

    def _update_habit_tracker_icon(self, page_id: str, checkbox_properties: Dict[str, Any]) -> None:
        """Update Habit Tracker page icon based on workout checkboxes.

        Icon scheme:
        - 🏋️ Weightlifting only
        - 🏃 Run only
        - 🧗 Climb only
        - 🧘 Yoga only
        - 💪 Strength + Cardio combo
        - 🔥 3+ different workout types (beast mode)
        - 📅 No workouts (default)

        Args:
            page_id: Habit Tracker page ID
            checkbox_properties: Dict of checkbox properties being set
        """
        # Get all current checkboxes from the page
        try:
            page = self.client.client.pages.retrieve(page_id)
            properties = page.get("properties", {})

            # Check which workout checkboxes are true
            has_weightlifting = properties.get("Weightlifting", {}).get("checkbox", False)
            has_run = properties.get("Run", {}).get("checkbox", False)
            has_climb = properties.get("Climb", {}).get("checkbox", False)
            has_yoga = properties.get("Yoga", {}).get("checkbox", False)

            # Count workout types
            workout_types = []
            if has_weightlifting:
                workout_types.append("weightlifting")
            if has_run:
                workout_types.append("run")
            if has_climb:
                workout_types.append("climb")
            if has_yoga:
                workout_types.append("yoga")

            workout_count = len(workout_types)

            # Determine icon
            if workout_count == 0:
                icon = "📅"  # No workouts
            elif workout_count >= 3:
                icon = "🔥"  # Beast mode - 3+ workout types
            elif workout_count == 2:
                # Combo day - strength + cardio
                if has_weightlifting and (has_run or has_climb):
                    icon = "💪"  # Strength + cardio combo
                else:
                    icon = "🔥"  # Other combo
            else:
                # Single workout type
                if has_weightlifting:
                    icon = "🏋️"
                elif has_run:
                    icon = "🏃"
                elif has_climb:
                    icon = "🧗"
                elif has_yoga:
                    icon = "🧘"
                else:
                    icon = "📅"

            # Update page icon
            self.client.client.pages.update(
                page_id=page_id,
                icon={"type": "emoji", "emoji": icon}
            )

            logger.debug(f"Updated page icon to {icon} for workout types: {workout_types}")

        except Exception as e:
            logger.warning(f"Failed to update page icon: {e}")

    def update_habit_tracker_workout_summary(self, target_date: date, workouts: List[WorkoutData]) -> Dict[str, Any]:
        """Update Habit Tracker page content with workout summaries.

        Only updates if content has changed (avoids expensive delete/recreate operations).

        Args:
            target_date: Date to update
            workouts: List of WorkoutData objects for this date

        Returns:
            Dict with success status
        """
        if not workouts:
            return {"success": True, "message": "No workouts to add"}

        database_id = Config.NOTION_HABITS_DATABASE_ID
        if not database_id:
            return {"success": False, "error": "NOTION_HABITS_DATABASE_ID not configured"}

        # Get Habit Tracker page
        date_str = target_date.strftime('%Y-%m-%d')
        page_id = self.client.get_or_create_page(
            database_id=database_id,
            query_property="Date",
            query_value=date_str,
            create_properties={
                "Name": {"title": [{"text": {"content": date_str}}]},
                "Date": {"date": {"start": date_str}}
            }
        )

        if not page_id:
            return {"success": False, "error": "Failed to find Habit Tracker page"}

        # Generate formatted workout summary blocks
        new_blocks = self._generate_workout_summary_blocks(workouts)

        # Update page content
        try:
            # Get existing blocks
            existing_blocks_response = self.client.client.blocks.children.list(page_id)
            existing_blocks = existing_blocks_response.get("results", [])

            # Check if content needs updating by comparing block count and types
            needs_update = self._needs_content_update(existing_blocks, new_blocks, workouts)

            if not needs_update:
                logger.info(f"Habit Tracker page content unchanged for {date_str}")
                return {"success": True, "message": "No changes needed", "workouts_added": len(workouts)}

            # Delete existing blocks
            for block in existing_blocks:
                try:
                    self.client.client.blocks.delete(block["id"])
                except Exception as e:
                    logger.warning(f"Failed to delete block {block['id']}: {e}")

            # Add new blocks
            self.client.client.blocks.children.append(page_id, children=new_blocks)

            logger.info(f"Updated Habit Tracker page content for {date_str} with {len(workouts)} workout(s)")
            return {"success": True, "workouts_added": len(workouts)}

        except Exception as e:
            logger.error(f"Failed to update Habit Tracker page content: {e}")
            return {"success": False, "error": str(e)}

    def _needs_content_update(self, existing_blocks: List[Dict], new_blocks: List[Dict], workouts: List[WorkoutData]) -> bool:
        """Check if page content needs updating.

        Simple heuristic: Check if workout count matches by counting heading_3 blocks.

        Args:
            existing_blocks: Existing Notion blocks
            new_blocks: New blocks to add
            workouts: Workout data

        Returns:
            True if content needs updating
        """
        # Count heading blocks in existing content (one per workout)
        existing_heading_count = sum(1 for block in existing_blocks if block.get("type") == "heading_3")

        # Expected heading count from new workouts
        expected_heading_count = len(workouts)

        # If counts don't match, update needed
        if existing_heading_count != expected_heading_count:
            return True

        # If counts match, assume content is the same (avoids expensive comparison)
        # This is a heuristic - could be improved with full content hash comparison
        return False

    def _generate_workout_summary_blocks(self, workouts: List[WorkoutData]) -> List[Dict[str, Any]]:
        """Generate Notion blocks for workout summaries.

        Args:
            workouts: List of WorkoutData objects

        Returns:
            List of Notion block objects
        """
        blocks = []

        for workout in workouts:
            # Get workout name (use notes for Gymaholic, type for others)
            workout_name = workout.notes if (workout.source == "Gymaholic" and workout.notes) else workout.workout_type

            # Format duration
            duration_str = ""
            if workout.duration_minutes:
                hours = int(workout.duration_minutes // 60)
                mins = int(workout.duration_minutes % 60)
                secs = int((workout.duration_minutes % 1) * 60)
                if hours > 0:
                    duration_str = f" @ {hours}h{mins}m{secs}s"
                else:
                    duration_str = f" @ {mins}m{secs}s"

            # Format distance for cardio
            distance_str = ""
            if workout.distance_miles:
                distance_str = f"{workout.distance_miles:.2f}mi"

            # Build header
            if distance_str and duration_str:
                header_text = f"{workout_name}\n{distance_str}{duration_str}"
            elif duration_str:
                header_text = f"{workout_name}{duration_str}"
            else:
                header_text = workout_name

            # Workout header (bold via heading)
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": header_text}, "annotations": {"bold": True}}]
                }
            })

            # Add exercises if present (Gymaholic strength workouts)
            if workout.exercises:
                # Section header with emoji
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "🏋️ Exercises"}, "annotations": {"bold": True}}]
                    }
                })

                for exercise in workout.exercises:
                    # Format exercise with sets/reps/weight
                    if exercise.weight and exercise.reps:
                        sets_info = []
                        for w, r in zip(exercise.weight, exercise.reps):
                            if w > 0:
                                sets_info.append(f"{int(w)} lbs × {int(r)}")
                            else:
                                sets_info.append(f"bodyweight × {int(r)}")
                        exercise_text = f"{exercise.name}: {', '.join(sets_info)}"
                    else:
                        exercise_text = f"{exercise.name}: {exercise.sets} sets"

                    # Italicize exercise name, bold the sets/reps
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"{exercise.name}:"}, "annotations": {"italic": True}},
                                {"type": "text", "text": {"content": f" {', '.join(sets_info) if exercise.weight and exercise.reps else f'{exercise.sets} sets'}"}}
                            ]
                        }
                    })

            # Add additional details for cardio workouts
            elif workout.calories or workout.avg_heart_rate or workout.elevation_feet:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Stats"}, "annotations": {"bold": True}}]
                    }
                })

                details = []
                if workout.calories:
                    details.append(f"Calories: {int(workout.calories)}")
                if workout.avg_heart_rate:
                    details.append(f"Avg HR: {int(workout.avg_heart_rate)} bpm")
                if workout.elevation_feet:
                    details.append(f"Elevation: {int(workout.elevation_feet)} ft")

                for detail in details:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": detail}}]
                        }
                    })

            # Add spacing between workouts
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            })

        return blocks

    def sync_health_stats_for_date_range(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync Health Stats for a date range (ETL process).

        Extracts metrics from Habit Tracker, transforms to time-series format,
        and loads to Health Stats table for charting.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dict with sync summary:
                - success: bool
                - entries_created: int
                - entries_updated: int
                - errors: List[str]
        """
        logger.info(f"Running Health Stats ETL for {start_date} to {end_date}")

        summary = {
            "success": True,
            "entries_created": 0,
            "entries_updated": 0,
            "errors": []
        }

        try:
            # Step 1: Extract metrics from Habit Tracker
            habit_entries = self._extract_metrics_from_habit_tracker(start_date, end_date)
            logger.info(f"Extracted {len(habit_entries)} days of data from Habit Tracker")

            # Step 2: Transform to time-series format
            time_series_entries = self._transform_to_time_series(habit_entries)
            logger.info(f"Transformed to {len(time_series_entries)} time-series entries")

            # Step 3: Load to Health Stats table
            for entry in time_series_entries:
                result = self._load_health_stat(entry)
                if result["success"]:
                    if result.get("created"):
                        summary["entries_created"] += 1
                    else:
                        summary["entries_updated"] += 1
                else:
                    error_msg = f"{entry['date']} {entry['tag']}: {result.get('error', 'Unknown error')}"
                    summary["errors"].append(error_msg)
                    logger.error(f"Failed to load health stat: {error_msg}")

            logger.info(
                f"Health Stats ETL complete: "
                f"{summary['entries_created']} created, "
                f"{summary['entries_updated']} updated, "
                f"{len(summary['errors'])} errors"
            )

        except Exception as e:
            logger.error(f"Health Stats ETL failed: {e}")
            summary["success"] = False
            summary["errors"].append(str(e))

        return summary

    def _extract_metrics_from_habit_tracker(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Extract health metrics from Habit Tracker for date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of dicts with date and metric values:
                - date: date
                - weight: Optional[float]
                - body_fat: Optional[float]
                - calories_in: Optional[float]
                - calories_out: Optional[float]
        """
        database_id = Config.NOTION_HABITS_DATABASE_ID
        if not database_id:
            raise ValueError("NOTION_HABITS_DATABASE_ID not configured")

        # Query Habit Tracker for date range
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        try:
            response = self.client.client.databases.query(
                database_id=database_id,
                filter={
                    "and": [
                        {"property": "Date", "date": {"on_or_after": start_str}},
                        {"property": "Date", "date": {"on_or_before": end_str}}
                    ]
                },
                sorts=[{"property": "Date", "direction": "ascending"}]
            )

            entries = []
            for page in response["results"]:
                props = page["properties"]

                # Extract date
                date_prop = props.get("Date", {}).get("date", {})
                if not date_prop:
                    continue
                entry_date = datetime.strptime(date_prop["start"], "%Y-%m-%d").date()

                # Extract metrics
                weight = props.get("Weight", {}).get("number")
                body_fat = props.get("BodyFat", {}).get("number")
                calories_in = props.get("CaloriesIn", {}).get("number")
                calories_out = props.get("CaloriesOut", {}).get("number")

                # Only include if at least one metric has a value
                if any([weight, body_fat, calories_in, calories_out]):
                    entries.append({
                        "date": entry_date,
                        "weight": weight,
                        "body_fat": body_fat,
                        "calories_in": calories_in,
                        "calories_out": calories_out
                    })

            return entries

        except Exception as e:
            logger.error(f"Failed to extract from Habit Tracker: {e}")
            raise

    def _transform_to_time_series(self, habit_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform wide format (1 row = 1 day) to long format (1 row = 1 metric).

        Args:
            habit_entries: List of habit tracker entries with multiple metrics

        Returns:
            List of time-series entries:
                - date: date
                - tag: str (lbs, bf, cals_in, cals_out)
                - value: float
                - title: str (auto-generated)
        """
        time_series = []

        for entry in habit_entries:
            entry_date = entry["date"]
            date_str = entry_date.strftime("%Y-%m-%d")

            # Weight
            if entry["weight"] is not None:
                time_series.append({
                    "date": entry_date,
                    "tag": "lbs",
                    "value": entry["weight"],
                    "title": f"lbs - {date_str}"
                })

            # Body fat
            if entry["body_fat"] is not None:
                time_series.append({
                    "date": entry_date,
                    "tag": "bf",
                    "value": entry["body_fat"],
                    "title": f"bf - {date_str}"
                })

            # Calories in
            if entry["calories_in"] is not None:
                time_series.append({
                    "date": entry_date,
                    "tag": "cals_in",
                    "value": entry["calories_in"],
                    "title": f"cals_in - {date_str}"
                })

            # Calories out
            if entry["calories_out"] is not None:
                time_series.append({
                    "date": entry_date,
                    "tag": "cals_out",
                    "value": entry["calories_out"],
                    "title": f"cals_out - {date_str}"
                })

        return time_series

    def _load_health_stat(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single health stat entry (upsert - create or update).

        Args:
            entry: Time-series entry with date, tag, value, title

        Returns:
            Dict with result:
                - success: bool
                - created: bool (true if created, false if updated)
                - page_id: str
        """
        database_id = Config.NOTION_HEALTH_STATS_DATABASE_ID
        if not database_id:
            return {
                "success": False,
                "error": "NOTION_HEALTH_STATS_DATABASE_ID not configured"
            }

        date_str = entry["date"].strftime("%Y-%m-%d")

        # Check if entry already exists (by date + tag)
        try:
            response = self.client.client.databases.query(
                database_id=database_id,
                filter={
                    "and": [
                        {"property": "date", "date": {"equals": date_str}},
                        {"property": "tags", "select": {"equals": entry["tag"]}}
                    ]
                }
            )

            existing_page_id = None
            if response["results"]:
                existing_page_id = response["results"][0]["id"]

        except Exception as e:
            logger.error(f"Failed to query Health Stats: {e}")
            return {"success": False, "error": str(e)}

        # Build properties
        properties = {
            "title": {"title": [{"text": {"content": entry["title"]}}]},
            "date": {"date": {"start": date_str}},
            "tags": {"select": {"name": entry["tag"]}},
            "value": {"number": entry["value"]}
        }

        try:
            if existing_page_id:
                # Update existing entry
                self.client.client.pages.update(
                    page_id=existing_page_id,
                    properties=properties
                )
                return {
                    "success": True,
                    "created": False,
                    "page_id": existing_page_id
                }
            else:
                # Create new entry
                response = self.client.client.pages.create(
                    parent={"database_id": database_id},
                    properties=properties
                )
                return {
                    "success": True,
                    "created": True,
                    "page_id": response["id"]
                }

        except Exception as e:
            logger.error(f"Failed to load health stat: {e}")
            return {"success": False, "error": str(e)}
