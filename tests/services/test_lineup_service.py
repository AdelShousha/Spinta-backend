"""
Tests for lineup service functions.

Tests the creation of match lineup records from Starting XI events.
"""

import pytest
from uuid import uuid4, UUID
from app.services.lineup_service import parse_both_lineups_from_events, create_match_lineups
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.match import Match
from app.models.player import Player
from app.models.opponent_player import OpponentPlayer
from app.models.match_lineup import MatchLineup
from datetime import date


# Test fixtures
def create_starting_xi_event(team_id: int, team_name: str, is_argentina: bool = True):
    """Helper to create Starting XI event with 11 players."""
    if is_argentina:
        lineup = [
            {"player": {"id": 6909, "name": "Player 1"}, "position": {"name": "Goalkeeper"}, "jersey_number": 1},
            {"player": {"id": 29201, "name": "Player 2"}, "position": {"name": "Right Back"}, "jersey_number": 2},
            {"player": {"id": 20572, "name": "Player 3"}, "position": {"name": "Right Center Back"}, "jersey_number": 3},
            {"player": {"id": 3090, "name": "Player 4"}, "position": {"name": "Left Center Back"}, "jersey_number": 4},
            {"player": {"id": 5507, "name": "Player 5"}, "position": {"name": "Left Back"}, "jersey_number": 5},
            {"player": {"id": 38718, "name": "Player 6"}, "position": {"name": "Center Midfield"}, "jersey_number": 6},
            {"player": {"id": 7797, "name": "Player 7"}, "position": {"name": "Right Midfield"}, "jersey_number": 7},
            {"player": {"id": 27886, "name": "Player 8"}, "position": {"name": "Left Midfield"}, "jersey_number": 8},
            {"player": {"id": 5597, "name": "Player 9"}, "position": {"name": "Right Wing"}, "jersey_number": 9},
            {"player": {"id": 5503, "name": "Player 10"}, "position": {"name": "Left Wing"}, "jersey_number": 10},
            {"player": {"id": 4926, "name": "Player 11"}, "position": {"name": "Center Forward"}, "jersey_number": 11},
        ]
    else:
        lineup = [
            {"player": {"id": 3099, "name": "Opponent 1"}, "position": {"name": "Goalkeeper"}, "jersey_number": 1},
            {"player": {"id": 4445, "name": "Opponent 2"}, "position": {"name": "Right Back"}, "jersey_number": 2},
            {"player": {"id": 5485, "name": "Opponent 3"}, "position": {"name": "Right Center Back"}, "jersey_number": 3},
            {"player": {"id": 8519, "name": "Opponent 4"}, "position": {"name": "Left Center Back"}, "jersey_number": 4},
            {"player": {"id": 7784, "name": "Opponent 5"}, "position": {"name": "Left Back"}, "jersey_number": 5},
            {"player": {"id": 5574, "name": "Opponent 6"}, "position": {"name": "Center Midfield"}, "jersey_number": 6},
            {"player": {"id": 5618, "name": "Opponent 7"}, "position": {"name": "Right Midfield"}, "jersey_number": 7},
            {"player": {"id": 3089, "name": "Opponent 8"}, "position": {"name": "Left Midfield"}, "jersey_number": 8},
            {"player": {"id": 3089, "name": "Opponent 9"}, "position": {"name": "Right Wing"}, "jersey_number": 9},
            {"player": {"id": 3009, "name": "Opponent 10"}, "position": {"name": "Left Wing"}, "jersey_number": 10},
            {"player": {"id": 3604, "name": "Opponent 11"}, "position": {"name": "Center Forward"}, "jersey_number": 11},
        ]

    return {
        "type": {"id": 35, "name": "Starting XI"},
        "possession_team": {"id": team_id, "name": team_name},
        "team": {"id": team_id, "name": team_name},
        "tactics": {"formation": 433, "lineup": lineup}
    }


class TestParseBothLineupsFromEvents:
    """Test parse_both_lineups_from_events helper function."""

    def test_extracts_11_our_players(self):
        """Test that function extracts all 11 players from our team's Starting XI."""
        # Given: Events with 2 Starting XI events
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Parse lineups
        result = parse_both_lineups_from_events(
            events=events,
            our_club_statsbomb_id=779,
            opponent_club_statsbomb_id=771
        )

        # Then: Our lineup has 11 players
        assert 'our_lineup' in result
        assert len(result['our_lineup']) == 11

        # Verify first player structure
        first_player = result['our_lineup'][0]
        assert 'player_name' in first_player
        assert 'statsbomb_player_id' in first_player
        assert 'jersey_number' in first_player
        assert 'position' in first_player

    def test_extracts_11_opponent_players(self):
        """Test that function extracts all 11 players from opponent's Starting XI."""
        # Given: Events with 2 Starting XI events
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Parse lineups
        result = parse_both_lineups_from_events(
            events=events,
            our_club_statsbomb_id=779,
            opponent_club_statsbomb_id=771
        )

        # Then: Opponent lineup has 11 players
        assert 'opponent_lineup' in result
        assert len(result['opponent_lineup']) == 11

        # Verify first player structure
        first_player = result['opponent_lineup'][0]
        assert 'player_name' in first_player
        assert 'statsbomb_player_id' in first_player
        assert 'jersey_number' in first_player
        assert 'position' in first_player

    def test_uses_team_id_for_our_team(self):
        """Test that function correctly identifies our team using team.id."""
        # Given: Events with 2 Starting XI events
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Parse lineups
        result = parse_both_lineups_from_events(
            events=events,
            our_club_statsbomb_id=779,
            opponent_club_statsbomb_id=771
        )

        # Then: Our lineup contains Argentina players
        assert result['our_lineup'][0]['player_name'] == "Player 1"
        assert result['our_lineup'][0]['statsbomb_player_id'] == 6909

    def test_uses_team_id_for_opponent_team(self):
        """Test that function correctly identifies opponent team using team.id."""
        # Given: Events with 2 Starting XI events
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Parse lineups
        result = parse_both_lineups_from_events(
            events=events,
            our_club_statsbomb_id=779,
            opponent_club_statsbomb_id=771
        )

        # Then: Opponent lineup contains France players
        assert result['opponent_lineup'][0]['player_name'] == "Opponent 1"
        assert result['opponent_lineup'][0]['statsbomb_player_id'] == 3099

    def test_raises_error_if_not_2_starting_xi_events(self):
        """Test that function raises error if there aren't exactly 2 Starting XI events."""
        # Given: Events with only 1 Starting XI event
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True)
        ]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Expected 2 Starting XI events"):
            parse_both_lineups_from_events(
                events=events,
                our_club_statsbomb_id=779,
                opponent_club_statsbomb_id=771
            )


class TestCreateMatchLineups:
    """Test create_match_lineups main function."""

    def test_creates_22_lineup_records(self, session):
        """Test that function creates exactly 22 lineup records (11 + 11)."""
        # Given: Match, clubs, and all players exist
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(
            opponent_name="Opponent FC",
            statsbomb_team_id=771
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create 11 our players
        our_player_ids = [6909, 29201, 20572, 3090, 5507, 38718, 7797, 27886, 5597, 5503, 4926]
        for i, sb_id in enumerate(our_player_ids, 1):
            player = Player(
                club_id=club.club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position",
                invite_code=f"INV-{i:04d}",
                is_linked=False
            )
            session.add(player)

        # Create 11 opponent players
        opp_player_ids = [3099, 4445, 5485, 8519, 7784, 5574, 5618, 3089, 3089, 3009, 3604]
        for i, sb_id in enumerate(opp_player_ids, 1):
            opp_player = OpponentPlayer(
                opponent_club_id=opponent_club.opponent_club_id,
                player_name=f"Opponent {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position"
            )
            session.add(opp_player)

        session.commit()

        # Given: Events
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Create lineups
        result = create_match_lineups(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: 22 lineups created
        assert result['lineups_created'] == 22

        # Verify in database
        lineups = session.query(MatchLineup).filter(
            MatchLineup.match_id == match.match_id
        ).all()
        assert len(lineups) == 22

    def test_creates_11_our_team_lineups(self, session):
        """Test that function creates 11 lineups with team_type='our_team'."""
        # Given: Setup (same as previous test)
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=771)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create players
        our_player_ids = [6909, 29201, 20572, 3090, 5507, 38718, 7797, 27886, 5597, 5503, 4926]
        for i, sb_id in enumerate(our_player_ids, 1):
            player = Player(
                club_id=club.club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position",
                invite_code=f"INV-{i:04d}",
                is_linked=False
            )
            session.add(player)

        opp_player_ids = [3099, 4445, 5485, 8519, 7784, 5574, 5618, 3089, 3089, 3009, 3604]
        for i, sb_id in enumerate(opp_player_ids, 1):
            opp_player = OpponentPlayer(
                opponent_club_id=opponent_club.opponent_club_id,
                player_name=f"Opponent {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position"
            )
            session.add(opp_player)
        session.commit()

        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Create lineups
        result = create_match_lineups(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: 11 our_team lineups
        assert result['our_team_count'] == 11

        our_team_lineups = session.query(MatchLineup).filter(
            MatchLineup.match_id == match.match_id,
            MatchLineup.team_type == 'our_team'
        ).all()
        assert len(our_team_lineups) == 11

        # Verify player_id is set, opponent_player_id is NULL
        for lineup in our_team_lineups:
            assert lineup.player_id is not None
            assert lineup.opponent_player_id is None

    def test_creates_11_opponent_team_lineups(self, session):
        """Test that function creates 11 lineups with team_type='opponent_team'."""
        # Given: Setup (same pattern)
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=771)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create players
        our_player_ids = [6909, 29201, 20572, 3090, 5507, 38718, 7797, 27886, 5597, 5503, 4926]
        for i, sb_id in enumerate(our_player_ids, 1):
            player = Player(
                club_id=club.club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position",
                invite_code=f"INV-{i:04d}",
                is_linked=False
            )
            session.add(player)

        opp_player_ids = [3099, 4445, 5485, 8519, 7784, 5574, 5618, 3089, 3089, 3009, 3604]
        for i, sb_id in enumerate(opp_player_ids, 1):
            opp_player = OpponentPlayer(
                opponent_club_id=opponent_club.opponent_club_id,
                player_name=f"Opponent {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position"
            )
            session.add(opp_player)
        session.commit()

        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Create lineups
        result = create_match_lineups(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: 11 opponent_team lineups
        assert result['opponent_team_count'] == 11

        opponent_team_lineups = session.query(MatchLineup).filter(
            MatchLineup.match_id == match.match_id,
            MatchLineup.team_type == 'opponent_team'
        ).all()
        assert len(opponent_team_lineups) == 11

        # Verify opponent_player_id is set, player_id is NULL
        for lineup in opponent_team_lineups:
            assert lineup.opponent_player_id is not None
            assert lineup.player_id is None

    def test_sets_denormalized_fields_correctly(self, session):
        """Test that denormalized fields (player_name, jersey_number, position) are set from events."""
        # Given: Setup
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=771)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create players
        our_player_ids = [6909, 29201, 20572, 3090, 5507, 38718, 7797, 27886, 5597, 5503, 4926]
        for i, sb_id in enumerate(our_player_ids, 1):
            player = Player(
                club_id=club.club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position",
                invite_code=f"INV-{i:04d}",
                is_linked=False
            )
            session.add(player)

        opp_player_ids = [3099, 4445, 5485, 8519, 7784, 5574, 5618, 3089, 3089, 3009, 3604]
        for i, sb_id in enumerate(opp_player_ids, 1):
            opp_player = OpponentPlayer(
                opponent_club_id=opponent_club.opponent_club_id,
                player_name=f"Opponent {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position"
            )
            session.add(opp_player)
        session.commit()

        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Create lineups
        create_match_lineups(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: Verify denormalized fields from events (not database)
        our_lineup = session.query(MatchLineup).filter(
            MatchLineup.match_id == match.match_id,
            MatchLineup.team_type == 'our_team'
        ).order_by(MatchLineup.jersey_number).all()

        # First player should have data from event
        assert our_lineup[0].player_name == "Player 1"  # From event
        assert our_lineup[0].jersey_number == 1  # From event
        assert our_lineup[0].position == "Goalkeeper"  # From event (not "Position")

    def test_matches_player_ids_correctly(self, session):
        """Test that function correctly matches players by statsbomb_player_id."""
        # Given: Setup
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=771)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create players
        our_player_ids = [6909, 29201, 20572, 3090, 5507, 38718, 7797, 27886, 5597, 5503, 4926]
        created_players = []
        for i, sb_id in enumerate(our_player_ids, 1):
            player = Player(
                club_id=club.club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position",
                invite_code=f"INV-{i:04d}",
                is_linked=False
            )
            session.add(player)
            session.flush()
            created_players.append(player)

        opp_player_ids = [3099, 4445, 5485, 8519, 7784, 5574, 5618, 3089, 3089, 3009, 3604]
        for i, sb_id in enumerate(opp_player_ids, 1):
            opp_player = OpponentPlayer(
                opponent_club_id=opponent_club.opponent_club_id,
                player_name=f"Opponent {i}",
                statsbomb_player_id=sb_id,
                jersey_number=i,
                position="Position"
            )
            session.add(opp_player)
        session.commit()

        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When: Create lineups
        create_match_lineups(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: Verify player_id matches the player with statsbomb_player_id=6909
        first_lineup = session.query(MatchLineup).filter(
            MatchLineup.match_id == match.match_id,
            MatchLineup.team_type == 'our_team',
            MatchLineup.jersey_number == 1
        ).first()

        assert first_lineup.player_id == created_players[0].player_id

    def test_raises_error_if_match_not_found(self, session):
        """Test that function raises error if match_id doesn't exist."""
        # Given: No match exists
        fake_match_id = uuid4()
        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Match with ID .* not found"):
            create_match_lineups(
                db=session,
                match_id=fake_match_id,
                events=events
            )

    def test_raises_error_if_player_not_found(self, session):
        """Test that function raises error if a player from lineup doesn't exist in database."""
        # Given: Match and clubs exist, but NO players
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=771)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Player .* not found in players table"):
            create_match_lineups(
                db=session,
                match_id=match.match_id,
                events=events
            )

    def test_raises_error_if_lineups_already_exist(self, session):
        """Test that function raises error if lineups already exist for this match."""
        # Given: Match, clubs, and players exist
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=779)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=771)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create one player for each team
        player = Player(
            club_id=club.club_id,
            player_name="Test Player",
            statsbomb_player_id=6909,
            jersey_number=1,
            position="Position",
            invite_code="INV-0001",
            is_linked=False
        )
        session.add(player)
        session.flush()

        # Given: Lineup already exists
        existing_lineup = MatchLineup(
            match_id=match.match_id,
            team_type='our_team',
            player_id=player.player_id,
            opponent_player_id=None,
            player_name="Test Player",
            jersey_number=1,
            position="Position"
        )
        session.add(existing_lineup)
        session.commit()

        events = [
            create_starting_xi_event(779, "Argentina", is_argentina=True),
            create_starting_xi_event(771, "France", is_argentina=False)
        ]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Lineups already exist for match"):
            create_match_lineups(
                db=session,
                match_id=match.match_id,
                events=events
            )
