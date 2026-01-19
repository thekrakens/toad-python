"""Health Stats ETL pipeline for TOAD Health module.

This module implements the Extract-Transform-Load pipeline that:
1. Extracts health metrics (weight, body fat %, calories) from Habit Tracker
2. Transforms data from wide format (1 row = 1 day) to long format (1 row = 1 metric)
3. Loads transformed data into Health Stats table for charting

This fixes the broken Notion formula approach by using TOAD for data transformation.
"""

from datetime import datetime
from typing import List, Optional

from toad.health.models import HealthMetric


class HealthStatsETL:
    """ETL pipeline for Health Stats data.

    Extracts metrics from Habit Tracker, transforms to time-series format,
    and loads into Health Stats table.
    """

    def __init__(self):
        """Initialize the Health Stats ETL pipeline."""
        raise NotImplementedError("Phase 5: Task 5.4 - To be implemented")

    def run_etl(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Run the complete ETL pipeline.

        Args:
            start_date: Start of date range to process (default: last sync)
            end_date: End of date range to process (default: today)

        Returns:
            Dictionary with ETL results:
                - extracted: Number of habit entries processed
                - transformed: Number of metrics created
                - loaded: Number of Health Stats entries upserted

        Raises:
            Exception: Various exceptions for different failure modes
        """
        raise NotImplementedError("Phase 5: Task 5.4 - To be implemented")

    def extract(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """Extract health metrics from Habit Tracker.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of habit entries with health metrics

        Phase 5: Task 5.1
        """
        raise NotImplementedError("Phase 5: Task 5.1 - To be implemented")

    def transform(self, habit_entries: List[dict]) -> List[HealthMetric]:
        """Transform habit entries to time-series format.

        Converts wide format (lbs, bf%, in, out in one row) to long format
        (one HealthMetric per metric per day).

        Args:
            habit_entries: List of habit entries from extract()

        Returns:
            List of HealthMetric objects

        Phase 5: Task 5.2
        """
        raise NotImplementedError("Phase 5: Task 5.2 - To be implemented")

    def load(self, metrics: List[HealthMetric]) -> int:
        """Load HealthMetric objects into Health Stats table.

        Upserts entries (create if new, update if exists).

        Args:
            metrics: List of HealthMetric objects to load

        Returns:
            Number of entries successfully upserted

        Phase 5: Task 5.3
        """
        raise NotImplementedError("Phase 5: Task 5.3 - To be implemented")
