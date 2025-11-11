"""
CRUD operations for Coach and Club models.

Functions:
- create_coach: Create coach record
- create_coach_with_club: Create coach + club in a transaction (for registration)
"""

from datetime import date
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.coach import Coach
from app.models.club import Club
from app.models.user import User
from app.crud.user import create_user


def create_coach(
    db: Session,
    user_id: str,
    birth_date: Optional[date] = None,
    gender: Optional[str] = None
) -> Coach:
    """
    Create a coach record linked to a user.

    Args:
        db: Database session
        user_id: UUID of the user account
        birth_date: Optional birth date
        gender: Optional gender

    Returns:
        Created Coach instance

    Example:
        >>> coach = create_coach(
        ...     db,
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     birth_date=date(1985, 6, 15),
        ...     gender="Male"
        ... )
    """
    coach = Coach(
        user_id=user_id,
        birth_date=birth_date,
        gender=gender
    )

    db.add(coach)
    db.flush()
    db.refresh(coach)

    return coach


def create_coach_with_club(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    club_name: str,
    birth_date: Optional[date] = None,
    gender: Optional[str] = None,
    country: Optional[str] = None,
    age_group: Optional[str] = None,
    stadium: Optional[str] = None,
    logo_url: Optional[str] = None
) -> Tuple[User, Coach, Club]:
    """
    Create user, coach, and club records in a single transaction.

    This function is used for coach registration endpoint.
    It creates all three records and returns them.

    The caller is responsible for committing or rolling back the transaction.

    Args:
        db: Database session
        email: Coach email (for user account)
        password: Plain-text password (will be hashed)
        full_name: Coach full name
        club_name: Club name (required)
        birth_date: Optional coach birth date
        gender: Optional coach gender
        country: Optional club country
        age_group: Optional team age group
        stadium: Optional stadium name
        logo_url: Optional club logo URL

    Returns:
        Tuple of (User, Coach, Club) instances

    Raises:
        IntegrityError: If email already exists or other constraint violations

    Example:
        >>> try:
        ...     user, coach, club = create_coach_with_club(
        ...         db,
        ...         email="john@email.com",
        ...         password="SecurePass123!",
        ...         full_name="John Smith",
        ...         club_name="Thunder United FC",
        ...         birth_date=date(1985, 6, 15),
        ...         gender="Male",
        ...         country="United States",
        ...         age_group="U16"
        ...     )
        ...     db.commit()
        ... except Exception as e:
        ...     db.rollback()
        ...     raise
    """
    # 1. Create user account
    user = create_user(
        db=db,
        email=email,
        password=password,
        full_name=full_name,
        user_type="coach"
    )

    # 2. Create coach record
    coach = create_coach(
        db=db,
        user_id=user.user_id,
        birth_date=birth_date,
        gender=gender
    )

    # 3. Create club record
    club = Club(
        coach_id=coach.coach_id,
        club_name=club_name,
        country=country,
        age_group=age_group,
        stadium=stadium,
        logo_url=logo_url
    )

    db.add(club)
    db.flush()
    db.refresh(club)

    return user, coach, club
