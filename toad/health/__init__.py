"""TOAD Health Module

Provides workout tracking and health statistics management.

This module handles:
- Parsing workout data from Gymaholic CSV exports and Apple Health data
- Syncing workouts to Notion databases
- Auto-checking habit tracker boxes based on workout types
- Generating workout summaries
- ETL pipeline for Health Stats visualization
"""

from toad.health.models import WorkoutData, ExerciseData, HealthMetric

__all__ = [
    'WorkoutData',
    'ExerciseData',
    'HealthMetric',
]
