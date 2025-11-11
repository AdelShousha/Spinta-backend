"""
Player Model

Stores player profiles, including incomplete players (before signup).

IMPORTANT - User Account Deletion Behavior:
When a user deletes their account, the player record PERSISTS (not deleted).
The Foreign Key is set to SET NULL, so:
- user_id becomes NULL
- Player reverts to incomplete state
- Player can potentially be re-linked to a new account

Future Implementation Note:
When implementing user account deletion endpoint, consider also updating:
- is_linked = False (mark as incomplete again)
- linked_at = NULL (clear signup timestamp)
This provides a clean state for potential re-linking.

Example deletion logic:
    if user.player:
        user.player.is_linked = False
        user.player.linked_at = None
        # user_id will be set to NULL automatically by SET NULL cascade

This model handles TWO states:

1. Incomplete Player (before signup):
   - Created by admin during match processing
   - user_id = NULL
   - is_linked = FALSE
   - Only basic fields filled: player_name, jersey_number, position, invite_code
   - birth_date, height, profile_image_url are NULL

2. Complete Player (after signup):
   - Player completes signup using invite code
   - user_id is set (links to users table)
   - is_linked = TRUE
   - linked_at = NOW()
   - All profile fields filled

Fields (15 total):
1. player_id - UUID primary key (separate from user_id)
2. user_id - UUID FK to users (UNIQUE, NULL before signup)
3. club_id - UUID FK to clubs (NOT NULL)
4. player_name - Player name (VARCHAR 255, NOT NULL)
5. statsbomb_player_id - StatsBomb player ID (INTEGER, NULL)
6. jersey_number - Jersey number (INTEGER, NOT NULL)
7. position - Player position (VARCHAR 50, NOT NULL)
8. invite_code - Unique signup code (VARCHAR 10, UNIQUE, NOT NULL)
9. is_linked - Has player signed up? (BOOLEAN, DEFAULT FALSE)
10. linked_at - When player completed signup (TIMESTAMP, NULL)
11. birth_date - Birth date (DATE, NULL)
12. height - Height in cm (INTEGER, NULL)
13. profile_image_url - Profile photo (TEXT, NULL)
14. created_at - Auto timestamp
15. updated_at - Auto timestamp

Relationships:
- Many-to-one with Club (club has many players)
- One-to-one with User (after signup, via user_id)
"""

from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, TimestampMixin, generate_uuid, GUID


class Player(Base, TimestampMixin):
    """
    Player Profile Model

    Handles both incomplete players (before signup) and complete players (after signup).

    Design Pattern - Two States:
    1. Incomplete: Created by admin, minimal data, user_id = NULL
    2. Complete: After signup, user_id set, all fields filled

    Why player_id != user_id?
    - player_id exists BEFORE user account (incomplete players)
    - user_id is set AFTER signup (linking player to user account)
    - Separates player identity from user account
    """

    __tablename__ = "players"

    # Primary Key (separate from user_id)
    player_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique player identifier"
    )

    # Foreign Key to Users table (NULL before signup)
    user_id = Column(
        GUID,
        ForeignKey('users.user_id', ondelete='SET NULL'),  # Set to NULL if user deletes account
        unique=True,  # One player per user account
        nullable=True,  # NULL for incomplete players
        index=True,  # Index for fast lookups
        comment="Reference to user account (NULL before signup or after user deletion)"
    )

    # Foreign Key to Clubs table
    club_id = Column(
        GUID,
        ForeignKey('clubs.club_id', ondelete='CASCADE'),  # Delete player if club is deleted
        nullable=False,  # Every player belongs to a club
        index=True,  # Index for filtering by club
        comment="Player's club"
    )

    # Player basic information (filled by admin)
    player_name = Column(
        String(255),
        nullable=False,
        comment="Player name (source of truth for display)"
    )

    statsbomb_player_id = Column(
        Integer,
        nullable=True,
        index=True,  # Index for matching StatsBomb events
        comment="StatsBomb player ID from event data"
    )

    jersey_number = Column(
        Integer,
        nullable=False,
        comment="Player's jersey/shirt number"
    )

    position = Column(
        String(50),
        nullable=False,
        comment="Player position (e.g., 'Forward', 'Midfielder')"
    )

    # Invite code for signup
    invite_code = Column(
        String(10),
        unique=True,  # Must be unique across all players
        nullable=False,
        index=True,  # Index for fast lookup during signup
        comment="Unique signup code (format: XXX-NNNN)"
    )

    # Signup tracking
    is_linked = Column(
        Boolean,
        nullable=False,
        default=False,  # FALSE until player signs up
        index=True,  # Index for filtering linked/unlinked players
        comment="Has player completed signup?"
    )

    linked_at = Column(
        DateTime(timezone=True),
        nullable=True,  # NULL until signup
        comment="Timestamp when player completed signup"
    )

    # Player profile information (filled on signup)
    birth_date = Column(
        Date,
        nullable=True,  # NULL until signup
        comment="Player's birth date (filled on signup)"
    )

    height = Column(
        Integer,
        nullable=True,  # NULL until signup
        comment="Player height in cm (filled on signup)"
    )

    profile_image_url = Column(
        String,  # TEXT type for long URLs
        nullable=True,  # NULL until signup
        comment="Profile photo URL (filled on signup)"
    )

    # Timestamps inherited from TimestampMixin:
    # - created_at (auto-set on creation)
    # - updated_at (auto-update on modification)

    # Relationships

    # One-to-one with User (after signup)
    user = relationship(
        "User",
        back_populates="player",  # Will add this to User model
        uselist=False,  # Single object, not a list
        lazy="joined"  # Eager load user data
    )

    # Many-to-one with Club
    club = relationship(
        "Club",
        back_populates="players",  # Will add this to Club model
        lazy="joined"  # Eager load club data
    )

    # One-to-many with PlayerMatchStatistics
    player_match_statistics = relationship(
        "PlayerMatchStatistics",
        back_populates="player",
        cascade="all, delete-orphan"
    )

    # One-to-one with PlayerSeasonStatistics
    player_season_statistics = relationship(
        "PlayerSeasonStatistics",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # One-to-many with TrainingPlans
    training_plans = relationship(
        "TrainingPlan",
        back_populates="player",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        """
        String representation for debugging.

        Returns:
            str: Player info (name, jersey, linked status)
        """
        linked_status = "linked" if self.is_linked else "unlinked"
        return f"<Player(name='{self.player_name}', jersey=#{self.jersey_number}, {linked_status})>"

    @property
    def email(self):
        """
        Get player's email from user account.

        Returns:
            str: Email if linked, None if not
        """
        return self.user.email if self.user else None

    @property
    def is_incomplete(self):
        """
        Check if player is incomplete (hasn't signed up yet).

        Returns:
            bool: True if player hasn't signed up
        """
        return not self.is_linked

    def complete_signup(self, user_id: str):
        """
        Mark player as complete after signup.

        This should be called when a player completes registration.

        Args:
            user_id (str): The user_id from the newly created user account

        Usage:
            player.complete_signup(new_user.user_id)
            player.is_linked = True
            player.linked_at = datetime.now(timezone.utc)
        """
        self.user_id = user_id
        self.is_linked = True
        self.linked_at = datetime.now(timezone.utc)



"""
Example Usage:

# 1. Create incomplete player (by admin during match processing):
incomplete_player = Player(
    club_id=club.club_id,
    player_name="John Smith",
    statsbomb_player_id=456,
    jersey_number=10,
    position="Forward",
    invite_code="MRC-1827",
    # user_id is NULL
    # is_linked is FALSE (default)
    # birth_date, height, profile_image_url are NULL
)
db.add(incomplete_player)
db.commit()

# 2. Player signs up using invite code:
# First, create user account
new_user = User(
    email="player@example.com",
    password_hash="$2b$12$...",
    full_name="John Smith",
    user_type="player"
)
db.add(new_user)
db.flush()  # Get user_id

# Then, link player to user
player = db.query(Player).filter(Player.invite_code == "MRC-1827").first()
player.complete_signup(new_user.user_id)
player.birth_date = date(2008, 3, 15)
player.height = 175
player.profile_image_url = "https://example.com/photos/john.jpg"
db.commit()

# 3. Querying:
# Get incomplete players
incomplete = db.query(Player).filter(Player.is_linked == False).all()

# Get players in a club
club_players = db.query(Player).filter(Player.club_id == some_club_id).all()

# Get player by invite code
player = db.query(Player).filter(Player.invite_code == "MRC-1827").first()

# Get player by StatsBomb ID (for event processing)
player = db.query(Player).filter(Player.statsbomb_player_id == 456).first()
"""
