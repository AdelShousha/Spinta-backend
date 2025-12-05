"""
Pydantic schemas for coach endpoints.

This module contains request and response schemas for:
- Match upload endpoint (POST /api/coach/matches)
- Dashboard endpoint (GET /api/coach/dashboard)
- Match detail endpoint (GET /api/coach/matches/{match_id})
- Players list endpoint (GET /api/coach/players)
- Player detail endpoint (GET /api/coach/players/{player_id})
- Player match stats endpoint (GET /api/coach/players/{player_id}/matches/{match_id})
- Coach profile endpoint (GET /api/coach/profile)
- Training plan endpoints (CRUD + AI generation)

All schemas follow the specification in docs/05_COACH_ENDPOINTS.md
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union
from datetime import date, datetime


# ============================================================================
# COMMON SCHEMAS (Reusable across endpoints)
# ============================================================================

class CoachBasicInfo(BaseModel):
    """Coach basic information for dashboard header."""
    model_config = ConfigDict(from_attributes=True)
    full_name: str = Field(..., description="Coach full name")


class ClubBasicInfo(BaseModel):
    """Club basic information."""
    model_config = ConfigDict(from_attributes=True)
    club_id: str = Field(..., description="Club UUID")
    club_name: str = Field(..., description="Club name")
    logo_url: Optional[str] = Field(None, description="Club logo URL")


class SeasonRecord(BaseModel):
    """Season win/draw/loss record."""
    wins: int = Field(..., description="Number of wins", ge=0)
    draws: int = Field(..., description="Number of draws", ge=0)
    losses: int = Field(..., description="Number of losses", ge=0)


class MatchSummary(BaseModel):
    """Match summary for lists."""
    model_config = ConfigDict(from_attributes=True)
    match_id: str = Field(..., description="Match UUID")
    opponent_name: str = Field(..., description="Opponent team name")
    match_date: date = Field(..., description="Match date")
    our_score: int = Field(..., description="Our team's score", ge=0)
    opponent_score: int = Field(..., description="Opponent's score", ge=0)
    result: str = Field(..., description="Match result (W/D/L)")


class PaginatedMatches(BaseModel):
    """Paginated matches list."""
    total_count: int = Field(..., description="Total number of matches", ge=0)
    matches: List[MatchSummary] = Field(..., description="List of matches")


# ============================================================================
# MATCH UPLOAD SCHEMAS (Already implemented)
# ============================================================================

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


# ============================================================================
# DASHBOARD SCHEMAS (GET /api/coach/dashboard)
# ============================================================================

class SeasonSummaryStats(BaseModel):
    """Season summary statistics."""
    matches_played: int = Field(..., description="Total matches played", ge=0)
    goals_scored: int = Field(..., description="Total goals scored", ge=0)
    goals_conceded: int = Field(..., description="Total goals conceded", ge=0)
    total_assists: int = Field(..., description="Total assists", ge=0)


class AttackingStats(BaseModel):
    """Attacking statistics."""
    avg_goals_per_match: Optional[float] = Field(None, description="Average goals per match")
    avg_xg_per_match: Optional[float] = Field(None, description="Average expected goals per match")
    avg_total_shots: Optional[float] = Field(None, description="Average total shots")
    avg_shots_on_target: Optional[float] = Field(None, description="Average shots on target")
    avg_dribbles: Optional[float] = Field(None, description="Average dribbles")
    avg_successful_dribbles: Optional[float] = Field(None, description="Average successful dribbles")


class PassesStats(BaseModel):
    """Passing statistics."""
    avg_possession_percentage: Optional[float] = Field(None, description="Average possession percentage")
    avg_passes: Optional[float] = Field(None, description="Average total passes")
    pass_completion_percentage: Optional[float] = Field(None, description="Pass completion percentage")
    avg_final_third_passes: Optional[float] = Field(None, description="Average passes in final third")
    avg_crosses: Optional[float] = Field(None, description="Average crosses")


class DefendingStats(BaseModel):
    """Defending statistics."""
    total_clean_sheets: int = Field(..., description="Total clean sheets", ge=0)
    avg_goals_conceded_per_match: Optional[float] = Field(None, description="Average goals conceded per match")
    avg_tackles: Optional[float] = Field(None, description="Average tackles")
    tackle_success_percentage: Optional[float] = Field(None, description="Tackle success percentage")
    avg_interceptions: Optional[float] = Field(None, description="Average interceptions")
    interception_success_percentage: Optional[float] = Field(None, description="Interception success percentage")
    avg_ball_recoveries: Optional[float] = Field(None, description="Average ball recoveries")
    avg_saves_per_match: Optional[float] = Field(None, description="Average saves per match")


class DashboardStatistics(BaseModel):
    """Complete dashboard statistics."""
    season_summary: SeasonSummaryStats
    attacking: AttackingStats
    passes: PassesStats
    defending: DefendingStats


class DashboardResponse(BaseModel):
    """Response schema for GET /api/coach/dashboard."""
    model_config = ConfigDict(from_attributes=True)
    coach: CoachBasicInfo
    club: ClubBasicInfo
    season_record: SeasonRecord
    team_form: str = Field(..., description="Last 5 match results (e.g., 'WWDLW')")
    matches: PaginatedMatches
    statistics: DashboardStatistics


# ============================================================================
# MATCH DETAIL SCHEMAS (GET /api/coach/matches/{match_id})
# ============================================================================

class MatchBasicInfo(BaseModel):
    """Basic match information."""
    model_config = ConfigDict(from_attributes=True)
    match_id: str = Field(..., description="Match UUID")
    match_date: date = Field(..., description="Match date")
    our_score: int = Field(..., description="Our team's score", ge=0)
    opponent_score: int = Field(..., description="Opponent's score", ge=0)
    result: str = Field(..., description="Match result (W/D/L)")


class OpponentInfo(BaseModel):
    """Opponent team information."""
    opponent_name: str = Field(..., description="Opponent team name")
    logo_url: Optional[str] = Field(None, description="Opponent logo URL")


class TeamInfo(BaseModel):
    """Teams information for match."""
    our_club: ClubBasicInfo
    opponent: OpponentInfo


class GoalScorer(BaseModel):
    """Goal scorer information."""
    model_config = ConfigDict(from_attributes=True)
    goal_id: str = Field(..., description="Goal UUID")
    scorer_name: str = Field(..., description="Scorer's name")
    minute: int = Field(..., description="Minute of goal", ge=0)
    second: Optional[int] = Field(None, description="Second of goal", ge=0, le=59)
    is_our_goal: bool = Field(..., description="Whether goal was scored by our team")


class MatchSummarySection(BaseModel):
    """Match summary with goal scorers."""
    goal_scorers: List[GoalScorer] = Field(..., description="List of goal scorers")


class StatComparison(BaseModel):
    """Comparison statistic between teams."""
    our_team: Union[int, float] = Field(..., description="Our team's statistic")
    opponent: Union[int, float] = Field(..., description="Opponent's statistic")


class MatchOverviewStats(BaseModel):
    """Match overview statistics."""
    ball_possession: StatComparison
    expected_goals: StatComparison
    total_shots: StatComparison
    goalkeeper_saves: StatComparison
    total_passes: StatComparison
    total_dribbles: StatComparison


class MatchAttackingStats(BaseModel):
    """Match attacking statistics."""
    total_shots: StatComparison
    shots_on_target: StatComparison
    shots_off_target: StatComparison
    total_dribbles: StatComparison
    successful_dribbles: StatComparison


class MatchPassingStats(BaseModel):
    """Match passing statistics."""
    total_passes: StatComparison
    passes_completed: StatComparison
    passes_in_final_third: StatComparison
    long_passes: StatComparison
    crosses: StatComparison


class MatchDefendingStats(BaseModel):
    """Match defending statistics."""
    tackle_success_percentage: StatComparison
    total_tackles: StatComparison
    interceptions: StatComparison
    ball_recoveries: StatComparison
    goalkeeper_saves: StatComparison


class MatchDetailStatistics(BaseModel):
    """Complete match statistics."""
    match_overview: MatchOverviewStats
    attacking: MatchAttackingStats
    passing: MatchPassingStats
    defending: MatchDefendingStats


class OurTeamPlayer(BaseModel):
    """Our team player in lineup."""
    model_config = ConfigDict(from_attributes=True)
    player_id: str = Field(..., description="Player UUID")
    jersey_number: int = Field(..., description="Jersey number")
    player_name: str = Field(..., description="Player name")
    position: str = Field(..., description="Position")


class OpponentTeamPlayer(BaseModel):
    """Opponent team player in lineup."""
    model_config = ConfigDict(from_attributes=True)
    opponent_player_id: str = Field(..., description="Opponent player UUID")
    jersey_number: int = Field(..., description="Jersey number")
    player_name: str = Field(..., description="Player name")
    position: str = Field(..., description="Position")


class MatchLineups(BaseModel):
    """Match lineups for both teams."""
    our_team: List[OurTeamPlayer] = Field(..., description="Our team lineup")
    opponent_team: List[OpponentTeamPlayer] = Field(..., description="Opponent team lineup")


class MatchDetailResponse(BaseModel):
    """Response schema for GET /api/coach/matches/{match_id}."""
    match: MatchBasicInfo
    teams: TeamInfo
    summary: MatchSummarySection
    statistics: MatchDetailStatistics
    lineup: MatchLineups


# ============================================================================
# PLAYERS LIST SCHEMAS (GET /api/coach/players)
# ============================================================================

class PlayerSummary(BaseModel):
    """Player count summary."""
    total_players: int = Field(..., description="Total number of players", ge=0)
    joined: int = Field(..., description="Number of joined (linked) players", ge=0)
    pending: int = Field(..., description="Number of pending (unlinked) players", ge=0)


class PlayerListItem(BaseModel):
    """Player item in list."""
    model_config = ConfigDict(from_attributes=True)
    player_id: str = Field(..., description="Player UUID")
    player_name: str = Field(..., description="Player name")
    jersey_number: int = Field(..., description="Jersey number")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    is_linked: bool = Field(..., description="Whether player account is linked")


class PlayersListResponse(BaseModel):
    """Response schema for GET /api/coach/players."""
    summary: PlayerSummary
    players: List[PlayerListItem] = Field(..., description="List of players")


# ============================================================================
# PLAYER DETAIL SCHEMAS (GET /api/coach/players/{player_id})
# ============================================================================

class PlayerInfo(BaseModel):
    """Player basic information."""
    model_config = ConfigDict(from_attributes=True)
    player_id: str = Field(..., description="Player UUID")
    player_name: str = Field(..., description="Player name")
    jersey_number: int = Field(..., description="Jersey number")
    height: Optional[int] = Field(None, description="Height in cm")
    age: Optional[str] = Field(None, description="Age (e.g., '23 years')")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    is_linked: bool = Field(..., description="Whether player account is linked")


class PlayerAttributes(BaseModel):
    """Player attribute ratings."""
    attacking_rating: Optional[int] = Field(None, description="Attacking rating (0-100)")
    technique_rating: Optional[int] = Field(None, description="Technique rating (0-100)")
    creativity_rating: Optional[int] = Field(None, description="Creativity rating (0-100)")
    tactical_rating: Optional[int] = Field(None, description="Tactical rating (0-100)")
    defending_rating: Optional[int] = Field(None, description="Defending rating (0-100)")


class PlayerGeneralStats(BaseModel):
    """Player general statistics."""
    matches_played: int = Field(..., description="Matches played", ge=0)


class PlayerAttackingStats(BaseModel):
    """Player attacking statistics."""
    goals: int = Field(..., description="Goals scored", ge=0)
    assists: int = Field(..., description="Assists", ge=0)
    expected_goals: Optional[float] = Field(None, description="Expected goals (xG)")
    shots_per_game: Optional[float] = Field(None, description="Shots per game")
    shots_on_target_per_game: Optional[float] = Field(None, description="Shots on target per game")


class PlayerPassingStats(BaseModel):
    """Player passing statistics."""
    total_passes: Optional[int] = Field(None, description="Total passes")
    passes_completed: Optional[int] = Field(None, description="Passes completed")


class PlayerDribblingStats(BaseModel):
    """Player dribbling statistics."""
    total_dribbles: Optional[int] = Field(None, description="Total dribbles")
    successful_dribbles: Optional[int] = Field(None, description="Successful dribbles")


class PlayerDefendingStats(BaseModel):
    """Player defending statistics."""
    tackles: Optional[int] = Field(None, description="Tackles")
    tackle_success_rate: Optional[float] = Field(None, description="Tackle success rate")
    interceptions: Optional[int] = Field(None, description="Interceptions")
    interception_success_rate: Optional[float] = Field(None, description="Interception success rate")


class PlayerSeasonStatistics(BaseModel):
    """Player season statistics."""
    general: PlayerGeneralStats
    attacking: PlayerAttackingStats
    passing: PlayerPassingStats
    dribbling: PlayerDribblingStats
    defending: PlayerDefendingStats


class TrainingPlanSummary(BaseModel):
    """Training plan summary for player detail."""
    model_config = ConfigDict(from_attributes=True)
    plan_id: str = Field(..., description="Training plan UUID")
    plan_name: str = Field(..., description="Training plan name")
    created_at: date = Field(..., description="Creation date")
    status: str = Field(..., description="Plan status (pending/in_progress/completed)")


class PlayerDetailResponse(BaseModel):
    """Response schema for GET /api/coach/players/{player_id}."""
    player: PlayerInfo
    invite_code: Optional[str] = Field(None, description="Invite code (only for unlinked players)")
    attributes: PlayerAttributes
    season_statistics: PlayerSeasonStatistics
    matches: PaginatedMatches
    training_plans: List[TrainingPlanSummary] = Field(..., description="Player's training plans")


# ============================================================================
# PLAYER MATCH PERFORMANCE SCHEMAS (GET /api/coach/players/{player_id}/matches/{match_id})
# ============================================================================

class PlayerMatchSummary(BaseModel):
    """Player match summary."""
    player_name: str = Field(..., description="Player name")
    goals: int = Field(..., description="Goals scored", ge=0)
    assists: int = Field(..., description="Assists", ge=0)


class PlayerMatchAttacking(BaseModel):
    """Player match attacking statistics."""
    goals: int = Field(..., description="Goals scored", ge=0)
    assists: int = Field(..., description="Assists", ge=0)
    xg: Optional[float] = Field(None, description="Expected goals (xG)")
    total_shots: Optional[int] = Field(None, description="Total shots")
    shots_on_target: Optional[int] = Field(None, description="Shots on target")
    total_dribbles: Optional[int] = Field(None, description="Total dribbles")
    successful_dribbles: Optional[int] = Field(None, description="Successful dribbles")


class PlayerMatchPassing(BaseModel):
    """Player match passing statistics."""
    total_passes: Optional[int] = Field(None, description="Total passes")
    passes_completed: Optional[int] = Field(None, description="Passes completed")
    short_passes: Optional[int] = Field(None, description="Short passes")
    long_passes: Optional[int] = Field(None, description="Long passes")
    final_third: Optional[int] = Field(None, description="Passes in final third")
    crosses: Optional[int] = Field(None, description="Crosses")


class PlayerMatchDefending(BaseModel):
    """Player match defending statistics."""
    tackles: Optional[int] = Field(None, description="Tackles")
    tackle_success_rate: Optional[float] = Field(None, description="Tackle success rate")
    interceptions: Optional[int] = Field(None, description="Interceptions")
    interception_success_rate: Optional[float] = Field(None, description="Interception success rate")


class PlayerMatchStatisticsResponse(BaseModel):
    """Player match statistics."""
    attacking: PlayerMatchAttacking
    passing: PlayerMatchPassing
    defending: PlayerMatchDefending


class PlayerMatchDetailResponse(BaseModel):
    """Response schema for GET /api/coach/players/{player_id}/matches/{match_id}."""
    match: MatchBasicInfo
    teams: TeamInfo
    player_summary: PlayerMatchSummary
    statistics: PlayerMatchStatisticsResponse


# ============================================================================
# COACH PROFILE SCHEMAS (GET /api/coach/profile)
# ============================================================================

class CoachProfileInfo(BaseModel):
    """Coach profile information."""
    model_config = ConfigDict(from_attributes=True)
    full_name: str = Field(..., description="Coach full name")
    email: str = Field(..., description="Coach email")
    gender: Optional[str] = Field(None, description="Coach gender")
    birth_date: Optional[date] = Field(None, description="Coach birth date")


class ClubStats(BaseModel):
    """Club statistics for profile."""
    total_players: int = Field(..., description="Total linked players", ge=0)
    total_matches: int = Field(..., description="Total matches played", ge=0)
    win_rate_percentage: Optional[int] = Field(None, description="Win rate percentage", ge=0, le=100)


class CoachProfileResponse(BaseModel):
    """Response schema for GET /api/coach/profile."""
    coach: CoachProfileInfo
    club: ClubBasicInfo
    club_stats: ClubStats


# ============================================================================
# TRAINING PLAN SCHEMAS
# ============================================================================

# Request: Generate AI Training Plan (POST /api/coach/training-plans/generate-ai)
class GenerateAITrainingPlanRequest(BaseModel):
    """Request schema for AI training plan generation."""
    player_id: str = Field(..., description="Player UUID to generate plan for")


class GeneratedExercise(BaseModel):
    """Generated exercise from AI."""
    exercise_name: str = Field(..., description="Exercise name")
    description: Optional[str] = Field(None, description="Exercise description")
    sets: Optional[str] = Field(None, description="Number of sets")
    reps: Optional[str] = Field(None, description="Number of reps")
    duration_minutes: Optional[str] = Field(None, description="Duration in minutes")


class GenerateAITrainingPlanResponse(BaseModel):
    """Response schema for AI training plan generation."""
    player_name: str = Field(..., description="Player name")
    jersey_number: int = Field(..., description="Player jersey number")
    plan_name: str = Field(..., description="Generated plan name")
    duration: Optional[str] = Field(None, description="Plan duration")
    exercises: List[GeneratedExercise] = Field(..., description="Generated exercises")


# Request: Create Training Plan (POST /api/coach/training-plans)
class ExerciseCreate(BaseModel):
    """Exercise creation schema."""
    exercise_name: str = Field(..., min_length=2, max_length=255, description="Exercise name")
    description: Optional[str] = Field(None, description="Exercise description")
    sets: Optional[str] = Field(None, description="Number of sets")
    reps: Optional[str] = Field(None, description="Number of reps")
    duration_minutes: Optional[str] = Field(None, description="Duration in minutes")
    exercise_order: int = Field(..., ge=1, description="Exercise order in plan")


class CreateTrainingPlanRequest(BaseModel):
    """Request schema for creating training plan."""
    player_id: str = Field(..., description="Player UUID")
    plan_name: str = Field(..., min_length=2, max_length=255, description="Training plan name")
    duration: Optional[str] = Field(None, description="Plan duration (e.g., '2 weeks')")
    coach_notes: Optional[str] = Field(None, description="Coach notes for player")
    exercises: List[ExerciseCreate] = Field(..., min_length=1, description="List of exercises")


class CreateTrainingPlanResponse(BaseModel):
    """Response schema for creating training plan."""
    model_config = ConfigDict(from_attributes=True)
    plan_id: str = Field(..., description="Training plan UUID")
    player_id: str = Field(..., description="Player UUID")
    plan_name: str = Field(..., description="Training plan name")
    duration: Optional[str] = Field(None, description="Plan duration")
    status: str = Field(..., description="Plan status")
    coach_notes: Optional[str] = Field(None, description="Coach notes")
    exercise_count: int = Field(..., description="Number of exercises", ge=0)
    created_at: datetime = Field(..., description="Creation timestamp")


# Response: Training Plan Detail (GET /api/coach/training-plans/{plan_id})
class ExerciseDetail(BaseModel):
    """Exercise detail schema."""
    model_config = ConfigDict(from_attributes=True)
    exercise_id: str = Field(..., description="Exercise UUID")
    exercise_name: str = Field(..., description="Exercise name")
    description: Optional[str] = Field(None, description="Exercise description")
    sets: Optional[str] = Field(None, description="Number of sets")
    reps: Optional[str] = Field(None, description="Number of reps")
    duration_minutes: Optional[str] = Field(None, description="Duration in minutes")
    completed: bool = Field(..., description="Whether exercise is completed")
    exercise_order: int = Field(..., description="Exercise order")


class TrainingPlanInfo(BaseModel):
    """Training plan basic information."""
    model_config = ConfigDict(from_attributes=True)
    plan_id: str = Field(..., description="Training plan UUID")
    plan_name: str = Field(..., description="Training plan name")
    player_name: str = Field(..., description="Player name")
    player_jersey: int = Field(..., description="Player jersey number")
    status: str = Field(..., description="Plan status")
    created_at: date = Field(..., description="Creation date")


class TrainingProgress(BaseModel):
    """Training plan progress."""
    percentage: int = Field(..., description="Completion percentage", ge=0, le=100)
    completed_exercises: int = Field(..., description="Number of completed exercises", ge=0)
    total_exercises: int = Field(..., description="Total number of exercises", ge=0)


class TrainingPlanDetailResponse(BaseModel):
    """Response schema for GET /api/coach/training-plans/{plan_id}."""
    plan: TrainingPlanInfo
    progress: TrainingProgress
    exercises: List[ExerciseDetail] = Field(..., description="List of exercises")
    coach_notes: Optional[str] = Field(None, description="Coach notes")


# Request: Update Training Plan (PUT /api/coach/training-plans/{plan_id})
class ExerciseUpdate(BaseModel):
    """Exercise update schema."""
    exercise_id: Optional[str] = Field(None, description="Exercise UUID (None for new exercise)")
    exercise_name: str = Field(..., min_length=2, max_length=255, description="Exercise name")
    description: Optional[str] = Field(None, description="Exercise description")
    sets: Optional[str] = Field(None, description="Number of sets")
    reps: Optional[str] = Field(None, description="Number of reps")
    duration_minutes: Optional[str] = Field(None, description="Duration in minutes")
    exercise_order: int = Field(..., ge=1, description="Exercise order")


class UpdateTrainingPlanRequest(BaseModel):
    """Request schema for updating training plan."""
    plan_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Training plan name")
    duration: Optional[str] = Field(None, description="Plan duration")
    coach_notes: Optional[str] = Field(None, description="Coach notes")
    exercises: Optional[List[ExerciseUpdate]] = Field(None, description="Updated exercises list")


class UpdateTrainingPlanResponse(BaseModel):
    """Response schema for updating training plan."""
    model_config = ConfigDict(from_attributes=True)
    plan_id: str = Field(..., description="Training plan UUID")
    player_id: str = Field(..., description="Player UUID")
    plan_name: str = Field(..., description="Training plan name")
    duration: Optional[str] = Field(None, description="Plan duration")
    status: str = Field(..., description="Plan status")
    updated: bool = Field(..., description="Whether update was successful")


# Response: Delete Training Plan (DELETE /api/coach/training-plans/{plan_id})
class DeleteTrainingPlanResponse(BaseModel):
    """Response schema for deleting training plan."""
    deleted: bool = Field(..., description="Whether deletion was successful")
    plan_id: str = Field(..., description="Deleted training plan UUID")
