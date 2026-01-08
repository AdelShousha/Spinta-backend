"""
Pydantic schemas for player endpoints.

This module contains request and response schemas for:
- Dashboard endpoint (GET /api/player/dashboard)
- Matches list endpoint (GET /api/player/matches)
- Match detail endpoint (GET /api/player/matches/{match_id})
- Training plans list endpoint (GET /api/player/training)
- Training plan detail endpoint (GET /api/player/training/{plan_id})
- Toggle exercise endpoint (PUT /api/player/training/exercises/{exercise_id}/toggle)
- Profile endpoint (GET /api/player/profile)

All schemas follow the specification in docs/06_PLAYER_ENDPOINTS.md

Many schemas are reused from coach.py where applicable.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# Import reusable schemas from coach.py
from app.schemas.coach import (
    MatchBasicInfo,
    ClubBasicInfo,
    OpponentInfo,
    TeamInfo,
    PlayerAttributes,
    PlayerGeneralStats,
    PlayerAttackingStats,
    PlayerPassingStats,
    PlayerDribblingStats,
    PlayerDefendingStats,
    PlayerMatchSummary,
    PlayerMatchAttacking,
    PlayerMatchPassing,
    PlayerMatchDefending,
    PlayerMatchStatisticsResponse,
    TrainingProgress,
)


# ============================================================================
# DASHBOARD SCHEMAS (GET /api/player/dashboard)
# ============================================================================

class PlayerDashboardInfo(BaseModel):
    """Player info for dashboard."""
    model_config = ConfigDict(from_attributes=True)
    player_id: str = Field(..., description="Player UUID")
    player_name: str = Field(..., description="Player name")
    jersey_number: int = Field(..., description="Jersey number")
    height: Optional[int] = Field(None, description="Height in cm")
    age: Optional[str] = Field(None, description="Age (e.g., '23 years')")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")


class DashboardSeasonStatistics(BaseModel):
    """Season statistics grouped by category for dashboard."""
    general: PlayerGeneralStats
    attacking: PlayerAttackingStats
    passing: PlayerPassingStats
    dribbling: PlayerDribblingStats
    defending: PlayerDefendingStats


class PlayerDashboardResponse(BaseModel):
    """Response schema for GET /api/player/dashboard."""
    player: PlayerDashboardInfo
    attributes: PlayerAttributes
    season_statistics: DashboardSeasonStatistics


# ============================================================================
# MATCHES LIST SCHEMAS (GET /api/player/matches)
# ============================================================================

class PlayerMatchListItem(BaseModel):
    """Match item in player's matches list."""
    model_config = ConfigDict(from_attributes=True)
    match_id: str = Field(..., description="Match UUID")
    opponent_name: str = Field(..., description="Opponent team name")
    match_date: date = Field(..., description="Match date")
    our_score: int = Field(..., description="Our team's score", ge=0)
    opponent_score: int = Field(..., description="Opponent's score", ge=0)
    result: str = Field(..., description="Match result (W/D/L)")


class PlayerMatchesListResponse(BaseModel):
    """Response schema for GET /api/player/matches."""
    total_count: int = Field(..., description="Total number of matches", ge=0)
    matches: List[PlayerMatchListItem] = Field(..., description="List of matches")


# ============================================================================
# MATCH DETAIL SCHEMAS (GET /api/player/matches/{match_id})
# ============================================================================

class PlayerMatchDetailResponse(BaseModel):
    """Response schema for GET /api/player/matches/{match_id}."""
    match: MatchBasicInfo
    teams: TeamInfo
    player_summary: PlayerMatchSummary
    statistics: PlayerMatchStatisticsResponse


# ============================================================================
# TRAINING LIST SCHEMAS (GET /api/player/training)
# ============================================================================

class TrainingPlanListItem(BaseModel):
    """Training plan item for list."""
    model_config = ConfigDict(from_attributes=True)
    plan_id: str = Field(..., description="Training plan UUID")
    plan_name: str = Field(..., description="Training plan name")
    created_at: date = Field(..., description="Creation date")
    status: str = Field(..., description="Plan status (pending/in_progress/completed)")


class PlayerTrainingListResponse(BaseModel):
    """Response schema for GET /api/player/training."""
    training_plans: List[TrainingPlanListItem] = Field(..., description="List of training plans")


# ============================================================================
# TRAINING PLAN DETAIL SCHEMAS (GET /api/player/training/{plan_id})
# ============================================================================

class PlayerExerciseDetail(BaseModel):
    """Exercise with completion info for player view."""
    model_config = ConfigDict(from_attributes=True)
    exercise_id: str = Field(..., description="Exercise UUID")
    exercise_name: str = Field(..., description="Exercise name")
    description: Optional[str] = Field(None, description="Exercise description")
    sets: Optional[int] = Field(None, description="Number of sets")
    reps: Optional[int] = Field(None, description="Number of reps")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    exercise_order: int = Field(..., description="Exercise order")
    completed: bool = Field(..., description="Whether exercise is completed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class PlayerTrainingPlanInfo(BaseModel):
    """Training plan info for player view."""
    model_config = ConfigDict(from_attributes=True)
    plan_id: str = Field(..., description="Training plan UUID")
    plan_name: str = Field(..., description="Training plan name")
    player_name: str = Field(..., description="Player name")
    player_jersey: int = Field(..., description="Player jersey number")
    status: str = Field(..., description="Plan status")
    created_at: date = Field(..., description="Creation date")


class PlayerTrainingPlanDetailResponse(BaseModel):
    """Response schema for GET /api/player/training/{plan_id}."""
    plan: PlayerTrainingPlanInfo
    progress: TrainingProgress
    exercises: List[PlayerExerciseDetail] = Field(..., description="List of exercises")
    coach_notes: Optional[str] = Field(None, description="Coach notes for player")


# ============================================================================
# TOGGLE EXERCISE SCHEMAS (PUT /api/player/training/exercises/{exercise_id}/toggle)
# ============================================================================

class ToggleExerciseRequest(BaseModel):
    """Request schema for toggling exercise completion."""
    completed: bool = Field(..., description="Whether exercise is completed")


class PlanProgressUpdate(BaseModel):
    """Updated plan progress after toggle."""
    plan_id: str = Field(..., description="Training plan UUID")
    total_exercises: int = Field(..., description="Total exercises", ge=0)
    completed_exercises: int = Field(..., description="Completed exercises", ge=0)
    progress_percentage: int = Field(..., description="Progress percentage", ge=0, le=100)
    plan_status: str = Field(..., description="Updated plan status")


class ToggleExerciseResponse(BaseModel):
    """Response schema for exercise toggle."""
    exercise_id: str = Field(..., description="Exercise UUID")
    completed: bool = Field(..., description="New completion status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    plan_progress: PlanProgressUpdate = Field(..., description="Updated plan progress")


# ============================================================================
# PROFILE SCHEMAS (GET /api/player/profile)
# ============================================================================

class PlayerProfileInfo(BaseModel):
    """Player profile information."""
    model_config = ConfigDict(from_attributes=True)
    player_id: str = Field(..., description="Player UUID")
    player_name: str = Field(..., description="Player name")
    email: str = Field(..., description="Player email")
    jersey_number: int = Field(..., description="Jersey number")
    position: str = Field(..., description="Player position")
    height: Optional[int] = Field(None, description="Height in cm")
    birth_date: Optional[date] = Field(None, description="Birth date")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")


class PlayerClubInfo(BaseModel):
    """Club info for player profile."""
    club_name: str = Field(..., description="Club name")


class PlayerSeasonSummary(BaseModel):
    """Season summary for player profile."""
    matches_played: int = Field(..., description="Matches played", ge=0)
    goals: int = Field(..., description="Goals scored", ge=0)
    assists: int = Field(..., description="Assists", ge=0)


class PlayerProfileResponse(BaseModel):
    """Response schema for GET /api/player/profile."""
    player: PlayerProfileInfo
    club: PlayerClubInfo
    season_summary: PlayerSeasonSummary
