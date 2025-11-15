"""
Leaderboard building service.

Consolidates leaderboard logic from Home and EventView, eliminating ~200 lines
of duplicated code.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

from django.core.cache import cache

from superb_ock.models import Score, GolfEvent, GolfRound
from superb_ock.services.scoring import ScoringCalculator, DateCourseScoringCalculator
from superb_ock.logging_config import app_logger


@dataclass
class LeaderboardEntry:
    """
    Single player entry in a leaderboard.

    Contains all scoring information and round details for display.
    """
    player_name: str
    total_points: int
    rounds: List[Dict[str, Any]] = field(default_factory=list)
    position: Optional[int] = None

    def __repr__(self):
        return f"LeaderboardEntry({self.player_name}, {self.total_points} pts, pos={self.position})"


class LeaderboardBuilder:
    """
    Builds leaderboards for tournament events.

    Handles:
    - Fetching and grouping scores
    - Calculating totals using ScoringCalculator
    - Determining counting rounds
    - Sorting and ranking players
    """

    def __init__(self, event_id: int):
        """
        Initialize builder for specific event.

        Args:
            event_id: ID of the GolfEvent
        """
        self.event_id = event_id
        self.event = GolfEvent.objects.get(id=event_id)
        self.calculator = ScoringCalculator(self.event.scoring)
        app_logger.info(f"LeaderboardBuilder initialized for event {self.event.name} (ID: {event_id})")

    def build(self, use_cache: bool = True) -> List[LeaderboardEntry]:
        """
        Build complete leaderboard with rankings.

        Args:
            use_cache: Whether to use cached results (default: True)

        Returns:
            Sorted list of LeaderboardEntry objects
        """
        # Try to get from cache
        if use_cache:
            cache_key = self._get_cache_key()
            cached_leaderboard = cache.get(cache_key)
            if cached_leaderboard is not None:
                app_logger.debug(f"Leaderboard cache hit for event {self.event_id}")
                return cached_leaderboard

        # Fetch all scores for the event
        scores = self._fetch_scores()

        # Group scores by player and round
        player_rounds = self._group_scores_by_player(scores)

        # Calculate entries
        entries = self._calculate_entries(player_rounds, scores)

        # Sort by total points
        entries = self._sort_entries(entries)

        # Assign positions
        entries = self._assign_positions(entries)

        app_logger.info(f"Leaderboard built: {len(entries)} players")

        # Cache the result
        if use_cache:
            cache_key = self._get_cache_key()
            cache.set(cache_key, entries, timeout=300)  # Cache for 5 minutes
            app_logger.debug(f"Leaderboard cached for event {self.event_id}")

        return entries

    def _fetch_scores(self) -> List[Dict]:
        """Fetch all scores for the event."""
        return list(
            Score.objects.filter(golf_round__event=self.event_id).values(
                'player__first_name',
                'player__second_name',
                'stableford',
                'golf_round_id',
                'hole_id',
                'shots_taken',
                'hole__golf_course__name',
                'hole__golf_course__tees',
                'golf_round__event__scoring'
            )
        )

    def _group_scores_by_player(self, scores: List[Dict]) -> Dict[str, Dict[int, Dict]]:
        """
        Group scores by player and round.

        Returns:
            Dict[player_name][round_id] -> {total, course, scoring}
        """
        player_rounds = {}

        for score in scores:
            player_name = f"{score['player__first_name']} {score['player__second_name']}"
            round_id = score['golf_round_id']
            course = f"{score['hole__golf_course__name']} - {score['hole__golf_course__tees']}"

            if player_name not in player_rounds:
                player_rounds[player_name] = {}
            if round_id not in player_rounds[player_name]:
                player_rounds[player_name][round_id] = {
                    'total': 0,
                    'course': course,
                    'scoring': score['golf_round__event__scoring']
                }

            player_rounds[player_name][round_id]['total'] += score['stableford'] or 0

        return player_rounds

    def _calculate_entries(
        self,
        player_rounds: Dict[str, Dict[int, Dict]],
        all_scores: List[Dict]
    ) -> List[LeaderboardEntry]:
        """
        Calculate leaderboard entries for all players.

        Args:
            player_rounds: Grouped player round data
            all_scores: All scores (for extracting round numbers)

        Returns:
            List of LeaderboardEntry objects (unsorted)
        """
        entries = []

        # Get all round numbers for consistent display
        all_round_ids = sorted(set(score['golf_round_id'] for score in all_scores))

        for player_name, rounds_dict in player_rounds.items():
            # Extract just round_id -> total mapping for calculator
            round_totals = {rid: data['total'] for rid, data in rounds_dict.items()}

            # Calculate total using scoring calculator
            total_points = self.calculator.calculate_total(round_totals)

            # Get counting rounds
            counting_round_ids = self.calculator.get_counting_rounds(round_totals)

            # Get best round score for highlighting
            best_round_score = max(
                (data['total'] for data in rounds_dict.values()),
                default=0
            )

            # Build rounds list for display
            rounds = []
            for round_id in all_round_ids:
                round_info = rounds_dict.get(round_id)
                if round_info:
                    rounds.append({
                        'num': round_id,
                        'total': round_info['total'],
                        'course': round_info['course'],
                        'is_best': round_info['total'] == best_round_score,
                        'is_counting': round_id in counting_round_ids
                    })
                else:
                    rounds.append({
                        'num': round_id,
                        'total': None,
                        'course': None,
                        'is_best': False,
                        'is_counting': False
                    })

            entries.append(LeaderboardEntry(
                player_name=player_name,
                total_points=total_points,
                rounds=rounds
            ))

        return entries

    def _sort_entries(self, entries: List[LeaderboardEntry]) -> List[LeaderboardEntry]:
        """Sort entries by total points descending."""
        return sorted(entries, key=lambda x: x.total_points, reverse=True)

    def _assign_positions(self, entries: List[LeaderboardEntry]) -> List[LeaderboardEntry]:
        """
        Assign positions to entries, handling ties.

        Players with the same score get the same position.
        """
        if not entries:
            return entries

        current_position = 1
        previous_points = None

        for i, entry in enumerate(entries):
            if previous_points is not None and entry.total_points != previous_points:
                current_position = i + 1

            entry.position = current_position
            previous_points = entry.total_points

        return entries

    def to_dict_format(self, entries: List[LeaderboardEntry]) -> List[Dict]:
        """
        Convert entries to dictionary format for template compatibility.

        This maintains backward compatibility with existing template code.
        """
        return [
            {
                'player': entry.player_name,
                'rounds': entry.rounds,
                'best_3_total': entry.total_points,
                'position': entry.position
            }
            for entry in entries
        ]

    def get_courses_list(self, entries: List[LeaderboardEntry]) -> List[Dict]:
        """
        Extract courses list from leaderboard for display.

        Args:
            entries: List of leaderboard entries

        Returns:
            List of dicts with course info: [{'course': name, 'id': round_id}]
        """
        if not entries or not entries[0].rounds:
            return []

        return [
            {'course': round_data['course'], 'id': round_data['num']}
            for round_data in entries[0].rounds
        ]

    def _get_cache_key(self) -> str:
        """Generate cache key for this leaderboard."""
        return f'leaderboard_event_{self.event_id}'

    @classmethod
    def invalidate_cache(cls, event_id: int) -> None:
        """
        Invalidate cached leaderboard for an event.

        Call this when scores are added or modified.

        Args:
            event_id: ID of the GolfEvent to invalidate
        """
        cache_key = f'leaderboard_event_{event_id}'
        cache.delete(cache_key)
        app_logger.info(f"Leaderboard cache invalidated for event {event_id}")


class DateCourseLeaderboardBuilder(LeaderboardBuilder):
    """
    Extended leaderboard builder for Home view which groups by (date, course).

    The Home view has a special requirement: it groups rounds at the same
    course on the same day together, using (date, course) as the key instead
    of just round_id.
    """

    def __init__(self, event_id: int):
        """Initialize with DateCourseScoringCalculator."""
        super().__init__(event_id)
        self.calculator = DateCourseScoringCalculator(self.event.scoring)

    def _fetch_scores(self) -> List[Dict]:
        """Fetch scores with date information."""
        return list(
            Score.objects.filter(golf_round__event=self.event_id).values(
                'player__first_name',
                'player__second_name',
                'stableford',
                'golf_round_id',
                'hole_id',
                'shots_taken',
                'hole__golf_course__name',
                'hole__golf_course__tees',
                'golf_round__event__scoring',
                'golf_round__date_started'  # Additional field for date grouping
            )
        )

    def _group_scores_by_player(self, scores: List[Dict]) -> Dict[str, Dict[Tuple, Dict]]:
        """
        Group scores by player and (date, course) key.

        Returns:
            Dict[player_name][(date, course)] -> {total, course, date, round_ids, scoring}
        """
        player_rounds = {}

        for score in scores:
            player_name = f"{score['player__first_name']} {score['player__second_name']}"
            round_id = score['golf_round_id']
            round_date = score['golf_round__date_started']
            course = f"{score['hole__golf_course__name']} - {score['hole__golf_course__tees']}"

            # Create (date, course) key
            date_course_key = (round_date, course)

            if player_name not in player_rounds:
                player_rounds[player_name] = {}
            if date_course_key not in player_rounds[player_name]:
                player_rounds[player_name][date_course_key] = {
                    'total': 0,
                    'course': course,
                    'date': round_date,
                    'round_ids': set(),
                    'scoring': score['golf_round__event__scoring']
                }

            player_rounds[player_name][date_course_key]['total'] += score['stableford'] or 0
            player_rounds[player_name][date_course_key]['round_ids'].add(round_id)

        return player_rounds

    def _calculate_entries(
        self,
        player_rounds: Dict[str, Dict[Tuple, Dict]],
        all_scores: List[Dict]
    ) -> List[LeaderboardEntry]:
        """
        Calculate entries using (date, course) grouping.
        """
        entries = []

        # Get all (date, course) keys
        all_date_course_keys = set()
        for rounds_dict in player_rounds.values():
            all_date_course_keys.update(rounds_dict.keys())

        # Sort by date then by minimum round ID (chronological order)
        # Need to get the min round_id for each (date, course) key
        key_to_min_round_id = {}
        for rounds_dict in player_rounds.values():
            for key, data in rounds_dict.items():
                if key not in key_to_min_round_id:
                    key_to_min_round_id[key] = min(data['round_ids']) if data['round_ids'] else float('inf')
                else:
                    # Update if we find a lower round ID
                    current_min = min(data['round_ids']) if data['round_ids'] else float('inf')
                    key_to_min_round_id[key] = min(key_to_min_round_id[key], current_min)

        # Sort by (date, min_round_id) for chronological order
        sorted_keys = sorted(all_date_course_keys, key=lambda x: (x[0], key_to_min_round_id.get(x, float('inf'))))

        for player_name, rounds_dict in player_rounds.items():
            # Extract (date, course) -> total mapping
            date_course_totals = {key: data['total'] for key, data in rounds_dict.items()}

            # Calculate total using date/course calculator
            total_points = self.calculator.calculate_total_by_date_course(date_course_totals)

            # Get counting date/course keys
            counting_keys = self.calculator.get_counting_date_courses(date_course_totals)

            # Get best round score
            best_round_score = max(
                (data['total'] for data in rounds_dict.values()),
                default=0
            )

            # Build rounds list
            rounds = []
            for date_course_key in sorted_keys:
                round_info = rounds_dict.get(date_course_key)
                if round_info:
                    # Get first round_id from set for linking
                    first_round_id = min(round_info['round_ids']) if round_info['round_ids'] else None
                    rounds.append({
                        'key': date_course_key,
                        'num': first_round_id,
                        'total': round_info['total'],
                        'course': round_info['course'],
                        'date': round_info['date'],
                        'is_best': round_info['total'] == best_round_score,
                        'is_counting': date_course_key in counting_keys
                    })
                else:
                    rounds.append({
                        'key': date_course_key,
                        'num': None,
                        'total': None,
                        'course': date_course_key[1],
                        'date': date_course_key[0],
                        'is_best': False,
                        'is_counting': False
                    })

            entries.append(LeaderboardEntry(
                player_name=player_name,
                total_points=total_points,
                rounds=rounds
            ))

        return entries

    def get_courses_list(self, entries: List[LeaderboardEntry]) -> List[Dict]:
        """
        Extract courses list with date information.

        Overrides base class to include date information.
        """
        if not entries or not entries[0].rounds:
            return []

        return [
            {
                'course': round_data['course'],
                'id': round_data['num'],
                'date': round_data.get('date')
            }
            for round_data in entries[0].rounds
        ]
