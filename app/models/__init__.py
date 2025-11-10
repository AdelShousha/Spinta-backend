"""
Models Package

This package contains all SQLAlchemy ORM models for the Spinta backend.

Models:
- User: User accounts (coaches and players)
- Coach: Coach-specific information
- Club: Club/team information
- Player: Player profiles (incomplete before signup, complete after)

Import all models here to make them easily accessible and ensure
they're registered with SQLAlchemy's metadata.
"""
# anytime another part of your application imports the app.models package, all your models are guaranteed to be loaded and registered with Base.metadata
# essential for Alembic migrations, Alembic runs this __init__.py file, gets a complete list of all your tables, and can correctly compare it to the database.

from app.models.base import Base
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club, AgeGroup
from app.models.player import Player

# allow clean imports from app.models
# Instead of this:
# from app.models.user import User
# from app.models.club import Club, AgeGroup

# You can just do this:
# from app.models import User, Club, AgeGroup

__all__ = [
    "Base",
    "User",
    "Coach",
    "Club",
    "AgeGroup",
    "Player",
]
