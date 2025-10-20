"""
Statistics views subpackage.

Contains all statistical analysis and reporting views:
- General stats (heatmap data API)
- Player statistics (overview and detail)
- Course statistics (overview and detail)
"""

from .stats import heatmap_data
from .player_stats import player_stats_overview, player_detail_stats
from .course_stats import (
    course_stats_overview,
    course_detail_stats,
    course_difficulty_analysis_api
)

__all__ = [
    # General stats
    'heatmap_data',
    # Player stats
    'player_stats_overview',
    'player_detail_stats',
    # Course stats
    'course_stats_overview',
    'course_detail_stats',
    'course_difficulty_analysis_api',
]
