"""
Fixtures for coach endpoint testing.

Provides test data for:
- Matches with complete data
- Statistics (club, player, match)
- Goals and lineups
- Training plans with exercises
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from app.models.match import Match
from app.models.opponent_club import OpponentClub
from app.models.match_statistics import MatchStatistics
from app.models.goal import Goal
from app.models.match_lineup import MatchLineup
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.club_season_statistics import ClubSeasonStatistics
from app.models.player_season_statistics import PlayerSeasonStatistics
from app.models.training_plan import TrainingPlan
from app.models.training_exercise import TrainingExercise


@pytest.fixture
def sample_opponent_club(session):
    """Create opponent club for matches."""
    opponent = OpponentClub(
        opponent_name="France",
        statsbomb_team_id=792,
        logo_url="https://example.com/france.png"
    )
    session.add(opponent)
    session.commit()
    session.refresh(opponent)
    return opponent


@pytest.fixture
def sample_match(session, sample_club, sample_opponent_club):
    """Create a complete match record."""
    match = Match(
        club_id=sample_club.club_id,
        opponent_club_id=sample_opponent_club.opponent_club_id,
        opponent_name="France",
        match_date=date(2022, 12, 18),
        our_score=3,
        opponent_score=3,
        result="D"
    )
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


@pytest.fixture
def sample_goals(session, sample_match):
    """Create goals for a match."""
    goals = [
        Goal(
            match_id=sample_match.match_id,
            scorer_name="Kylian Mbappé",
            minute=23,
            second=12,
            is_our_goal=False
        ),
        Goal(
            match_id=sample_match.match_id,
            scorer_name="Lionel Messi",
            minute=63,
            second=45,
            is_our_goal=False
        ),
        Goal(
            match_id=sample_match.match_id,
            scorer_name="Our Player 1",
            minute=45,
            second=30,
            is_our_goal=True
        ),
        Goal(
            match_id=sample_match.match_id,
            scorer_name="Our Player 2",
            minute=78,
            second=15,
            is_our_goal=True
        ),
        Goal(
            match_id=sample_match.match_id,
            scorer_name="Kylian Mbappé",
            minute=90,
            second=5,
            is_our_goal=False
        ),
        Goal(
            match_id=sample_match.match_id,
            scorer_name="Our Player 3",
            minute=92,
            second=20,
            is_our_goal=True
        )
    ]

    for goal in goals:
        session.add(goal)

    session.commit()

    for goal in goals:
        session.refresh(goal)

    return goals


@pytest.fixture
def sample_match_statistics(session, sample_match):
    """Create match statistics for both teams."""
    our_stats = MatchStatistics(
        match_id=sample_match.match_id,
        team_type="our_team",
        possession_percentage=Decimal("52.5"),
        expected_goals=Decimal("2.8"),
        total_shots=18,
        shots_on_target=9,
        shots_off_target=9,
        goalkeeper_saves=8,
        total_passes=542,
        passes_completed=465,
        pass_completion_rate=Decimal("85.8"),
        passes_in_final_third=124,
        long_passes=45,
        crosses=18,
        total_dribbles=32,
        successful_dribbles=22,
        total_tackles=15,
        tackle_success_percentage=Decimal("73.3"),
        interceptions=12,
        ball_recoveries=48
    )

    opp_stats = MatchStatistics(
        match_id=sample_match.match_id,
        team_type="opponent_team",
        possession_percentage=Decimal("47.5"),
        expected_goals=Decimal("3.2"),
        total_shots=22,
        shots_on_target=11,
        shots_off_target=11,
        goalkeeper_saves=6,
        total_passes=489,
        passes_completed=398,
        pass_completion_rate=Decimal("81.4"),
        passes_in_final_third=145,
        long_passes=52,
        crosses=24,
        total_dribbles=45,
        successful_dribbles=31,
        total_tackles=18,
        tackle_success_percentage=Decimal("77.8"),
        interceptions=15,
        ball_recoveries=52
    )

    session.add(our_stats)
    session.add(opp_stats)
    session.commit()
    session.refresh(our_stats)
    session.refresh(opp_stats)

    return {"our_team": our_stats, "opponent_team": opp_stats}


@pytest.fixture
def sample_lineups(session, sample_match, sample_complete_player):
    """Create match lineups for both teams."""
    # Our team lineup
    our_lineup = [
        MatchLineup(
            match_id=sample_match.match_id,
            team_type="our_team",
            player_id=sample_complete_player.player_id,
            opponent_player_id=None,
            player_name=sample_complete_player.player_name,
            jersey_number=sample_complete_player.jersey_number,
            position="Forward"
        )
    ]

    # Add 10 more our team players
    for i in range(2, 12):
        our_lineup.append(
            MatchLineup(
                match_id=sample_match.match_id,
                team_type="our_team",
                player_id=None,
                opponent_player_id=None,
                player_name=f"Our Player {i}",
                jersey_number=i,
                position="Midfielder" if i < 7 else "Defender"
            )
        )

    # Opponent lineup
    opponent_lineup = []
    for i in range(1, 12):
        opponent_lineup.append(
            MatchLineup(
                match_id=sample_match.match_id,
                team_type="opponent_team",
                player_id=None,
                opponent_player_id=None,
                player_name=f"France Player {i}",
                jersey_number=i + 10,
                position="Forward" if i < 4 else "Midfielder"
            )
        )

    for lineup in our_lineup + opponent_lineup:
        session.add(lineup)

    session.commit()

    for lineup in our_lineup + opponent_lineup:
        session.refresh(lineup)

    return {"our_team": our_lineup, "opponent_team": opponent_lineup}


@pytest.fixture
def sample_player_match_statistics(session, sample_complete_player, sample_match):
    """Create player match statistics."""
    stats = PlayerMatchStatistics(
        player_id=sample_complete_player.player_id,
        match_id=sample_match.match_id,
        goals=2,
        assists=1,
        expected_goals=Decimal("1.8"),
        shots=6,
        shots_on_target=4,
        total_dribbles=8,
        successful_dribbles=6,
        total_passes=52,
        completed_passes=45,
        short_passes=38,
        long_passes=14,
        final_third_passes=18,
        crosses=4,
        tackles=3,
        tackle_success_rate=Decimal("66.7"),
        interceptions=2,
        interception_success_rate=Decimal("100.0")
    )

    session.add(stats)
    session.commit()
    session.refresh(stats)
    return stats


@pytest.fixture
def sample_club_season_statistics(session, sample_club):
    """Create club season statistics."""
    stats = ClubSeasonStatistics(
        club_id=sample_club.club_id,
        matches_played=10,
        wins=5,
        draws=3,
        losses=2,
        goals_scored=25,
        goals_conceded=18,
        total_assists=15,
        total_clean_sheets=3,
        avg_goals_per_match=Decimal("2.5"),
        avg_possession_percentage=Decimal("54.2"),
        avg_total_shots=Decimal("18.5"),
        avg_shots_on_target=Decimal("9.2"),
        avg_xg_per_match=Decimal("2.3"),
        avg_goals_conceded_per_match=Decimal("1.8"),
        avg_total_passes=Decimal("520.5"),
        pass_completion_rate=Decimal("84.3"),
        avg_final_third_passes=Decimal("128.4"),
        avg_crosses=Decimal("19.2"),
        avg_dribbles=Decimal("35.8"),
        avg_successful_dribbles=Decimal("24.6"),
        avg_tackles=Decimal("16.3"),
        tackle_success_rate=Decimal("74.5"),
        avg_interceptions=Decimal("13.7"),
        interception_success_rate=Decimal("82.1"),
        avg_ball_recoveries=Decimal("49.8"),
        avg_saves_per_match=Decimal("5.4"),
        team_form="WWDLW"
    )

    session.add(stats)
    session.commit()
    session.refresh(stats)
    return stats


@pytest.fixture
def sample_player_season_statistics(session, sample_complete_player):
    """Create player season statistics."""
    stats = PlayerSeasonStatistics(
        player_id=sample_complete_player.player_id,
        matches_played=10,
        goals=8,
        assists=5,
        expected_goals=Decimal("7.2"),
        shots_per_game=Decimal("4.5"),
        shots_on_target_per_game=Decimal("2.8"),
        total_passes=425,
        passes_completed=368,
        total_dribbles=68,
        successful_dribbles=52,
        tackles=28,
        tackle_success_rate=Decimal("71.4"),
        interceptions=18,
        interception_success_rate=Decimal("88.9"),
        attacking_rating=85,
        technique_rating=82,
        creativity_rating=78,
        tactical_rating=75,
        defending_rating=62
    )

    session.add(stats)
    session.commit()
    session.refresh(stats)
    return stats


@pytest.fixture
def sample_training_plan(session, sample_complete_player, sample_coach):
    """Create training plan with exercises."""
    plan = TrainingPlan(
        player_id=sample_complete_player.player_id,
        created_by=sample_coach.coach_id,
        plan_name="Speed and Agility Training",
        duration="2 weeks",
        status="in_progress",
        coach_notes="Focus on improving sprint technique and quick direction changes."
    )

    session.add(plan)
    session.commit()
    session.refresh(plan)

    # Add exercises
    exercises = [
        TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name="Sprint Intervals",
            description="20m sprint with 30s rest",
            sets="5",
            reps="8",
            duration_minutes="15",
            exercise_order=1,
            completed=True
        ),
        TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name="Cone Drills",
            description="Zigzag pattern through cones",
            sets="4",
            reps="10",
            duration_minutes="12",
            exercise_order=2,
            completed=True
        ),
        TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name="Ladder Drills",
            description="Quick feet exercises",
            sets="3",
            reps="6",
            duration_minutes="10",
            exercise_order=3,
            completed=False
        )
    ]

    for exercise in exercises:
        session.add(exercise)

    session.commit()

    for exercise in exercises:
        session.refresh(exercise)

    return {"plan": plan, "exercises": exercises}


@pytest.fixture
def sample_training_plan_empty(session, sample_incomplete_player, sample_coach):
    """Create training plan without exercises (for testing)."""
    plan = TrainingPlan(
        player_id=sample_incomplete_player.player_id,
        created_by=sample_coach.coach_id,
        plan_name="Test Plan",
        duration="1 week",
        status="pending",
        coach_notes=None
    )

    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan
