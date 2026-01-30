"""HealthAutoExport JSON parser for TOAD Health module.

This parser handles HealthAutoExport app JSON exports and converts them
into standardized WorkoutData objects.

JSON Format:
- Monthly aggregated files (e.g., HealthAutoExport-2026-01-17.json)
- Structure: {"data": {"workouts": [...]}}
- Files are updated in place, not created new
"""

from pathlib import Path
from typing import List
from datetime import datetime, timezone
import json

from toad.health.models import WorkoutData


class HealthAutoExportParser:
    """Parser for HealthAutoExport JSON files.

    HealthAutoExport exports workouts as JSON with workout data including
    calories, heart rate, duration, and other metrics.
    """

    # Map HealthAutoExport workout names to TOAD workout types
    WORKOUT_TYPE_MAP = {
        "Climbing": "Climb",
        "Running": "Run",
        "Traditional Strength Training": "Strength",
        "Hiking": "Hike",
        "Walking": "Walk",
        "Functional Strength Training": "Strength",
        "Core Training": "Strength",
        "Cycling": "Cycle",
        "Swimming": "Swim",
        # Add more mappings as needed
    }

    def parse(self, file_path: Path) -> List[WorkoutData]:
        """Parse a HealthAutoExport JSON file into list of WorkoutData objects.

        Args:
            file_path: Path to the HealthAutoExport JSON file

        Returns:
            List of WorkoutData objects (may be empty if no workouts)

        Raises:
            ValueError: If JSON is malformed or missing required fields
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON parsing fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read and parse JSON
        content = file_path.read_text(encoding='utf-8')

        if not content or content.strip() == "":
            raise ValueError("JSON file is empty or contains no data")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        # Validate structure
        if "data" not in data:
            raise ValueError("Missing 'data' key in JSON")

        if "workouts" not in data["data"]:
            raise ValueError("Missing 'workouts' key in data")

        workouts_list = data["data"]["workouts"]

        # Parse each workout
        workout_objects = []
        for workout in workouts_list:
            try:
                workout_obj = self._parse_workout(workout, file_path)
                if workout_obj:
                    workout_objects.append(workout_obj)
            except Exception as e:
                # Log warning but continue parsing other workouts
                print(f"Warning: Failed to parse workout: {e}")
                continue

        return workout_objects

    def _parse_workout(self, workout: dict, file_path: Path) -> WorkoutData:
        """Parse a single workout object into WorkoutData.

        Args:
            workout: Workout dictionary from JSON
            file_path: Original file path for tracking

        Returns:
            WorkoutData object

        Raises:
            ValueError: If required fields are missing
        """
        # Extract required fields
        if "name" not in workout:
            raise ValueError("Missing 'name' in workout")
        if "start" not in workout:
            raise ValueError("Missing 'start' in workout")
        if "duration" not in workout:
            raise ValueError("Missing 'duration' in workout")

        workout_name = workout["name"]
        workout_type = self._map_workout_type(workout_name)

        # Parse start date
        # Format: "2026-01-17 10:51:41 -0800"
        start_str = workout["start"]
        date = self._parse_date(start_str)

        # Convert duration from seconds to minutes
        duration_seconds = workout["duration"]
        duration_minutes = round(duration_seconds / 60, 2)

        # Extract calories from activeEnergyBurned
        calories = None
        if "activeEnergyBurned" in workout:
            energy_data = workout["activeEnergyBurned"]
            if isinstance(energy_data, dict) and "qty" in energy_data:
                calories = round(energy_data["qty"])

        # Extract average heart rate
        avg_heart_rate = None
        if "avgHeartRate" in workout:
            hr_data = workout["avgHeartRate"]
            if isinstance(hr_data, dict) and "qty" in hr_data:
                avg_heart_rate = round(hr_data["qty"])

        # Extract distance (if present)
        distance_miles = None
        if "distance" in workout:
            dist_data = workout["distance"]
            if isinstance(dist_data, dict) and "qty" in dist_data:
                distance_qty = dist_data["qty"]
                units = dist_data.get("units", "km")  # Default to km

                # Convert to miles if needed
                if units == "km":
                    distance_miles = round(distance_qty * 0.621371, 2)
                elif units in ["mi", "miles"]:
                    distance_miles = round(distance_qty, 2)
                else:
                    # Unknown units, log warning and assume km
                    distance_miles = round(distance_qty * 0.621371, 2)

        # Build notes with workout ID for deduplication
        notes = None
        if "id" in workout:
            workout_id = workout["id"]
            notes = f"HealthAutoExport ID: {workout_id}"

        return WorkoutData(
            date=date,
            workout_type=workout_type,
            source="HealthAutoExport",
            duration_minutes=duration_minutes,
            calories=calories,
            avg_heart_rate=avg_heart_rate,
            distance_miles=distance_miles,
            notes=notes,
            raw_file_path=str(file_path),
            exercises=None  # HealthAutoExport doesn't include exercise details
        )

    def _map_workout_type(self, workout_name: str) -> str:
        """Map HealthAutoExport workout name to TOAD workout type.

        Args:
            workout_name: Workout name from HealthAutoExport

        Returns:
            TOAD workout type string
        """
        # Check if we have a direct mapping
        if workout_name in self.WORKOUT_TYPE_MAP:
            return self.WORKOUT_TYPE_MAP[workout_name]

        # Default to the workout name itself if no mapping exists
        return workout_name

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from HealthAutoExport format.

        Args:
            date_str: Date string (e.g., "2026-01-17 10:51:41 -0800")

        Returns:
            datetime object (timezone-aware, UTC)
        """
        # Format: "2026-01-17 10:51:41 -0800"
        # Parse with timezone offset and convert to UTC
        try:
            # Parse the full datetime including timezone offset
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
            # Convert to UTC
            return dt.astimezone(timezone.utc)
        except ValueError as e:
            raise ValueError(f"Failed to parse date '{date_str}': {e}")
