"""
Pydantic schemas for match upload and processing.

These schemas handle the complex StatsBomb event data structure
and match upload requests/responses for the admin endpoint.
"""

from typing import List, Optional, Dict, Any
from datetime import date, time
from pydantic import BaseModel, Field, field_validator


# StatsBomb Event Schemas (nested structure)

class NamedEntity(BaseModel):
    """Generic schema for entities with id and name (teams, types, outcomes, etc.)"""
    id: int
    name: str


class PlayerInfo(BaseModel):
    """Player information in events"""
    id: int
    name: str


class PositionInfo(BaseModel):
    """Position information"""
    id: int
    name: str


class LineupPlayer(BaseModel):
    """Player in Starting XI lineup"""
    player: PlayerInfo
    position: PositionInfo
    jersey_number: int


class TacticsInfo(BaseModel):
    """Tactics information with formation and lineup"""
    formation: int
    lineup: List[LineupPlayer]


class StatsBombEvent(BaseModel):
    """
    StatsBomb event schema.

    This is a flexible schema that accepts the full StatsBomb event structure.
    We store the entire event as JSONB and extract key fields for indexing.
    """
    # Required fields (present in all events)
    id: str
    index: int
    period: int
    timestamp: str
    minute: int
    second: int
    type: NamedEntity
    possession: int
    possession_team: NamedEntity
    play_pattern: NamedEntity
    team: NamedEntity

    # Optional fields (vary by event type)
    duration: Optional[float] = None
    player: Optional[PlayerInfo] = None
    position: Optional[PositionInfo] = None
    location: Optional[List[float]] = None

    # Event-specific data (stored as flexible dict)
    tactics: Optional[TacticsInfo] = None
    shot: Optional[Dict[str, Any]] = None
    pass_: Optional[Dict[str, Any]] = Field(None, alias="pass")
    dribble: Optional[Dict[str, Any]] = None
    duel: Optional[Dict[str, Any]] = None
    interception: Optional[Dict[str, Any]] = None
    # ... other event types stored as raw dict

    # Allow any additional fields
    class Config:
        extra = "allow"  # Accept fields not explicitly defined
        populate_by_name = True  # Allow both 'pass' and 'pass_' field names


# Match Upload Request Schema

class MatchUploadRequest(BaseModel):
    """
    Request body for POST /api/coach/matches

    Contains match metadata and full StatsBomb event data.
    """
    opponent_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Opponent team name",
        examples=["City Strikers"]
    )

    opponent_logo_url: Optional[str] = Field(
        None,
        description="Opponent team logo URL",
        examples=["https://storage.example.com/opponents/city-strikers.png"]
    )

    match_date: date = Field(
        ...,
        description="Match date (YYYY-MM-DD)",
        examples=["2025-10-08"]
    )

    match_time: time = Field(
        ...,
        description="Match kickoff time (HH:MM:SS)",
        examples=["15:30:00"]
    )

    is_home_match: bool = Field(
        ...,
        description="true = home match, false = away match",
        examples=[True]
    )

    home_score: int = Field(
        ...,
        ge=0,
        description="Final score for home team",
        examples=[3]
    )

    away_score: int = Field(
        ...,
        ge=0,
        description="Final score for away team",
        examples=[2]
    )

    statsbomb_events: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Full StatsBomb event data (typically ~3000 events)",
        examples=[[{
            "id": "a3f7e8c2-1234-5678-9abc-def012345678",
            "index": 1,
            "period": 1,
            "type": {"id": 35, "name": "Starting XI"}
        }]]
    )

    @field_validator('statsbomb_events')
    @classmethod
    def validate_events_not_empty(cls, v):
        """Ensure events array is not empty"""
        if not v:
            raise ValueError("statsbomb_events cannot be empty")
        return v


# Match Upload Response Schemas

class NewPlayerInfo(BaseModel):
    """Information about a newly created player"""
    player_name: str
    jersey_number: int
    invite_code: str


class MatchUploadSummary(BaseModel):
    """Summary of match upload processing"""
    events_processed: int = Field(..., description="Number of events inserted into database")
    goals_extracted: int = Field(..., description="Number of goals extracted and created")
    players_created: int = Field(..., description="Number of new player records created")
    players_updated: int = Field(..., description="Number of existing players updated")
    opponent_players_created: int = Field(..., description="Number of opponent players created")
    warnings: List[str] = Field(default_factory=list, description="Any validation warnings")


class MatchUploadResponse(BaseModel):
    """
    Response for successful match upload

    Example:
    {
        "success": true,
        "match_id": "550e8400-e29b-41d4-a716-446655440000",
        "summary": {
            "events_processed": 3247,
            "goals_extracted": 5,
            "players_created": 3,
            "players_updated": 8,
            "opponent_players_created": 11,
            "warnings": []
        },
        "new_players": [
            {
                "player_name": "Marcus Silva",
                "jersey_number": 10,
                "invite_code": "MRC-1827"
            }
        ]
    }
    """
    success: bool = Field(True, description="Always true for successful uploads")
    match_id: str = Field(..., description="Created match UUID")
    summary: MatchUploadSummary
    new_players: List[NewPlayerInfo] = Field(
        default_factory=list,
        description="List of newly created players with invite codes"
    )


# Error Response Schemas

class ValidationError(BaseModel):
    """Validation error response"""
    detail: str = "Validation failed"
    errors: Dict[str, str]


class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str
