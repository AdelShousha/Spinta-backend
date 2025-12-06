"""
API routes for player endpoints.

Endpoints:
- GET /api/player/dashboard - My Stats tab (attributes + season stats)
- GET /api/player/matches - Paginated matches list
- GET /api/player/matches/{match_id} - Player match performance
- GET /api/player/training - Training plans list
- GET /api/player/training/{plan_id} - Training plan detail
- PUT /api/player/training/exercises/{exercise_id}/toggle - Toggle exercise completion
- GET /api/player/profile - Player profile

All endpoints require authentication with user_type='player'.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.core.dependencies import require_player
from app.models.user import User
from app.services import player_endpoint_service
from app.schemas.player import (
    PlayerDashboardResponse,
    PlayerMatchesListResponse,
    PlayerMatchDetailResponse,
    PlayerTrainingListResponse,
    PlayerTrainingPlanDetailResponse,
    ToggleExerciseRequest,
    ToggleExerciseResponse,
    PlayerProfileResponse,
)

router = APIRouter()


# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================

@router.get(
    "/dashboard",
    response_model=PlayerDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player dashboard (My Stats tab)",
    description="Returns player's attributes and season statistics."
)
def get_dashboard(
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Get player dashboard data for My Stats tab.

    Returns:
    - Player info (name, jersey, height, age, image)
    - Attributes (5 ratings for radar chart)
    - Season statistics grouped by category
    """
    try:
        # Get player_id from authenticated user's player relationship
        player_id = player.player.player_id

        result = player_endpoint_service.get_player_dashboard(db, player_id)
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
# MATCHES ENDPOINTS
# ============================================================================

@router.get(
    "/matches",
    response_model=PlayerMatchesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player's matches list",
    description="Returns paginated list of matches player participated in."
)
def get_matches(
    limit: int = Query(default=20, ge=1, le=100, description="Number of matches to return"),
    offset: int = Query(default=0, ge=0, description="Number of matches to skip"),
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of player's matches.

    Query Parameters:
    - limit: Number of matches to return (default 20, max 100)
    - offset: Number to skip for pagination (default 0)

    Returns:
    - total_count: Total number of matches player participated in
    - matches: List of match summaries with result
    """
    try:
        player_id = player.player.player_id

        result = player_endpoint_service.get_player_matches(
            db, player_id, limit, offset
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get matches: {str(e)}"
        )


@router.get(
    "/matches/{match_id}",
    response_model=PlayerMatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player match detail",
    description="Returns player's performance in a specific match."
)
def get_match_detail(
    match_id: UUID,
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Get player's performance in specific match.

    Path Parameters:
    - match_id: UUID of the match

    Returns:
    - Match info (date, score, result)
    - Teams info (our club, opponent)
    - Player summary (goals, assists)
    - Statistics (attacking, passing, defending)

    Raises:
    - 404: If match not found or player didn't participate
    """
    try:
        player_id = player.player.player_id

        result = player_endpoint_service.get_player_match_detail(
            db, player_id, match_id
        )
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match detail: {str(e)}"
        )


# ============================================================================
# TRAINING ENDPOINTS
# ============================================================================

@router.get(
    "/training",
    response_model=PlayerTrainingListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player's training plans",
    description="Returns all training plans assigned to player."
)
def get_training_plans(
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Get all training plans for player.

    Returns:
    - training_plans: List of plans with name, date, status
    """
    try:
        player_id = player.player.player_id

        result = player_endpoint_service.get_player_training_plans(db, player_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training plans: {str(e)}"
        )


@router.get(
    "/training/{plan_id}",
    response_model=PlayerTrainingPlanDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get training plan detail",
    description="Returns training plan with exercises and progress."
)
def get_training_plan_detail(
    plan_id: UUID,
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Get training plan detail for player.

    Path Parameters:
    - plan_id: UUID of the training plan

    Returns:
    - Plan info (name, status, date)
    - Progress (percentage, completed/total)
    - Exercises with completion status
    - Coach notes

    Raises:
    - 404: If plan not found
    - 403: If plan not assigned to player
    """
    try:
        player_id = player.player.player_id

        result = player_endpoint_service.get_player_training_plan_detail(
            db, player_id, plan_id
        )
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training plan: {str(e)}"
        )


@router.put(
    "/training/exercises/{exercise_id}/toggle",
    response_model=ToggleExerciseResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle exercise completion",
    description="Mark exercise as complete/incomplete."
)
def toggle_exercise(
    exercise_id: UUID,
    request: ToggleExerciseRequest,
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Toggle exercise completion status.

    Path Parameters:
    - exercise_id: UUID of the exercise

    Request Body:
    - completed: bool - New completion status

    Returns:
    - exercise_id: UUID
    - completed: bool
    - completed_at: datetime (if completed)
    - plan_progress: Updated plan progress with status

    Raises:
    - 404: If exercise not found
    - 403: If exercise not part of player's plan
    """
    try:
        player_id = player.player.player_id

        result = player_endpoint_service.toggle_exercise_completion(
            db, player_id, exercise_id, request.completed
        )

        db.commit()
        return result
    except ValueError as e:
        db.rollback()
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle exercise: {str(e)}"
        )


# ============================================================================
# PROFILE ENDPOINT
# ============================================================================

@router.get(
    "/profile",
    response_model=PlayerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player profile",
    description="Returns player profile information."
)
def get_profile(
    player: User = Depends(require_player),
    db: Session = Depends(get_db)
):
    """
    Get player profile.

    Returns:
    - Player info (name, email, jersey, position, height, birth_date, image)
    - Club info (name)
    - Season summary (matches, goals, assists)
    """
    try:
        player_id = player.player.player_id

        result = player_endpoint_service.get_player_profile(db, player_id)
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
