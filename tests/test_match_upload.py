"""
Consolidated tests for match upload endpoint and related functionality.

Tests cover:
- Match upload endpoint (12-step pipeline)
- CRUD operations for match-related models
- Statistics calculations
- Error scenarios
"""

import pytest
from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.match import Match
from app.models.event import Event
from app.models.goal import Goal
from app.models.opponent_club import OpponentClub
from app.models.opponent_player import OpponentPlayer
from app.models.match_statistics import MatchStatistics
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.club_season_statistics import ClubSeasonStatistics
from app.models.player_season_statistics import PlayerSeasonStatistics


class TestMatchUploadEndpoint:
    """Tests for POST /api/coach/matches endpoint"""

    def test_successful_match_upload(
        self,
        client,
        session,
        sample_club,
        auth_headers,
        match_upload_payload
    ):
        """
        Test complete match upload flow (happy path).

        Verifies all 12 steps:
        1. Authentication & authorization
        2. Team identification
        3. Opponent club creation
        4. Match record creation
        5. Event insertion
        6. Goal extraction
        7. Player creation/update
        8. Opponent player creation
        9. Match statistics calculation
        10. Player match statistics
        11. Club season statistics update
        12. Player season statistics update
        """
        # Send match upload request
        response = client.post(
            "/api/coach/matches",
            json=match_upload_payload,
            headers=auth_headers
        )

        # Assert response
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "match_id" in data
        assert data["summary"]["events_processed"] == 4
        assert data["summary"]["goals_extracted"] == 1
        assert data["summary"]["players_created"] == 11
        assert data["summary"]["opponent_players_created"] == 11
        assert len(data["new_players"]) == 11

        # Verify database records
        match_id = data["match_id"]

        # Check match created
        match = session.query(Match).filter(Match.match_id == match_id).first()
        assert match is not None
        assert match.club_id == sample_club.club_id
        assert match.opponent_name == "Alavés"
        assert match.home_score == 1
        assert match.away_score == 0

        # Check events inserted
        events = session.query(Event).filter(Event.match_id == match_id).all()
        assert len(events) == 4

        # Check goals extracted
        goals = session.query(Goal).filter(Goal.match_id == match_id).all()
        assert len(goals) == 1
        assert goals[0].scorer_name == "Lionel Messi"
        assert goals[0].assist_name == "Ivan Rakitić"

        # Check players created
        players = session.query(Player).filter(Player.club_id == sample_club.club_id).all()
        assert len(players) == 11

        # Verify specific players
        messi = session.query(Player).filter(
            Player.club_id == sample_club.club_id,
            Player.statsbomb_player_id == 5503
        ).first()
        assert messi is not None
        assert messi.player_name == "Lionel Messi"
        assert messi.jersey_number == 10
        assert messi.invite_code.startswith("LME-")
        assert messi.is_linked is False

        # Check opponent club created
        opponent_club = session.query(OpponentClub).filter(
            OpponentClub.statsbomb_team_id == 206
        ).first()
        assert opponent_club is not None
        assert opponent_club.opponent_name == "Alavés"

        # Check opponent players created
        opponent_players = session.query(OpponentPlayer).filter(
            OpponentPlayer.opponent_club_id == opponent_club.opponent_club_id
        ).all()
        assert len(opponent_players) == 11

        # Check match statistics (both teams)
        match_stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match_id
        ).all()
        assert len(match_stats) == 2  # our_team and opponent_team

        # Check player match statistics
        player_match_stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.match_id == match_id
        ).all()
        assert len(player_match_stats) == 11  # All 11 players

        # Verify Messi's stats (he scored 1 goal)
        messi_stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.player_id == messi.player_id,
            PlayerMatchStatistics.match_id == match_id
        ).first()
        assert messi_stats is not None
        assert messi_stats.goals == 1
        assert messi_stats.assists == 0

        # Check club season statistics updated
        club_stats = session.query(ClubSeasonStatistics).filter(
            ClubSeasonStatistics.club_id == sample_club.club_id
        ).first()
        assert club_stats is not None
        assert club_stats.matches_played == 1
        assert club_stats.wins == 1  # 1-0 victory
        assert club_stats.goals_scored == 1

        # Check player season statistics updated
        messi_season = session.query(PlayerSeasonStatistics).filter(
            PlayerSeasonStatistics.player_id == messi.player_id
        ).first()
        assert messi_season is not None
        assert messi_season.matches_played == 1
        assert messi_season.goals == 1
        # Check attributes were calculated
        assert messi_season.attacking_rating is not None
        assert messi_season.technique_rating is not None

    def test_unauthenticated_request_rejected(self, client, match_upload_payload):
        """Test that unauthenticated requests are rejected with 401"""
        response = client.post(
            "/api/coach/matches",
            json=match_upload_payload
        )
        assert response.status_code == 401

    def test_player_user_cannot_upload_matches(
        self,
        client,
        session,
        sample_player_user,
        match_upload_payload
    ):
        """Test that player users cannot upload matches (only coaches)"""
        from app.core.security import create_access_token

        # Create token for player user
        player_token = create_access_token(
            data={
                "sub": sample_player_user.email,
                "user_id": str(sample_player_user.user_id),
                "user_type": "player"
            }
        )

        response = client.post(
            "/api/coach/matches",
            json=match_upload_payload,
            headers={"Authorization": f"Bearer {player_token}"}
        )
        assert response.status_code == 403
        assert "Only coaches" in response.json()["detail"]

    def test_missing_starting_xi_rejected(
        self,
        client,
        session,
        sample_club,
        auth_headers,
        match_upload_payload
    ):
        """Test that events without Starting XI are rejected"""
        # Remove Starting XI events
        payload = match_upload_payload.copy()
        payload["statsbomb_events"] = [
            e for e in payload["statsbomb_events"]
            if e["type"]["name"] != "Starting XI"
        ]

        response = client.post(
            "/api/coach/matches",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Expected 2 Starting XI events" in response.json()["detail"]

    def test_invalid_lineup_size_rejected(
        self,
        client,
        session,
        sample_club,
        auth_headers,
        match_upload_payload
    ):
        """Test that lineups without exactly 11 players are rejected"""
        # Remove one player from Barcelona lineup
        payload = match_upload_payload.copy()
        barcelona_xi = next(
            e for e in payload["statsbomb_events"]
            if e["type"]["name"] == "Starting XI" and e["team"]["name"] == "Barcelona"
        )
        barcelona_xi["tactics"]["lineup"] = barcelona_xi["tactics"]["lineup"][:10]  # Only 10 players

        response = client.post(
            "/api/coach/matches",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "has 10 players (expected 11)" in response.json()["detail"]

    def test_team_name_mismatch_rejected(
        self,
        client,
        session,
        sample_club,
        auth_headers,
        match_upload_payload
    ):
        """Test that unmatched team names are rejected"""
        # Change club name to something that doesn't match
        sample_club.club_name = "Real Madrid"
        session.commit()

        response = client.post(
            "/api/coach/matches",
            json=match_upload_payload,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Cannot match your club name" in response.json()["detail"]

    def test_duplicate_player_handling(
        self,
        client,
        session,
        sample_club,
        auth_headers,
        match_upload_payload
    ):
        """Test that uploading same player twice updates instead of duplicating"""
        # First upload
        response1 = client.post(
            "/api/coach/matches",
            json=match_upload_payload,
            headers=auth_headers
        )
        assert response1.status_code == 201
        assert response1.json()["summary"]["players_created"] == 11

        # Second upload (same players)
        payload2 = match_upload_payload.copy()
        payload2["match_date"] = "2018-08-25"  # Different date

        response2 = client.post(
            "/api/coach/matches",
            json=payload2,
            headers=auth_headers
        )
        assert response2.status_code == 201
        assert response2.json()["summary"]["players_created"] == 0
        assert response2.json()["summary"]["players_updated"] == 11

        # Verify only 11 players exist (not 22)
        players = session.query(Player).filter(Player.club_id == sample_club.club_id).all()
        assert len(players) == 11

    def test_season_statistics_accumulation(
        self,
        client,
        session,
        sample_club,
        auth_headers,
        match_upload_payload
    ):
        """Test that season statistics accumulate across multiple matches"""
        # Upload first match
        response1 = client.post(
            "/api/coach/matches",
            json=match_upload_payload,
            headers=auth_headers
        )
        assert response1.status_code == 201

        # Check club stats after first match
        club_stats = session.query(ClubSeasonStatistics).filter(
            ClubSeasonStatistics.club_id == sample_club.club_id
        ).first()
        assert club_stats.matches_played == 1
        assert club_stats.wins == 1
        assert club_stats.goals_scored == 1

        # Upload second match (another 1-0 win)
        payload2 = match_upload_payload.copy()
        payload2["match_date"] = "2018-08-25"

        response2 = client.post(
            "/api/coach/matches",
            json=payload2,
            headers=auth_headers
        )
        assert response2.status_code == 201

        # Check accumulated stats
        session.refresh(club_stats)
        assert club_stats.matches_played == 2
        assert club_stats.wins == 2
        assert club_stats.goals_scored == 2

        # Check player season stats accumulated
        messi = session.query(Player).filter(
            Player.club_id == sample_club.club_id,
            Player.statsbomb_player_id == 5503
        ).first()
        messi_season = session.query(PlayerSeasonStatistics).filter(
            PlayerSeasonStatistics.player_id == messi.player_id
        ).first()
        assert messi_season.matches_played == 2
        assert messi_season.goals == 2  # Scored in both matches


class TestMatchCRUDOperations:
    """Consolidated tests for match-related CRUD operations"""

    def test_create_and_retrieve_opponent_club(self, session):
        """Test opponent club creation and retrieval"""
        from app.crud.opponent_club import create_opponent_club, get_opponent_club_by_statsbomb_id

        # Create opponent club
        club = create_opponent_club(
            db=session,
            opponent_name="Real Madrid",
            statsbomb_team_id=999,
            logo_url="https://example.com/logo.png"
        )
        session.commit()

        # Retrieve by StatsBomb ID
        retrieved = get_opponent_club_by_statsbomb_id(session, 999)
        assert retrieved is not None
        assert retrieved.opponent_name == "Real Madrid"
        assert retrieved.opponent_club_id == club.opponent_club_id

    def test_bulk_event_insertion(self, session, sample_club):
        """Test bulk insertion of events"""
        from app.crud.match import create_match
        from app.crud.event import create_events_bulk
        from datetime import date, time

        # Create match
        match = create_match(
            db=session,
            club_id=str(sample_club.club_id),
            opponent_name="Test Opponent",
            match_date=date(2025, 1, 1),
            is_home_match=True
        )
        session.commit()

        # Prepare event data
        events_data = [
            {
                "event_data": {"type": "Pass", "index": i},
                "statsbomb_player_id": 123,
                "event_type_name": "Pass",
                "minute": i
            }
            for i in range(100)
        ]

        # Bulk insert
        count = create_events_bulk(
            db=session,
            match_id=str(match.match_id),
            events_data=events_data
        )
        session.commit()

        assert count == 100

        # Verify insertion
        events = session.query(Event).filter(Event.match_id == match.match_id).all()
        assert len(events) == 100

    def test_statistics_recalculation(self, session, sample_club):
        """Test club season statistics recalculation"""
        from app.crud.club_season_statistics import recalculate_club_season_statistics
        from app.crud.match import create_match
        from datetime import date

        # Create multiple matches with different results
        matches = [
            create_match(
                db=session,
                club_id=str(sample_club.club_id),
                opponent_name=f"Opponent {i}",
                match_date=date(2025, 1, i+1),
                is_home_match=True,
                home_score=score[0],
                away_score=score[1]
            )
            for i, score in enumerate([(3, 0), (2, 2), (1, 2)])  # Win, Draw, Loss
        ]
        session.commit()

        # Recalculate stats
        stats = recalculate_club_season_statistics(
            db=session,
            club_id=str(sample_club.club_id)
        )
        session.commit()

        # Verify calculations
        assert stats.matches_played == 3
        assert stats.wins == 1
        assert stats.draws == 1
        assert stats.losses == 1
        assert stats.goals_scored == 6  # 3 + 2 + 1
        assert stats.goals_conceded == 4  # 0 + 2 + 2
        assert stats.total_clean_sheets == 1

    def test_player_attribute_calculation(self, session, sample_club):
        """Test player attribute rating calculation"""
        from app.crud.player_season_statistics import calculate_player_attributes

        # Test with good offensive stats
        attrs = calculate_player_attributes(
            goals=15,
            assists=10,
            shots_per_game=5.0,
            total_passes=500,
            passes_completed=450,
            total_dribbles=50,
            successful_dribbles=40,
            tackles=20,
            tackle_success_rate=75.0,
            interceptions=15
        )

        # Verify ratings are in valid range (0-100)
        assert 0 <= attrs["attacking_rating"] <= 100
        assert 0 <= attrs["technique_rating"] <= 100
        assert 0 <= attrs["tactical_rating"] <= 100
        assert 0 <= attrs["defending_rating"] <= 100
        assert 0 <= attrs["creativity_rating"] <= 100

        # High goals/assists should give high attacking rating
        assert attrs["attacking_rating"] > 70

        # High pass completion should give high technique rating
        assert attrs["technique_rating"] > 80


# Run tests with: pytest tests/test_match_upload.py -v
