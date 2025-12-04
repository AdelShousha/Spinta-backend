"""
Pydantic schemas for coach endpoints.

This module contains request and response schemas for:
- Match upload endpoint
- Future coach endpoints (to be added)

All schemas follow the specification in docs/07_ADMIN_ENDPOINTS.md
"""

from pydantic import BaseModel, Field, ConfigDict


class MatchUploadResponse(BaseModel):
    """Response schema for successful match upload."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "match_id": "550e8400-e29b-41d4-a716-446655440000",
                "summary": {
                    "opponent_club_id": "660e8400-e29b-41d4-a716-446655440001",
                    "our_players_processed": 11,
                    "our_players_created": 3,
                    "our_players_updated": 8,
                    "opponent_players_processed": 11,
                    "opponent_players_created": 11,
                    "lineups_created": 22,
                    "events_inserted": 3542,
                    "goals_extracted": 6,
                    "match_statistics_created": 2,
                    "player_match_stats_created": 22,
                    "club_season_stats_updated": 2,
                    "player_season_stats_updated": 11
                },
                "details": {
                    "team_identification": {
                        "our_team_id": 123,
                        "our_team_name": "Thunder United FC",
                        "opponent_team_id": 456,
                        "opponent_team_name": "France"
                    },
                    "our_players": [
                        {
                            "player_id": "player-uuid",
                            "player_name": "John Doe",
                            "jersey_number": 10,
                            "position": "Forward"
                        }
                    ],
                    "opponent_players": [
                        {
                            "player_id": "opponent-player-uuid",
                            "player_name": "Jane Smith",
                            "jersey_number": 9,
                            "position": "Forward"
                        }
                    ]
                }
            }
        }
    )

    success: bool = Field(..., description="Whether the upload was successful")
    match_id: str = Field(..., description="UUID of the created match")
    summary: dict = Field(..., description="Summary of all processing steps with counts")
    details: dict = Field(..., description="Detailed information about teams and players")
