"""
Opponent club service.

This module provides database operations for opponent clubs.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.opponent_club import OpponentClub


def get_or_create_opponent_club(
    db: Session,
    opponent_statsbomb_team_id: int,
    opponent_name: str,
    logo_url: Optional[str] = None
) -> UUID:
    """
    Get or create opponent club record.

    Retrieves existing opponent club by statsbomb_team_id, or creates new one if not found.
    Updates name and logo_url if they have changed in StatsBomb data.

    Args:
        db: Database session
        opponent_statsbomb_team_id: StatsBomb team ID for opponent
        opponent_name: Opponent team name
        logo_url: Optional logo URL for opponent team

    Returns:
        UUID: The opponent_club_id (existing or newly created)
    """
    # Check if opponent club exists by statsbomb_team_id
    opponent_club = db.query(OpponentClub).filter(
        OpponentClub.statsbomb_team_id == opponent_statsbomb_team_id
    ).first()

    if opponent_club:
        # Update opponent_name and logo_url if changed
        if opponent_club.opponent_name != opponent_name:
            opponent_club.opponent_name = opponent_name

        if opponent_club.logo_url != logo_url:
            opponent_club.logo_url = logo_url

        db.flush()  # Flush changes without committing (caller manages transaction)

        return opponent_club.opponent_club_id

    else:
        # Create new opponent club
        new_opponent_club = OpponentClub(
            statsbomb_team_id=opponent_statsbomb_team_id,
            opponent_name=opponent_name,
            logo_url=logo_url
        )

        db.add(new_opponent_club)
        db.flush()  # Flush to database without committing (caller manages transaction)

        return new_opponent_club.opponent_club_id
