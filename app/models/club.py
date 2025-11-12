"""
Club Model

Stores club/team information.

Each club is owned by one coach. When a coach registers,
they create their club. A coach can only have one club.

Fields (10 total):
1. club_id - UUID primary key
2. coach_id - UUID foreign key to coaches (UNIQUE, NOT NULL)
3. club_name - Club name (VARCHAR 255, NOT NULL)
4. statsbomb_team_id - StatsBomb team ID (INTEGER, UNIQUE, NULL)
5. country - Club country (VARCHAR 100, NULL)
6. age_group - Team age group like "U16" (VARCHAR 20, NULL)
7. stadium - Home stadium name (VARCHAR 255, NULL)
8. logo_url - Club logo image URL (TEXT, NULL)
9. created_at - Auto timestamp
10. updated_at - Auto timestamp

Relationships:
- One-to-one with Coach (one club per coach)
- One-to-many with Players (club has multiple players)
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin, generate_uuid, GUID


class AgeGroup(str, enum.Enum):
    """
    Age group categories for youth soccer teams.

    Values represent maximum age for each category.
    """
    U6 = "U6"      # Under 6
    U8 = "U8"      # Under 8
    U10 = "U10"    # Under 10
    U12 = "U12"    # Under 12
    U14 = "U14"    # Under 14
    U16 = "U16"    # Under 16
    U18 = "U18"    # Under 18
    U21 = "U21"    # Under 21
    SENIOR = "Senior (18+)"  # Senior/Adult (18+)


class Club(Base, TimestampMixin):
    """
    Club/Team Model

    Represents a youth soccer club managed by a coach.

    Business Rules:
    - Each coach can create/own exactly one club (UNIQUE constraint on coach_id)
    - statsbomb_team_id is NULL initially, automatically populated from first match upload
    - Used to match club to StatsBomb event data
    """

    __tablename__ = "clubs"

    # Primary Key
    club_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique club identifier"
    )

    # Foreign Key to Coaches table
    coach_id = Column(
        GUID,
        ForeignKey('coaches.coach_id', ondelete='CASCADE'),  # Delete club if coach is deleted
        unique=True,  # One club per coach
        nullable=False,  # Must have a coach
        index=True,  # Index for fast lookups
        comment="Owner coach (one-to-one)"
    )

    # Club information
    club_name = Column(
        String(255),
        nullable=False,
        comment="Club/team name"
    )

    statsbomb_team_id = Column(
        Integer,
        unique=True,  # Each StatsBomb team ID is unique
        nullable=True,  # NULL until first match is uploaded
        comment="StatsBomb team ID for data matching"
    )

    country = Column(
        String(100),
        nullable=True,
        comment="Club's country"
    )

    age_group = Column(
        SQLEnum(AgeGroup),
        nullable=True,
        comment="Team age group (U6, U8, U10, U12, U14, U16, U18, U21, or Senior)"
    )

    stadium = Column(
        String(255),
        nullable=True,
        comment="Home stadium name"
    )

    logo_url = Column(
        Text,
        nullable=True,
        comment="Club logo image URL"
    )

    # Timestamps inherited from TimestampMixin:
    # - created_at (auto-set on creation)
    # - updated_at (auto-update on modification)

    # Relationships

    # One-to-one with Coach
    coach = relationship(
        "Coach",
        back_populates="club",  # Will add this to Coach model
        uselist=False,  # Single object, not a list
        lazy="joined"  # Eager load coach data
    )

    # One-to-many with Players
    # A club has multiple players
    players = relationship(
        "Player",
        back_populates="club",
        cascade="all, delete-orphan"  # Delete players if club is deleted
    )

    # One-to-many with Matches
    # A club has multiple matches
    matches = relationship(
        "Match",
        back_populates="club",
        cascade="all, delete-orphan"  # Delete matches if club is deleted
    )

    # One-to-one with ClubSeasonStatistics
    season_statistics = relationship(
        "ClubSeasonStatistics",
        back_populates="club",
        cascade="all, delete-orphan",
        uselist=False
    )

    def __repr__(self):
        """
        String representation for debugging.

        Returns:
            str: Club info (name, id, coach_id)
        """
        return f"<Club(name='{self.club_name}', id='{self.club_id}', coach_id='{self.coach_id}')>"

    @property
    def coach_name(self):
        """
        Convenience property to get coach's name.

        Returns:
            str: Coach's full name
        """
        return self.coach.full_name if self.coach else None

    @property
    def player_count(self):
        """
        Get number of players in the club.

        Returns:
            int: Number of players (will work once Player model is added)
        """
        return len(self.players) if hasattr(self, 'players') else 0



"""
Example Usage:

# When a coach creates their club:
# Assume coach already exists with coach_id

club = Club(
    coach_id=coach.coach_id,
    club_name="Manchester City U16",
    country="England",
    age_group=AgeGroup.U16,  # Use enum value
    stadium="Etihad Campus",
    logo_url="https://example.com/logos/mancity.png",
    # statsbomb_team_id is NULL initially
)
db.add(club)
db.commit()

# Available age groups:
# AgeGroup.U6, AgeGroup.U8, AgeGroup.U10, AgeGroup.U12,
# AgeGroup.U14, AgeGroup.U16, AgeGroup.U18, AgeGroup.U21,
# AgeGroup.SENIOR

# Later, when first match is uploaded, update statsbomb_team_id:
club.statsbomb_team_id = 123
db.commit()

# Querying:
# Get club with coach data (eager loading)
club = db.query(Club).filter(Club.club_id == some_club_id).first()
print(club.coach.full_name)  # Access coach name
print(club.coach_name)  # Or via property

# Get club by coach
coach_club = db.query(Club).filter(Club.coach_id == some_coach_id).first()

# Get club by StatsBomb team ID
club = db.query(Club).filter(Club.statsbomb_team_id == 123).first()
"""
