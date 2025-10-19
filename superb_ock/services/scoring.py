"""
Scoring calculation service.

Centralizes all scoring logic for different tournament formats, eliminating
duplication between Home, EventView, and other views.
"""

from typing import List, Dict, Tuple, Optional
from django.db.models import QuerySet

from superb_ock.constants import ScoringFormat
from superb_ock.logging_config import scoring_logger


class ScoringCalculator:
    """
    Handles scoring calculations for different tournament formats.

    Supports:
    - Best 3 of 5 rounds
    - Best 2 of first 4 + last round counts
    """

    def __init__(self, scoring_format: str):
        """
        Initialize calculator with scoring format.

        Args:
            scoring_format: Tournament scoring format (from ScoringFormat constants)
        """
        self.scoring_format = scoring_format
        scoring_logger.info(f"ScoringCalculator initialized with format: {scoring_format}")

    def calculate_total(
        self,
        player_rounds: Dict[int, int],
    ) -> int:
        """
        Calculate total score for a player based on scoring format.

        Args:
            player_rounds: Dictionary mapping round_id -> total_stableford

        Returns:
            Total stableford points based on scoring format
        """
        valid_rounds = [
            {'round_id': round_id, 'total': total}
            for round_id, total in player_rounds.items()
            if total is not None
        ]

        if not valid_rounds:
            return 0

        if self.scoring_format == ScoringFormat.BEST_THREE_OF_FIVE:
            return self._calculate_best_three_of_five(valid_rounds)
        elif self.scoring_format == ScoringFormat.BEST_LAST_ROUNDS_COUNTS:
            return self._calculate_best_last_rounds(valid_rounds)
        else:
            # Default to best 3
            scoring_logger.warning(f"Unknown scoring format '{self.scoring_format}', defaulting to best 3")
            return self._calculate_best_three_of_five(valid_rounds)

    def get_counting_rounds(
        self,
        player_rounds: Dict[int, int],
    ) -> List[int]:
        """
        Get list of round IDs that count towards player's total.

        Args:
            player_rounds: Dictionary mapping round_id -> total_stableford

        Returns:
            List of round IDs that count towards total
        """
        valid_rounds = [
            {'round_id': round_id, 'total': total}
            for round_id, total in player_rounds.items()
            if total is not None
        ]

        if not valid_rounds:
            return []

        if self.scoring_format == ScoringFormat.BEST_THREE_OF_FIVE:
            counting = self._get_best_three_rounds(valid_rounds)
        elif self.scoring_format == ScoringFormat.BEST_LAST_ROUNDS_COUNTS:
            counting = self._get_best_last_rounds(valid_rounds)
        else:
            counting = self._get_best_three_rounds(valid_rounds)

        return [r['round_id'] for r in counting]

    def _calculate_best_three_of_five(self, valid_rounds: List[Dict]) -> int:
        """
        Calculate score for 'Best 3 of 5' format.

        Takes the top 3 rounds by stableford points, regardless of order.
        """
        top_3 = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
        total = sum(r['total'] for r in top_3)
        scoring_logger.debug(f"Best 3 of 5: {len(valid_rounds)} rounds, top 3 total={total}")
        return total

    def _calculate_best_last_rounds(self, valid_rounds: List[Dict]) -> int:
        """
        Calculate score for 'Best last rounds counts' format.

        - If 3+ rounds: Best 2 of first rounds + last round counts
        - If <3 rounds: Sum all rounds
        """
        if len(valid_rounds) < 3:
            total = sum(r['total'] for r in valid_rounds)
            scoring_logger.debug(f"Best last (< 3 rounds): {len(valid_rounds)} rounds, total={total}")
            return total

        # Sort by round ID (chronological)
        sorted_rounds = sorted(valid_rounds, key=lambda x: x['round_id'])
        last_round = sorted_rounds[-1]
        first_rounds = sorted_rounds[:-1]

        # Best 2 of the first rounds
        best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]

        total = sum(r['total'] for r in best_first_two) + last_round['total']
        scoring_logger.debug(
            f"Best last rounds: {len(valid_rounds)} rounds, "
            f"best 2 of first + last = {total}"
        )
        return total

    def _get_best_three_rounds(self, valid_rounds: List[Dict]) -> List[Dict]:
        """Get the best 3 rounds by score."""
        return sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]

    def _get_best_last_rounds(self, valid_rounds: List[Dict]) -> List[Dict]:
        """Get counting rounds for best last rounds format."""
        if len(valid_rounds) < 3:
            return valid_rounds

        sorted_rounds = sorted(valid_rounds, key=lambda x: x['round_id'])
        last_round = sorted_rounds[-1]
        first_rounds = sorted_rounds[:-1]
        best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]

        return best_first_two + [last_round]


class DateCourseKey:
    """
    Helper class for (date, course) tuple keys used in Home view.

    The Home view groups rounds by (date, course) to combine rounds
    at the same course on the same day.
    """

    def __init__(self, date, course_name):
        self.date = date
        self.course_name = course_name
        self.key = (date, course_name)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.key == other
        return self.key == other.key

    def __lt__(self, other):
        """For sorting: date first, then course name."""
        if isinstance(other, tuple):
            return self.key < other
        return self.key < other.key

    def __repr__(self):
        return f"DateCourseKey({self.date}, {self.course_name})"


class DateCourseScoringCalculator(ScoringCalculator):
    """
    Extended scoring calculator for Home view which groups by (date, course).

    This handles the special case where rounds are keyed by (date, course)
    instead of round_id.
    """

    def calculate_total_by_date_course(
        self,
        player_date_courses: Dict[Tuple, int]
    ) -> int:
        """
        Calculate total for rounds grouped by (date, course).

        Args:
            player_date_courses: Dict mapping (date, course) -> total_stableford

        Returns:
            Total stableford points
        """
        valid_rounds = [
            {'key': key, 'total': total}
            for key, total in player_date_courses.items()
            if total is not None
        ]

        if not valid_rounds:
            return 0

        if self.scoring_format == ScoringFormat.BEST_THREE_OF_FIVE:
            top_3 = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
            return sum(r['total'] for r in top_3)
        elif self.scoring_format == ScoringFormat.BEST_LAST_ROUNDS_COUNTS:
            if len(valid_rounds) < 3:
                return sum(r['total'] for r in valid_rounds)

            # Sort by date (first element of tuple key)
            sorted_rounds = sorted(valid_rounds, key=lambda x: x['key'][0])
            last_round = sorted_rounds[-1]
            first_rounds = sorted_rounds[:-1]
            best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]

            return sum(r['total'] for r in best_first_two) + last_round['total']
        else:
            top_3 = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
            return sum(r['total'] for r in top_3)

    def get_counting_date_courses(
        self,
        player_date_courses: Dict[Tuple, int]
    ) -> List[Tuple]:
        """
        Get list of (date, course) keys that count towards total.

        Args:
            player_date_courses: Dict mapping (date, course) -> total_stableford

        Returns:
            List of (date, course) tuples that count
        """
        valid_rounds = [
            {'key': key, 'total': total}
            for key, total in player_date_courses.items()
            if total is not None
        ]

        if not valid_rounds:
            return []

        if self.scoring_format == ScoringFormat.BEST_THREE_OF_FIVE:
            counting = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
        elif self.scoring_format == ScoringFormat.BEST_LAST_ROUNDS_COUNTS:
            if len(valid_rounds) < 3:
                counting = valid_rounds
            else:
                sorted_rounds = sorted(valid_rounds, key=lambda x: x['key'][0])  # Sort by date
                last_round = sorted_rounds[-1]
                first_rounds = sorted_rounds[:-1]
                best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]
                counting = best_first_two + [last_round]
        else:
            counting = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]

        return [r['key'] for r in counting]
