"""HealthAutoExport Activity Metrics JSON parser for TOAD Health module.

This parser handles HealthAutoExport app JSON exports for activity metrics
(calories, weight, body fat) and converts them into DailyActivityMetrics objects
for updating Habit Tracker fields.

JSON Format:
- Daily aggregated files (e.g., HealthAutoExport-2026-01-17.json)
- Structure: {"data": {"metrics": [...]}}
- Files are updated in place, not created new
"""

from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Any

from toad.health.models import DailyActivityMetrics


class HealthAutoExportMetricsParser:
    """Parser for HealthAutoExport activity metrics JSON files.

    Parses TOAD_Activity daily JSON files and extracts health metrics
    (dietary_energy, active_energy, weight_body_mass, body_fat_percentage)
    for updating Habit Tracker fields.
    """

    # Map HealthAutoExport metric names to DailyActivityMetrics fields
    METRIC_FIELD_MAP = {
        "dietary_energy": "calories_in",
        "active_energy": "calories_out",
        "weight_body_mass": "weight",
        "body_fat_percentage": "body_fat",
    }

    def parse(self, file_path: Path) -> DailyActivityMetrics:
        """Parse a HealthAutoExport activity metrics JSON file.

        Args:
            file_path: Path to the HealthAutoExport JSON file

        Returns:
            DailyActivityMetrics object with aggregated daily metrics

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

        if "metrics" not in data["data"]:
            raise ValueError("Missing 'metrics' key in data")

        metrics_list = data["data"]["metrics"]

        # Parse and aggregate metrics
        return self._parse_metrics(metrics_list, file_path)

    def _parse_metrics(self, metrics_list: List[Dict[str, Any]], file_path: Path) -> DailyActivityMetrics:
        """Parse metrics list and aggregate into DailyActivityMetrics.

        Args:
            metrics_list: List of metric dictionaries from JSON
            file_path: Original file path for error messages

        Returns:
            DailyActivityMetrics object with aggregated values
        """
        # Collect all metric values by type
        metric_values = {
            "dietary_energy": [],
            "active_energy": [],
            "weight_body_mass": [],
            "body_fat_percentage": [],
        }

        date = None

        for metric in metrics_list:
            metric_name = metric.get("name")

            # Only process metrics we care about
            if metric_name not in self.METRIC_FIELD_MAP:
                continue

            # Extract data points
            data_points = metric.get("data", [])
            for point in data_points:
                qty = point.get("qty")
                point_date_str = point.get("date")

                if qty is not None:
                    metric_values[metric_name].append(qty)

                    # Extract date (use first date found)
                    if date is None and point_date_str:
                        date = self._parse_date(point_date_str)

        # If no date found, try to extract from filename
        if date is None:
            date = self._extract_date_from_filename(file_path)

        # Aggregate values
        aggregated = self._aggregate_metrics(metric_values)

        return DailyActivityMetrics(
            date=date,
            source="HealthAutoExport",
            calories_in=aggregated.get("calories_in"),
            calories_out=aggregated.get("calories_out"),
            weight=aggregated.get("weight"),
            body_fat=aggregated.get("body_fat"),
        )

    def _aggregate_metrics(self, metric_values: Dict[str, List[float]]) -> Dict[str, float]:
        """Aggregate metric values according to business rules.

        Calories (dietary_energy, active_energy): Sum all values
        Weight/BodyFat: Average all values

        Args:
            metric_values: Dictionary of metric name to list of values

        Returns:
            Dictionary of aggregated values mapped to DailyActivityMetrics field names
        """
        aggregated = {}

        # Sum calories
        if metric_values["dietary_energy"]:
            aggregated["calories_in"] = round(sum(metric_values["dietary_energy"]), 1)

        if metric_values["active_energy"]:
            aggregated["calories_out"] = round(sum(metric_values["active_energy"]), 1)

        # Average weight and body fat
        if metric_values["weight_body_mass"]:
            avg_weight = sum(metric_values["weight_body_mass"]) / len(metric_values["weight_body_mass"])
            aggregated["weight"] = round(avg_weight, 1)

        if metric_values["body_fat_percentage"]:
            avg_bf = sum(metric_values["body_fat_percentage"]) / len(metric_values["body_fat_percentage"])
            # Convert percentage to decimal (18.9% → 0.189) for Notion percentage field
            aggregated["body_fat"] = round(avg_bf / 100, 4)

        return aggregated

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from HealthAutoExport format.

        Args:
            date_str: Date string (e.g., "2026-01-17 00:00:00 -0800")

        Returns:
            datetime object (timezone-naive, date only)
        """
        # Format: "2026-01-17 00:00:00 -0800"
        # Extract just the date part (YYYY-MM-DD)
        date_part = date_str.split()[0]  # Get "2026-01-17"

        try:
            return datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Failed to parse date '{date_str}': {e}")

    def _extract_date_from_filename(self, file_path: Path) -> datetime:
        """Extract date from HealthAutoExport filename.

        Args:
            file_path: Path to file (e.g., HealthAutoExport-2026-01-17.json)

        Returns:
            datetime object for the date

        Raises:
            ValueError: If filename doesn't match expected format
        """
        # Expected format: HealthAutoExport-YYYY-MM-DD.json
        filename = file_path.name
        if not filename.startswith("HealthAutoExport-"):
            raise ValueError(f"Unexpected filename format: {filename}")

        # Extract date part: "HealthAutoExport-2026-01-17.json" → "2026-01-17"
        date_part = filename.replace("HealthAutoExport-", "").replace(".json", "")

        try:
            return datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Failed to extract date from filename '{filename}': {e}")
