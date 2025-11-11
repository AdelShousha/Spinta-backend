"""
Pytest Configuration and Fixtures

This file contains shared fixtures for all tests.

Fixtures are reusable components that set up test environments.
They run before tests and provide resources like database sessions.

Key Fixtures:
- engine: SQLAlchemy engine for test database
- session: Database session for each test (isolated, rolled back)
- sample_user: Pre-created user for testing
- sample_coach: Pre-created coach for testing
- sample_club: Pre-created club for testing
- sample_player: Pre-created player for testing
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, datetime

from app.models.base import Base
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player
from app.core.security import get_password_hash


# Test Database Configuration
# Using SQLite in-memory for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine():
    """
    Create a test database engine.

    Scope: function (new database for each test)

    Why SQLite in-memory?
    - Fast: No disk I/O
    - Isolated: Each test gets clean database
    - No cleanup needed: Database disappears after test

    IMPORTANT: check_same_thread=False allows the in-memory database
    to be accessed from FastAPI's threadpool during endpoint testing.

    Yields:
        SQLAlchemy Engine connected to in-memory SQLite database
    """
    # Create engine with thread-safety for SQLite
    # This is crucial for FastAPI TestClient which uses threads
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},  # Allow cross-thread access
        poolclass=StaticPool  # Use single connection pool for in-memory DB
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Cleanup: Drop all tables
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """
    Create a database session for testing.

    Scope: function (new session for each test)

    Each test gets a fresh session that's rolled back after the test.
    This ensures test isolation - no test affects another.

    Args:
        engine: SQLAlchemy engine from engine fixture

    Yields:
        SQLAlchemy Session for database operations
    """
    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        # Rollback any uncommitted changes
        db.rollback()
        db.close()


@pytest.fixture
def sample_user(session):
    """
    Create a sample user for testing.

    Useful for tests that need an existing user.
    Password is "password123" (hashed with bcrypt).

    Args:
        session: Database session from session fixture

    Returns:
        User: A committed user record
    """
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("password123"),  # Real bcrypt hash
        full_name="Test User",
        user_type="coach"
    )
    session.add(user)
    session.commit()
    session.refresh(user)  # Get database-generated fields
    return user


@pytest.fixture
def sample_coach(session, sample_user):
    """
    Create a sample coach for testing.

    Depends on sample_user fixture (creates user first).

    Args:
        session: Database session
        sample_user: User from sample_user fixture

    Returns:
        Coach: A committed coach record linked to sample_user
    """
    coach = Coach(
        user_id=sample_user.user_id,
        birth_date=date(1985, 5, 15),
        gender="male"
    )
    session.add(coach)
    session.commit()
    session.refresh(coach)
    return coach


@pytest.fixture
def sample_club(session, sample_coach):
    """
    Create a sample club for testing.

    Depends on sample_coach fixture (creates user and coach first).

    Args:
        session: Database session
        sample_coach: Coach from sample_coach fixture

    Returns:
        Club: A committed club record owned by sample_coach
    """
    club = Club(
        coach_id=sample_coach.coach_id,
        club_name="Test FC",
        country="England",
        age_group="U16"
    )
    session.add(club)
    session.commit()
    session.refresh(club)
    return club


@pytest.fixture
def sample_incomplete_player(session, sample_club):
    """
    Create a sample incomplete player for testing.

    This represents a player BEFORE signup (user_id is NULL).

    Args:
        session: Database session
        sample_club: Club from sample_club fixture

    Returns:
        Player: A committed incomplete player record
    """
    player = Player(
        club_id=sample_club.club_id,
        player_name="Test Player",
        jersey_number=10,
        position="Forward",
        invite_code="TST-1234",
        is_linked=False
        # user_id is NULL
    )
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


@pytest.fixture
def sample_player_user(session):
    """
    Create a sample player user account for testing.

    This is separate from sample_user (which is a coach).
    Password is "password123" (hashed with bcrypt).

    Args:
        session: Database session

    Returns:
        User: A committed player user record
    """
    user = User(
        email="player@example.com",
        password_hash=get_password_hash("password123"),  # Real bcrypt hash
        full_name="Test Player User",
        user_type="player"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def sample_complete_player(session, sample_club, sample_player_user):
    """
    Create a sample complete player for testing.

    This represents a player AFTER signup (user_id is set).

    Args:
        session: Database session
        sample_club: Club from sample_club fixture
        sample_player_user: User from sample_player_user fixture

    Returns:
        Player: A committed complete player record
    """
    player = Player(
        user_id=sample_player_user.user_id,
        club_id=sample_club.club_id,
        player_name="Complete Player",
        jersey_number=7,
        position="Midfielder",
        invite_code="CMP-5678",
        is_linked=True,
        linked_at=datetime.utcnow(),
        birth_date=date(2008, 3, 15),
        height=175
    )
    session.add(player)
    session.commit()
    session.refresh(player)
    return player
