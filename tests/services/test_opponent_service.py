"""
Tests for opponent club service.
"""

import pytest
from uuid import UUID

from app.services.opponent_service import get_or_create_opponent_club
from app.models.opponent_club import OpponentClub


class TestGetOrCreateOpponentClub:
    """Test get_or_create_opponent_club function."""

    def test_create_new_opponent_club(self, session):
        """Test creating a new opponent club when it doesn't exist."""
        # Given: No opponent club exists with this statsbomb_team_id
        opponent_statsbomb_team_id = 792
        opponent_name = "Australia"
        logo_url = "https://example.com/australia.png"

        # When: We call get_or_create_opponent_club
        result_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=opponent_statsbomb_team_id,
            opponent_name=opponent_name,
            logo_url=logo_url
        )

        # Then: A new opponent club is created
        # Result can be UUID (PostgreSQL) or str (SQLite)
        assert isinstance(result_id, (UUID, str))

        # Verify the club was created in database
        club = session.query(OpponentClub).filter(
            OpponentClub.statsbomb_team_id == opponent_statsbomb_team_id
        ).first()

        assert club is not None
        assert club.opponent_club_id == result_id
        assert club.statsbomb_team_id == opponent_statsbomb_team_id
        assert club.opponent_name == opponent_name
        assert club.logo_url == logo_url

    def test_get_existing_opponent_club(self, session):
        """Test retrieving an existing opponent club by statsbomb_team_id."""
        # Given: An opponent club already exists
        existing_club = OpponentClub(
            statsbomb_team_id=779,
            opponent_name="Argentina",
            logo_url="https://example.com/argentina.png"
        )
        session.add(existing_club)
        session.commit()
        session.refresh(existing_club)
        existing_id = existing_club.opponent_club_id

        # When: We call get_or_create_opponent_club with same statsbomb_team_id
        result_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=779,
            opponent_name="Argentina",  # Same name
            logo_url="https://example.com/argentina.png"
        )

        # Then: The existing club ID is returned (not a new one created)
        assert result_id == existing_id

        # Verify only one club exists with this statsbomb_team_id
        count = session.query(OpponentClub).filter(
            OpponentClub.statsbomb_team_id == 779
        ).count()
        assert count == 1

    def test_logo_url_optional(self, session):
        """Test that logo_url is optional (can be None)."""
        # Given: No logo_url provided
        opponent_statsbomb_team_id = 800
        opponent_name = "Brazil"

        # When: We call get_or_create_opponent_club without logo_url
        result_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=opponent_statsbomb_team_id,
            opponent_name=opponent_name,
            logo_url=None
        )

        # Then: Club is created successfully with None logo_url
        # Result can be UUID (PostgreSQL) or str (SQLite)
        assert isinstance(result_id, (UUID, str))

        club = session.query(OpponentClub).filter(
            OpponentClub.statsbomb_team_id == opponent_statsbomb_team_id
        ).first()

        assert club is not None
        assert club.logo_url is None

    def test_update_name_if_changed(self, session):
        """Test that opponent_name is updated if StatsBomb data has changed."""
        # Given: An opponent club exists with old name
        existing_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Australia Old Name",
            logo_url="https://example.com/australia.png"
        )
        session.add(existing_club)
        session.commit()
        session.refresh(existing_club)
        existing_id = existing_club.opponent_club_id

        # When: StatsBomb data has updated name
        new_name = "Australia"
        result_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=792,
            opponent_name=new_name,
            logo_url="https://example.com/australia.png"
        )

        # Then: Same club ID returned, but opponent_name is updated
        assert result_id == existing_id

        session.refresh(existing_club)
        assert existing_club.opponent_name == new_name

    def test_update_logo_url_if_changed(self, session):
        """Test that logo_url is updated if StatsBomb data has changed."""
        # Given: An opponent club exists with old logo
        existing_club = OpponentClub(
            statsbomb_team_id=779,
            opponent_name="Argentina",
            logo_url="https://example.com/old-logo.png"
        )
        session.add(existing_club)
        session.commit()
        session.refresh(existing_club)
        existing_id = existing_club.opponent_club_id

        # When: StatsBomb data has updated logo_url
        new_logo_url = "https://example.com/new-logo.png"
        result_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=779,
            opponent_name="Argentina",
            logo_url=new_logo_url
        )

        # Then: Same club ID returned, but logo_url is updated
        assert result_id == existing_id

        session.refresh(existing_club)
        assert existing_club.logo_url == new_logo_url

    def test_multiple_creates_return_same_id(self, session):
        """Test that multiple calls with same statsbomb_team_id return same ID."""
        # Given: Initial call creates a club
        first_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=800,
            opponent_name="Brazil",
            logo_url="https://example.com/brazil.png"
        )

        # When: We call again with same statsbomb_team_id
        second_id = get_or_create_opponent_club(
            db=session,
            opponent_statsbomb_team_id=800,
            opponent_name="Brazil",
            logo_url="https://example.com/brazil.png"
        )

        # Then: Same ID is returned
        assert first_id == second_id

        # Only one record exists
        count = session.query(OpponentClub).filter(
            OpponentClub.statsbomb_team_id == 800
        ).count()
        assert count == 1
