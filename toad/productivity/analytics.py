"""
Analytics and metrics calculation for TOAD productivity data.
Handles time block analysis, adherence metrics, and productivity insights.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TimeBlockMetrics:
    """Container for time block analysis metrics."""
    adherence_rate: float
    fragmentation_score: float
    optimal_block_size: float
    planning_effectiveness: float
    productivity_rate: float
    interruption_rate: float
    block_completion_rate: float

@dataclass
class DailyTimeBlockSummary:
    """Summary of time block metrics for a single day."""
    date: datetime
    total_blocks: int
    completed_blocks: int
    adhered_blocks: int
    total_planned_minutes: float
    total_actual_minutes: float
    fragmentation_score: float
    productivity_rate: float
    avg_block_size: float
    interruption_count: int

class TimeBlockAnalytics:
    """Advanced analytics for time block productivity data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_adherence_metrics(self, time_blocks_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate block adherence rates comparing planned vs actual execution.
        
        Args:
            time_blocks_df: DataFrame with time block data
            
        Returns:
            Dictionary with adherence metrics
        """
        self.logger.info("Calculating block adherence metrics...")
        
        metrics = {
            "overall_adherence": {},
            "temporal_adherence": {},
            "duration_adherence": {},
            "completion_adherence": {}
        }
        
        if len(time_blocks_df) == 0:
            return metrics
        
        # Overall adherence rate
        if "is_adhered" in time_blocks_df.columns:
            total_blocks = len(time_blocks_df)
            adhered_blocks = time_blocks_df["is_adhered"].sum()
            
            metrics["overall_adherence"] = {
                "rate": round((adhered_blocks / total_blocks) * 100, 2) if total_blocks > 0 else 0,
                "adhered_blocks": int(adhered_blocks),
                "total_blocks": int(total_blocks),
                "non_adhered_blocks": int(total_blocks - adhered_blocks)
            }
        
        # Duration adherence (planned vs actual duration)
        if "Duration (minutes)" in time_blocks_df.columns and "calculated_duration_minutes" in time_blocks_df.columns:
            duration_df = time_blocks_df.dropna(subset=["Duration (minutes)", "calculated_duration_minutes"])
            
            if not duration_df.empty:
                duration_variance = duration_df["calculated_duration_minutes"] - duration_df["Duration (minutes)"]
                duration_accuracy = 1 - (abs(duration_variance) / duration_df["Duration (minutes)"])
                
                # Consider blocks with <15% variance as duration-adherent
                duration_adherent = (abs(duration_variance) / duration_df["Duration (minutes)"]) <= 0.15
                
                metrics["duration_adherence"] = {
                    "rate": round((duration_adherent.sum() / len(duration_df)) * 100, 2),
                    "avg_accuracy": round(duration_accuracy.mean() * 100, 2),
                    "avg_variance_minutes": round(duration_variance.mean(), 2),
                    "median_variance_minutes": round(duration_variance.median(), 2)
                }
        
        # Completion adherence
        if "is_completed" in time_blocks_df.columns:
            total_blocks = len(time_blocks_df)
            completed_blocks = time_blocks_df["is_completed"].sum()
            
            metrics["completion_adherence"] = {
                "completion_rate": round((completed_blocks / total_blocks) * 100, 2) if total_blocks > 0 else 0,
                "completed_blocks": int(completed_blocks),
                "incomplete_blocks": int(total_blocks - completed_blocks)
            }
        
        # Temporal adherence by time of day
        if "start_hour" in time_blocks_df.columns and "is_adhered" in time_blocks_df.columns:
            temporal_adherence = time_blocks_df.groupby("start_hour")["is_adhered"].agg([
                "count", "sum", "mean"
            ]).round(3)
            
            metrics["temporal_adherence"] = {
                "by_hour": temporal_adherence.to_dict("index"),
                "best_hour": int(temporal_adherence["mean"].idxmax()) if not temporal_adherence.empty else None,
                "worst_hour": int(temporal_adherence["mean"].idxmin()) if not temporal_adherence.empty else None
            }
        
        self.logger.info(f"Calculated adherence metrics for {len(time_blocks_df)} blocks")
        return metrics
    
    def calculate_fragmentation_scores(self, time_blocks_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate fragmentation efficiency scores based on block patterns.
        
        Args:
            time_blocks_df: DataFrame with time block data
            
        Returns:
            Dictionary with fragmentation analysis
        """
        self.logger.info("Calculating fragmentation efficiency scores...")
        
        fragmentation = {
            "overall_score": 0.0,
            "daily_fragmentation": {},
            "block_pattern_analysis": {},
            "interruption_impact": {},
            "context_switching": {}
        }
        
        if len(time_blocks_df) == 0:
            return fragmentation
        
        # Calculate daily fragmentation scores
        if "block_start_time" in time_blocks_df.columns:
            # Group by date
            time_blocks_df["date"] = pd.to_datetime(time_blocks_df["block_start_time"]).dt.date
            
            daily_fragmentation = {}
            for date, day_blocks in time_blocks_df.groupby("date"):
                if len(day_blocks) > 0:
                    daily_fragmentation[str(date)] = self._calculate_daily_fragmentation(day_blocks)
            
            fragmentation["daily_fragmentation"] = daily_fragmentation
            
            # Overall fragmentation score (average of daily scores)
            if daily_fragmentation:
                scores = [day["fragmentation_score"] for day in daily_fragmentation.values()]
                fragmentation["overall_score"] = round(np.mean(scores), 2)
        
        # Block pattern analysis
        if "Duration (minutes)" in time_blocks_df.columns:
            durations = time_blocks_df["Duration (minutes)"].dropna()
            
            if not durations.empty:
                # Analyze block size distribution
                fragmentation["block_pattern_analysis"] = {
                    "avg_block_size": round(durations.mean(), 2),
                    "median_block_size": round(durations.median(), 2),
                    "block_size_std": round(durations.std(), 2),
                    "micro_blocks_pct": round((durations <= 15).mean() * 100, 2),  # ≤15 min
                    "short_blocks_pct": round(((durations > 15) & (durations <= 30)).mean() * 100, 2),  # 15-30 min
                    "medium_blocks_pct": round(((durations > 30) & (durations <= 60)).mean() * 100, 2),  # 30-60 min
                    "long_blocks_pct": round((durations > 60).mean() * 100, 2),  # >60 min
                    "fragmentation_index": self._calculate_fragmentation_index(durations)
                }
        
        # Interruption impact analysis
        if "is_interrupted" in time_blocks_df.columns:
            interrupted_blocks = time_blocks_df["is_interrupted"].sum()
            total_blocks = len(time_blocks_df)
            
            fragmentation["interruption_impact"] = {
                "interruption_rate": round((interrupted_blocks / total_blocks) * 100, 2) if total_blocks > 0 else 0,
                "interrupted_blocks": int(interrupted_blocks),
                "uninterrupted_blocks": int(total_blocks - interrupted_blocks)
            }
            
            # Productivity impact of interruptions
            if "productive_time_minutes" in time_blocks_df.columns:
                interrupted_productivity = time_blocks_df[time_blocks_df["is_interrupted"] == True]["productive_time_minutes"].mean()
                uninterrupted_productivity = time_blocks_df[time_blocks_df["is_interrupted"] == False]["productive_time_minutes"].mean()
                
                if pd.notna(interrupted_productivity) and pd.notna(uninterrupted_productivity):
                    fragmentation["interruption_impact"]["productivity_impact"] = {
                        "interrupted_avg_productivity": round(interrupted_productivity, 2),
                        "uninterrupted_avg_productivity": round(uninterrupted_productivity, 2),
                        "productivity_loss_pct": round(((uninterrupted_productivity - interrupted_productivity) / uninterrupted_productivity) * 100, 2)
                    }
        
        self.logger.info(f"Calculated fragmentation scores for {len(time_blocks_df)} blocks")
        return fragmentation
    
    def _calculate_daily_fragmentation(self, day_blocks: pd.DataFrame) -> Dict[str, Any]:
        """Calculate fragmentation score for a single day."""
        if len(day_blocks) == 0:
            return {"fragmentation_score": 0.0, "block_count": 0, "total_time": 0.0}
        
        durations = day_blocks["Duration (minutes)"].dropna()
        if durations.empty:
            return {"fragmentation_score": 0.0, "block_count": len(day_blocks), "total_time": 0.0}
        
        # Fragmentation score based on:
        # 1. Number of blocks (more blocks = more fragmented)
        # 2. Size variance (high variance = fragmented)
        # 3. Average block size (smaller blocks = more fragmented)
        
        block_count = len(durations)
        avg_duration = durations.mean()
        duration_std = durations.std()
        total_time = durations.sum()
        
        # Normalize factors (0-1 scale where 1 is most fragmented)
        block_count_factor = min(block_count / 10.0, 1.0)  # 10+ blocks = max fragmentation
        size_factor = max(0, 1 - (avg_duration / 60))  # <60 min avg = more fragmented
        variance_factor = min((duration_std / avg_duration) if avg_duration > 0 else 0, 1.0)
        
        # Weighted fragmentation score (lower is better)
        fragmentation_score = (block_count_factor * 0.4 + size_factor * 0.4 + variance_factor * 0.2) * 100
        
        return {
            "fragmentation_score": round(100 - fragmentation_score, 2),  # Invert so higher = better
            "block_count": int(block_count),
            "total_time": round(total_time, 2),
            "avg_block_size": round(avg_duration, 2),
            "block_size_variance": round(duration_std, 2)
        }
    
    def _calculate_fragmentation_index(self, durations: pd.Series) -> float:
        """Calculate a fragmentation index based on block size distribution."""
        if len(durations) <= 1:
            return 0.0
        
        # Coefficient of variation as fragmentation measure
        cv = durations.std() / durations.mean() if durations.mean() > 0 else 0
        
        # Normalize to 0-100 scale
        fragmentation_index = min(cv * 100, 100)
        return round(fragmentation_index, 2)
    
    def analyze_optimal_block_sizes(self, time_blocks_df: pd.DataFrame, tasks_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Analyze optimal block sizes based on productivity and completion rates.
        
        Args:
            time_blocks_df: DataFrame with time block data
            tasks_df: Optional tasks DataFrame for additional context
            
        Returns:
            Dictionary with optimal block size analysis
        """
        self.logger.info("Analyzing optimal block sizes...")
        
        analysis = {
            "productivity_by_size": {},
            "completion_by_size": {},
            "adherence_by_size": {},
            "recommendations": {}
        }
        
        if len(time_blocks_df) == 0:
            return analysis
        
        # Analyze productivity by block size category
        if "block_size_category" in time_blocks_df.columns and "productive_time_minutes" in time_blocks_df.columns:
            productivity_by_size = time_blocks_df.groupby("block_size_category").agg({
                "productive_time_minutes": ["mean", "sum", "count"],
                "Duration (minutes)": "mean"
            }).round(2)
            
            # Calculate productivity rate for each size category
            for category in productivity_by_size.index:
                category_data = time_blocks_df[time_blocks_df["block_size_category"] == category]
                total_time = category_data["Duration (minutes)"].sum()
                productive_time = category_data["productive_time_minutes"].sum()
                
                analysis["productivity_by_size"][category] = {
                    "avg_productive_minutes": round(category_data["productive_time_minutes"].mean(), 2),
                    "total_productive_minutes": round(productive_time, 2),
                    "productivity_rate": round((productive_time / total_time) * 100, 2) if total_time > 0 else 0,
                    "block_count": int(len(category_data)),
                    "avg_duration": round(category_data["Duration (minutes)"].mean(), 2)
                }
        
        # Analyze completion rates by block size
        if "block_size_category" in time_blocks_df.columns and "is_completed" in time_blocks_df.columns:
            completion_by_size = time_blocks_df.groupby("block_size_category")["is_completed"].agg([
                "count", "sum", "mean"
            ]).round(3)
            
            for category in completion_by_size.index:
                analysis["completion_by_size"][category] = {
                    "completion_rate": round(completion_by_size.loc[category, "mean"] * 100, 2),
                    "completed_blocks": int(completion_by_size.loc[category, "sum"]),
                    "total_blocks": int(completion_by_size.loc[category, "count"])
                }
        
        # Analyze adherence by block size
        if "block_size_category" in time_blocks_df.columns and "is_adhered" in time_blocks_df.columns:
            adherence_by_size = time_blocks_df.groupby("block_size_category")["is_adhered"].agg([
                "count", "sum", "mean"
            ]).round(3)
            
            for category in adherence_by_size.index:
                analysis["adherence_by_size"][category] = {
                    "adherence_rate": round(adherence_by_size.loc[category, "mean"] * 100, 2),
                    "adhered_blocks": int(adherence_by_size.loc[category, "sum"]),
                    "total_blocks": int(adherence_by_size.loc[category, "count"])
                }
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_block_size_recommendations(analysis)
        
        self.logger.info(f"Analyzed optimal block sizes for {len(time_blocks_df)} blocks")
        return analysis
    
    def _generate_block_size_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on block size analysis."""
        recommendations = {
            "most_productive_size": None,
            "most_adherent_size": None,
            "best_completion_size": None,
            "overall_recommendation": "",
            "insights": []
        }
        
        # Find most productive block size
        if analysis["productivity_by_size"]:
            best_productivity = max(
                analysis["productivity_by_size"].items(),
                key=lambda x: x[1]["productivity_rate"]
            )
            recommendations["most_productive_size"] = {
                "category": best_productivity[0],
                "productivity_rate": best_productivity[1]["productivity_rate"]
            }
        
        # Find most adherent block size
        if analysis["adherence_by_size"]:
            best_adherence = max(
                analysis["adherence_by_size"].items(),
                key=lambda x: x[1]["adherence_rate"]
            )
            recommendations["most_adherent_size"] = {
                "category": best_adherence[0],
                "adherence_rate": best_adherence[1]["adherence_rate"]
            }
        
        # Find best completion size
        if analysis["completion_by_size"]:
            best_completion = max(
                analysis["completion_by_size"].items(),
                key=lambda x: x[1]["completion_rate"]
            )
            recommendations["best_completion_size"] = {
                "category": best_completion[0],
                "completion_rate": best_completion[1]["completion_rate"]
            }
        
        # Generate overall recommendation
        if recommendations["most_productive_size"]:
            productive_size = recommendations["most_productive_size"]["category"]
            recommendations["overall_recommendation"] = f"Consider using {productive_size} blocks for optimal productivity"
            
            if recommendations["most_adherent_size"]:
                adherent_size = recommendations["most_adherent_size"]["category"]
                if productive_size != adherent_size:
                    recommendations["insights"].append(
                        f"Trade-off detected: {productive_size} blocks are most productive, "
                        f"but {adherent_size} blocks have better adherence"
                    )
        
        return recommendations
    
    def compare_planning_methods(self, time_blocks_df: pd.DataFrame, tasks_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare effectiveness of time blocks vs simple timeline planning.
        
        Args:
            time_blocks_df: DataFrame with time block data
            tasks_df: DataFrame with task data
            
        Returns:
            Dictionary comparing planning method effectiveness
        """
        self.logger.info("Comparing planning method effectiveness...")
        
        comparison = {
            "time_blocks_method": {},
            "simple_timeline_method": {},
            "effectiveness_comparison": {},
            "recommendations": {}
        }
        
        if len(tasks_df) == 0:
            return comparison
        
        # Separate tasks by planning method
        tasks_with_blocks = tasks_df[tasks_df.get("Has Time Blocks", False) == True]
        tasks_simple_timeline = tasks_df[
            (tasks_df.get("Has Time Blocks", False) == False) & 
            (tasks_df["Planned Timeline"].notna())
        ]
        
        # Analyze time blocks method
        if len(tasks_with_blocks) > 0:
            comparison["time_blocks_method"] = self._analyze_planning_method(
                tasks_with_blocks, "Time Blocks"
            )
        
        # Analyze simple timeline method
        if len(tasks_simple_timeline) > 0:
            comparison["simple_timeline_method"] = self._analyze_planning_method(
                tasks_simple_timeline, "Simple Timeline"
            )
        
        # Compare effectiveness
        if comparison["time_blocks_method"] and comparison["simple_timeline_method"]:
            tb_method = comparison["time_blocks_method"]
            st_method = comparison["simple_timeline_method"]
            
            comparison["effectiveness_comparison"] = {
                "completion_rate_diff": round(
                    tb_method["completion_rate"] - st_method["completion_rate"], 2
                ),
                "adherence_diff": round(
                    tb_method.get("adherence_rate", 0) - st_method.get("adherence_rate", 0), 2
                ),
                "time_accuracy_diff": round(
                    tb_method.get("time_accuracy", 0) - st_method.get("time_accuracy", 0), 2
                ),
                "better_method": self._determine_better_method(tb_method, st_method)
            }
        
        # Generate recommendations
        comparison["recommendations"] = self._generate_planning_recommendations(comparison)
        
        self.logger.info("Completed planning method comparison")
        return comparison
    
    def _analyze_planning_method(self, tasks_subset: pd.DataFrame, method_name: str) -> Dict[str, Any]:
        """Analyze effectiveness metrics for a specific planning method."""
        method_analysis = {
            "method": method_name,
            "task_count": len(tasks_subset),
            "completion_rate": 0.0,
            "adherence_rate": 0.0,
            "time_accuracy": 0.0,
            "avg_task_age": 0.0
        }
        
        # Completion rate
        if "is_completed" in tasks_subset.columns:
            completed = tasks_subset["is_completed"].sum()
            method_analysis["completion_rate"] = round((completed / len(tasks_subset)) * 100, 2)
        
        # Time accuracy (estimated vs logged)
        if "Est Hours" in tasks_subset.columns and "logged_hours" in tasks_subset.columns:
            time_data = tasks_subset.dropna(subset=["Est Hours", "logged_hours"])
            if not time_data.empty:
                accuracy = 1 - abs(time_data["Est Hours"] - time_data["logged_hours"]) / time_data["Est Hours"]
                method_analysis["time_accuracy"] = round(accuracy.mean() * 100, 2)
        
        # Task age
        if "days_since_created" in tasks_subset.columns:
            method_analysis["avg_task_age"] = round(tasks_subset["days_since_created"].mean(), 2)
        
        return method_analysis
    
    def _determine_better_method(self, tb_method: Dict, st_method: Dict) -> str:
        """Determine which planning method is more effective overall."""
        tb_score = (
            tb_method["completion_rate"] * 0.4 +
            tb_method.get("adherence_rate", 0) * 0.3 +
            tb_method.get("time_accuracy", 0) * 0.3
        )
        
        st_score = (
            st_method["completion_rate"] * 0.4 +
            st_method.get("adherence_rate", 0) * 0.3 +
            st_method.get("time_accuracy", 0) * 0.3
        )
        
        if tb_score > st_score:
            return "Time Blocks"
        elif st_score > tb_score:
            return "Simple Timeline"
        else:
            return "Equal"
    
    def _generate_planning_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations based on planning method comparison."""
        recommendations = []
        
        if not comparison.get("effectiveness_comparison"):
            return recommendations
        
        effectiveness = comparison["effectiveness_comparison"]
        better_method = effectiveness.get("better_method")
        
        if better_method == "Time Blocks":
            recommendations.append(
                "Time blocks show superior effectiveness. Consider using time blocks for more tasks."
            )
        elif better_method == "Simple Timeline":
            recommendations.append(
                "Simple timeline planning is more effective. Consider reducing time block complexity."
            )
        else:
            recommendations.append(
                "Both planning methods show similar effectiveness. Use based on task complexity."
            )
        
        # Specific recommendations based on metrics
        completion_diff = effectiveness.get("completion_rate_diff", 0)
        if abs(completion_diff) > 10:
            method = "time blocks" if completion_diff > 0 else "simple timeline"
            recommendations.append(
                f"Completion rates are {abs(completion_diff):.1f}% higher with {method} planning."
            )
        
        return recommendations
    
    def generate_daily_summaries(self, time_blocks_df: pd.DataFrame) -> Dict[str, DailyTimeBlockSummary]:
        """
        Generate daily summary aggregations of time block metrics.
        
        Args:
            time_blocks_df: DataFrame with time block data
            
        Returns:
            Dictionary mapping dates to DailyTimeBlockSummary objects
        """
        self.logger.info("Generating daily time block summaries...")
        
        daily_summaries = {}
        
        if len(time_blocks_df) == 0:
            return daily_summaries
        
        # Ensure we have date information
        if "block_start_time" not in time_blocks_df.columns:
            self.logger.warning("No block_start_time column found for daily aggregation")
            return daily_summaries
        
        # Group by date
        time_blocks_df["date"] = pd.to_datetime(time_blocks_df["block_start_time"]).dt.date
        
        for date, day_blocks in time_blocks_df.groupby("date"):
            if len(day_blocks) == 0:
                continue
            
            # Calculate daily metrics
            total_blocks = len(day_blocks)
            completed_blocks = day_blocks.get("is_completed", pd.Series([False] * total_blocks)).sum()
            adhered_blocks = day_blocks.get("is_adhered", pd.Series([False] * total_blocks)).sum()
            
            total_planned = day_blocks.get("Duration (minutes)", pd.Series([0] * total_blocks)).sum()
            total_actual = day_blocks.get("calculated_duration_minutes", pd.Series([0] * total_blocks)).sum()
            
            # Fragmentation score for the day
            fragmentation_data = self._calculate_daily_fragmentation(day_blocks)
            fragmentation_score = fragmentation_data["fragmentation_score"]
            
            # Productivity rate
            productive_time = day_blocks.get("productive_time_minutes", pd.Series([0] * total_blocks)).sum()
            productivity_rate = (productive_time / total_planned * 100) if total_planned > 0 else 0
            
            # Average block size
            avg_block_size = day_blocks.get("Duration (minutes)", pd.Series([0] * total_blocks)).mean()
            
            # Interruption count
            interruption_count = day_blocks.get("is_interrupted", pd.Series([False] * total_blocks)).sum()
            
            # Create daily summary
            summary = DailyTimeBlockSummary(
                date=datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc),
                total_blocks=int(total_blocks),
                completed_blocks=int(completed_blocks),
                adhered_blocks=int(adhered_blocks),
                total_planned_minutes=round(total_planned, 2),
                total_actual_minutes=round(total_actual, 2),
                fragmentation_score=round(fragmentation_score, 2),
                productivity_rate=round(productivity_rate, 2),
                avg_block_size=round(avg_block_size, 2),
                interruption_count=int(interruption_count)
            )
            
            daily_summaries[str(date)] = summary
        
        self.logger.info(f"Generated daily summaries for {len(daily_summaries)} days")
        return daily_summaries
    
    def generate_weekly_summaries(self, daily_summaries: Dict[str, DailyTimeBlockSummary]) -> Dict[str, Any]:
        """
        Generate weekly aggregations from daily summaries.
        
        Args:
            daily_summaries: Dictionary of daily summaries
            
        Returns:
            Dictionary with weekly aggregated metrics
        """
        self.logger.info("Generating weekly time block summaries...")
        
        if not daily_summaries:
            return {}
        
        # Convert to DataFrame for easier aggregation
        data = []
        for date_str, summary in daily_summaries.items():
            data.append({
                "date": summary.date,
                "week": summary.date.isocalendar()[1],  # ISO week number
                "year": summary.date.year,
                "total_blocks": summary.total_blocks,
                "completed_blocks": summary.completed_blocks,
                "adhered_blocks": summary.adhered_blocks,
                "total_planned_minutes": summary.total_planned_minutes,
                "total_actual_minutes": summary.total_actual_minutes,
                "fragmentation_score": summary.fragmentation_score,
                "productivity_rate": summary.productivity_rate,
                "avg_block_size": summary.avg_block_size,
                "interruption_count": summary.interruption_count
            })
        
        df = pd.DataFrame(data)
        df["week_year"] = df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
        
        # Aggregate by week
        weekly_summaries = {}
        for week_year, week_data in df.groupby("week_year"):
            weekly_summaries[week_year] = {
                "week_period": week_year,
                "days_with_blocks": len(week_data),
                "total_blocks": int(week_data["total_blocks"].sum()),
                "total_completed_blocks": int(week_data["completed_blocks"].sum()),
                "total_adhered_blocks": int(week_data["adhered_blocks"].sum()),
                "completion_rate": round((week_data["completed_blocks"].sum() / week_data["total_blocks"].sum()) * 100, 2) if week_data["total_blocks"].sum() > 0 else 0,
                "adherence_rate": round((week_data["adhered_blocks"].sum() / week_data["total_blocks"].sum()) * 100, 2) if week_data["total_blocks"].sum() > 0 else 0,
                "total_planned_hours": round(week_data["total_planned_minutes"].sum() / 60, 2),
                "total_actual_hours": round(week_data["total_actual_minutes"].sum() / 60, 2),
                "avg_fragmentation_score": round(week_data["fragmentation_score"].mean(), 2),
                "avg_productivity_rate": round(week_data["productivity_rate"].mean(), 2),
                "avg_block_size": round(week_data["avg_block_size"].mean(), 2),
                "total_interruptions": int(week_data["interruption_count"].sum()),
                "avg_daily_blocks": round(week_data["total_blocks"].mean(), 2)
            }
        
        self.logger.info(f"Generated weekly summaries for {len(weekly_summaries)} weeks")
        return weekly_summaries
    
    def generate_comprehensive_analysis(self, time_blocks_df: pd.DataFrame, tasks_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive time block analysis report.
        
        Args:
            time_blocks_df: DataFrame with time block data
            tasks_df: DataFrame with task data
            
        Returns:
            Dictionary with complete analysis
        """
        self.logger.info("Generating comprehensive time block analysis...")
        
        analysis = {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_summary": {
                "time_blocks_count": len(time_blocks_df),
                "tasks_count": len(tasks_df),
                "analysis_period": None
            },
            "adherence_metrics": {},
            "fragmentation_analysis": {},
            "optimal_block_analysis": {},
            "planning_method_comparison": {},
            "daily_summaries": {},
            "weekly_summaries": {},
            "key_insights": [],
            "recommendations": []
        }
        
        # Set analysis period
        if not time_blocks_df.empty and "block_start_time" in time_blocks_df.columns:
            start_date = pd.to_datetime(time_blocks_df["block_start_time"]).min()
            end_date = pd.to_datetime(time_blocks_df["block_start_time"]).max()
            analysis["data_summary"]["analysis_period"] = {
                "start": start_date.isoformat() if pd.notna(start_date) else None,
                "end": end_date.isoformat() if pd.notna(end_date) else None,
                "days": (end_date - start_date).days if pd.notna(start_date) and pd.notna(end_date) else 0
            }
        
        # Run all analyses
        analysis["adherence_metrics"] = self.calculate_adherence_metrics(time_blocks_df)
        analysis["fragmentation_analysis"] = self.calculate_fragmentation_scores(time_blocks_df)
        analysis["optimal_block_analysis"] = self.analyze_optimal_block_sizes(time_blocks_df, tasks_df)
        analysis["planning_method_comparison"] = self.compare_planning_methods(time_blocks_df, tasks_df)
        
        # Generate summaries
        daily_summaries = self.generate_daily_summaries(time_blocks_df)
        analysis["daily_summaries"] = {k: vars(v) for k, v in daily_summaries.items()}
        analysis["weekly_summaries"] = self.generate_weekly_summaries(daily_summaries)
        
        # Generate insights and recommendations
        analysis["key_insights"] = self._generate_key_insights(analysis)
        analysis["recommendations"] = self._generate_comprehensive_recommendations(analysis)
        
        self.logger.info("Completed comprehensive time block analysis")
        return analysis
    
    def _generate_key_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key insights from the comprehensive analysis."""
        insights = []
        
        # Adherence insights
        adherence = analysis.get("adherence_metrics", {}).get("overall_adherence", {})
        if adherence:
            rate = adherence.get("rate", 0)
            if rate >= 80:
                insights.append(f"Excellent adherence rate of {rate}% indicates strong planning discipline")
            elif rate >= 60:
                insights.append(f"Good adherence rate of {rate}% with room for improvement")
            else:
                insights.append(f"Low adherence rate of {rate}% suggests planning adjustments needed")
        
        # Fragmentation insights
        fragmentation = analysis.get("fragmentation_analysis", {})
        overall_score = fragmentation.get("overall_score", 0)
        if overall_score >= 70:
            insights.append(f"Low fragmentation score of {overall_score} indicates good time consolidation")
        elif overall_score <= 40:
            insights.append(f"High fragmentation score of {overall_score} suggests too many small blocks")
        
        # Block size insights
        block_analysis = analysis.get("optimal_block_analysis", {})
        recommendations = block_analysis.get("recommendations", {})
        if recommendations.get("most_productive_size"):
            productive_size = recommendations["most_productive_size"]["category"]
            insights.append(f"{productive_size} blocks show highest productivity rates")
        
        # Planning method insights
        planning_comparison = analysis.get("planning_method_comparison", {})
        effectiveness = planning_comparison.get("effectiveness_comparison", {})
        better_method = effectiveness.get("better_method")
        if better_method and better_method != "Equal":
            insights.append(f"{better_method} planning method is more effective overall")
        
        return insights
    
    def _generate_comprehensive_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations from the analysis."""
        recommendations = []
        
        # Adherence recommendations
        adherence = analysis.get("adherence_metrics", {}).get("overall_adherence", {})
        if adherence.get("rate", 0) < 70:
            recommendations.append("Focus on improving adherence through realistic time estimates and block sizing")
        
        # Fragmentation recommendations
        fragmentation = analysis.get("fragmentation_analysis", {})
        block_patterns = fragmentation.get("block_pattern_analysis", {})
        micro_blocks_pct = block_patterns.get("micro_blocks_pct", 0)
        if micro_blocks_pct > 30:
            recommendations.append("Consider consolidating micro blocks (≤15 min) into larger, more productive blocks")
        
        # Block size recommendations
        block_analysis = analysis.get("optimal_block_analysis", {})
        if block_analysis.get("recommendations", {}).get("insights"):
            recommendations.extend(block_analysis["recommendations"]["insights"])
        
        # Planning method recommendations
        planning_comparison = analysis.get("planning_method_comparison", {})
        if planning_comparison.get("recommendations"):
            recommendations.extend(planning_comparison["recommendations"])
        
        # Weekly pattern recommendations
        weekly_summaries = analysis.get("weekly_summaries", {})
        if weekly_summaries:
            avg_completion_rates = [week["completion_rate"] for week in weekly_summaries.values()]
            if avg_completion_rates and np.mean(avg_completion_rates) < 60:
                recommendations.append("Weekly completion rates below 60% suggest need for better task estimation")
        
        return recommendations
