"""
FastAPI dependencies for authentication and authorization.

Dependencies:
- get_current_user: Validate JWT token and return authenticated user
- require_coach: Ensure user is a coach (403 if not)
- require_player: Ensure user is a player (403 if not)

Usage:
    from fastapi import Depends
    from app.core.dependencies import get_current_user, require_coach

    @router.get("/coach-only")
    def coach_endpoint(user: User = Depends(require_coach)):
        # user is guaranteed to be a coach
        return {"message": f"Hello Coach {user.full_name}"}
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.crud.user import get_user_by_id
from app.models.user import User


# HTTP Bearer token security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token and return the authenticated user.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Decodes and validates the token
    3. Retrieves the user from the database
    4. Returns the user instance

    Args:
        credentials: HTTPAuthorizationCredentials from HTTPBearer
        db: Database session

    Returns:
        Authenticated User instance

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found

    Example:
        @router.get("/profile")
        def get_profile(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}
    """
    # Get token from credentials
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from payload
    user_id: Optional[str] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_coach(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure the authenticated user is a coach.

    This dependency builds on get_current_user and adds role verification.

    Args:
        current_user: Authenticated user from get_current_user dependency

    Returns:
        User instance (guaranteed to be a coach)

    Raises:
        HTTPException 403: If user is not a coach

    Example:
        @router.post("/clubs")
        def create_club(
            club_data: ClubCreate,
            coach: User = Depends(require_coach)
        ):
            # coach is guaranteed to be user_type='coach'
            return {"coach_id": coach.coach.coach_id}
    """
    if not current_user.is_coach():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to coaches"
        )

    return current_user


def require_player(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure the authenticated user is a player.

    This dependency builds on get_current_user and adds role verification.

    Args:
        current_user: Authenticated user from get_current_user dependency

    Returns:
        User instance (guaranteed to be a player)

    Raises:
        HTTPException 403: If user is not a player

    Example:
        @router.get("/my-stats")
        def get_player_stats(
            player: User = Depends(require_player)
        ):
            # player is guaranteed to be user_type='player'
            return {"player_id": player.player.player_id}
    """
    if not current_user.is_player():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to players"
        )

    return current_user
