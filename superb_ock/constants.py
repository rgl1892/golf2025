"""
Constants for the golf2025 application.

This module centralizes all magic numbers and configuration values
used throughout the application to improve maintainability.
"""

# Golf game constants
HOLES_PER_ROUND = 18
MAX_PLAYERS_PER_ROUND = 4
TOTAL_SCORES_PER_ROUND = HOLES_PER_ROUND * MAX_PLAYERS_PER_ROUND  # 72

# Par values
PAR_VALUES = [3, 4, 5]
MIN_PAR = 3
MAX_PAR = 5


# Scoring formats
class ScoringFormat:
    """Golf event scoring format options."""

    BEST_THREE_OF_FIVE = 'best_three_of_five'
    BEST_LAST_ROUNDS_COUNTS = 'best_last_rounds_counts'

    CHOICES = [
        (BEST_THREE_OF_FIVE, 'Best 3 of 5'),
        (BEST_LAST_ROUNDS_COUNTS, 'Best Last Rounds Count'),
    ]

    @classmethod
    def get_display_name(cls, format_value: str) -> str:
        """Get human-readable name for scoring format."""
        format_map = dict(cls.CHOICES)
        return format_map.get(format_value, format_value)


# Stableford scoring points
class StablefordPoints:
    """Stableford points based on score relative to par."""

    EAGLE_OR_BETTER = 4  # 2 or more under par
    BIRDIE = 3           # 1 under par
    PAR = 2              # Equal to par
    BOGEY = 1            # 1 over par
    DOUBLE_BOGEY_OR_WORSE = 0  # 2 or more over par


# Media handling constants
class MediaSettings:
    """Settings for media file processing."""

    # Thumbnail generation
    THUMBNAIL_QUALITY = 95
    THUMBNAIL_POSITION = 0.5  # Midpoint of video

    # Preview generation
    PREVIEW_COUNT = 3
    PREVIEW_POSITIONS = [0.25, 0.5, 0.75]  # 25%, 50%, 75% through video
    PREVIEW_QUALITY = 95

    # Image enhancement factors
    SHARPNESS_FACTOR = 1.5
    CONTRAST_FACTOR = 1.2
    COLOR_SATURATION_FACTOR = 1.1

    # Allowed video formats
    VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv']

    # Allowed image formats
    IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif']


# Handedness choices
class Handedness:
    """Player handedness options."""

    LEFT = 'left'
    RIGHT = 'right'

    CHOICES = [
        (LEFT, 'Left'),
        (RIGHT, 'Right'),
    ]


# Notification settings
class NotificationSettings:
    """Web push notification configuration."""

    # Notification types
    ROUND_START = 'round_start'
    HOLE_COMPLETED = 'hole_completed'
    ROUND_COMPLETED = 'round_completed'

    # Default preferences
    DEFAULT_ENABLED = False
    DEFAULT_NOTIFY_ROUND_START = True
    DEFAULT_NOTIFY_HOLE_COMPLETED = False
    DEFAULT_NOTIFY_ROUND_COMPLETED = True

    # Push notification settings
    PUSH_ICON_URL = '/static/superb_ock/images/logo.png'
    PUSH_BADGE_URL = '/static/superb_ock/images/logo.ico'


# Carousel settings
class CarouselSettings:
    """Homepage carousel configuration."""

    DEFAULT_FOCAL_POINT_X = 50  # Percentage
    DEFAULT_FOCAL_POINT_Y = 50  # Percentage
    MAX_ACTIVE_IMAGES = 10
    DEFAULT_ORDER = 0


# Course difficulty ratings
class CourseDifficulty:
    """Golf course difficulty thresholds."""

    # Slope rating categories (from USGA)
    SLOPE_EASY = 113
    SLOPE_MODERATE = 125
    SLOPE_DIFFICULT = 135
    SLOPE_VERY_DIFFICULT = 145

    # Course rating relative to par
    RATING_EASY = 0.0  # At or below par
    RATING_MODERATE = 2.0  # 2 strokes over par
    RATING_DIFFICULT = 4.0  # 4 strokes over par


# Admin settings
class AdminSettings:
    """Django admin interface configuration."""

    # List display pagination
    DEFAULT_LIST_PER_PAGE = 25
    SCORES_PER_PAGE = 50
    HIGHLIGHTS_PER_PAGE = 20

    # Bulk action limits
    MAX_BULK_LINK_HIGHLIGHTS = 100


# Statistics settings
class StatsSettings:
    """Statistics and analytics configuration."""

    # Heatmap settings
    HEATMAP_MIN_ROUNDS = 3  # Minimum rounds for meaningful stats

    # Player stats
    RECENT_ROUNDS_LIMIT = 5
    TOP_PLAYERS_LIMIT = 10

    # Course stats
    COURSE_DIFFICULTY_SAMPLES = 10  # Minimum rounds to calculate difficulty
