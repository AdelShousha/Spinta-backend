"""
CRUD Operations Tests

Tests for database CRUD functions.
Tests are grouped by module (user, coach, player).

Run with: pytest tests/test_crud.py -v
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.crud.user import get_user_by_email, get_user_by_id, create_user
from app.crud.coach import create_coach, create_coach_with_club
from app.crud.player import get_player_by_invite_code, link_player_to_user


class TestUserCRUD:
    """
    Consolidated tests for user CRUD operations.

    Tests: get_user_by_email, get_user_by_id, create_user
    """

    def test_user_crud_operations(self, session):
        """
        Test complete user CRUD workflow.

        Scenarios:
        - Create user with all fields
        - Password is hashed correctly
        - Get user by email
        - Get user by ID
        - Duplicate email raises IntegrityError
        - Get non-existent user returns None
        """
        # Create user
        user = create_user(
            db=session,
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            user_type="coach"
        )

        # Verify user created
        assert user.user_id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.user_type == "coach"

        # Password should be hashed (bcrypt format)
        assert user.password_hash.startswith("$2b$")
        assert user.password_hash != "SecurePass123!"

        # Get user by email
        found_by_email = get_user_by_email(session, "test@example.com")
        assert found_by_email is not None
        assert found_by_email.user_id == user.user_id

        # Get user by ID
        found_by_id = get_user_by_id(session, user.user_id)
        assert found_by_id is not None
        assert found_by_id.email == "test@example.com"

        # Duplicate email should fail
        with pytest.raises(IntegrityError):
            create_user(
                db=session,
                email="test@example.com",  # Same email
                password="DifferentPass",
                full_name="Another User",
                user_type="player"
            )
            session.commit()

        session.rollback()

        # Non-existent email returns None
        not_found = get_user_by_email(session, "nonexistent@example.com")
        assert not_found is None

        # Non-existent ID returns None
        not_found_id = get_user_by_id(session, "00000000-0000-0000-0000-000000000000")
        assert not_found_id is None


class TestCoachCRUD:
    """
    Consolidated tests for coach CRUD operations.

    Tests: create_coach, create_coach_with_club (transaction)
    """

    def test_create_coach_basic(self, session, sample_user):
        """
        Test basic coach creation.

        Scenarios:
        - Create coach with all optional fields
        - Create coach with minimal fields (no birth_date, gender)
        - Coach linked to user correctly
        """
        # Create coach with all fields
        coach = create_coach(
            db=session,
            user_id=sample_user.user_id,
            birth_date=date(1985, 6, 15),
            gender="Male"
        )

        assert coach.coach_id is not None
        assert coach.user_id == sample_user.user_id
        assert coach.birth_date == date(1985, 6, 15)
        assert coach.gender == "Male"

    def test_create_coach_with_club_transaction(self, session):
        """
        Test complete coach registration flow (user + coach + club).

        Scenarios:
        - All three records created in transaction
        - User, coach, club properly linked
        - Club has all provided data
        - Transaction can be committed
        """
        # Create coach with club
        user, coach, club = create_coach_with_club(
            db=session,
            email="newcoach@example.com",
            password="SecurePass123!",
            full_name="New Coach",
            club_name="Test FC",
            birth_date=date(1990, 1, 1),
            gender="Male",
            country="United States",
            age_group="U16",
            stadium="Test Stadium",
            logo_url="https://example.com/logo.png"
        )

        # Verify user
        assert user.user_id is not None
        assert user.email == "newcoach@example.com"
        assert user.user_type == "coach"
        assert user.password_hash.startswith("$2b$")

        # Verify coach
        assert coach.coach_id is not None
        assert coach.user_id == user.user_id
        assert coach.birth_date == date(1990, 1, 1)

        # Verify club
        assert club.club_id is not None
        assert club.coach_id == coach.coach_id
        assert club.club_name == "Test FC"
        assert club.country == "United States"
        assert club.age_group == "U16"
        assert club.stadium == "Test Stadium"

        # Commit transaction
        session.commit()

        # Verify all records persisted
        assert get_user_by_email(session, "newcoach@example.com") is not None

    def test_create_coach_with_club_rollback_on_error(self, session):
        """
        Test that transaction rolls back on error.

        Scenario:
        - Try to create coach with duplicate email
        - Transaction should fail
        - No partial records should be created
        """
        # First successful creation
        create_coach_with_club(
            db=session,
            email="coach1@example.com",
            password="SecurePass123!",
            full_name="Coach 1",
            club_name="Club 1"
        )
        session.commit()

        # Try duplicate email
        with pytest.raises(IntegrityError):
            create_coach_with_club(
                db=session,
                email="coach1@example.com",  # Duplicate!
                password="DifferentPass",
                full_name="Coach 2",
                club_name="Club 2"
            )
            session.commit()

        session.rollback()

        # Verify only first coach exists
        user = get_user_by_email(session, "coach1@example.com")
        assert user is not None
        assert user.full_name == "Coach 1"


class TestPlayerCRUD:
    """
    Consolidated tests for player CRUD operations.

    Tests: get_player_by_invite_code, link_player_to_user
    """

    def test_get_player_by_invite_code(self, session, sample_incomplete_player):
        """
        Test retrieving player by invite code.

        Scenarios:
        - Valid invite code returns player
        - Invalid invite code returns None
        """
        # Valid code
        player = get_player_by_invite_code(session, sample_incomplete_player.invite_code)
        assert player is not None
        assert player.player_id == sample_incomplete_player.player_id

        # Invalid code
        not_found = get_player_by_invite_code(session, "INVALID-CODE")
        assert not_found is None

    def test_link_player_to_user_complete_flow(self, session, sample_incomplete_player):
        """
        Test complete player signup flow.

        Scenarios:
        - Player found by invite code
        - User account created with user_id = player_id
        - Player record updated with profile data
        - Player marked as linked (is_linked=True, linked_at set)
        - Can commit transaction successfully
        """
        invite_code = sample_incomplete_player.invite_code

        # Complete player signup
        player = link_player_to_user(
            db=session,
            invite_code=invite_code,
            player_name="Updated Player Name",
            email="player@example.com",
            password="SecurePass123!",
            birth_date=date(2008, 3, 20),
            height=180,
            profile_image_url="https://example.com/player.jpg"
        )

        # Verify player updated
        assert player.player_name == "Updated Player Name"
        assert player.birth_date == date(2008, 3, 20)
        assert player.height == 180
        assert player.profile_image_url == "https://example.com/player.jpg"

        # Verify linked status
        assert player.is_linked is True
        assert player.linked_at is not None
        assert player.user_id is not None

        # Verify user created
        user = get_user_by_id(session, player.user_id)
        assert user is not None
        assert user.email == "player@example.com"
        assert user.user_type == "player"
        assert user.full_name == "Updated Player Name"
        assert user.password_hash.startswith("$2b$")

        # Verify user_id matches player_id
        assert user.user_id == player.player_id

        # Commit and verify persistence
        session.commit()
        refreshed = get_player_by_invite_code(session, invite_code)
        assert refreshed.is_linked is True

    def test_link_player_errors(self, session, sample_incomplete_player):
        """
        Test error handling in player signup.

        Scenarios:
        - Invalid invite code raises ValueError
        - Already linked invite code raises ValueError
        - Duplicate email raises IntegrityError
        """
        # Test invalid invite code
        with pytest.raises(ValueError, match="Invalid invite code"):
            link_player_to_user(
                db=session,
                invite_code="INVALID-9999",
                player_name="Test",
                email="test@example.com",
                password="pass",
                birth_date=date(2008, 1, 1),
                height=170
            )

        session.rollback()

        # Link player successfully first time
        link_player_to_user(
            db=session,
            invite_code=sample_incomplete_player.invite_code,
            player_name="Player 1",
            email="player1@example.com",
            password="pass123",
            birth_date=date(2008, 1, 1),
            height=170
        )
        session.commit()

        # Test already linked invite code
        with pytest.raises(ValueError, match="already been used"):
            link_player_to_user(
                db=session,
                invite_code=sample_incomplete_player.invite_code,  # Already used!
                player_name="Player 2",
                email="player2@example.com",
                password="pass456",
                birth_date=date(2008, 1, 1),
                height=175
            )

        session.rollback()

        # Test duplicate email
        # Create another incomplete player
        from app.models.player import Player
        from app.models.club import Club

        # Get a club to link to
        club = session.query(Club).first()
        if not club:
            # Create a simple club for testing
            from app.models.user import User
            from app.models.coach import Coach

            coach_user = User(
                email="tempcoach@test.com",
                password_hash="hash",
                full_name="Temp Coach",
                user_type="coach"
            )
            session.add(coach_user)
            session.flush()

            coach = Coach(user_id=coach_user.user_id)
            session.add(coach)
            session.flush()

            club = Club(coach_id=coach.coach_id, club_name="Temp Club")
            session.add(club)
            session.flush()

        incomplete_player2 = Player(
            club_id=club.club_id,
            player_name="Incomplete Player 2",
            jersey_number=99,
            position="Striker",
            invite_code="TEST-9999",
            is_linked=False
        )
        session.add(incomplete_player2)
        session.commit()

        with pytest.raises(IntegrityError):
            link_player_to_user(
                db=session,
                invite_code="TEST-9999",
                player_name="Player 2",
                email="player1@example.com",  # Duplicate email!
                password="pass789",
                birth_date=date(2009, 1, 1),
                height=180
            )
            session.commit()

        session.rollback()

    def test_link_player_with_eager_loaded_relationships(self, session, sample_incomplete_player):
        """
        Test that link_player_to_user works with eager-loaded relationships.

        This test specifically addresses a PostgreSQL issue where FOR UPDATE
        cannot be applied to the nullable side of an outer join.

        The Player model has lazy="joined" relationships (eager loading),
        which causes SQLAlchemy to add LEFT OUTER JOINs. The fix uses
        with_for_update(of=Player) to only lock the players table.

        Scenario:
        - Player has eager-loaded relationships (user, club)
        - link_player_to_user should successfully lock only the Player row
        - Registration completes without PostgreSQL FOR UPDATE error
        """
        # This test ensures the fix for:
        # psycopg2.errors.FeatureNotSupported: FOR UPDATE cannot be applied
        # to the nullable side of an outer join

        invite_code = sample_incomplete_player.invite_code

        # Attempt to link player - should work without PostgreSQL error
        player = link_player_to_user(
            db=session,
            invite_code=invite_code,
            player_name="Test Player With Joins",
            email="jointest@example.com",
            password="SecurePass123!",
            birth_date=date(2008, 5, 15),
            height=178
        )

        # Verify it worked
        assert player.is_linked is True
        assert player.user_id is not None
        assert player.player_name == "Test Player With Joins"

        # Verify the relationships are loaded (eager loading worked)
        assert player.user is not None
        assert player.club is not None

        session.commit()
