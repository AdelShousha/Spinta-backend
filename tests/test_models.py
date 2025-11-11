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
