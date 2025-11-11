"""
Coach Model

Stores coach-specific information.

This table has a one-to-one relationship with users table via user_id.
When a user registers as a coach, a coach record is created with their user_id.

Fields (6 total):
1. coach_id - UUID primary key (separate from user_id)
2. user_id - UUID foreign key to users (UNIQUE, NOT NULL)
3. birth_date - Coach's birth date (NULL)
4. gender - Coach's gender (NULL)
5. created_at - Auto timestamp
6. updated_at - Auto timestamp

Relationships:
- One-to-one with User (via user_id foreign key)
- One-to-one with Club (coach creates/owns one club)
"""

from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, generate_uuid, GUID


class Coach(Base, TimestampMixin):
    """
    Coach Account Model

    Represents coach-specific data linked to a user account.

    Design Pattern:
    - coach_id is a separate primary key (auto-generated)
    - user_id is a foreign key with UNIQUE constraint
    - This keeps PK independent from FK (cleaner, more flexible)

    Why separate coach_id from user_id?
    - Clearer data model (PK vs FK are different concepts)
    - Easier to understand relationships
    - More flexible for future changes
    - Standard database design pattern
    """

    __tablename__ = "coaches"

    # Primary Key (separate from user_id)
    coach_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique coach identifier"
    )

    # Foreign Key to Users table
    user_id = Column(
        GUID,
        ForeignKey('users.user_id', ondelete='CASCADE'),  # Delete coach if user is deleted
        unique=True,  # One coach per user
        nullable=False,  # Must have a linked user
        index=True,  # Index for fast lookups
        comment="Reference to user account (one-to-one)"
    )

    # Profile fields (optional, can be filled later)
    birth_date = Column(
        Date,
        nullable=True,
        comment="Coach's birth date"
    )

    gender = Column(
        String(20),
        nullable=True,
        comment="Coach's gender"
    )

    # Timestamps inherited from TimestampMixin:
    # - created_at (auto-set on creation)
    # - updated_at (auto-update on modification)

    # Relationships

    # One-to-one with User
    user = relationship(
        "User",
        back_populates="coach",  # Will add this to User model
        uselist=False,  # Single object, not a list
        lazy="joined"  # Load user data automatically (eager loading)
    )

    # One-to-one with Club
    # A coach can create/own one club
    club = relationship(
        "Club",
        back_populates="coach",
        uselist=False,  # Single object, not a list
        cascade="all, delete-orphan"  # Delete club if coach is deleted
    )

    # One-to-many with TrainingPlans
    # A coach can create multiple training plans for players
    training_plans = relationship(
        "TrainingPlan",
        back_populates="coach"
    )

    def __repr__(self):
        """
        String representation for debugging.

        Returns:
            str: Coach info (id, user_id)
        """
        return f"<Coach(id='{self.coach_id}', user_id='{self.user_id}')>"

    @property
    def email(self):
        """
        Convenience property to get coach's email from user.

        Returns:
            str: Coach's email address
        """
        return self.user.email if self.user else None

    @property
    def full_name(self):
        """
        Convenience property to get coach's name from user.

        Returns:
            str: Coach's full name
        """
        return self.user.full_name if self.user else None



"""
Example Usage:

# When a user registers as a coach:
# 1. Create user account
user = User(
    email="coach@example.com",
    password_hash="$2b$12$...",
    full_name="John Doe",
    user_type="coach"
)
db.add(user)
db.flush()  # Get user_id without committing

# 2. Create coach record linked to user
coach = Coach(
    user_id=user.user_id,
    birth_date=date(1985, 5, 15),
    gender="male"
)
db.add(coach)
db.commit()

# Querying:
# Get coach with user data (eager loading)
coach = db.query(Coach).filter(Coach.user_id == some_user_id).first()
print(coach.email)  # Access user email via property
print(coach.user.full_name)  # Or directly from relationship

# Get all coaches
all_coaches = db.query(Coach).all()
"""
