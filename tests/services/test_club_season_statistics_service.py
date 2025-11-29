"""
Tests for club season statistics service.

Tests the calculation and update of club season-level statistics aggregated from matches,
goals, match_statistics, and player_match_statistics tables.
Follows TDD pattern with helper function tests and main function tests.
"""

import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.services.club_season_statistics_service import (
    calculate_club_season_statistics,
    update_club_season_statistics
)
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.match import Match
from app.models.goal import Goal
from app.models.match_statistics import MatchStatistics
from app.models.player import Player
from app.models.match_lineup import MatchLineup
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.club_season_statistics import ClubSeasonStatistics


# =============================================================================
# TEST FIXTURES - Database Setup Helpers
# =============================================================================

def create_test_club(session: Session, club_id: UUID = None, statsbomb_team_id: int = None) -> Club:
    """Create a test club for season statistics."""
    if club_id is None:
        club_id = uuid4()

    club = Club(
        club_id=club_id,
        coach_id=uuid4(),  # Required field
        club_name="Test FC",
        statsbomb_team_id=statsbomb_team_id,  # Can be None to avoid uniqueness issues
        country="Test Country"
    )
    session.add(club)
    session.commit()
    return club


def create_test_opponent(session: Session, opponent_id: UUID = None, statsbomb_id: int = 218) -> OpponentClub:
    """Create a test opponent club."""
    if opponent_id is None:
        opponent_id = uuid4()

    opponent = OpponentClub(
        opponent_club_id=opponent_id,
        opponent_name="Opponent FC",
        statsbomb_team_id=statsbomb_id
    )
    session.add(opponent)
    session.commit()
    return opponent


def create_test_match(
    session: Session,
    club: Club,
    opponent: OpponentClub,
    match_date: date,
    result: str,  # 'W', 'D', 'L'
    our_score: int,
    opponent_score: int
) -> Match:
    """Create a test match with specified result and score."""
    match = Match(
        match_id=uuid4(),
        club_id=club.club_id,
        opponent_club_id=opponent.opponent_club_id,
        opponent_name=opponent.opponent_name,  # Required field
        match_date=match_date,
        result=result,
        our_score=our_score,
        opponent_score=opponent_score
    )
    session.add(match)
    session.commit()
    return match


def create_test_goals(
    session: Session,
    match: Match,
    our_goals: int,
    opponent_goals: int
):
    """Create goal records for a match."""
    # Our goals
    for i in range(our_goals):
        goal = Goal(
            goal_id=uuid4(),
            match_id=match.match_id,
            is_our_goal=True,
            scorer_name=f"Player {i+1}",
            minute=10 + (i * 10)
        )
        session.add(goal)

    # Opponent goals
    for i in range(opponent_goals):
        goal = Goal(
            goal_id=uuid4(),
            match_id=match.match_id,
            is_our_goal=False,
            scorer_name=f"Opponent {i+1}",
            minute=15 + (i * 10)
        )
        session.add(goal)

    session.commit()


def create_test_match_statistics(
    session: Session,
    match: Match,
    team_type: str = 'our_team',
    possession_percentage: Decimal = Decimal('55.00'),
    total_passes: int = 500,
    passes_completed: int = 400,
    total_shots: int = 15,
    shots_on_target: int = 8,
    expected_goals: Decimal = Decimal('1.500000'),
    passes_in_final_third: int = 150,
    crosses: int = 20,
    total_dribbles: int = 30,
    successful_dribbles: int = 20,
    total_tackles: int = 25,
    tackle_success_percentage: Decimal = Decimal('80.00'),
    interceptions: int = 15,
    ball_recoveries: int = 40,
    goalkeeper_saves: int = 5
) -> MatchStatistics:
    """Create test match statistics."""
    stats = MatchStatistics(
        match_id=match.match_id,
        team_type=team_type,
        possession_percentage=possession_percentage,
        total_passes=total_passes,
        passes_completed=passes_completed,
        pass_completion_rate=Decimal('80.00') if total_passes > 0 else None,
        total_shots=total_shots,
        shots_on_target=shots_on_target,
        shots_off_target=total_shots - shots_on_target if total_shots else 0,
        expected_goals=expected_goals,
        passes_in_final_third=passes_in_final_third,
        long_passes=50,
        crosses=crosses,
        total_dribbles=total_dribbles,
        successful_dribbles=successful_dribbles,
        total_tackles=total_tackles,
        tackle_success_percentage=tackle_success_percentage,
        interceptions=interceptions,
        ball_recoveries=ball_recoveries,
        goalkeeper_saves=goalkeeper_saves
    )
    session.add(stats)
    session.commit()
    return stats


def create_test_player(session: Session, statsbomb_id: int = 5503, club_id: UUID = None) -> Player:
    """Create a test player."""
    if club_id is None:
        # Create a club for the player
        club = create_test_club(session)
        club_id = club.club_id

    player = Player(
        player_id=uuid4(),
        club_id=club_id,
        player_name="Test Player",
        statsbomb_player_id=statsbomb_id,
        jersey_number=10,
        position="Forward",
        invite_code=f"TST-{statsbomb_id}"
    )
    session.add(player)
    session.commit()
    return player


def create_test_player_match_statistics(
    session: Session,
    match: Match,
    player: Player,
    assists: int = 0,
    interceptions: int = 0,
    interception_success_rate: Decimal = None
) -> PlayerMatchStatistics:
    """Create test player match statistics."""
    stats = PlayerMatchStatistics(
        match_id=match.match_id,
        player_id=player.player_id,
        goals=0,
        assists=assists,
        shots=5,
        shots_on_target=3,
        expected_goals=Decimal('0.500000'),
        completed_passes=50,
        total_passes=60,
        crosses=3,
        total_dribbles=5,
        successful_dribbles=3,
        tackles=4,
        interceptions=interceptions,
        interception_success_rate=interception_success_rate
    )
    session.add(stats)
    session.commit()
    return stats


# =============================================================================
# TEST CLASS: calculate_club_season_statistics() - Helper Function
# =============================================================================

class TestCalculateClubSeasonStatistics:
    """Tests for the calculate_club_season_statistics helper function."""

    def test_calculates_basic_counts_correctly(self, session: Session):
        """Test that basic count statistics are calculated correctly."""
        # Setup: Create club with 5 matches (3W, 1D, 1L)
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        base_date = date(2024, 1, 1)

        # 3 wins
        for i in range(3):
            match = create_test_match(
                session, club, opponent,
                match_date=base_date + timedelta(days=i*7),
                result='W', our_score=2, opponent_score=0
            )

        # 1 draw
        match = create_test_match(
            session, club, opponent,
            match_date=base_date + timedelta(days=21),
            result='D', our_score=1, opponent_score=1
        )

        # 1 loss
        match = create_test_match(
            session, club, opponent,
            match_date=base_date + timedelta(days=28),
            result='L', our_score=0, opponent_score=2
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        assert result['matches_played'] == 5
        assert result['wins'] == 3
        assert result['draws'] == 1
        assert result['losses'] == 1

    def test_calculates_goals_scored_and_conceded_correctly(self, session: Session):
        """Test that goals scored and conceded are calculated correctly from goals table."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Match 1: Win 3-1
        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=3, opponent_score=1
        )
        create_test_goals(session, match1, our_goals=3, opponent_goals=1)

        # Match 2: Draw 2-2
        match2 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='D', our_score=2, opponent_score=2
        )
        create_test_goals(session, match2, our_goals=2, opponent_goals=2)

        # Match 3: Loss 0-1
        match3 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 15),
            result='L', our_score=0, opponent_score=1
        )
        create_test_goals(session, match3, our_goals=0, opponent_goals=1)

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        assert result['goals_scored'] == 5  # 3 + 2 + 0
        assert result['goals_conceded'] == 4  # 1 + 2 + 1

    def test_calculates_total_assists_correctly(self, session: Session):
        """Test that total assists are aggregated from player_match_statistics."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=2, opponent_score=0
        )

        match2 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='W', our_score=3, opponent_score=1
        )

        # Create players with assists
        player1 = create_test_player(session, statsbomb_id=5503)
        player2 = create_test_player(session, statsbomb_id=5504)
        player3 = create_test_player(session, statsbomb_id=5505)

        # Match 1: Player1 (2 assists), Player2 (1 assist)
        create_test_player_match_statistics(session, match1, player1, assists=2)
        create_test_player_match_statistics(session, match1, player2, assists=1)

        # Match 2: Player1 (1 assist), Player3 (2 assists)
        create_test_player_match_statistics(session, match2, player1, assists=1)
        create_test_player_match_statistics(session, match2, player3, assists=2)

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        assert result['total_assists'] == 6  # 2 + 1 + 1 + 2

    def test_calculates_total_clean_sheets_correctly(self, session: Session):
        """Test that clean sheets are counted correctly (opponent_score = 0)."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # 2 clean sheets
        create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=2, opponent_score=0
        )
        create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='W', our_score=1, opponent_score=0
        )

        # Not a clean sheet
        create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 15),
            result='W', our_score=3, opponent_score=1
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        assert result['total_clean_sheets'] == 2

    def test_calculates_team_form_correctly(self, session: Session):
        """Test that team_form shows last 5 matches with most recent on LEFT."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Create 7 matches in chronological order (oldest to newest)
        results = ['W', 'W', 'L', 'D', 'W', 'L', 'W']
        base_date = date(2024, 1, 1)

        for i, result in enumerate(results):
            create_test_match(
                session, club, opponent,
                match_date=base_date + timedelta(days=i*7),
                result=result,
                our_score=2 if result == 'W' else (1 if result == 'D' else 0),
                opponent_score=0 if result == 'W' else (1 if result == 'D' else 2)
            )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert - Last 5 matches: L(2), D(3), W(4), L(5), W(6)
        # With most recent on left: W(6), L(5), W(4), D(3), L(2)
        assert result['team_form'] == 'WLWDL'  # Most recent (index 6) on left

    def test_calculates_simple_averages_correctly(self, session: Session):
        """Test that simple averages are calculated correctly from match_statistics."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Match 1
        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=2, opponent_score=0
        )
        create_test_match_statistics(
            session, match1, team_type='our_team',
            possession_percentage=Decimal('60.00'),
            total_shots=20,
            shots_on_target=10,
            expected_goals=Decimal('2.000000'),
            total_passes=600,
            passes_in_final_third=200,
            crosses=25,
            total_dribbles=40,
            successful_dribbles=30,
            total_tackles=20,
            interceptions=18,
            ball_recoveries=50,
            goalkeeper_saves=3
        )

        # Match 2
        match2 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='D', our_score=1, opponent_score=1
        )
        create_test_match_statistics(
            session, match2, team_type='our_team',
            possession_percentage=Decimal('50.00'),
            total_shots=10,
            shots_on_target=6,
            expected_goals=Decimal('1.000000'),
            total_passes=400,
            passes_in_final_third=100,
            crosses=15,
            total_dribbles=20,
            successful_dribbles=10,
            total_tackles=30,
            interceptions=12,
            ball_recoveries=30,
            goalkeeper_saves=7
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        assert result['avg_possession_percentage'] == Decimal('55.00')  # (60+50)/2
        assert result['avg_total_shots'] == Decimal('15.00')  # (20+10)/2
        assert result['avg_shots_on_target'] == Decimal('8.00')  # (10+6)/2
        assert result['avg_xg_per_match'] == Decimal('1.50')  # (2.0+1.0)/2
        assert result['avg_total_passes'] == Decimal('500.00')  # (600+400)/2
        assert result['avg_final_third_passes'] == Decimal('150.00')  # (200+100)/2
        assert result['avg_crosses'] == Decimal('20.00')  # (25+15)/2
        assert result['avg_dribbles'] == Decimal('30.00')  # (40+20)/2
        assert result['avg_successful_dribbles'] == Decimal('20.00')  # (30+10)/2
        assert result['avg_tackles'] == Decimal('25.00')  # (20+30)/2
        assert result['avg_interceptions'] == Decimal('15.00')  # (18+12)/2
        assert result['avg_ball_recoveries'] == Decimal('40.00')  # (50+30)/2
        assert result['avg_saves_per_match'] == Decimal('5.00')  # (3+7)/2

    def test_calculates_weighted_pass_completion_rate_correctly(self, session: Session):
        """Test that pass_completion_rate uses weighted average, not simple average."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Match 1: 10/20 passes = 50% (low volume)
        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=1, opponent_score=0
        )
        create_test_match_statistics(
            session, match1, team_type='our_team',
            total_passes=20,
            passes_completed=10
        )

        # Match 2: 90/100 passes = 90% (high volume)
        match2 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='W', our_score=2, opponent_score=0
        )
        create_test_match_statistics(
            session, match2, team_type='our_team',
            total_passes=100,
            passes_completed=90
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        # Simple average would be: (50 + 90) / 2 = 70% ❌ WRONG
        # Weighted average: (10 + 90) / (20 + 100) = 100/120 = 83.33% ✓ CORRECT
        assert result['pass_completion_rate'] == Decimal('83.33')

    def test_calculates_weighted_tackle_success_rate_correctly(self, session: Session):
        """Test that tackle_success_rate uses weighted average by back-calculating from percentages."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Match 1: 10 tackles at 60% success = 6 successful
        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=1, opponent_score=0
        )
        create_test_match_statistics(
            session, match1, team_type='our_team',
            total_tackles=10,
            tackle_success_percentage=Decimal('60.00')
        )

        # Match 2: 20 tackles at 80% success = 16 successful
        match2 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='W', our_score=2, opponent_score=0
        )
        create_test_match_statistics(
            session, match2, team_type='our_team',
            total_tackles=20,
            tackle_success_percentage=Decimal('80.00')
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        # Simple average would be: (60 + 80) / 2 = 70% ❌ WRONG
        # Weighted: (6 + 16) / (10 + 20) = 22/30 = 73.33% ✓ CORRECT
        assert result['tackle_success_rate'] == Decimal('73.33')

    def test_calculates_weighted_interception_success_rate_from_player_stats(self, session: Session):
        """Test that interception_success_rate is calculated from player_match_statistics."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=1, opponent_score=0
        )

        player1 = create_test_player(session, statsbomb_id=5503)
        player2 = create_test_player(session, statsbomb_id=5504)

        # Player 1: 10 interceptions at 60% = 6 successful
        create_test_player_match_statistics(
            session, match1, player1,
            interceptions=10,
            interception_success_rate=Decimal('60.00')
        )

        # Player 2: 20 interceptions at 80% = 16 successful
        create_test_player_match_statistics(
            session, match1, player2,
            interceptions=20,
            interception_success_rate=Decimal('80.00')
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        # Weighted: (6 + 16) / (10 + 20) = 22/30 = 73.33% ✓ CORRECT
        assert result['interception_success_rate'] == Decimal('73.33')

    def test_calculates_calculated_ratios_correctly(self, session: Session):
        """Test that calculated ratios (goals per match, goals conceded per match) are correct."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # 4 matches total
        matches_data = [
            (date(2024, 1, 1), 'W', 3, 0),
            (date(2024, 1, 8), 'W', 2, 1),
            (date(2024, 1, 15), 'D', 1, 1),
            (date(2024, 1, 22), 'L', 0, 2)
        ]

        for match_date, result, our_score, opp_score in matches_data:
            match = create_test_match(
                session, club, opponent,
                match_date=match_date,
                result=result,
                our_score=our_score,
                opponent_score=opp_score
            )
            create_test_goals(session, match, our_goals=our_score, opponent_goals=opp_score)

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert
        # Total goals scored: 3+2+1+0 = 6, matches: 4 → 6/4 = 1.50
        assert result['avg_goals_per_match'] == Decimal('1.50')
        # Total goals conceded: 0+1+1+2 = 4, matches: 4 → 4/4 = 1.00
        assert result['avg_goals_conceded_per_match'] == Decimal('1.00')

    def test_handles_club_with_no_matches(self, session: Session):
        """Test that function handles club with no matches gracefully."""
        # Setup
        club = create_test_club(session)

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert - All counts should be 0, averages should be None or 0.00
        assert result['matches_played'] == 0
        assert result['wins'] == 0
        assert result['draws'] == 0
        assert result['losses'] == 0
        assert result['goals_scored'] == 0
        assert result['goals_conceded'] == 0
        assert result['total_assists'] == 0
        assert result['total_clean_sheets'] == 0
        assert result['team_form'] == ''
        assert result['avg_goals_per_match'] is None
        assert result['avg_goals_conceded_per_match'] is None

    def test_handles_null_statistics_gracefully(self, session: Session):
        """Test that function handles NULL values in match_statistics."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Match with NULL statistics
        match = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=1, opponent_score=0
        )

        # Create match_statistics with many NULL fields
        stats = MatchStatistics(
            match_id=match.match_id,
            team_type='our_team',
            possession_percentage=None,
            total_passes=None,
            passes_completed=None,
            total_shots=None,
            shots_on_target=None,
            expected_goals=None,
            total_tackles=None,
            tackle_success_percentage=None,
            interceptions=None,
            ball_recoveries=None,
            goalkeeper_saves=None
        )
        session.add(stats)
        session.commit()

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert - Should not crash, should return None or 0 for averages with NULL data
        assert result['matches_played'] == 1
        assert result['avg_possession_percentage'] is None or result['avg_possession_percentage'] == Decimal('0.00')
        assert result['pass_completion_rate'] is None

    def test_division_by_zero_protection(self, session: Session):
        """Test that division by zero is handled properly in weighted averages."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        match = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=1, opponent_score=0
        )

        # Create match_statistics with 0 total_passes (would cause division by zero)
        create_test_match_statistics(
            session, match, team_type='our_team',
            total_passes=0,
            passes_completed=0
        )

        # Act
        result = calculate_club_season_statistics(club.club_id, session)

        # Assert - Should not crash, pass_completion_rate should be None
        assert result['pass_completion_rate'] is None


# =============================================================================
# TEST CLASS: update_club_season_statistics() - Main Function
# =============================================================================

class TestUpdateClubSeasonStatistics:
    """Tests for the update_club_season_statistics main function."""

    def test_creates_new_record_for_club_with_no_existing_statistics(self, session: Session):
        """Test that a new ClubSeasonStatistics record is created when none exists."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        match = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=2, opponent_score=0
        )
        create_test_goals(session, match, our_goals=2, opponent_goals=0)

        # Verify no existing record
        existing = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert existing is None

        # Act
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

        # Verify record was created
        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert stats is not None
        assert stats.matches_played == 1
        assert stats.wins == 1
        assert stats.goals_scored == 2
        assert stats.goals_conceded == 0

    def test_updates_existing_record_when_called_again(self, session: Session):
        """Test that existing ClubSeasonStatistics record is updated, not duplicated."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Create first match and update statistics
        match1 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=2, opponent_score=0
        )
        create_test_goals(session, match1, our_goals=2, opponent_goals=0)

        # First update
        update_club_season_statistics(session, club.club_id)

        # Verify initial state
        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert stats.matches_played == 1
        assert stats.wins == 1

        # Create second match
        match2 = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 8),
            result='D', our_score=1, opponent_score=1
        )
        create_test_goals(session, match2, our_goals=1, opponent_goals=1)

        # Act - Second update
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

        # Verify only ONE record exists (update, not insert)
        all_stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).all()
        assert len(all_stats) == 1

        # Verify record was updated
        updated_stats = all_stats[0]
        assert updated_stats.matches_played == 2
        assert updated_stats.wins == 1
        assert updated_stats.draws == 1
        assert updated_stats.goals_scored == 3
        assert updated_stats.goals_conceded == 1

    def test_stores_all_27_fields_correctly(self, session: Session):
        """Test that all 27 statistics fields are stored in the database."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        # Create match with comprehensive data
        match = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=3, opponent_score=1
        )
        create_test_goals(session, match, our_goals=3, opponent_goals=1)

        # Create match statistics
        create_test_match_statistics(
            session, match, team_type='our_team',
            possession_percentage=Decimal('55.00'),
            total_passes=500,
            passes_completed=400,
            total_shots=15,
            shots_on_target=8,
            expected_goals=Decimal('2.500000'),
            passes_in_final_third=150,
            crosses=20,
            total_dribbles=30,
            successful_dribbles=20,
            total_tackles=25,
            tackle_success_percentage=Decimal('80.00'),
            interceptions=15,
            ball_recoveries=40,
            goalkeeper_saves=5
        )

        # Create player statistics for assists and interceptions
        player = create_test_player(session)
        create_test_player_match_statistics(
            session, match, player,
            assists=2,
            interceptions=10,
            interception_success_rate=Decimal('70.00')
        )

        # Act
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert stats is not None

        # Verify all 27 fields are populated
        assert stats.matches_played == 1
        assert stats.wins == 1
        assert stats.draws == 0
        assert stats.losses == 0
        assert stats.goals_scored == 3
        assert stats.goals_conceded == 1
        assert stats.total_assists == 2
        assert stats.total_clean_sheets == 0
        assert stats.team_form == 'W'
        assert stats.avg_goals_per_match == Decimal('3.00')
        assert stats.avg_goals_conceded_per_match == Decimal('1.00')
        assert stats.avg_possession_percentage == Decimal('55.00')
        assert stats.avg_total_shots == Decimal('15.00')
        assert stats.avg_shots_on_target == Decimal('8.00')
        assert stats.avg_xg_per_match == Decimal('2.50')
        assert stats.avg_total_passes == Decimal('500.00')
        assert stats.avg_final_third_passes == Decimal('150.00')
        assert stats.avg_crosses == Decimal('20.00')
        assert stats.avg_dribbles == Decimal('30.00')
        assert stats.avg_successful_dribbles == Decimal('20.00')
        assert stats.avg_tackles == Decimal('25.00')
        assert stats.avg_interceptions == Decimal('15.00')
        assert stats.avg_ball_recoveries == Decimal('40.00')
        assert stats.avg_saves_per_match == Decimal('5.00')
        assert stats.pass_completion_rate == Decimal('80.00')
        assert stats.tackle_success_rate == Decimal('80.00')
        assert stats.interception_success_rate == Decimal('70.00')

    def test_handles_null_values_appropriately(self, session: Session):
        """Test that NULL values are handled correctly in the database record."""
        # Setup - Club with no matches
        club = create_test_club(session)

        # Act
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert stats is not None
        assert stats.matches_played == 0
        assert stats.team_form == ''
        assert stats.avg_goals_per_match is None
        assert stats.avg_goals_conceded_per_match is None

    def test_commits_transaction_successfully(self, session: Session):
        """Test that the function commits the transaction to the database."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        match = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=2, opponent_score=0
        )
        create_test_goals(session, match, our_goals=2, opponent_goals=0)

        # Act
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

        # Rollback the session to simulate a new session
        session.rollback()

        # Query again - if committed, data should still be there
        # Note: In our test environment with session fixture, this verifies the commit happened
        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        # Since we're using the same session and it was committed, we need to query fresh
        # The fact that we can query it means it was committed
        session.expire_all()
        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert stats is not None

    def test_returns_true_on_success(self, session: Session):
        """Test that the function returns True when successful."""
        # Setup
        club = create_test_club(session)
        opponent = create_test_opponent(session)

        match = create_test_match(
            session, club, opponent,
            match_date=date(2024, 1, 1),
            result='W', our_score=1, opponent_score=0
        )

        # Act
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

    def test_handles_club_with_no_matches(self, session: Session):
        """Test that the function handles a club with no matches without errors."""
        # Setup
        club = create_test_club(session)

        # Act
        result = update_club_season_statistics(session, club.club_id)

        # Assert
        assert result is True

        stats = session.query(ClubSeasonStatistics).filter_by(club_id=club.club_id).first()
        assert stats is not None
        assert stats.matches_played == 0
        assert stats.wins == 0
        assert stats.draws == 0
        assert stats.losses == 0
