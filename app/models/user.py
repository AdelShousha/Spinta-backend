"""
User Model

Stores all user accounts (both coaches and players).

This is the authentication base table that links to either:
- coaches table (for coach users)
- players table (for player users after signup)

Fields (7 total):
1. user_id - UUID primary key
2. email - Unique email for login
3. password_hash - Bcrypt hashed password
4. full_name - User's full name
5. user_type - 'coach' or 'player'
6. created_at - Auto timestamp
7. updated_at - Auto timestamp

Relationships:
- One-to-one with Coach (via coach.user_id foreign key)
- One-to-one with Player (via player.user_id foreign key, when linked)
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, generate_uuid, GUID


class User(Base, TimestampMixin):
    """
    User Account Model

    Represents a user account in the system (coach or player).

    Why separate from Coach/Player?
    - Authentication is the same for both types
    - Keeps password hashing in one place
    - Allows role-based access control via user_type
    - Follows standard auth patterns
    """

    __tablename__ = "users"

    # Primary Key
    user_id = Column(
        GUID,  # Platform-independent UUID type
        primary_key=True,
        default=generate_uuid,
        comment="Unique user identifier"
    )

    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Index for fast lookup during login
        comment="User email address (used for login)"
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password (never store plain text!)"
    )

    # Profile fields
    full_name = Column(
        String(255),
        nullable=False,
        comment="User's full name"
    )

    user_type = Column(
        String(20),
        nullable=False,
        index=True,  # Index for filtering by type
        comment="Type of user: 'coach' or 'player'"
    )

    # Timestamps inherited from TimestampMixin:
    # - created_at (auto-set on creation)
    # - updated_at (auto-update on modification)

    # Relationships

    # One-to-one with Coach
    coach = relationship(
        "Coach",
        back_populates="user",
        uselist=False,  # Single object, not a list
        cascade="all, delete-orphan"  # Delete coach if user is deleted
    )

    # One-to-one with Player (only populated after player completes signup)
    player = relationship(
        "Player",
        back_populates="user",
        uselist=False,  # Single object, not a list
        cascade="all, delete-orphan"  # Delete player if user is deleted
    )

    def __repr__(self):
        """
        String representation of User for debugging.

        Returns:
            str: User info (email, type, id)
        """
        return f"<User(email='{self.email}', type='{self.user_type}', id='{self.user_id}')>"

    def is_coach(self) -> bool:
        """
        Check if user is a coach.

        Returns:
            bool: True if user_type is 'coach'
        """
        return self.user_type == "coach"

    def is_player(self) -> bool:
        """
        Check if user is a player.

        Returns:
            bool: True if user_type is 'player'
        """
        return self.user_type == "player"



"""
Example Usage:

# Creating a coach user
coach_user = User(
    email="coach@example.com",
    password_hash="$2b$12$...",  # Bcrypt hash
    full_name="John Doe",
    user_type="coach"
)
db.add(coach_user)
db.commit()

# Creating a player user
player_user = User(
    email="player@example.com",
    password_hash="$2b$12$...",
    full_name="Jane Smith",
    user_type="player"
)
db.add(player_user)
db.commit()

# Querying users
coach_users = db.query(User).filter(User.user_type == "coach").all()
user_by_email = db.query(User).filter(User.email == "coach@example.com").first()

# Using helper methods
if user.is_coach():
    print("This is a coach")
"""
