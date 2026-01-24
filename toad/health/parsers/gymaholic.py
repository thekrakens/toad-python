"""Gymaholic CSV parser for TOAD Health module.

This parser handles Gymaholic app CSV exports (semicolon-delimited format)
and converts them into standardized WorkoutData objects.

CSV Format:
- Delimiter: semicolon (;)
- Workout metadata in header rows
- Exercise data in subsequent rows
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone
import re

from toad.health.models import WorkoutData, ExerciseData


class GymaholicParser:
    """Parser for Gymaholic CSV exports.

    Gymaholic exports workouts as semicolon-delimited CSV files with
    metadata and exercise details.
    """

    def parse(self, file_path: Path) -> WorkoutData:
        """Parse a Gymaholic CSV file into WorkoutData.

        Args:
            file_path: Path to the Gymaholic CSV file

        Returns:
            WorkoutData object with parsed workout information

        Raises:
            ValueError: If CSV is malformed or missing required fields
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        content = file_path.read_text(encoding='utf-8')

        if not content or content.strip() == "":
            raise ValueError("CSV file is empty or contains no data")

        lines = content.strip().split('\n')

        # Parse metadata from header
        metadata = self._parse_metadata(lines)

        # Parse exercises
        exercises = self._extract_exercises(lines)

        # Build WorkoutData object
        return WorkoutData(
            date=metadata['date'],
            workout_type="Strength",  # Gymaholic is primarily strength training
            source="Gymaholic",
            duration_minutes=metadata.get('duration'),
            calories=metadata.get('calories'),
            avg_heart_rate=metadata.get('heart_rate'),
            notes=metadata.get('workout_name'),
            raw_file_path=str(file_path),
            exercises=exercises if exercises else None
        )

    def _parse_metadata(self, lines: List[str]) -> Dict:
        """Parse workout metadata from header section.

        Args:
            lines: All lines from the CSV file

        Returns:
            Dictionary with metadata fields

        Raises:
            ValueError: If required fields are missing
        """
        metadata = {}

        for line in lines:
            if not line.startswith(';'):
                continue

            parts = line.split(';')

            # Extract workout name (between dashes)
            if '-----------------' in line:
                continue
            if len(parts) >= 2 and parts[1] and not any(char in parts[1] for char in [':', 'Date', 'Duration', 'KCAL', 'Heart']):
                metadata['workout_name'] = parts[1].strip()

            # Parse key-value pairs
            if len(parts) >= 3:
                key = parts[1].strip()
                value = parts[2].strip()

                if key == 'Date':
                    metadata['date'] = self._parse_date(value)
                elif key == 'Duration':
                    metadata['duration'] = self._parse_duration(value)
                elif key == 'KCAL':
                    metadata['calories'] = int(value)
                elif key == 'Heart rate':
                    # Extract number from "116 bpm"
                    hr_match = re.search(r'(\d+)', value)
                    if hr_match:
                        metadata['heart_rate'] = int(hr_match.group(1))

        # Validate required fields
        if 'date' not in metadata:
            raise ValueError("Required field 'Date' is missing from CSV")

        return metadata

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from Gymaholic format (e.g., 'Jan 14., 06:04').

        Args:
            date_str: Date string from CSV

        Returns:
            datetime object (timezone-aware, UTC)
        """
        # Format: "Jan 14., 06:04"
        # Remove the period after day
        date_str = date_str.replace('.,', '')

        # Parse with current year (Gymaholic doesn't include year)
        current_year = datetime.now().year
        date_str_with_year = f"{date_str} {current_year}"

        try:
            dt = datetime.strptime(date_str_with_year, "%b %d %H:%M %Y")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            # Fallback: try without time
            dt = datetime.strptime(f"{date_str.split(',')[0]} {current_year}", "%b %d %Y")
            return dt.replace(tzinfo=timezone.utc)

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration from format '1h:28m' to minutes.

        Args:
            duration_str: Duration string (e.g., "1h:28m")

        Returns:
            Total duration in minutes
        """
        # Format: "1h:28m" or "0h:40m"
        match = re.match(r'(\d+)h:(\d+)m', duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        return 0

    def _extract_exercises(self, lines: List[str]) -> List[ExerciseData]:
        """Extract exercise details from CSV data.

        Args:
            lines: All lines from the CSV file

        Returns:
            List of ExerciseData objects
        """
        exercises = []
        current_exercise = None
        working_sets = []  # Track working sets (exclude warmup 'W')

        for line in lines:
            # Exercise header starts with #
            if line.startswith('#;'):
                # Save previous exercise if exists
                if current_exercise and working_sets:
                    exercises.append(self._create_exercise_data(current_exercise, working_sets))

                # Parse exercise name (first field after #;)
                parts = line.split(';')
                current_exercise = parts[1].strip() if len(parts) > 1 else None
                working_sets = []

            # Exercise set data (starts with digit or W for warmup)
            elif line and (line[0].isdigit() or line.startswith('W;')):
                if current_exercise:
                    # Skip warmup sets (marked with W)
                    if line.startswith('W;'):
                        continue

                    working_sets.append(line)

        # Don't forget the last exercise
        if current_exercise and working_sets:
            exercises.append(self._create_exercise_data(current_exercise, working_sets))

        return exercises

    def _create_exercise_data(self, exercise_name: str, set_lines: List[str]) -> ExerciseData:
        """Create an ExerciseData object from exercise name and set lines.

        Args:
            exercise_name: Name of the exercise
            set_lines: Lines containing set data

        Returns:
            ExerciseData object
        """
        reps = []
        weights = []

        for line in set_lines:
            parts = line.split(';')

            # REPS column is typically parts[2] (after set number and empty field)
            # Format examples:
            #   "95 lbs x 5" - weight and reps
            #   " x 8" - just reps
            #   "" - time-based exercise

            if len(parts) > 2:
                reps_field = parts[2].strip()

                if reps_field:
                    # Parse "95 lbs x 5" or " x 8" or "1 lbs x 8"
                    match = re.match(r'(?:(\d+(?:\.\d+)?)\s*lbs\s*)?x\s*(\d+)', reps_field)
                    if match:
                        weight_str = match.group(1)
                        rep_count = match.group(2)

                        weights.append(float(weight_str) if weight_str else 0.0)
                        reps.append(int(rep_count))

        # If no reps/weights found, it might be a time-based exercise
        # For now, return empty lists
        if not reps:
            reps = []
            weights = []

        return ExerciseData(
            name=exercise_name,
            sets=len(set_lines),
            reps=reps,
            weight=weights,
            notes=None
        )
