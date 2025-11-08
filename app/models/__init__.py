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

from app.models.base import Base
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player


# Export all models
__all__ = [
    "Base",
    "User",
    "Coach",
    "Club",
    "Player",
]
