"""
API routes for coach endpoints.

This module contains all endpoints that coaches can access:
- POST /api/coach/matches - Upload match with StatsBomb JSON file
- GET /api/coach/dashboard - Coach dashboard with statistics
- GET /api/coach/matches/{match_id} - Match details
- GET /api/coach/players - List all players
- GET /api/coach/players/{player_id} - Player details
- GET /api/coach/players/{player_id}/matches/{match_id} - Player match performance
- GET /api/coach/profile - Coach profile
- POST /api/coach/training-plans/generate-ai - Generate AI-powered training plan
- POST /api/coach/training-plans - Create training plan
- GET /api/coach/training-plans/{plan_id} - Training plan details
- PUT /api/coach/training-plans/{plan_id} - Update training plan
- DELETE /api/coach/training-plans/{plan_id} - Delete training plan
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import json

from app.database import get_db
from app.core.dependencies import require_coach
from app.schemas.coach import (
    MatchUploadResponse,
    DashboardResponse,
    MatchDetailResponse,
    PlayersListResponse,
    PlayerDetailResponse,
    PlayerMatchDetailResponse,
    CoachProfileResponse,
    GenerateAITrainingPlanRequest,
    GenerateAITrainingPlanResponse,
    CreateTrainingPlanRequest,
    CreateTrainingPlanResponse,
    TrainingPlanDetailResponse,
    UpdateTrainingPlanRequest,
    UpdateTrainingPlanResponse,
    DeleteTrainingPlanResponse
)
from app.services.match_processor import process_match_upload
from app.services import coach_service
from app.models.user import User


router = APIRouter()


@router.post(
    "/matches",
    response_model=MatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload match with StatsBomb JSON file",
    description="Upload StatsBomb JSON file with match metadata. Processes all 12 iterations: team identification, opponent creation, match record, players, lineups, events, goals, statistics."
)
async def upload_match(
    events_file: UploadFile = File(..., description="StatsBomb JSON file with events array"),
    opponent_name: str = Form(..., min_length=2, max_length=255, description="Opponent team name"),
    match_date: str = Form(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Match date (YYYY-MM-DD)"),
    our_score: int = Form(..., ge=0, description="Our team's score"),
    opponent_score: int = Form(..., ge=0, description="Opponent's score"),
    opponent_logo_url: Optional[str] = Form(None, description="Opponent logo URL (optional)"),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Upload and process match data with StatsBomb events JSON file.

    **Request Type:** multipart/form-data

    **Form Fields:**
    - events_file: JSON file containing StatsBomb events array (required)
    - opponent_name: Opponent team name (required, 2-255 chars)
    - match_date: Match date in YYYY-MM-DD format (required)
    - our_score: Our team's final score (required, >= 0)
    - opponent_score: Opponent's final score (required, >= 0)
    - opponent_logo_url: Opponent logo URL (optional)

    **File Format:**
    - Must be valid JSON file
    - Must contain an array of StatsBomb event objects
    - Typical size: 10-20 MB (3000-4000 events)
    - Max size: 50 MB

    **Processing Steps (all atomic):**
    1. Team identification
    2. Opponent club creation
    3. Match record creation
    4. Extract our players
    5. Extract opponent players
    6. Create match lineups
    7. Insert events
    8. Extract goals
    9. Calculate match statistics
    10. Calculate player match statistics
    11. Update club season statistics
    12. Update player season statistics

    All 12 steps succeed or all fail together (rollback on error).

    **Errors:**
    - 400: Validation error (invalid file, missing fields, invalid JSON)
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach)
    - 413: Payload too large (>50MB)
    - 500: Processing error (database error, unexpected failure)
    """
    # Validate file type
    if not events_file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file (.json extension)"
        )

    # Get coach_id from authenticated user
    coach_id = UUID(str(coach.coach.coach_id))

    try:
        # Read and parse JSON file
        file_content = await events_file.read()

        # Validate file size (50 MB limit)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 50:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds 50 MB limit"
            )

        # Parse JSON
        try:
            statsbomb_events = json.loads(file_content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON file: {str(e)}"
            )

        # Validate JSON is an array
        if not isinstance(statsbomb_events, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON file must contain an array of events"
            )

        # Validate array is not empty
        if len(statsbomb_events) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Events array cannot be empty"
            )

        # Prepare match_data dict for processor
        match_data = {
            "opponent_name": opponent_name,
            "opponent_logo_url": opponent_logo_url,
            "match_date": match_date,
            "our_score": our_score,
            "opponent_score": opponent_score,
            "statsbomb_events": statsbomb_events
        }

        # Process match through all 12 iterations
        result = process_match_upload(db, coach_id, match_data)
        return result

    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise

    except ValueError as e:
        # Validation errors from match_processor
        # Examples: invalid date, coach not found, team identification failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected errors (database errors, etc.)
        # Don't commit - match_processor handles rollback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process match upload: {str(e)}"
        )


# ============================================================================
# PROFILE & DASHBOARD ENDPOINTS
# ============================================================================

@router.get(
    "/profile",
    response_model=CoachProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coach profile",
    description="Get coach profile information with club stats."
)
def get_profile(
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get coach profile information.

    Returns coach info, club info, and club statistics (total players, matches, win rate).

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach)
    - 500: Internal server error
    """
    try:
        result = coach_service.get_coach_profile(db, coach.user_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coach dashboard",
    description="Get dashboard data with club statistics, season record, matches, and team form."
)
def get_dashboard(
    matches_limit: int = 20,
    matches_offset: int = 0,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get coach dashboard data.

    Returns comprehensive dashboard information including:
    - Coach and club info
    - Season record (wins/draws/losses)
    - Team form (last 5 matches)
    - Recent matches with pagination
    - Complete statistics (attacking, passing, defending)

    **Query Parameters:**
    - matches_limit: Number of matches to return (default: 20, max: 100)
    - matches_offset: Offset for pagination (default: 0)

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach)
    - 500: Internal server error
    """
    try:
        result = coach_service.get_dashboard_data(
            db,
            coach.user_id,
            matches_limit,
            matches_offset
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


# ============================================================================
# MATCH ENDPOINTS
# ============================================================================

@router.get(
    "/matches/{match_id}",
    response_model=MatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get match details",
    description="Get complete match details with statistics, goals, and lineups."
)
def get_match_detail(
    match_id: UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get complete match details.

    Returns:
    - Match basic info (date, score, result)
    - Teams info (our club, opponent)
    - Goal scorers with timestamps
    - Complete statistics comparison (match overview, attacking, passing, defending)
    - Lineups for both teams

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or match doesn't belong to club)
    - 404: Match not found
    - 500: Internal server error
    """
    try:
        # Get coach's club
        club = coach_service.get_coach_club(db, coach.user_id)

        # Get match detail
        result = coach_service.get_match_detail(db, match_id, club.club_id)
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match detail: {str(e)}"
        )


# ============================================================================
# PLAYER ENDPOINTS
# ============================================================================

@router.get(
    "/players",
    response_model=PlayersListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all players",
    description="Get list of all players in coach's club with summary counts."
)
def get_players(
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get all players in coach's club.

    Returns:
    - Summary counts (total, joined, pending)
    - List of all players ordered by jersey number

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach)
    - 500: Internal server error
    """
    try:
        # Get coach's club
        club = coach_service.get_coach_club(db, coach.user_id)

        # Get players list
        result = coach_service.get_players_list(db, club.club_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get players: {str(e)}"
        )


@router.get(
    "/players/{player_id}",
    response_model=PlayerDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player details",
    description="Get complete player details with attributes, statistics, matches, and training plans."
)
def get_player_detail(
    player_id: UUID,
    matches_limit: int = 20,
    matches_offset: int = 0,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get complete player details.

    Returns:
    - Player info (with age calculated from birth_date)
    - Invite code (only if player is unlinked)
    - Player attributes (attacking, technique, creativity, tactical, defending)
    - Season statistics (general, attacking, passing, dribbling, defending)
    - Player's matches with pagination
    - Training plans assigned to player

    **Query Parameters:**
    - matches_limit: Number of matches to return (default: 20, max: 100)
    - matches_offset: Offset for pagination (default: 0)

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or player doesn't belong to club)
    - 404: Player not found
    - 500: Internal server error
    """
    try:
        # Get coach's club
        club = coach_service.get_coach_club(db, coach.user_id)

        # Get player detail
        result = coach_service.get_player_detail(
            db,
            player_id,
            club.club_id,
            matches_limit,
            matches_offset
        )
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player detail: {str(e)}"
        )


@router.get(
    "/players/{player_id}/matches/{match_id}",
    response_model=PlayerMatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player match performance",
    description="Get player's performance statistics for a specific match."
)
def get_player_match_performance(
    player_id: UUID,
    match_id: UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get player's performance in specific match.

    Returns:
    - Match basic info
    - Teams info
    - Player summary (goals, assists)
    - Complete player statistics (attacking, passing, defending)

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or player/match don't belong to club)
    - 404: Player, match, or statistics not found
    - 500: Internal server error
    """
    try:
        # Get coach's club
        club = coach_service.get_coach_club(db, coach.user_id)

        # Get player match stats
        result = coach_service.get_player_match_stats(
            db,
            player_id,
            match_id,
            club.club_id
        )
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player match stats: {str(e)}"
        )


# ============================================================================
# TRAINING PLAN ENDPOINTS
# ============================================================================

@router.post(
    "/training-plans/generate-ai",
    response_model=GenerateAITrainingPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI training plan",
    description="Generate AI-powered training plan for player using Pydantic AI and RAG knowledge base."
)
async def generate_ai_training_plan(
    request: GenerateAITrainingPlanRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered training plan for player.

    Uses Pydantic AI with Google Gemini and RAG (PostgreSQL pgvector) to create
    personalized training plans based on player weaknesses and coaching knowledge.

    **Request Body:**
    - player_id: UUID of player to generate plan for

    **Returns:**
    - player_name: Player's name
    - jersey_number: Player's jersey number
    - plan_name: Generated plan name
    - duration: Plan duration
    - exercises: List of generated exercises (3-10)

    **AI Process:**
    1. Analyzes player attributes and season statistics
    2. Identifies weaknesses (attributes < 60, poor stats)
    3. Queries coaching knowledge base via RAG tool
    4. Generates personalized exercises targeting weaknesses

    **Errors:**
    - 400: GEMINI_API_KEY not configured
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or player doesn't belong to club)
    - 404: Player not found
    - 500: Internal server error (AI generation failed)
    """
    try:
        # Get coach's club
        club = coach_service.get_coach_club(db, coach.user_id)

        # Generate AI plan
        result = await coach_service.generate_ai_training_plan(
            db,
            UUID(request.player_id),
            club.club_id
        )
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "api_key" in error_msg or "gemini" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI training plan: {str(e)}"
        )


@router.post(
    "/training-plans",
    response_model=CreateTrainingPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create training plan",
    description="Create new training plan with exercises for a player."
)
def create_training_plan(
    request: CreateTrainingPlanRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Create new training plan with exercises.

    **Request Body:**
    - player_id: UUID of player to assign plan to
    - plan_name: Name of training plan
    - duration: Optional duration (e.g., "2 weeks")
    - coach_notes: Optional notes for player
    - exercises: List of exercises (at least 1)
      - exercise_name: Name of exercise
      - description: Optional description
      - sets, reps, duration_minutes: Optional exercise parameters
      - exercise_order: Order in plan (starting from 1)

    **Returns:**
    - plan_id: UUID of created plan
    - exercise_count: Number of exercises created
    - created_at: Creation timestamp

    **Errors:**
    - 400: Validation error (invalid data)
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or player doesn't belong to club)
    - 404: Player not found
    - 500: Internal server error
    """
    try:
        # Get coach ID
        coach_record = db.query(coach_service.Coach).filter(
            coach_service.Coach.user_id == coach.user_id
        ).first()

        if not coach_record:
            raise ValueError("Coach not found")

        # Create training plan
        result = coach_service.create_training_plan(
            db,
            UUID(request.player_id),
            coach_record.coach_id,
            request.dict()
        )

        db.commit()
        return result
    except ValueError as e:
        db.rollback()
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create training plan: {str(e)}"
        )


@router.get(
    "/training-plans/{plan_id}",
    response_model=TrainingPlanDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get training plan details",
    description="Get complete training plan details with exercises and progress."
)
def get_training_plan(
    plan_id: UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get training plan details.

    Returns:
    - Plan info (name, player, status, created date)
    - Progress (percentage, completed exercises, total exercises)
    - Exercises list ordered by exercise_order
    - Coach notes

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or plan doesn't belong to club)
    - 404: Training plan not found
    - 500: Internal server error
    """
    try:
        # Get coach ID
        coach_record = db.query(coach_service.Coach).filter(
            coach_service.Coach.user_id == coach.user_id
        ).first()

        if not coach_record:
            raise ValueError("Coach not found")

        # Get training plan detail
        result = coach_service.get_training_plan_detail(
            db,
            plan_id,
            coach_record.coach_id
        )
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training plan: {str(e)}"
        )


@router.put(
    "/training-plans/{plan_id}",
    response_model=UpdateTrainingPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update training plan",
    description="Update training plan and exercises."
)
def update_training_plan(
    plan_id: UUID,
    request: UpdateTrainingPlanRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Update training plan and exercises.

    **Request Body:**
    - plan_name: Optional new plan name
    - duration: Optional new duration
    - coach_notes: Optional new notes
    - exercises: Optional exercises list
      - exercise_id: UUID of existing exercise (None for new)
      - exercise_name, description, sets, reps, duration_minutes: Exercise data
      - exercise_order: Order in plan

    **Exercise Update Logic:**
    - With exercise_id: UPDATE existing exercise
    - Without exercise_id (None): INSERT new exercise
    - Not in request list: DELETE exercise

    **Errors:**
    - 400: Validation error
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or plan doesn't belong to club)
    - 404: Training plan not found
    - 500: Internal server error
    """
    try:
        # Get coach ID
        coach_record = db.query(coach_service.Coach).filter(
            coach_service.Coach.user_id == coach.user_id
        ).first()

        if not coach_record:
            raise ValueError("Coach not found")

        # Update training plan
        result = coach_service.update_training_plan(
            db,
            plan_id,
            coach_record.coach_id,
            request.dict(exclude_unset=True)
        )

        db.commit()
        return result
    except ValueError as e:
        db.rollback()
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update training plan: {str(e)}"
        )


@router.delete(
    "/training-plans/{plan_id}",
    response_model=DeleteTrainingPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete training plan",
    description="Delete training plan (cascades to exercises)."
)
def delete_training_plan(
    plan_id: UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Delete training plan.

    Deletes the training plan and all associated exercises (cascade delete).

    **Errors:**
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (user is not a coach or plan doesn't belong to club)
    - 404: Training plan not found
    - 500: Internal server error
    """
    try:
        # Get coach ID
        coach_record = db.query(coach_service.Coach).filter(
            coach_service.Coach.user_id == coach.user_id
        ).first()

        if not coach_record:
            raise ValueError("Coach not found")

        # Delete training plan
        result = coach_service.delete_training_plan(
            db,
            plan_id,
            coach_record.coach_id
        )

        db.commit()
        return result
    except ValueError as e:
        db.rollback()
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete training plan: {str(e)}"
        )

