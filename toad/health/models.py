"""Data models for TOAD Health module.

This module defines the core data structures used throughout the health
tracking system, including workout data, exercise details, and health metrics.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class WorkoutData:
    """Represents a parsed workout session.

    Attributes:
        date: Date and time of the workout
        workout_type: Type of workout (Strength, Run, Climb, Hike, Walk, Other)
        source: Data source (Gymaholic, Apple Health Export, etc.)
        duration_minutes: Duration of workout in minutes (optional)
        calories: Calories burned during workout (optional)
        avg_heart_rate: Average heart rate in BPM (optional)
        distance_miles: Distance covered in miles for cardio workouts (optional)
        elevation_feet: Elevation gain in feet for hiking/climbing (optional)
        notes: User notes or auto-generated summary (optional)
        raw_file_path: Path to original data file (optional)
        exercises: List of exercises for strength workouts (optional)
    """
    date: datetime
    workout_type: str  # Strength, Run, Climb, Hike, Walk, Other
    source: str  # Gymaholic, Apple Health Export, Health Auto Export, Manual
    duration_minutes: Optional[int] = None
    calories: Optional[int] = None
    avg_heart_rate: Optional[int] = None
    distance_miles: Optional[float] = None
    elevation_feet: Optional[int] = None
    notes: Optional[str] = None
    raw_file_path: Optional[str] = None
    exercises: Optional[List['ExerciseData']] = None


@dataclass
class ExerciseData:
    """Represents a single exercise within a strength workout.

    Attributes:
        name: Exercise name (e.g., "Bench Press", "Squat")
        sets: Number of sets performed
        reps: List of reps completed per set
        weight: List of weight used per set in pounds
        notes: Optional notes about the exercise (form cues, etc.)
    """
    name: str
    sets: int
    reps: List[int]  # Reps per set
    weight: List[float]  # Weight per set (lbs)
    notes: Optional[str] = None


@dataclass
class HealthMetric:
    """Represents a single health metric for Health Stats table.

    This is used for the ETL pipeline that transforms Habit Tracker data
    into time-series format for charting.

    Attributes:
        date: Date of the measurement
        tag: Metric type (lbs, bf, cals_in, cals_out)
        value: Numeric value of the metric
    """
    date: datetime
    tag: str  # lbs, bf, cals_in, cals_out
    value: float
