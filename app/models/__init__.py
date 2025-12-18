"""
Models Package

This package contains all SQLAlchemy ORM models for the Spinta backend.

Models:
- User: User accounts (coaches and players)
- Coach: Coach-specific information
- Club: Club/team information
- Player: Player profiles (incomplete before signup, complete after)
- OpponentClub: Opponent team information
- Match: Match records
- OpponentPlayer: Opponent player information
- Goal: Goal events from matches
- Event: Raw StatsBomb event data

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

from app.models.opponent_club import OpponentClub
from app.models.match import Match
from app.models.match_lineup import MatchLineup
from app.models.opponent_player import OpponentPlayer
from app.models.goal import Goal
from app.models.event import Event

from app.models.match_statistics import MatchStatistics
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.club_season_statistics import ClubSeasonStatistics
from app.models.player_season_statistics import PlayerSeasonStatistics

from app.models.training_plan import TrainingPlan
from app.models.training_exercise import TrainingExercise

from app.models.knowledge_embedding import KnowledgeEmbedding
from app.models.conversation_message import ConversationMessage

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
    "OpponentClub",
    "Match",
    "MatchLineup",
    "OpponentPlayer",
    "Goal",
    "Event",
    "MatchStatistics",
    "PlayerMatchStatistics",
    "ClubSeasonStatistics",
    "PlayerSeasonStatistics",
    "TrainingPlan",
    "TrainingExercise",
    "KnowledgeEmbedding",
    "ConversationMessage",
]
