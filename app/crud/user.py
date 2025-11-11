"""
CRUD operations for User model.

Functions:
- get_user_by_email: Find user by email address
- get_user_by_id: Find user by user_id
- create_user: Create new user account
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User instance if found, None otherwise

    Example:
        >>> user = get_user_by_email(db, "john@email.com")
        >>> if user:
        ...     print(user.full_name)
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """
    Retrieve a user by user_id.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        User instance if found, None otherwise

    Example:
        >>> user = get_user_by_id(db, "550e8400-e29b-41d4-a716-446655440000")
        >>> if user:
        ...     print(user.email)
    """
    return db.query(User).filter(User.user_id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    user_type: str,
    user_id: Optional[str] = None
) -> User:
    """
    Create a new user account with hashed password.

    Args:
        db: Database session
        email: User's email address (must be unique)
        password: Plain-text password (will be hashed)
        full_name: User's full name
        user_type: 'coach' or 'player'
        user_id: Optional UUID (for player signup where user_id = player_id)

    Returns:
        Created User instance

    Raises:
        IntegrityError: If email already exists

    Example:
        >>> user = create_user(
        ...     db,
        ...     email="john@email.com",
        ...     password="SecurePass123!",
        ...     full_name="John Smith",
        ...     user_type="coach"
        ... )
        >>> print(user.user_id)
    """
    # Hash the password
    password_hash = get_password_hash(password)

    # Create user instance
    if user_id:
        # For player signup: use existing player_id as user_id
        user = User(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            user_type=user_type
        )
    else:
        # For coach signup: auto-generate UUID
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            user_type=user_type
        )

    db.add(user)
    db.flush()  # Flush to get user_id without committing transaction
    db.refresh(user)

    return user
