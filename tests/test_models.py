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

    def test_create_user_with_all_fields(self, session):
        """
        Test creating a user with all required fields.

        Expected: User is created successfully with all fields set.
        """
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

    def test_user_email_must_be_unique(self, session, sample_user):
        """
        Test that duplicate emails are rejected.

        Expected: IntegrityError when creating user with existing email.
        """
        duplicate_user = User(
            email=sample_user.email,  # Same email as sample_user
            password_hash="$2b$12$different_hash",
            full_name="Different User",
            user_type="player"
        )
        session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_user_is_coach_method(self, session):
        """
        Test the is_coach() helper method.

        Expected: Returns True for coaches, False for players.
        """
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

    def test_user_is_player_method(self, session):
        """
        Test the is_player() helper method.

        Expected: Returns True for players, False for coaches.
        """
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

    def test_user_repr(self, sample_user):
        """
        Test the __repr__ method for debugging.

        Expected: Returns formatted string with user info.
        """
        repr_string = repr(sample_user)
        assert "User" in repr_string
        assert sample_user.email in repr_string
        assert sample_user.user_type in repr_string


class TestCoachModel:
    """
    Test Suite for Coach Model

    Tests coach creation, user relationship, and optional fields.
    """

    def test_create_coach_with_user_id(self, session, sample_user):
        """
        Test creating a coach linked to a user.

        Expected: Coach is created with auto-generated coach_id and user_id link.
        """
        coach = Coach(
            user_id=sample_user.user_id,
            birth_date=date(1990, 1, 1),
            gender="male"
        )
        session.add(coach)
        session.commit()
        session.refresh(coach)

        # Verify fields
        assert coach.coach_id is not None, "coach_id should be auto-generated"
        assert coach.user_id == sample_user.user_id
        assert coach.birth_date == date(1990, 1, 1)
        assert coach.gender == "male"
        assert coach.created_at is not None
        assert coach.updated_at is not None

    def test_coach_user_id_must_be_unique(self, session, sample_coach):
        """
        Test that one user can only have one coach record.

        Expected: IntegrityError when creating second coach with same user_id.
        """
        duplicate_coach = Coach(
            user_id=sample_coach.user_id,  # Same user_id
            birth_date=date(1985, 5, 15)
        )
        session.add(duplicate_coach)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_coach_user_relationship(self, session, sample_coach, sample_user):
        """
        Test one-to-one relationship between coach and user.

        Expected: Coach can access user data via relationship.
        """
        # Access user from coach
        assert sample_coach.user is not None
        assert sample_coach.user.email == sample_user.email

        # Access coach from user
        assert sample_user.coach is not None
        assert sample_user.coach.coach_id == sample_coach.coach_id

    def test_coach_email_property(self, session, sample_coach, sample_user):
        """
        Test the email convenience property.

        Expected: Coach.email returns user's email.
        """
        assert sample_coach.email == sample_user.email

    def test_coach_full_name_property(self, session, sample_coach, sample_user):
        """
        Test the full_name convenience property.

        Expected: Coach.full_name returns user's full_name.
        """
        assert sample_coach.full_name == sample_user.full_name

    def test_coach_optional_fields_can_be_null(self, session, sample_user):
        """
        Test that birth_date and gender are optional.

        Expected: Coach can be created with NULL optional fields.
        """
        coach = Coach(user_id=sample_user.user_id)
        session.add(coach)
        session.commit()
        session.refresh(coach)

        assert coach.birth_date is None
        assert coach.gender is None

    def test_delete_user_cascades_to_coach(self, session, sample_user, sample_coach):
        """
        Test CASCADE delete from user to coach.

        Expected: Deleting user also deletes associated coach.
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

    def test_create_club_with_all_fields(self, session, sample_coach):
        """
        Test creating a club with all fields.

        Expected: Club is created with all fields set correctly.
        """
        club = Club(
            coach_id=sample_coach.coach_id,
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
        assert club.coach_id == sample_coach.coach_id
        assert club.club_name == "Manchester City U16"
        assert club.statsbomb_team_id == 123
        assert club.country == "England"
        assert club.age_group == "U16"
        assert club.stadium == "Etihad Campus"
        assert club.logo_url == "https://example.com/logo.png"
        assert club.created_at is not None
        assert club.updated_at is not None

    def test_club_coach_id_must_be_unique(self, session, sample_club):
        """
        Test that one coach can only have one club.

        Expected: IntegrityError when creating second club for same coach.
        """
        duplicate_club = Club(
            coach_id=sample_club.coach_id,  # Same coach_id
            club_name="Another Club"
        )
        session.add(duplicate_club)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_club_statsbomb_team_id_must_be_unique(self, session, sample_coach):
        """
        Test that StatsBomb team IDs are unique.

        Expected: IntegrityError when using duplicate statsbomb_team_id.
        """
        # Create first club with statsbomb_team_id
        club1 = Club(
            coach_id=sample_coach.coach_id,
            club_name="Club 1",
            statsbomb_team_id=999
        )
        session.add(club1)
        session.commit()

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

        # Try to create club with duplicate statsbomb_team_id
        club2 = Club(
            coach_id=coach2.coach_id,
            club_name="Club 2",
            statsbomb_team_id=999  # Same StatsBomb ID
        )
        session.add(club2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_club_coach_relationship(self, session, sample_club, sample_coach):
        """
        Test one-to-one relationship between club and coach.

        Expected: Club can access coach, coach can access club.
        """
        # Access coach from club
        assert sample_club.coach is not None
        assert sample_club.coach.coach_id == sample_coach.coach_id

        # Access club from coach
        assert sample_coach.club is not None
        assert sample_coach.club.club_id == sample_club.club_id

    def test_club_coach_name_property(self, session, sample_club, sample_user):
        """
        Test the coach_name convenience property.

        Expected: Club.coach_name returns coach's full name.
        """
        assert sample_club.coach_name == sample_user.full_name

    def test_club_optional_fields_can_be_null(self, session, sample_coach):
        """
        Test that optional fields can be NULL.

        Expected: Club can be created with minimal fields.
        """
        club = Club(
            coach_id=sample_coach.coach_id,
            club_name="Minimal Club"
            # All other fields NULL
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        assert club.statsbomb_team_id is None
        assert club.country is None
        assert club.age_group is None
        assert club.stadium is None
        assert club.logo_url is None

    def test_delete_coach_cascades_to_club(self, session, sample_coach, sample_club):
        """
        Test CASCADE delete from coach to club.

        Expected: Deleting coach also deletes associated club.
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

    def test_create_incomplete_player(self, session, sample_club):
        """
        Test creating an incomplete player (before signup).

        Expected: Player is created with user_id = NULL, is_linked = False.
        """
        player = Player(
            club_id=sample_club.club_id,
            player_name="John Smith",
            statsbomb_player_id=456,
            jersey_number=10,
            position="Forward",
            invite_code="ABC-1234",
            is_linked=False
        )
        session.add(player)
        session.commit()
        session.refresh(player)

        # Verify incomplete state
        assert player.player_id is not None
        assert player.user_id is None, "Incomplete player should have NULL user_id"
        assert player.is_linked is False
        assert player.linked_at is None
        assert player.birth_date is None
        assert player.height is None
        assert player.profile_image_url is None

        # Verify basic fields
        assert player.club_id == sample_club.club_id
        assert player.player_name == "John Smith"
        assert player.jersey_number == 10
        assert player.position == "Forward"
        assert player.invite_code == "ABC-1234"

    def test_create_complete_player(self, session, sample_club, sample_player_user):
        """
        Test creating a complete player (after signup).

        Expected: Player is created with user_id set, is_linked = True.
        """
        player = Player(
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
        session.add(player)
        session.commit()
        session.refresh(player)

        # Verify complete state
        assert player.user_id == sample_player_user.user_id
        assert player.is_linked is True
        assert player.linked_at is not None
        assert player.birth_date == date(2008, 3, 15)
        assert player.height == 175
        assert player.profile_image_url == "https://example.com/photo.jpg"

    def test_player_complete_signup_method(self, session, sample_incomplete_player, sample_player_user):
        """
        Test the complete_signup() method.

        Expected: Player transitions from incomplete to complete state.
        """
        # Before signup
        assert sample_incomplete_player.user_id is None
        assert sample_incomplete_player.is_linked is False
        assert sample_incomplete_player.linked_at is None

        # Complete signup
        sample_incomplete_player.complete_signup(sample_player_user.user_id)
        session.commit()
        session.refresh(sample_incomplete_player)

        # After signup
        assert sample_incomplete_player.user_id == sample_player_user.user_id
        assert sample_incomplete_player.is_linked is True
        assert sample_incomplete_player.linked_at is not None

    def test_player_invite_code_must_be_unique(self, session, sample_club):
        """
        Test that invite codes are unique.

        Expected: IntegrityError when using duplicate invite code.
        """
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

    def test_player_user_id_must_be_unique_when_set(self, session, sample_club, sample_player_user):
        """
        Test that one user can only link to one player.

        Expected: IntegrityError when two players have same user_id.
        """
        player1 = Player(
            user_id=sample_player_user.user_id,
            club_id=sample_club.club_id,
            player_name="Player 1",
            jersey_number=1,
            position="Forward",
            invite_code="UNQ-1111",
            is_linked=True
        )
        session.add(player1)
        session.commit()

        player2 = Player(
            user_id=sample_player_user.user_id,  # Same user_id
            club_id=sample_club.club_id,
            player_name="Player 2",
            jersey_number=2,
            position="Defender",
            invite_code="UNQ-2222",
            is_linked=True
        )
        session.add(player2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_player_club_relationship(self, session, sample_incomplete_player, sample_club):
        """
        Test many-to-one relationship between player and club.

        Expected: Player can access club, club can access players.
        """
        # Access club from player
        assert sample_incomplete_player.club is not None
        assert sample_incomplete_player.club.club_id == sample_club.club_id

        # Access players from club
        assert len(sample_club.players) > 0
        player_ids = [p.player_id for p in sample_club.players]
        assert sample_incomplete_player.player_id in player_ids

    def test_player_user_relationship(self, session, sample_complete_player, sample_player_user):
        """
        Test one-to-one relationship between player and user.

        Expected: Complete player can access user, user can access player.
        """
        # Access user from player
        assert sample_complete_player.user is not None
        assert sample_complete_player.user.user_id == sample_player_user.user_id

        # Access player from user
        assert sample_player_user.player is not None
        assert sample_player_user.player.player_id == sample_complete_player.player_id

    def test_player_email_property(self, session, sample_complete_player, sample_player_user):
        """
        Test the email convenience property.

        Expected: Complete player returns user's email, incomplete returns None.
        """
        # Complete player has email
        assert sample_complete_player.email == sample_player_user.email

    def test_player_email_property_incomplete(self, session, sample_incomplete_player):
        """
        Test email property for incomplete player.

        Expected: Returns None when player has no user.
        """
        assert sample_incomplete_player.email is None

    def test_player_is_incomplete_property(self, session, sample_incomplete_player, sample_complete_player):
        """
        Test the is_incomplete property.

        Expected: Returns True for unlinked players, False for linked.
        """
        assert sample_incomplete_player.is_incomplete is True
        assert sample_complete_player.is_incomplete is False

    def test_delete_club_cascades_to_players(self, session, sample_club, sample_incomplete_player):
        """
        Test CASCADE delete from club to players.

        Expected: Deleting club also deletes all associated players.
        """
        player_id = sample_incomplete_player.player_id

        # Delete club
        session.delete(sample_club)
        session.commit()

        # Player should be deleted
        deleted_player = session.query(Player).filter(Player.player_id == player_id).first()
        assert deleted_player is None

    def test_delete_user_cascades_to_complete_player(self, session, sample_complete_player, sample_player_user):
        """
        Test CASCADE delete from user to complete player.

        Expected: Deleting user also deletes linked player.
        """
        player_id = sample_complete_player.player_id

        # Delete user
        session.delete(sample_player_user)
        session.commit()

        # Player should be deleted
        deleted_player = session.query(Player).filter(Player.player_id == player_id).first()
        assert deleted_player is None


class TestFullDataFlow:
    """
    Integration tests for complete workflows.

    Tests realistic scenarios involving multiple models.
    """

    def test_coach_registration_flow(self, session):
        """
        Test complete coach registration flow.

        Simulates: User signs up → Coach record created → Club created
        """
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

    def test_player_signup_flow(self, session, sample_club):
        """
        Test complete player signup flow.

        Simulates: Admin creates incomplete player → Player signs up → Profile completed
        """
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

        When user is deleted:
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
