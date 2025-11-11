"""
CRUD operations for Player model.

Functions:
- get_player_by_invite_code: Find player by invite code
- link_player_to_user: Complete player signup (link to user account)
"""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.user import User
from app.crud.user import create_user


def get_player_by_invite_code(db: Session, invite_code: str) -> Optional[Player]:
    """
    Retrieve a player by invite code.

    Args:
        db: Database session
        invite_code: Player's unique invite code

    Returns:
        Player instance if found, None otherwise

    Example:
        >>> player = get_player_by_invite_code(db, "MRC-1827")
        >>> if player:
        ...     print(player.player_name)
    """
    return db.query(Player).filter(Player.invite_code == invite_code).first()


def link_player_to_user(
    db: Session,
    invite_code: str,
    player_name: str,
    email: str,
    password: str,
    birth_date: date,
    height: int,
    profile_image_url: Optional[str] = None
) -> Player:
    """
    Complete player signup: create user account and link to existing player.

    This function:
    1. Validates invite code exists and is not already linked
    2. Creates user account with user_id = player_id
    3. Updates player record with profile data
    4. Marks player as linked

    The caller is responsible for committing or rolling back the transaction.

    Args:
        db: Database session
        invite_code: Player's invite code
        player_name: Player's full name (can update from admin-created name)
        email: Player email (for user account)
        password: Plain-text password (will be hashed)
        birth_date: Player birth date
        height: Player height in cm
        profile_image_url: Optional profile image URL

    Returns:
        Updated Player instance with linked user

    Raises:
        ValueError: If invite code not found or already linked
        IntegrityError: If email already exists

    Example:
        >>> try:
        ...     player = link_player_to_user(
        ...         db,
        ...         invite_code="MRC-1827",
        ...         player_name="Marcus Silva",
        ...         email="marcus@email.com",
        ...         password="SecurePass123!",
        ...         birth_date=date(2008, 3, 20),
        ...         height=180,
        ...         profile_image_url="https://example.com/marcus.jpg"
        ...     )
        ...     db.commit()
        ... except Exception as e:
        ...     db.rollback()
        ...     raise
    """
    # 1. Get player by invite code (with row lock to prevent race conditions)
    player = (
        db.query(Player)
        .filter(Player.invite_code == invite_code)
        .with_for_update(of=Player)  # Lock only Player table, not joined tables
        .first()
    )

    if not player:
        raise ValueError(f"Invalid invite code: {invite_code}")

    if player.is_linked:
        raise ValueError(f"Invite code {invite_code} has already been used")

    # 2. Create user account with user_id = player_id
    user = create_user(
        db=db,
        email=email,
        password=password,
        full_name=player_name,
        user_type="player",
        user_id=player.player_id  # Important: use player's existing ID
    )

    # 3. Update player record
    player.player_name = player_name
    player.birth_date = birth_date
    player.height = height
    player.profile_image_url = profile_image_url

    # 4. Mark as linked
    player.complete_signup(user.user_id)

    db.flush()
    db.refresh(player)

    return player
