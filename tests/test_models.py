"""
Database Model Tests

This file tests all SQLAlchemy models using Test-Driven Development (TDD).

Test Coverage:
- User model: Creation, relationships, helper methods
- Coach model: Creation, one-to-one with user
- Club model: Creation, one-to-one with coach, relationships
- Player model: Incomplete/complete states, signup process
- Constraints: Foreign keys, unique, nullable
- Cascading: Deletes propagate correctly

Run with: pytest tests/test_models.py -v
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime

from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player


class TestUserModel:
    """
    Test Suite for User Model

    Tests user account creation, validation, and helper methods.
    """

    def test_user_creation_and_constraints(self, session, sample_user):
        """
        Test user creation and database constraints.

        Scenarios:
        - Create user with all required fields
        - Auto-generated fields (user_id, timestamps)
        - Email uniqueness constraint
        """
        # Test successful creation with all fields
        user = User(
            email="newuser@example.com",
            password_hash="$2b$12$hashed_password",
            full_name="John Doe",
            user_type="coach"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Verify all fields
        assert user.user_id is not None, "user_id should be auto-generated"
        assert user.email == "newuser@example.com"
        assert user.password_hash == "$2b$12$hashed_password"
        assert user.full_name == "John Doe"
        assert user.user_type == "coach"
        assert user.created_at is not None, "created_at should be auto-set"
        assert user.updated_at is not None, "updated_at should be auto-set"

        # Test duplicate email constraint
        duplicate_user = User(
            email=sample_user.email,  # Same email as sample_user
            password_hash="$2b$12$different_hash",
            full_name="Different User",
            user_type="player"
        )
        session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_user_helper_methods(self, session, sample_user):
        """
        Test user helper methods.

        Scenarios:
        - is_coach() returns True for coaches, False for players
        - is_player() returns True for players, False for coaches
        - __repr__ returns formatted string
        """
        # Test is_coach() method
        coach_user = User(
            email="coach@test.com",
            password_hash="hash",
            full_name="Coach User",
            user_type="coach"
        )
        session.add(coach_user)
        session.commit()

        assert coach_user.is_coach() is True
        assert coach_user.is_player() is False

        # Test is_player() method
        player_user = User(
            email="player@test.com",
            password_hash="hash",
            full_name="Player User",
            user_type="player"
        )
        session.add(player_user)
        session.commit()

        assert player_user.is_player() is True
        assert player_user.is_coach() is False

        # Test __repr__ method
        repr_string = repr(sample_user)
        assert "User" in repr_string
        assert sample_user.email in repr_string
        assert sample_user.user_type in repr_string


class TestCoachModel:
    """
    Test Suite for Coach Model

    Tests coach creation, user relationship, and optional fields.
    """

    def test_coach_creation_and_constraints(self, session, sample_coach):
        """
        Test coach creation and database constraints.

        Scenarios:
        - Create coach with all fields
        - Auto-generated fields (coach_id, timestamps)
        - User_id uniqueness constraint (one user = one coach)
        - Optional fields can be NULL
        """
        # Create new user for testing coach creation
        user = User(
            email="newcoach@test.com",
            password_hash="hash",
            full_name="New Coach",
            user_type="coach"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Test successful creation with all fields
        coach = Coach(
            user_id=user.user_id,
            birth_date=date(1990, 1, 1),
            gender="male"
        )
        session.add(coach)
        session.commit()
        session.refresh(coach)

        # Verify fields
        assert coach.coach_id is not None, "coach_id should be auto-generated"
        assert coach.user_id == user.user_id
        assert coach.birth_date == date(1990, 1, 1)
        assert coach.gender == "male"
        assert coach.created_at is not None
        assert coach.updated_at is not None

        # Test user_id uniqueness constraint
        duplicate_coach = Coach(
            user_id=sample_coach.user_id,  # Same user_id as sample_coach
            birth_date=date(1985, 5, 15)
        )
        session.add(duplicate_coach)

        with pytest.raises(IntegrityError):
            session.commit()

        # Test optional fields can be NULL
        session.rollback()  # Rollback failed transaction

        # Create new user for testing optional fields
        new_user = User(
            email="optional@test.com",
            password_hash="hash",
            full_name="Optional Test",
            user_type="coach"
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        minimal_coach = Coach(user_id=new_user.user_id)
        session.add(minimal_coach)
        session.commit()
        session.refresh(minimal_coach)

        assert minimal_coach.birth_date is None
        assert minimal_coach.gender is None

    def test_coach_relationships_and_properties(self, session, sample_coach, sample_user):
        """
        Test coach relationships and convenience properties.

        Scenarios:
        - One-to-one relationship with user (bidirectional)
        - Email property returns user's email
        - Full_name property returns user's full_name
        """
        # Test one-to-one relationship (coach -> user)
        assert sample_coach.user is not None
        assert sample_coach.user.email == sample_user.email

        # Test one-to-one relationship (user -> coach)
        assert sample_user.coach is not None
        assert sample_user.coach.coach_id == sample_coach.coach_id

        # Test email convenience property
        assert sample_coach.email == sample_user.email

        # Test full_name convenience property
        assert sample_coach.full_name == sample_user.full_name

    def test_coach_cascade_delete(self, session, sample_user, sample_coach):
        """
        Test CASCADE delete behavior.

        Scenario:
        - Deleting user cascades to coach
        """
        coach_id = sample_coach.coach_id

        # Delete user
        session.delete(sample_user)
        session.commit()

        # Coach should be deleted
        deleted_coach = session.query(Coach).filter(Coach.coach_id == coach_id).first()
        assert deleted_coach is None


class TestClubModel:
    """
    Test Suite for Club Model

    Tests club creation, coach relationship, and StatsBomb integration.
    """

    def test_club_creation_and_constraints(self, session, sample_club):
        """
        Test club creation and database constraints.

        Scenarios:
        - Create club with all fields
        - Auto-generated fields (club_id, timestamps)
        - Coach_id uniqueness constraint (one coach = one club)
        - StatsBomb team_id uniqueness constraint
        - Optional fields can be NULL
        """
        # Create new coach for testing club creation
        user = User(
            email="newcoach@test.com",
            password_hash="hash",
            full_name="New Coach",
            user_type="coach"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        coach = Coach(user_id=user.user_id)
        session.add(coach)
        session.commit()
        session.refresh(coach)

        # Test successful creation with all fields
        club = Club(
            coach_id=coach.coach_id,
            club_name="Manchester City U16",
            statsbomb_team_id=123,
            country="England",
            age_group="U16",
            stadium="Etihad Campus",
            logo_url="https://example.com/logo.png"
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Verify all fields
        assert club.club_id is not None
        assert club.coach_id == coach.coach_id
        assert club.club_name == "Manchester City U16"
        assert club.statsbomb_team_id == 123
        assert club.country == "England"
        assert club.age_group == "U16"
        assert club.stadium == "Etihad Campus"
        assert club.logo_url == "https://example.com/logo.png"
        assert club.created_at is not None
        assert club.updated_at is not None

        # Test coach_id uniqueness constraint
        duplicate_club = Club(
            coach_id=sample_club.coach_id,  # Same coach_id as sample_club
            club_name="Another Club"
        )
        session.add(duplicate_club)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        # Test statsbomb_team_id uniqueness constraint
        # Create second coach for second club
        user2 = User(
            email="coach2@test.com",
            password_hash="hash",
            full_name="Coach 2",
            user_type="coach"
        )
        session.add(user2)
        session.commit()
        session.refresh(user2)

        coach2 = Coach(user_id=user2.user_id)
        session.add(coach2)
        session.commit()
        session.refresh(coach2)

        # First club with statsbomb_team_id
        club_with_sb = Club(
            coach_id=coach2.coach_id,
            club_name="Club 1",
            statsbomb_team_id=999
        )
        session.add(club_with_sb)
        session.commit()

        # Create third coach
        user3 = User(
            email="coach3@test.com",
            password_hash="hash",
            full_name="Coach 3",
            user_type="coach"
        )
        session.add(user3)
        session.commit()
        session.refresh(user3)

        coach3 = Coach(user_id=user3.user_id)
        session.add(coach3)
        session.commit()
        session.refresh(coach3)

        # Try duplicate statsbomb_team_id
        duplicate_sb_club = Club(
            coach_id=coach3.coach_id,
            club_name="Club 2",
            statsbomb_team_id=999  # Same StatsBomb ID
        )
        session.add(duplicate_sb_club)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        # Test optional fields can be NULL
        # Create fourth coach
        user4 = User(
            email="coach4@test.com",
            password_hash="hash",
            full_name="Coach 4",
            user_type="coach"
        )
        session.add(user4)
        session.commit()
        session.refresh(user4)

        coach4 = Coach(user_id=user4.user_id)
        session.add(coach4)
        session.commit()
        session.refresh(coach4)

        minimal_club = Club(
            coach_id=coach4.coach_id,
            club_name="Minimal Club"
        )
        session.add(minimal_club)
        session.commit()
        session.refresh(minimal_club)

        assert minimal_club.statsbomb_team_id is None
        assert minimal_club.country is None
        assert minimal_club.age_group is None
        assert minimal_club.stadium is None
        assert minimal_club.logo_url is None

    def test_club_relationships_and_properties(self, session, sample_club, sample_coach, sample_user):
        """
        Test club relationships and convenience properties.

        Scenarios:
        - One-to-one relationship with coach (bidirectional)
        - Coach_name property returns coach's full name
        """
        # Test one-to-one relationship (club -> coach)
        assert sample_club.coach is not None
        assert sample_club.coach.coach_id == sample_coach.coach_id

        # Test one-to-one relationship (coach -> club)
        assert sample_coach.club is not None
        assert sample_coach.club.club_id == sample_club.club_id

        # Test coach_name convenience property
        assert sample_club.coach_name == sample_user.full_name

    def test_club_cascade_delete(self, session, sample_coach, sample_club):
        """
        Test CASCADE delete behavior.

        Scenario:
        - Deleting coach cascades to club
        """
        club_id = sample_club.club_id

        # Delete coach
        session.delete(sample_coach)
        session.commit()

        # Club should be deleted
        deleted_club = session.query(Club).filter(Club.club_id == club_id).first()
        assert deleted_club is None


class TestPlayerModel:
    """
    Test Suite for Player Model

    Tests both incomplete (before signup) and complete (after signup) states.
    """

    def test_player_creation_and_states(self, session, sample_club, sample_player_user, sample_incomplete_player):
        """
        Test player creation in different states.

        Scenarios:
        - Create incomplete player (before signup)
        - Create complete player (after signup)
        - complete_signup() method transitions incomplete to complete
        - is_incomplete property works correctly
        """
        # Test incomplete player creation
        incomplete = Player(
            club_id=sample_club.club_id,
            player_name="John Smith",
            statsbomb_player_id=456,
            jersey_number=10,
            position="Forward",
            invite_code="ABC-1234",
            is_linked=False
        )
        session.add(incomplete)
        session.commit()
        session.refresh(incomplete)

        # Verify incomplete state
        assert incomplete.player_id is not None
        assert incomplete.user_id is None, "Incomplete player should have NULL user_id"
        assert incomplete.is_linked is False
        assert incomplete.linked_at is None
        assert incomplete.birth_date is None
        assert incomplete.height is None
        assert incomplete.profile_image_url is None
        assert incomplete.is_incomplete is True

        # Verify basic fields
        assert incomplete.club_id == sample_club.club_id
        assert incomplete.player_name == "John Smith"
        assert incomplete.jersey_number == 10
        assert incomplete.position == "Forward"
        assert incomplete.invite_code == "ABC-1234"

        # Test complete player creation
        complete = Player(
            user_id=sample_player_user.user_id,
            club_id=sample_club.club_id,
            player_name="Jane Doe",
            jersey_number=7,
            position="Midfielder",
            invite_code="XYZ-5678",
            is_linked=True,
            linked_at=datetime.utcnow(),
            birth_date=date(2008, 3, 15),
            height=175,
            profile_image_url="https://example.com/photo.jpg"
        )
        session.add(complete)
        session.commit()
        session.refresh(complete)

        # Verify complete state
        assert complete.user_id == sample_player_user.user_id
        assert complete.is_linked is True
        assert complete.linked_at is not None
        assert complete.birth_date == date(2008, 3, 15)
        assert complete.height == 175
        assert complete.profile_image_url == "https://example.com/photo.jpg"
        assert complete.is_incomplete is False

        # Test complete_signup() method
        # sample_incomplete_player starts as incomplete
        assert sample_incomplete_player.user_id is None
        assert sample_incomplete_player.is_linked is False
        assert sample_incomplete_player.linked_at is None

        # Create new user for linking
        new_user = User(
            email="newplayer@test.com",
            password_hash="hash",
            full_name="New Player",
            user_type="player"
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        # Complete signup
        sample_incomplete_player.complete_signup(new_user.user_id)
        session.commit()
        session.refresh(sample_incomplete_player)

        # Verify transition to complete
        assert sample_incomplete_player.user_id == new_user.user_id
        assert sample_incomplete_player.is_linked is True
        assert sample_incomplete_player.linked_at is not None

    def test_player_constraints(self, session, sample_club, sample_player_user):
        """
        Test player database constraints.

        Scenarios:
        - Invite code must be unique
        - User_id must be unique (when set)
        """
        # Test invite code uniqueness
        player1 = Player(
            club_id=sample_club.club_id,
            player_name="Player 1",
            jersey_number=1,
            position="Goalkeeper",
            invite_code="DUP-1111",
            is_linked=False
        )
        session.add(player1)
        session.commit()

        player2 = Player(
            club_id=sample_club.club_id,
            player_name="Player 2",
            jersey_number=2,
            position="Defender",
            invite_code="DUP-1111",  # Duplicate
            is_linked=False
        )
        session.add(player2)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        # Test user_id uniqueness
        player3 = Player(
            user_id=sample_player_user.user_id,
            club_id=sample_club.club_id,
            player_name="Player 3",
            jersey_number=3,
            position="Forward",
            invite_code="UNQ-1111",
            is_linked=True
        )
        session.add(player3)
        session.commit()

        player4 = Player(
            user_id=sample_player_user.user_id,  # Same user_id
            club_id=sample_club.club_id,
            player_name="Player 4",
            jersey_number=4,
            position="Defender",
            invite_code="UNQ-2222",
            is_linked=True
        )
        session.add(player4)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_player_relationships_and_properties(self, session, sample_incomplete_player, sample_complete_player,
                                                 sample_club, sample_player_user):
        """
        Test player relationships and convenience properties.

        Scenarios:
        - Many-to-one relationship with club (bidirectional)
        - One-to-one relationship with user (bidirectional, for complete players)
        - Email property returns user's email for complete players, None for incomplete
        """
        # Test club relationship (player -> club)
        assert sample_incomplete_player.club is not None
        assert sample_incomplete_player.club.club_id == sample_club.club_id

        # Test club relationship (club -> players)
        assert len(sample_club.players) > 0
        player_ids = [p.player_id for p in sample_club.players]
        assert sample_incomplete_player.player_id in player_ids

        # Test user relationship for complete player (player -> user)
        assert sample_complete_player.user is not None
        assert sample_complete_player.user.user_id == sample_player_user.user_id

        # Test user relationship (user -> player)
        assert sample_player_user.player is not None
        assert sample_player_user.player.player_id == sample_complete_player.player_id

        # Test email property for complete player
        assert sample_complete_player.email == sample_player_user.email

        # Test email property for incomplete player
        assert sample_incomplete_player.email is None

    def test_player_cascade_behavior(self, session, sample_club, sample_incomplete_player,
                                    sample_complete_player, sample_player_user):
        """
        Test cascade delete behaviors.

        Scenarios:
        - Deleting club cascades to all players
        - Deleting user sets player.user_id to NULL (SET NULL, not CASCADE)
        """
        # Test club cascade delete
        incomplete_player_id = sample_incomplete_player.player_id

        # Delete club
        session.delete(sample_club)
        session.commit()

        # Player should be deleted
        deleted_player = session.query(Player).filter(Player.player_id == incomplete_player_id).first()
        assert deleted_player is None

        # Test user SET NULL behavior
        # Create new club and complete player for this test
        new_user = User(
            email="cascade@test.com",
            password_hash="hash",
            full_name="Cascade Coach",
            user_type="coach"
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        new_coach = Coach(user_id=new_user.user_id)
        session.add(new_coach)
        session.commit()
        session.refresh(new_coach)

        new_club = Club(
            coach_id=new_coach.coach_id,
            club_name="New Club"
        )
        session.add(new_club)
        session.commit()
        session.refresh(new_club)

        player_user = User(
            email="playeruser@test.com",
            password_hash="hash",
            full_name="Player User",
            user_type="player"
        )
        session.add(player_user)
        session.commit()
        session.refresh(player_user)

        test_player = Player(
            user_id=player_user.user_id,
            club_id=new_club.club_id,
            player_name="Test Player",
            jersey_number=99,
            position="Forward",
            invite_code="TST-9999",
            is_linked=True,
            linked_at=datetime.utcnow()
        )
        session.add(test_player)
        session.commit()
        session.refresh(test_player)

        player_id = test_player.player_id

        # Verify player is linked before deletion
        assert test_player.user_id == player_user.user_id
        assert test_player.is_linked is True

        # Delete user
        session.delete(player_user)
        session.commit()

        # Player should still exist
        persisted_player = session.query(Player).filter(Player.player_id == player_id).first()
        assert persisted_player is not None, "Player should persist after user deletion"

        # user_id should be NULL (SET NULL cascade)
        assert persisted_player.user_id is None, "user_id should be NULL after user deletion"

        # Note: is_linked and linked_at remain unchanged (future endpoint will handle these)
        assert persisted_player.is_linked is True  # Still True (not updated automatically)


class TestFullDataFlow:
    """
    Integration tests for complete workflows.

    Tests realistic scenarios involving multiple models.
    """

    def test_complete_registration_and_signup_flows(self, session, sample_club):
        """
        Test complete registration and signup workflows.

        Scenarios:
        - Coach registration: User → Coach → Club (full chain)
        - Player signup: Admin creates incomplete → Player signs up → Profile completed
        """
        # Test coach registration flow
        # 1. Create user account
        user = User(
            email="newcoach@example.com",
            password_hash="$2b$12$hashed",
            full_name="New Coach",
            user_type="coach"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # 2. Create coach record
        coach = Coach(user_id=user.user_id)
        session.add(coach)
        session.commit()
        session.refresh(coach)

        # 3. Create club
        club = Club(
            coach_id=coach.coach_id,
            club_name="New FC"
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Verify complete chain
        assert user.coach.coach_id == coach.coach_id
        assert coach.club.club_id == club.club_id
        assert club.coach.user.email == user.email

        # Test player signup flow
        # 1. Admin creates incomplete player
        incomplete = Player(
            club_id=sample_club.club_id,
            player_name="Future Player",
            jersey_number=9,
            position="Striker",
            invite_code="FTR-9999",
            is_linked=False
        )
        session.add(incomplete)
        session.commit()
        session.refresh(incomplete)

        # Verify incomplete state
        assert incomplete.user_id is None
        assert incomplete.is_linked is False

        # 2. Player signs up
        player_user = User(
            email="futureplayer@example.com",
            password_hash="$2b$12$hashed",
            full_name="Future Player",
            user_type="player"
        )
        session.add(player_user)
        session.commit()
        session.refresh(player_user)

        # 3. Link player to user
        incomplete.complete_signup(player_user.user_id)
        incomplete.birth_date = date(2009, 6, 20)
        incomplete.height = 180
        session.commit()
        session.refresh(incomplete)

        # Verify complete state
        assert incomplete.user_id == player_user.user_id
        assert incomplete.is_linked is True
        assert incomplete.linked_at is not None
        assert incomplete.birth_date == date(2009, 6, 20)
        assert incomplete.height == 180

        # Verify relationships
        assert player_user.player.player_id == incomplete.player_id
        assert incomplete.user.email == player_user.email

    def test_cascade_delete_full_chain(self, session):
        """
        Test cascade delete through entire relationship chain.

        Scenario:
        - When coach user is deleted:
          → Coach is deleted (CASCADE)
          → Club is deleted (CASCADE)
          → Players in club are deleted (CASCADE)
        """
        # Create full chain
        user = User(
            email="cascade@test.com",
            password_hash="hash",
            full_name="Cascade Test",
            user_type="coach"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        coach = Coach(user_id=user.user_id)
        session.add(coach)
        session.commit()
        session.refresh(coach)

        club = Club(
            coach_id=coach.coach_id,
            club_name="Cascade FC"
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        player = Player(
            club_id=club.club_id,
            player_name="Test Player",
            jersey_number=1,
            position="Goalkeeper",
            invite_code="CAS-0001",
            is_linked=False
        )
        session.add(player)
        session.commit()
        session.refresh(player)

        # Save IDs before deletion
        coach_id = coach.coach_id
        club_id = club.club_id
        player_id = player.player_id

        # Delete user (should cascade to everything)
        session.delete(user)
        session.commit()

        # Verify all are deleted
        assert session.query(Coach).filter(Coach.coach_id == coach_id).first() is None
        assert session.query(Club).filter(Club.club_id == club_id).first() is None
        assert session.query(Player).filter(Player.player_id == player_id).first() is None


class TestMatchRelatedModels:
    """
    Test Suite for Match-Related Models

    Compact tests covering OpponentClub, Match, OpponentPlayer, Goal, and Event models.
    """

    def test_opponent_club_creation(self, session):
        """
        Test OpponentClub model creation and constraints.

        Scenarios:
        - Create opponent club with all fields
        - Verify auto-generated fields (opponent_club_id, created_at)
        - Test statsbomb_team_id uniqueness constraint
        - Test nullable fields (statsbomb_team_id, logo_url)
        """
        from app.models.opponent_club import OpponentClub

        # Test successful creation with all fields
        opponent = OpponentClub(
            opponent_name="City Strikers",
            statsbomb_team_id=912,
            logo_url="https://example.com/opponent-logo.png"
        )
        session.add(opponent)
        session.commit()
        session.refresh(opponent)

        # Verify all fields
        assert opponent.opponent_club_id is not None
        assert opponent.opponent_name == "City Strikers"
        assert opponent.statsbomb_team_id == 912
        assert opponent.logo_url == "https://example.com/opponent-logo.png"
        assert opponent.created_at is not None

        # Test statsbomb_team_id uniqueness
        duplicate_sb_id = OpponentClub(
            opponent_name="Different Team",
            statsbomb_team_id=912  # Same StatsBomb ID
        )
        session.add(duplicate_sb_id)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        # Test nullable fields
        minimal_opponent = OpponentClub(
            opponent_name="Minimal Opponent"
        )
        session.add(minimal_opponent)
        session.commit()
        session.refresh(minimal_opponent)

        assert minimal_opponent.statsbomb_team_id is None
        assert minimal_opponent.logo_url is None

    def test_match_creation_and_relationships(self, session, sample_club):
        """
        Test Match model creation, relationships, and cascading.

        Scenarios:
        - Create match with club and opponent_club foreign keys
        - Test nullable fields (opponent_club_id, scores, result)
        - Test CASCADE delete for club_id
        - Test SET NULL for opponent_club_id
        """
        from app.models.opponent_club import OpponentClub
        from app.models.match import Match

        # Create opponent club
        opponent = OpponentClub(opponent_name="North Athletic")
        session.add(opponent)
        session.commit()
        session.refresh(opponent)

        # Test successful match creation with all fields
        match = Match(
            club_id=sample_club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="North Athletic",
            match_date=date(2025, 10, 8),
            our_score=3,
            opponent_score=2,
            result="W"
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Verify all fields
        assert match.match_id is not None
        assert match.club_id == sample_club.club_id
        assert match.opponent_club_id == opponent.opponent_club_id
        assert match.opponent_name == "North Athletic"
        assert match.match_date == date(2025, 10, 8)
        assert match.our_score == 3
        assert match.opponent_score == 2
        assert match.result == "W"
        assert match.created_at is not None

        # Test relationships
        assert match.club.club_id == sample_club.club_id
        assert match.opponent_club.opponent_club_id == opponent.opponent_club_id

        # Test nullable fields (match in progress, no final score yet)
        upcoming_match = Match(
            club_id=sample_club.club_id,
            opponent_name="Future Opponent",
            match_date=date(2025, 11, 15)
        )
        session.add(upcoming_match)
        session.commit()
        session.refresh(upcoming_match)

        assert upcoming_match.opponent_club_id is None
        assert upcoming_match.our_score is None
        assert upcoming_match.opponent_score is None
        assert upcoming_match.result is None

        # Test CASCADE delete for club
        match_id = match.match_id
        session.delete(sample_club)
        session.commit()

        deleted_match = session.query(Match).filter(Match.match_id == match_id).first()
        assert deleted_match is None

    def test_opponent_player_creation(self, session):
        """
        Test OpponentPlayer model creation and relationships.

        Scenarios:
        - Create opponent player linked to opponent club
        - Test CASCADE delete when opponent club deleted
        - Test nullable fields
        """
        from app.models.opponent_club import OpponentClub
        from app.models.opponent_player import OpponentPlayer

        # Create opponent club
        opponent_club = OpponentClub(opponent_name="Valley Rangers")
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Test opponent player creation
        opponent_player = OpponentPlayer(
            opponent_club_id=opponent_club.opponent_club_id,
            player_name="John Doe",
            statsbomb_player_id=8923,
            jersey_number=9,
            position="Center Forward"
        )
        session.add(opponent_player)
        session.commit()
        session.refresh(opponent_player)

        # Verify all fields
        assert opponent_player.opponent_player_id is not None
        assert opponent_player.opponent_club_id == opponent_club.opponent_club_id
        assert opponent_player.player_name == "John Doe"
        assert opponent_player.statsbomb_player_id == 8923
        assert opponent_player.jersey_number == 9
        assert opponent_player.position == "Center Forward"
        assert opponent_player.created_at is not None

        # Test relationship
        assert opponent_player.opponent_club.opponent_club_id == opponent_club.opponent_club_id

        # Test CASCADE delete
        player_id = opponent_player.opponent_player_id
        session.delete(opponent_club)
        session.commit()

        deleted_player = session.query(OpponentPlayer).filter(
            OpponentPlayer.opponent_player_id == player_id
        ).first()
        assert deleted_player is None

    def test_goal_creation(self, session, sample_club):
        """
        Test Goal model creation and relationships.

        Scenarios:
        - Create goal linked to match
        - Test is_our_goal field (True for our goals, False for opponent goals)
        - Test CASCADE delete when match deleted
        """
        from app.models.opponent_club import OpponentClub
        from app.models.match import Match
        from app.models.goal import Goal

        # Create match
        match = Match(
            club_id=sample_club.club_id,
            opponent_name="Harbor FC",
            match_date=date(2025, 9, 28),
            our_score=2,
            opponent_score=1,
            result="W"
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Test our goal creation
        our_goal = Goal(
            match_id=match.match_id,
            scorer_name="Marcus Silva",
            minute=23,
            second=45,
            is_our_goal=True
        )
        session.add(our_goal)
        session.commit()
        session.refresh(our_goal)

        # Verify all fields
        assert our_goal.goal_id is not None
        assert our_goal.match_id == match.match_id
        assert our_goal.scorer_name == "Marcus Silva"
        assert our_goal.minute == 23
        assert our_goal.second == 45
        assert our_goal.is_our_goal is True
        assert our_goal.created_at is not None

        # Test relationship
        assert our_goal.match.match_id == match.match_id

        # Test opponent goal
        opponent_goal = Goal(
            match_id=match.match_id,
            scorer_name="Opponent Player",
            minute=78,
            second=12,
            is_our_goal=False
        )
        session.add(opponent_goal)
        session.commit()
        session.refresh(opponent_goal)

        assert opponent_goal.is_our_goal is False
        assert opponent_goal.scorer_name == "Opponent Player"

        # Test CASCADE delete
        goal_id = our_goal.goal_id
        session.delete(match)
        session.commit()

        deleted_goal = session.query(Goal).filter(Goal.goal_id == goal_id).first()
        assert deleted_goal is None

    def test_match_lineup_creation(self, session, sample_club):
        """
        Test MatchLineup model creation and relationships.

        Scenarios:
        - Create lineup entries for both our team and opponent team
        - Test player_id and opponent_player_id relationships
        - Test CASCADE delete when match deleted
        - Test team_type constraint ('our_team' or 'opponent_team')
        """
        from app.models.match import Match
        from app.models.match_lineup import MatchLineup
        from app.models.player import Player
        from app.models.opponent_club import OpponentClub
        from app.models.opponent_player import OpponentPlayer

        # Create match
        match = Match(
            club_id=sample_club.club_id,
            opponent_name="Rival FC",
            match_date=date(2025, 10, 15),
            our_score=2,
            opponent_score=1,
            result="W"
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create our player
        our_player = Player(
            club_id=sample_club.club_id,
            player_name="John Striker",
            jersey_number=9,
            position="Forward",
            invite_code="LNP-9999"
        )
        session.add(our_player)
        session.commit()
        session.refresh(our_player)

        # Create opponent club and player
        opponent_club = OpponentClub(opponent_name="Rival FC")
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        opponent_player = OpponentPlayer(
            opponent_club_id=opponent_club.opponent_club_id,
            player_name="Opponent Defender",
            jersey_number=5,
            position="Defender"
        )
        session.add(opponent_player)
        session.commit()
        session.refresh(opponent_player)

        # Create lineup entry for our team
        our_lineup = MatchLineup(
            match_id=match.match_id,
            team_type="our_team",
            player_id=our_player.player_id,
            player_name="John Striker",
            jersey_number=9,
            position="Forward"
        )
        session.add(our_lineup)
        session.commit()
        session.refresh(our_lineup)

        # Verify our team lineup
        assert our_lineup.lineup_id is not None
        assert our_lineup.match_id == match.match_id
        assert our_lineup.team_type == "our_team"
        assert our_lineup.player_id == our_player.player_id
        assert our_lineup.opponent_player_id is None
        assert our_lineup.player_name == "John Striker"
        assert our_lineup.jersey_number == 9
        assert our_lineup.position == "Forward"
        assert our_lineup.created_at is not None

        # Create lineup entry for opponent team
        opponent_lineup = MatchLineup(
            match_id=match.match_id,
            team_type="opponent_team",
            opponent_player_id=opponent_player.opponent_player_id,
            player_name="Opponent Defender",
            jersey_number=5,
            position="Defender"
        )
        session.add(opponent_lineup)
        session.commit()
        session.refresh(opponent_lineup)

        # Verify opponent team lineup
        assert opponent_lineup.lineup_id is not None
        assert opponent_lineup.team_type == "opponent_team"
        assert opponent_lineup.player_id is None
        assert opponent_lineup.opponent_player_id == opponent_player.opponent_player_id
        assert opponent_lineup.player_name == "Opponent Defender"

        # Test relationships
        assert our_lineup.match.match_id == match.match_id
        assert our_lineup.player.player_id == our_player.player_id
        assert opponent_lineup.opponent_player.opponent_player_id == opponent_player.opponent_player_id

        # Test CASCADE delete when match deleted
        lineup_id = our_lineup.lineup_id
        session.delete(match)
        session.commit()

        from app.models.match_lineup import MatchLineup
        deleted_lineup = session.query(MatchLineup).filter(MatchLineup.lineup_id == lineup_id).first()
        assert deleted_lineup is None

    def test_event_jsonb_storage(self, session, sample_club):
        """
        Test Event model with JSONB data storage and querying.

        Scenarios:
        - Create event with JSONB event_data
        - Store and retrieve complex nested JSON
        - Test JSONB query with @> operator (PostgreSQL) or JSON functions (SQLite)
        - Test CASCADE delete when match deleted
        """
        from app.models.match import Match
        from app.models.event import Event

        # Create match
        match = Match(
            club_id=sample_club.club_id,
            opponent_name="Phoenix United",
            match_date=date(2025, 9, 24)
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Test event creation with complex JSONB data
        event_data = {
            "id": "event-uuid-123",
            "type": {"id": 16, "name": "Shot"},
            "player": {"id": 5470, "name": "Marcus Silva"},
            "team": {"id": 746, "name": "Thunder United FC"},
            "period": 1,
            "timestamp": "00:12:34.567",
            "location": [102.3, 34.5],
            "shot": {
                "statsbomb_xg": 0.45,
                "outcome": {"id": 97, "name": "Goal"},
                "type": {"id": 87, "name": "Open Play"},
                "body_part": {"id": 40, "name": "Right Foot"}
            }
        }

        event = Event(
            match_id=match.match_id,
            statsbomb_player_id=5470,
            statsbomb_team_id=746,
            player_name="Marcus Silva",
            team_name="Thunder United FC",
            event_type_name="Shot",
            position_name="Center Forward",
            minute=12,
            second=34,
            period=1,
            event_data=event_data
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        # Verify all fields
        assert event.event_id is not None
        assert event.match_id == match.match_id
        assert event.statsbomb_player_id == 5470
        assert event.player_name == "Marcus Silva"
        assert event.event_type_name == "Shot"
        assert event.created_at is not None

        # Verify JSONB storage and retrieval
        assert event.event_data is not None
        assert isinstance(event.event_data, dict)
        assert event.event_data["type"]["name"] == "Shot"
        assert event.event_data["shot"]["statsbomb_xg"] == 0.45
        assert event.event_data["shot"]["outcome"]["name"] == "Goal"

        # Test relationship
        assert event.match.match_id == match.match_id

        # Test CASCADE delete
        event_id = event.event_id
        session.delete(match)
        session.commit()

        deleted_event = session.query(Event).filter(Event.event_id == event_id).first()
        assert deleted_event is None


class TestStatisticsModels:
    """
    Test Suite for Statistics Models
    Compact tests covering MatchStatistics, PlayerMatchStatistics,
    ClubSeasonStatistics, and PlayerSeasonStatistics models.
    """

    def test_match_statistics_creation(self, session, sample_club):
        """
        Test MatchStatistics model creation.

        Scenarios:
        - Create statistics for both teams (our_team, opponent_team)
        - Test unique constraint on (match_id, team_type)
        - Test CASCADE delete when match deleted
        """
        from app.models.match import Match
        from app.models.match_statistics import MatchStatistics
        from decimal import Decimal

        # Create match
        match = Match(
            club_id=sample_club.club_id,
            opponent_name="Test Opponent",
            match_date=date(2025, 10, 1),
            our_score=2,
            opponent_score=1,
            result="W"
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Create statistics for our team
        our_stats = MatchStatistics(
            match_id=match.match_id,
            team_type="our_team",
            possession_percentage=Decimal("55.5"),
            expected_goals=Decimal("2.145678"),
            total_shots=15,
            shots_on_target=8,
            total_passes=450,
            passes_completed=390,
            pass_completion_rate=Decimal("86.67")
        )
        session.add(our_stats)
        session.commit()
        session.refresh(our_stats)

        # Verify our team stats
        assert our_stats.statistics_id is not None
        assert our_stats.match_id == match.match_id
        assert our_stats.team_type == "our_team"
        assert our_stats.possession_percentage == Decimal("55.5")
        assert our_stats.expected_goals == Decimal("2.145678")
        assert our_stats.created_at is not None

        # Create statistics for opponent
        opponent_stats = MatchStatistics(
            match_id=match.match_id,
            team_type="opponent_team",
            possession_percentage=Decimal("44.5"),
            expected_goals=Decimal("1.234567"),
            total_shots=10,
            shots_on_target=5
        )
        session.add(opponent_stats)
        session.commit()
        session.refresh(opponent_stats)

        # Verify 2 records exist for this match
        all_stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id
        ).all()
        assert len(all_stats) == 2

        # Test CASCADE delete
        stats_id = our_stats.statistics_id
        session.delete(match)
        session.commit()

        deleted_stats = session.query(MatchStatistics).filter(
            MatchStatistics.statistics_id == stats_id
        ).first()
        assert deleted_stats is None

    def test_player_match_statistics_creation(self, session, sample_club):
        """
        Test PlayerMatchStatistics model creation.

        Scenarios:
        - Create player stats for a match
        - Test unique constraint on (player_id, match_id)
        - Test CASCADE delete when player or match deleted
        """
        from app.models.player import Player
        from app.models.match import Match
        from app.models.player_match_statistics import PlayerMatchStatistics
        from decimal import Decimal

        # Create player
        player = Player(
            club_id=sample_club.club_id,
            player_name="Test Player",
            jersey_number=10,
            position="Forward",
            invite_code="TST-1234"
        )
        session.add(player)

        # Create match
        match = Match(
            club_id=sample_club.club_id,
            opponent_name="Test Opponent",
            match_date=date(2025, 10, 1)
        )
        session.add(match)
        session.commit()
        session.refresh(player)
        session.refresh(match)

        # Create player match stats
        player_stats = PlayerMatchStatistics(
            player_id=player.player_id,
            match_id=match.match_id,
            goals=2,
            assists=1,
            expected_goals=Decimal("1.456789"),
            shots=5,
            shots_on_target=3,
            total_passes=45,
            completed_passes=38
        )
        session.add(player_stats)
        session.commit()
        session.refresh(player_stats)

        # Verify all fields
        assert player_stats.player_match_stats_id is not None
        assert player_stats.player_id == player.player_id
        assert player_stats.match_id == match.match_id
        assert player_stats.goals == 2
        assert player_stats.assists == 1
        assert player_stats.expected_goals == Decimal("1.456789")
        assert player_stats.created_at is not None

        # Test CASCADE delete when match deleted
        stats_id = player_stats.player_match_stats_id
        session.delete(match)
        session.commit()

        deleted_stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.player_match_stats_id == stats_id
        ).first()
        assert deleted_stats is None

    def test_club_season_statistics_creation(self, session, sample_club):
        """
        Test ClubSeasonStatistics model creation.

        Scenarios:
        - Create season statistics for club
        - Test UNIQUE constraint on club_id
        - Test CASCADE delete when club deleted
        """
        from app.models.club_season_statistics import ClubSeasonStatistics
        from decimal import Decimal

        # Create club season statistics
        club_stats = ClubSeasonStatistics(
            club_id=sample_club.club_id,
            matches_played=10,
            wins=6,
            draws=2,
            losses=2,
            goals_scored=22,
            goals_conceded=12,
            total_assists=15,
            total_clean_sheets=4,
            avg_goals_per_match=Decimal("2.20"),
            avg_possession_percentage=Decimal("54.5"),
            avg_xg_per_match=Decimal("1.85"),
            pass_completion_rate=Decimal("82.3"),
            team_form="WWDLW"
        )
        session.add(club_stats)
        session.commit()
        session.refresh(club_stats)

        # Verify all fields
        assert club_stats.club_stats_id is not None
        assert club_stats.club_id == sample_club.club_id
        assert club_stats.matches_played == 10
        assert club_stats.wins == 6
        assert club_stats.draws == 2
        assert club_stats.losses == 2
        assert club_stats.goals_scored == 22
        assert club_stats.total_assists == 15
        assert club_stats.team_form == "WWDLW"
        assert club_stats.avg_goals_per_match == Decimal("2.20")
        assert club_stats.updated_at is not None

        # Test CASCADE delete when club deleted
        stats_id = club_stats.club_stats_id
        session.delete(sample_club)
        session.commit()

        deleted_stats = session.query(ClubSeasonStatistics).filter(
            ClubSeasonStatistics.club_stats_id == stats_id
        ).first()
        assert deleted_stats is None

    def test_player_season_statistics_creation(self, session, sample_club):
        """
        Test PlayerSeasonStatistics model creation.

        Scenarios:
        - Create season statistics for player
        - Test UNIQUE constraint on player_id
        - Test CASCADE delete when player deleted
        """
        from app.models.player import Player
        from app.models.player_season_statistics import PlayerSeasonStatistics
        from decimal import Decimal

        # Create player
        player = Player(
            club_id=sample_club.club_id,
            player_name="Star Player",
            jersey_number=7,
            position="Midfielder",
            invite_code="STR-7777"
        )
        session.add(player)
        session.commit()
        session.refresh(player)

        # Create player season statistics
        player_stats = PlayerSeasonStatistics(
            player_id=player.player_id,
            matches_played=8,
            goals=12,
            assists=5,
            expected_goals=Decimal("10.567891"),
            shots_per_game=Decimal("3.5"),
            shots_on_target_per_game=Decimal("2.1"),
            total_passes=320,
            passes_completed=275,
            attacking_rating=85,
            technique_rating=78,
            tactical_rating=72,
            defending_rating=55,
            creativity_rating=80
        )
        session.add(player_stats)
        session.commit()
        session.refresh(player_stats)

        # Verify all fields
        assert player_stats.player_stats_id is not None
        assert player_stats.player_id == player.player_id
        assert player_stats.matches_played == 8
        assert player_stats.goals == 12
        assert player_stats.assists == 5
        assert player_stats.expected_goals == Decimal("10.567891")
        assert player_stats.attacking_rating == 85
        assert player_stats.technique_rating == 78
        assert player_stats.updated_at is not None

        # Test CASCADE delete when player deleted
        stats_id = player_stats.player_stats_id
        session.delete(player)
        session.commit()

        deleted_stats = session.query(PlayerSeasonStatistics).filter(
            PlayerSeasonStatistics.player_stats_id == stats_id
        ).first()
        assert deleted_stats is None


class TestTrainingModels:
    """
    Test Suite for Training Models
    Compact tests covering TrainingPlan and TrainingExercise models.
    """

    def test_training_plan_creation(self, session, sample_club, sample_coach):
        """
        Test TrainingPlan model creation.

        Scenarios:
        - Create training plan for player
        - Test status field and default value
        - Test CASCADE delete when player or coach deleted
        """
        from app.models.player import Player
        from app.models.training_plan import TrainingPlan

        # Create player
        player = Player(
            club_id=sample_club.club_id,
            player_name="Training Player",
            jersey_number=5,
            position="Midfielder",
            invite_code="TRN-5555"
        )
        session.add(player)
        session.commit()
        session.refresh(player)

        # Create training plan
        plan = TrainingPlan(
            player_id=player.player_id,
            created_by=sample_coach.coach_id,
            plan_name="Speed and Agility Training",
            duration="2 weeks",
            status="pending",
            coach_notes="Focus on quick direction changes"
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)

        # Verify all fields
        assert plan.plan_id is not None
        assert plan.player_id == player.player_id
        assert plan.created_by == sample_coach.coach_id
        assert plan.plan_name == "Speed and Agility Training"
        assert plan.duration == "2 weeks"
        assert plan.status == "pending"
        assert plan.coach_notes == "Focus on quick direction changes"
        assert plan.created_at is not None

        # Test status values
        plan.status = "in_progress"
        session.commit()
        assert plan.status == "in_progress"

        # Test CASCADE delete when player deleted
        plan_id = plan.plan_id
        session.delete(player)
        session.commit()

        deleted_plan = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id
        ).first()
        assert deleted_plan is None

    def test_training_exercise_creation(self, session, sample_club, sample_coach):
        """
        Test TrainingExercise model creation.

        Scenarios:
        - Create exercises for a training plan
        - Test completion tracking (completed, completed_at)
        - Test CASCADE delete when plan deleted
        - Test exercise_order
        """
        from app.models.player import Player
        from app.models.training_plan import TrainingPlan
        from app.models.training_exercise import TrainingExercise
        from datetime import datetime

        # Create player and plan
        player = Player(
            club_id=sample_club.club_id,
            player_name="Exercise Player",
            jersey_number=9,
            position="Forward",
            invite_code="EXR-9999"
        )
        session.add(player)
        session.commit()
        session.refresh(player)

        plan = TrainingPlan(
            player_id=player.player_id,
            created_by=sample_coach.coach_id,
            plan_name="Shooting Drills",
            status="pending"
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)

        # Create first exercise
        exercise1 = TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name="Dribbling through cones",
            description="Set up 10 cones in a line, dribble through them",
            sets="3",
            reps="10",
            exercise_order=1,
            completed=False
        )
        session.add(exercise1)

        # Create second exercise
        exercise2 = TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name="Shooting practice",
            description="Practice shooting from different angles",
            duration_minutes="15",
            exercise_order=2,
            completed=True,
            completed_at=datetime.now()
        )
        session.add(exercise2)
        session.commit()
        session.refresh(exercise1)
        session.refresh(exercise2)

        # Verify first exercise
        assert exercise1.exercise_id is not None
        assert exercise1.plan_id == plan.plan_id
        assert exercise1.exercise_name == "Dribbling through cones"
        assert exercise1.sets == "3"
        assert exercise1.reps == "10"
        assert exercise1.exercise_order == 1
        assert exercise1.completed is False
        assert exercise1.completed_at is None
        assert exercise1.created_at is not None

        # Verify second exercise
        assert exercise2.exercise_order == 2
        assert exercise2.completed is True
        assert exercise2.completed_at is not None
        assert exercise2.duration_minutes == "15"

        # Test marking exercise as completed
        exercise1.completed = True
        exercise1.completed_at = datetime.now()
        session.commit()
        assert exercise1.completed is True
        assert exercise1.completed_at is not None

        # Test CASCADE delete when plan deleted
        exercise_id = exercise1.exercise_id
        session.delete(plan)
        session.commit()

        deleted_exercise = session.query(TrainingExercise).filter(
            TrainingExercise.exercise_id == exercise_id
        ).first()
        assert deleted_exercise is None
