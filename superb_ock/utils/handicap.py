"""
Handicap calculation utilities.

Provides functions for calculating course handicap and playing handicap
according to golf standards.
"""


def calculate_course_handicap(handicap_index, slope_rating, course_rating, par):
    """
    Calculate course handicap.

    Formula: Handicap Index × (Slope Rating ÷ 113) + (Course Rating − Par)

    Args:
        handicap_index: Player's handicap index
        slope_rating: Course slope rating
        course_rating: Course rating
        par: Course par

    Returns:
        Rounded course handicap
    """
    return round(
        handicap_index * (slope_rating / 113) + course_rating - par
    )


def calculate_playing_handicap(handicap_index, slope_rating, course_rating, par, use_playing_handicap=False):
    """
    Calculate handicap for play.

    If use_playing_handicap is True, applies 95% allowance (England Golf standard).
    Otherwise returns full course handicap.

    Args:
        handicap_index: Player's handicap index
        slope_rating: Course slope rating
        course_rating: Course rating
        par: Course par
        use_playing_handicap: If True, apply 95% allowance

    Returns:
        Rounded playing handicap
    """
    course_handicap = calculate_course_handicap(
        handicap_index, slope_rating, course_rating, par
    )

    if use_playing_handicap:
        return round(course_handicap * 0.95)

    return course_handicap
