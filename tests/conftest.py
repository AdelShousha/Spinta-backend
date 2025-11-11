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
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
import json

from app.models.base import Base
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player
from app.core.security import get_password_hash, create_access_token
from app.database import get_db
from app.main import app


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
        club_name="Barcelona",  # Matches StatsBomb sample data
        country="Spain",
        age_group="U16",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
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


@pytest.fixture(scope="function")
def client(session):
    """
    FastAPI test client with database dependency override.

    Overrides the get_db dependency to use the test database.

    Args:
        session: Test database session

    Yields:
        TestClient: FastAPI test client for making HTTP requests
    """
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(sample_user):
    """
    Generate JWT token for authenticated requests.

    Args:
        sample_user: User from sample_user fixture

    Returns:
        str: JWT access token
    """
    token = create_access_token(
        data={
            "sub": sample_user.email,
            "user_id": str(sample_user.user_id),
            "user_type": sample_user.user_type
        }
    )
    return token


@pytest.fixture
def auth_headers(auth_token):
    """
    Authorization headers for authenticated requests.

    Args:
        auth_token: JWT token from auth_token fixture

    Returns:
        dict: Headers dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def minimal_statsbomb_events():
    """
    Minimal valid StatsBomb events for testing.

    Includes:
    - 2 Starting XI events (11 players each)
    - 1 Pass event (assist)
    - 1 Shot event (Goal)

    Returns:
        list: List of StatsBomb event dictionaries
    """
    return [
        # Barcelona Starting XI
        {
            "id": "start-xi-barcelona",
            "index": 1,
            "period": 1,
            "timestamp": "00:00:00.000",
            "minute": 0,
            "second": 0,
            "type": {"id": 35, "name": "Starting XI"},
            "possession": 1,
            "possession_team": {"id": 217, "name": "Barcelona"},
            "play_pattern": {"id": 1, "name": "Regular Play"},
            "team": {"id": 217, "name": "Barcelona"},
            "duration": 0.0,
            "tactics": {
                "formation": 442,
                "lineup": [
                    {"player": {"id": 20055, "name": "Marc-André ter Stegen"}, "position": {"id": 1, "name": "Goalkeeper"}, "jersey_number": 1},
                    {"player": {"id": 6374, "name": "Nélson Semedo"}, "position": {"id": 2, "name": "Right Back"}, "jersey_number": 2},
                    {"player": {"id": 5213, "name": "Gerard Piqué"}, "position": {"id": 3, "name": "Right Center Back"}, "jersey_number": 3},
                    {"player": {"id": 5492, "name": "Samuel Umtiti"}, "position": {"id": 5, "name": "Left Center Back"}, "jersey_number": 23},
                    {"player": {"id": 5211, "name": "Jordi Alba"}, "position": {"id": 6, "name": "Left Back"}, "jersey_number": 18},
                    {"player": {"id": 5203, "name": "Sergio Busquets"}, "position": {"id": 9, "name": "Right Defensive Midfield"}, "jersey_number": 5},
                    {"player": {"id": 5470, "name": "Ivan Rakitić"}, "position": {"id": 11, "name": "Left Defensive Midfield"}, "jersey_number": 4},
                    {"player": {"id": 6379, "name": "Arthur"}, "position": {"id": 13, "name": "Right Center Midfield"}, "jersey_number": 8},
                    {"player": {"id": 5246, "name": "Luis Suárez"}, "position": {"id": 21, "name": "Left Center Forward"}, "jersey_number": 9},
                    {"player": {"id": 5503, "name": "Lionel Messi"}, "position": {"id": 23, "name": "Center Forward"}, "jersey_number": 10},
                    {"player": {"id": 5477, "name": "Ousmane Dembélé"}, "position": {"id": 24, "name": "Right Wing"}, "jersey_number": 11}
                ]
            }
        },
        # Alavés Starting XI
        {
            "id": "start-xi-alaves",
            "index": 2,
            "period": 1,
            "timestamp": "00:00:00.000",
            "minute": 0,
            "second": 0,
            "type": {"id": 35, "name": "Starting XI"},
            "possession": 1,
            "possession_team": {"id": 217, "name": "Barcelona"},
            "play_pattern": {"id": 1, "name": "Regular Play"},
            "team": {"id": 206, "name": "Alavés"},
            "duration": 0.0,
            "tactics": {
                "formation": 433,
                "lineup": [
                    {"player": {"id": 6567, "name": "Fernando Pacheco"}, "position": {"id": 1, "name": "Goalkeeper"}, "jersey_number": 1},
                    {"player": {"id": 6560, "name": "Martín Aguirregabiria"}, "position": {"id": 2, "name": "Right Back"}, "jersey_number": 2},
                    {"player": {"id": 6568, "name": "Guillermo Maripán"}, "position": {"id": 3, "name": "Right Center Back"}, "jersey_number": 3},
                    {"player": {"id": 6565, "name": "Víctor Laguardia"}, "position": {"id": 5, "name": "Left Center Back"}, "jersey_number": 5},
                    {"player": {"id": 6569, "name": "Rubén Duarte"}, "position": {"id": 6, "name": "Left Back"}, "jersey_number": 6},
                    {"player": {"id": 6561, "name": "Tomás Pina"}, "position": {"id": 10, "name": "Center Defensive Midfield"}, "jersey_number": 10},
                    {"player": {"id": 6562, "name": "Manu García"}, "position": {"id": 13, "name": "Right Center Midfield"}, "jersey_number": 14},
                    {"player": {"id": 6566, "name": "Daniel Torres"}, "position": {"id": 15, "name": "Left Center Midfield"}, "jersey_number": 8},
                    {"player": {"id": 6563, "name": "Ibai Gómez"}, "position": {"id": 17, "name": "Left Wing"}, "jersey_number": 7},
                    {"player": {"id": 6570, "name": "Jony"}, "position": {"id": 21, "name": "Left Center Forward"}, "jersey_number": 11},
                    {"player": {"id": 6564, "name": "Borja Bastón"}, "position": {"id": 23, "name": "Center Forward"}, "jersey_number": 9}
                ]
            }
        },
        # Pass event (assist)
        {
            "id": "pass-assist",
            "index": 100,
            "period": 1,
            "timestamp": "00:15:30.000",
            "minute": 15,
            "second": 30,
            "type": {"id": 30, "name": "Pass"},
            "possession": 5,
            "possession_team": {"id": 217, "name": "Barcelona"},
            "play_pattern": {"id": 1, "name": "Regular Play"},
            "team": {"id": 217, "name": "Barcelona"},
            "player": {"id": 5470, "name": "Ivan Rakitić"},
            "position": {"id": 11, "name": "Left Defensive Midfield"},
            "location": [50.0, 40.0],
            "duration": 0.8,
            "pass": {
                "recipient": {"id": 5503, "name": "Lionel Messi"},
                "length": 15.5,
                "angle": 0.45,
                "end_location": [60.0, 45.0],
                "goal_assist": True,
                "body_part": {"id": 40, "name": "Right Foot"},
                "type": {"id": 65, "name": "Through Ball"}
            }
        },
        # Shot event (Goal)
        {
            "id": "shot-goal",
            "index": 101,
            "period": 1,
            "timestamp": "00:15:31.000",
            "minute": 15,
            "second": 31,
            "type": {"id": 16, "name": "Shot"},
            "possession": 5,
            "possession_team": {"id": 217, "name": "Barcelona"},
            "play_pattern": {"id": 1, "name": "Regular Play"},
            "team": {"id": 217, "name": "Barcelona"},
            "player": {"id": 5503, "name": "Lionel Messi"},
            "position": {"id": 23, "name": "Center Forward"},
            "location": [102.0, 38.0],
            "duration": 1.2,
            "shot": {
                "statsbomb_xg": 0.65,
                "end_location": [120.0, 40.0, 1.5],
                "key_pass_id": "pass-assist",
                "outcome": {"id": 97, "name": "Goal"},
                "type": {"id": 87, "name": "Open Play"},
                "body_part": {"id": 38, "name": "Left Foot"}
            }
        }
    ]


@pytest.fixture
def match_upload_payload(minimal_statsbomb_events):
    """
    Standard match upload request payload.

    Args:
        minimal_statsbomb_events: Events from minimal_statsbomb_events fixture

    Returns:
        dict: Match upload request body
    """
    return {
        "opponent_name": "Alavés",
        "match_date": "2018-08-18",
        "match_time": "20:15:00",
        "is_home_match": True,
        "home_score": 1,
        "away_score": 0,
        "statsbomb_events": minimal_statsbomb_events
    }
