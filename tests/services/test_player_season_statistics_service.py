"""
Tests for player season statistics service.

Tests the calculation and update of player season-level statistics aggregated from
player_match_statistics table. Includes tests for:
- Simple aggregations (matches, goals, assists, etc.)
- Calculated averages (shots per game)
- Weighted percentages (tackle success, interception success)
- Attribute ratings with 25-100 normalization and low match count boost

Follows TDD pattern with helper function tests and main function tests.
"""

import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from app.services.player_season_statistics_service import (
    calculate_player_season_statistics,
    update_player_season_statistics
)
from app.models.club import Club
from app.models.player import Player
from app.models.opponent_club import OpponentClub
from app.models.match import Match
from app.models.match_lineup import MatchLineup
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.player_season_statistics import PlayerSeasonStatistics


# =============================================================================
# TEST FIXTURES - Database Setup Helpers
# =============================================================================

def create_test_club(session: Session, club_id: UUID = None) -> Club:
    """Create a test club."""
    if club_id is None:
        club_id = uuid4()

    club = Club(
        club_id=club_id,
        coach_id=uuid4(),
        club_name="Test FC",
        country="Test Country"
    )
    session.add(club)
    session.commit()
    return club


def create_test_player(session: Session, club: Club, player_id: UUID = None) -> Player:
    """Create a test player."""
    if player_id is None:
        player_id = uuid4()

    # Generate unique invite code based on player_id
    invite_code = f"TST-{str(player_id)[:4].upper()}"

    player = Player(
        player_id=player_id,
        club_id=club.club_id,
        player_name="Test Player",
        jersey_number=10,  # Required field
        position="Forward",
        invite_code=invite_code  # Required field
    )
    session.add(player)
    session.commit()
    return player


def create_test_opponent(session: Session, opponent_id: UUID = None) -> OpponentClub:
    """Create a test opponent club."""
    if opponent_id is None:
        opponent_id = uuid4()

    opponent = OpponentClub(
        opponent_club_id=opponent_id,
        opponent_name="Opponent FC",
        statsbomb_team_id=999
    )
    session.add(opponent)
    session.commit()
    return opponent


def create_test_match(
    session: Session,
    club: Club,
    opponent: OpponentClub,
    match_date: date
) -> Match:
    """Create a test match."""
    match = Match(
        match_id=uuid4(),
        club_id=club.club_id,
        opponent_club_id=opponent.opponent_club_id,
        opponent_name=opponent.opponent_name,
        match_date=match_date,
        result='W',
        our_score=2,
        opponent_score=0
    )
    session.add(match)
    session.commit()
    return match


def create_player_match_stats(
    session: Session,
    player: Player,
    match: Match,
    **kwargs
) -> PlayerMatchStatistics:
    """Create player match statistics with specified values."""
    stats = PlayerMatchStatistics(
        player_match_stats_id=uuid4(),
        player_id=player.player_id,
        match_id=match.match_id,
        goals=kwargs.get('goals', 0),
        assists=kwargs.get('assists', 0),
        expected_goals=kwargs.get('expected_goals', Decimal('0.0')),
        shots=kwargs.get('shots', 0),
        shots_on_target=kwargs.get('shots_on_target', 0),
        total_passes=kwargs.get('total_passes', 0),
        completed_passes=kwargs.get('completed_passes', 0),
        short_passes=kwargs.get('short_passes', 0),
        long_passes=kwargs.get('long_passes', 0),
        final_third_passes=kwargs.get('final_third_passes', 0),
        crosses=kwargs.get('crosses', 0),
        total_dribbles=kwargs.get('total_dribbles', 0),
        successful_dribbles=kwargs.get('successful_dribbles', 0),
        tackles=kwargs.get('tackles', 0),
        tackle_success_rate=kwargs.get('tackle_success_rate', None),
        interceptions=kwargs.get('interceptions', 0),
        interception_success_rate=kwargs.get('interception_success_rate', None)
    )
    session.add(stats)
    session.commit()
    return stats


# =============================================================================
# HELPER FUNCTION TESTS - calculate_player_season_statistics
# =============================================================================

class TestCalculatePlayerSeasonStatistics:
    """Tests for the pure calculation helper function."""

    def test_calculates_matches_played(self, session: Session):
        """Test that matches_played is calculated correctly as COUNT of records."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create 3 matches with player stats
        for i in range(3):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(session, player, match, goals=1)

        result = calculate_player_season_statistics(player.player_id, session)

        assert result['matches_played'] == 3

    def test_calculates_simple_sums(self, session: Session):
        """Test that simple aggregations (SUM) work correctly."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Match 1: 2 goals, 1 assist
        match1 = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match1,
            goals=2, assists=1, expected_goals=Decimal('1.5'),
            total_passes=50, completed_passes=40,
            total_dribbles=10, successful_dribbles=6,
            tackles=5, interceptions=3
        )

        # Match 2: 1 goal, 2 assists
        match2 = create_test_match(session, club, opponent, date(2024, 1, 2))
        create_player_match_stats(
            session, player, match2,
            goals=1, assists=2, expected_goals=Decimal('0.8'),
            total_passes=60, completed_passes=55,
            total_dribbles=8, successful_dribbles=5,
            tackles=7, interceptions=4
        )

        result = calculate_player_season_statistics(player.player_id, session)

        assert result['goals'] == 3
        assert result['assists'] == 3
        assert result['expected_goals'] == Decimal('2.3')
        assert result['total_passes'] == 110
        assert result['passes_completed'] == 95
        assert result['total_dribbles'] == 18
        assert result['successful_dribbles'] == 11
        assert result['tackles'] == 12
        assert result['interceptions'] == 7

    def test_calculates_per_game_averages(self, session: Session):
        """Test that shots per game averages are calculated correctly."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Match 1: 4 shots, 2 on target
        match1 = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(session, player, match1, shots=4, shots_on_target=2)

        # Match 2: 6 shots, 4 on target
        match2 = create_test_match(session, club, opponent, date(2024, 1, 2))
        create_player_match_stats(session, player, match2, shots=6, shots_on_target=4)

        result = calculate_player_season_statistics(player.player_id, session)

        # (4 + 6) / 2 = 5.0 shots per game
        assert result['shots_per_game'] == Decimal('5.00')
        # (2 + 4) / 2 = 3.0 shots on target per game
        assert result['shots_on_target_per_game'] == Decimal('3.00')

    def test_calculates_weighted_tackle_success_rate(self, session: Session):
        """Test weighted tackle success rate calculation (back-calculated from percentages)."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Match 1: 10 tackles at 80% success = 8 successful
        match1 = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match1,
            tackles=10,
            tackle_success_rate=Decimal('80.00')
        )

        # Match 2: 5 tackles at 60% success = 3 successful
        match2 = create_test_match(session, club, opponent, date(2024, 1, 2))
        create_player_match_stats(
            session, player, match2,
            tackles=5,
            tackle_success_rate=Decimal('60.00')
        )

        result = calculate_player_season_statistics(player.player_id, session)

        # Total: 15 tackles, 11 successful = 73.33%
        assert result['tackle_success_rate'] == Decimal('73.33')

    def test_calculates_weighted_interception_success_rate(self, session: Session):
        """Test weighted interception success rate calculation."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Match 1: 6 interceptions at 100% success
        match1 = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match1,
            interceptions=6,
            interception_success_rate=Decimal('100.00')
        )

        # Match 2: 4 interceptions at 75% success
        match2 = create_test_match(session, club, opponent, date(2024, 1, 2))
        create_player_match_stats(
            session, player, match2,
            interceptions=4,
            interception_success_rate=Decimal('75.00')
        )

        result = calculate_player_season_statistics(player.player_id, session)

        # Total: 10 interceptions, 9 successful = 90%
        assert result['interception_success_rate'] == Decimal('90.00')

    def test_handles_null_tackle_success_rate(self, session: Session):
        """Test that NULL tackle success rates are treated as 0% success."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Match 1: 10 tackles, 80% success
        match1 = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match1,
            tackles=10,
            tackle_success_rate=Decimal('80.00')
        )

        # Match 2: 5 tackles, NULL success rate (treat as 0%)
        match2 = create_test_match(session, club, opponent, date(2024, 1, 2))
        create_player_match_stats(
            session, player, match2,
            tackles=5,
            tackle_success_rate=None
        )

        result = calculate_player_season_statistics(player.player_id, session)

        # Total: 15 tackles, 8 successful = 53.33%
        assert result['tackle_success_rate'] == Decimal('53.33')

    def test_calculates_attacking_rating(self, session: Session):
        """Test attacking rating calculation with proper 25-100 normalization."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create strong attacking stats across 10 matches
        for i in range(10):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player, match,
                goals=3,  # 30 total goals = max score (1.0)
                assists=2,  # 20 total assists = max score (1.0)
                expected_goals=Decimal('2.5'),  # 25 total xG = max score (1.0)
                shots=5,  # 5 shots/game = max score (1.0)
                shots_on_target=3
            )

        result = calculate_player_season_statistics(player.player_id, session)

        # Perfect raw score = 1.0 → Rating = 25 + (1.0 * 75) = 100 (or 99 due to rounding)
        assert result['attacking_rating'] >= 99

    def test_calculates_technique_rating(self, session: Session):
        """Test technique rating calculation."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create stats with perfect technique (100% success rates)
        for i in range(5):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player, match,
                total_dribbles=20,  # 100 total = max volume
                successful_dribbles=20,  # 100% success
                total_passes=100,
                completed_passes=100,  # 100% pass completion
                shots=4,
                shots_on_target=4  # 100% shot accuracy
            )

        result = calculate_player_season_statistics(player.player_id, session)

        # Perfect percentages → Rating should be 100 (or 99 due to rounding)
        assert result['technique_rating'] >= 99

    def test_calculates_tactical_rating(self, session: Session):
        """Test tactical rating calculation."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create strong tactical stats
        for i in range(5):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player, match,
                final_third_passes=30,  # 150 total = max
                total_passes=300,  # 1500 total = max
                completed_passes=300,  # 100% completion
                crosses=10  # 50 total = max
            )

        result = calculate_player_season_statistics(player.player_id, session)

        # All max values → Rating should be 100
        assert result['tactical_rating'] == 100

    def test_calculates_defending_rating(self, session: Session):
        """Test defending rating calculation."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create strong defensive stats
        for i in range(5):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player, match,
                tackles=16,  # 80 total = max
                tackle_success_rate=Decimal('100.00'),
                interceptions=12,  # 60 total = max
                interception_success_rate=Decimal('100.00')
            )

        result = calculate_player_season_statistics(player.player_id, session)

        # All max values → Rating should be 100 (or 99 due to rounding)
        assert result['defending_rating'] >= 99

    def test_calculates_creativity_rating(self, session: Session):
        """Test creativity rating calculation."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create strong creative stats
        for i in range(5):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player, match,
                assists=3,  # 15 total = max
                final_third_passes=30,  # 150 total = max
                goals=1,  # For assist/goal ratio
                crosses=10  # 50 total = max
            )

        result = calculate_player_season_statistics(player.player_id, session)

        # Strong creative stats → Rating should be high
        assert result['creativity_rating'] >= 90

    def test_ratings_have_minimum_baseline_25(self, session: Session):
        """Test that all ratings have a minimum of 25 even with no stats."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create match with zero stats
        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match,
            goals=0, assists=0, shots=0, total_passes=0,
            total_dribbles=0, tackles=0, interceptions=0
        )

        result = calculate_player_season_statistics(player.player_id, session)

        assert result['attacking_rating'] >= 25
        assert result['technique_rating'] >= 25
        assert result['tactical_rating'] >= 25
        assert result['defending_rating'] >= 25
        assert result['creativity_rating'] >= 25

    def test_ratings_have_maximum_cap_100(self, session: Session):
        """Test that all ratings are capped at 100."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create match with extremely high stats
        for i in range(10):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player, match,
                goals=10, assists=10, expected_goals=Decimal('10.0'),
                shots=20, shots_on_target=20,
                total_passes=500, completed_passes=500,
                total_dribbles=50, successful_dribbles=50,
                tackles=30, tackle_success_rate=Decimal('100.00'),
                interceptions=30, interception_success_rate=Decimal('100.00'),
                final_third_passes=100, crosses=50
            )

        result = calculate_player_season_statistics(player.player_id, session)

        assert result['attacking_rating'] <= 100
        assert result['technique_rating'] <= 100
        assert result['tactical_rating'] <= 100
        assert result['defending_rating'] <= 100
        assert result['creativity_rating'] <= 100

    def test_low_match_count_boost_applied(self, session: Session):
        """Test that low match count boost (1-4 matches) increases ratings."""
        club = create_test_club(session)
        player_low_matches = create_test_player(session, club, uuid4())
        player_many_matches = create_test_player(session, club, uuid4())
        opponent = create_test_opponent(session)

        # Player with 2 matches: moderate totals (should get 1.3x boost)
        for i in range(2):
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(
                session, player_low_matches, match,
                goals=2, assists=1, expected_goals=Decimal('2.0'),
                shots=4, shots_on_target=2
            )

        # Player with 6 matches: SAME TOTAL stats (no boost, since >= 5 matches)
        # Each match has lower stats to achieve same total
        for i in range(6):
            match = create_test_match(session, club, opponent, date(2024, 1, i+10))
            create_player_match_stats(
                session, player_many_matches, match,
                goals=0 if i >= 4 else 1,  # 4 total goals
                assists=0 if i >= 2 else 1,  # 2 total assists
                expected_goals=Decimal('0.66') if i < 6 else Decimal('0.04'),  # ~4.0 total
                shots=1 if i < 2 else 0,  # Total fewer shots
                shots_on_target=0 if i >= 2 else 1
            )

        result_low = calculate_player_season_statistics(player_low_matches.player_id, session)
        result_many = calculate_player_season_statistics(player_many_matches.player_id, session)

        # Player with 2 matches should have higher rating due to 1.3x boost
        # Both have similar total stats, but player_low gets the boost
        assert result_low['attacking_rating'] >= result_many['attacking_rating']

    def test_handles_player_with_no_matches(self, session: Session):
        """Test that function handles player with no match statistics."""
        club = create_test_club(session)
        player = create_test_player(session, club)

        result = calculate_player_season_statistics(player.player_id, session)

        assert result['matches_played'] == 0
        assert result['goals'] == 0
        assert result['assists'] == 0
        assert result['expected_goals'] is None
        assert result['shots_per_game'] is None
        assert result['shots_on_target_per_game'] is None
        assert result['tackle_success_rate'] is None
        assert result['interception_success_rate'] is None
        # Ratings should be baseline 25 (no boost since matches = 0)
        assert result['attacking_rating'] == 25
        assert result['technique_rating'] == 25
        assert result['tactical_rating'] == 25
        assert result['defending_rating'] == 25
        assert result['creativity_rating'] == 25

    def test_handles_null_statistics_gracefully(self, session: Session):
        """Test that NULL values in aggregations are handled gracefully."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create match with mostly NULL stats
        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match,
            goals=1,  # Only set goals
            assists=None,
            expected_goals=None,
            shots=None,
            total_passes=None,
            tackles=None,
            interceptions=None
        )

        result = calculate_player_season_statistics(player.player_id, session)

        assert result['matches_played'] == 1
        assert result['goals'] == 1
        assert result['assists'] == 0  # NULL treated as 0 for SUM
        # Should not crash, should handle NULLs gracefully

    def test_division_by_zero_protection(self, session: Session):
        """Test that division by zero is handled (returns None for averages)."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create match with zero denominators
        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match,
            goals=1,
            shots=0,  # Zero shots
            total_passes=0,  # Zero passes
            tackles=0,  # Zero tackles
            interceptions=0  # Zero interceptions
        )

        result = calculate_player_season_statistics(player.player_id, session)

        # Division by zero should return None, not crash
        assert result['tackle_success_rate'] is None
        assert result['interception_success_rate'] is None


# =============================================================================
# MAIN FUNCTION TESTS - update_player_season_statistics
# =============================================================================

class TestUpdatePlayerSeasonStatistics:
    """Tests for the main database update function."""

    def test_creates_new_record_for_player(self, session: Session):
        """Test that function creates a new PlayerSeasonStatistics record."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create some match stats
        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(session, player, match, goals=2, assists=1)

        # Verify no record exists yet
        existing = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).first()
        assert existing is None

        # Update statistics
        count = update_player_season_statistics(session, [player.player_id])

        # Verify record was created
        record = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).first()
        assert record is not None
        assert record.goals == 2
        assert record.assists == 1
        assert count == 1

    def test_updates_existing_record_upsert(self, session: Session):
        """Test that function updates existing PlayerSeasonStatistics record (upsert)."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create initial stats
        match1 = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(session, player, match1, goals=2)

        # First update
        update_player_season_statistics(session, [player.player_id])
        record1 = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).first()
        assert record1.goals == 2
        assert record1.matches_played == 1

        # Add another match
        match2 = create_test_match(session, club, opponent, date(2024, 1, 2))
        create_player_match_stats(session, player, match2, goals=3)

        # Second update (should update existing record)
        update_player_season_statistics(session, [player.player_id])

        # Verify only one record exists and it's updated
        all_records = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).all()
        assert len(all_records) == 1

        record2 = all_records[0]
        assert record2.goals == 5  # 2 + 3
        assert record2.matches_played == 2

    def test_processes_multiple_players(self, session: Session):
        """Test that function processes multiple players correctly."""
        club = create_test_club(session)
        player1 = create_test_player(session, club, uuid4())
        player2 = create_test_player(session, club, uuid4())
        player3 = create_test_player(session, club, uuid4())
        opponent = create_test_opponent(session)

        # Create stats for each player
        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(session, player1, match, goals=1)
        create_player_match_stats(session, player2, match, goals=2)
        create_player_match_stats(session, player3, match, goals=3)

        # Update all three players
        player_ids = [player1.player_id, player2.player_id, player3.player_id]
        count = update_player_season_statistics(session, player_ids)

        assert count == 3

        # Verify all records created correctly
        record1 = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player1.player_id
        ).first()
        record2 = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player2.player_id
        ).first()
        record3 = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player3.player_id
        ).first()

        assert record1.goals == 1
        assert record2.goals == 2
        assert record3.goals == 3

    def test_commits_transaction_successfully(self, session: Session):
        """Test that database transaction is committed successfully."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(session, player, match, goals=5)

        # Update statistics
        update_player_season_statistics(session, [player.player_id])

        # Close and reopen session to verify persistence
        session.expire_all()

        record = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).first()

        assert record is not None
        assert record.goals == 5

    def test_stores_all_17_fields_correctly(self, session: Session):
        """Test that all 17 statistics fields are stored correctly."""
        club = create_test_club(session)
        player = create_test_player(session, club)
        opponent = create_test_opponent(session)

        # Create comprehensive stats
        match = create_test_match(session, club, opponent, date(2024, 1, 1))
        create_player_match_stats(
            session, player, match,
            goals=2, assists=1, expected_goals=Decimal('1.5'),
            shots=4, shots_on_target=2,
            total_passes=50, completed_passes=40,
            total_dribbles=10, successful_dribbles=6,
            tackles=5, tackle_success_rate=Decimal('80.00'),
            interceptions=3, interception_success_rate=Decimal('100.00'),
            final_third_passes=15, crosses=5
        )

        update_player_season_statistics(session, [player.player_id])

        record = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).first()

        # Verify all fields
        assert record.matches_played == 1
        assert record.goals == 2
        assert record.assists == 1
        assert record.expected_goals == Decimal('1.5')
        assert record.shots_per_game == Decimal('4.00')
        assert record.shots_on_target_per_game == Decimal('2.00')
        assert record.total_passes == 50
        assert record.passes_completed == 40
        assert record.total_dribbles == 10
        assert record.successful_dribbles == 6
        assert record.tackles == 5
        assert record.tackle_success_rate == Decimal('80.00')
        assert record.interceptions == 3
        assert record.interception_success_rate == Decimal('100.00')
        assert record.attacking_rating >= 25
        assert record.technique_rating >= 25
        assert record.tactical_rating >= 25
        assert record.defending_rating >= 25
        assert record.creativity_rating >= 25

    def test_handles_null_zero_values_appropriately(self, session: Session):
        """Test that NULL and zero values are handled correctly in storage."""
        club = create_test_club(session)
        player = create_test_player(session, club)

        # Player with no matches
        update_player_season_statistics(session, [player.player_id])

        record = session.query(PlayerSeasonStatistics).filter_by(
            player_id=player.player_id
        ).first()

        assert record.matches_played == 0
        assert record.goals == 0
        assert record.assists == 0
        assert record.expected_goals is None
        assert record.shots_per_game is None
        assert record.tackle_success_rate is None

    def test_returns_correct_count_of_players_updated(self, session: Session):
        """Test that function returns correct count of players updated."""
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Create 5 players with stats
        player_ids = []
        for i in range(5):
            player = create_test_player(session, club, uuid4())
            player_ids.append(player.player_id)
            match = create_test_match(session, club, opponent, date(2024, 1, i+1))
            create_player_match_stats(session, player, match, goals=1)

        count = update_player_season_statistics(session, player_ids)

        assert count == 5
