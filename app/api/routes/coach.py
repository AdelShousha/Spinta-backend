"""
API routes for coach endpoints.

This module contains all endpoints that coaches can access:
- POST /api/coach/matches - Upload match with StatsBomb JSON file
- Future endpoints will be added here
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import json

from app.database import get_db
from app.core.dependencies import require_coach
from app.schemas.coach import MatchUploadResponse
from app.services.match_processor import process_match_upload
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
