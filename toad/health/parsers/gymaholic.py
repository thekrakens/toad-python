"""Gymaholic CSV parser for TOAD Health module.

This parser handles Gymaholic app CSV exports (semicolon-delimited format)
and converts them into standardized WorkoutData objects.

CSV Format:
- Delimiter: semicolon (;)
- Workout metadata in header rows
- Exercise data in subsequent rows
"""

from pathlib import Path
from typing import List
from datetime import datetime

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
        raise NotImplementedError("Phase 2: Task 2.1 - To be implemented")

    def _extract_exercises(self, csv_data: str) -> List[ExerciseData]:
        """Extract exercise details from CSV data.

        Args:
            csv_data: Raw CSV content

        Returns:
            List of ExerciseData objects
        """
        raise NotImplementedError("Phase 2: Task 2.1 - To be implemented")
