"""
Views package for superb_ock application.

This package organizes views into logical modules while maintaining
backwards compatibility with the old monolithic views.py structure.

Imports all views so they can be accessed as:
    from superb_ock.views import Home, signUpUser, etc.
"""

# Utility functions
from .utils import jsonify, getWeather

# Authentication views
from .auth import signUpUser, logInUser, logOutUser

# Homepage
from .homepage import Home

# Round management views
from .rounds import NewRound, RoundsOverview, GolfRoundView

# Score editing views
from .scores import EditScore

# Visualization views
from .visualizations import HeatMap

# Event views
from .events import EventView

# Highlight views
from .highlights import HighlightsView

# Stats views
from .stats import (
    heatmap_data,
    player_stats_overview,
    player_detail_stats,
    course_stats_overview,
    course_detail_stats,
    course_difficulty_analysis_api
)

__all__ = [
    # Utils
    'jsonify',
    'getWeather',
    # Auth
    'signUpUser',
    'logInUser',
    'logOutUser',
    # Homepage
    'Home',
    # Rounds
    'NewRound',
    'RoundsOverview',
    'GolfRoundView',
    # Scores
    'EditScore',
    # Visualizations
    'HeatMap',
    # Events
    'EventView',
    # Highlights
    'HighlightsView',
    # Stats
    'heatmap_data',
    'player_stats_overview',
    'player_detail_stats',
    'course_stats_overview',
    'course_detail_stats',
    'course_difficulty_analysis_api',
]
