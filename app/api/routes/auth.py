"""
Authentication API Routes

Endpoints:
- POST /api/auth/register/coach - Coach registration + club creation
- POST /api/auth/verify-invite - Validate player invite code
- POST /api/auth/register/player - Complete player signup
- POST /api/auth/login - User login

All endpoints follow the specification in docs/04_AUTHENTICATION.md
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    CoachRegisterRequest,
    PlayerRegisterRequest,
    LoginRequest,
    VerifyInviteRequest,
    TokenResponse,
    CoachUserResponse,
    PlayerUserResponse,
    MinimalUserResponse,
    InviteValidationResponse,
    ClubResponse,
    PlayerDataResponse,
)
from app.crud.user import get_user_by_email
from app.crud.coach import create_coach_with_club
from app.crud.player import get_player_by_invite_code, link_player_to_user
from app.core.security import verify_password, create_access_token


router = APIRouter()


@router.post(
    "/register/coach",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new coach account",
    description="Create new coach account with club. Returns user data and JWT token."
)
def register_coach(
    request: CoachRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new coach account with club.

    This endpoint:
    1. Validates email uniqueness
    2. Creates user account with hashed password
    3. Creates coach record
    4. Creates club record
    5. Returns user data and JWT token

    All operations are performed in a single database transaction.

    **Errors:**
    - 409: Email already exists
    - 400: Validation error
    """
    # Check if email already exists
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # Create user, coach, and club in transaction
    try:
        user, coach, club = create_coach_with_club(
            db=db,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            club_name=request.club.club_name,
            birth_date=request.birth_date,
            gender=request.gender,
            country=request.club.country,
            age_group=request.club.age_group,
            stadium=request.club.stadium,
            logo_url=str(
                request.club.logo_url) if request.club.logo_url else None
        )

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create coach account: {str(e)}"
        )

    # Generate JWT token
    token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "user_type": user.user_type
    })

    # Build response with club data
    user_response = CoachUserResponse(
        user_id=user.user_id,
        email=user.email,
        user_type=user.user_type,
        full_name=user.full_name,
        club=ClubResponse(
            club_id=club.club_id,
            club_name=club.club_name,
            age_group=club.age_group,
            stadium=club.stadium,
            logo_url=club.logo_url
        )
    )

    return TokenResponse(user=user_response, token=token)


@router.post(
    "/verify-invite",
    response_model=InviteValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify player invite code",
    description="Validate invite code and return pre-filled player data."
)
def verify_invite(
    request: VerifyInviteRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a player invite code.

    This endpoint:
    1. Looks up player by invite code
    2. Checks if code has already been used
    3. Returns player and club data for pre-filling signup form

    **Errors:**
    - 404: Invalid invite code
    - 409: Invite code already used
    """
    # Get player by invite code
    player = get_player_by_invite_code(db, request.invite_code)

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code. Please check with your coach."
        )

    if player.is_linked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This invite code has already been used."
        )

    # Build response with player data
    player_data = PlayerDataResponse(
        player_id=player.player_id,
        player_name=player.player_name,
        jersey_number=player.jersey_number,
        position=player.position,
        club_name=player.club.club_name,
        club_logo_url=player.club.logo_url
    )

    return InviteValidationResponse(valid=True, player_data=player_data)


@router.post(
    "/register/player",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete player registration",
    description="Create player user account and link to existing player record."
)
def register_player(
    request: PlayerRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Complete player signup.

    This endpoint:
    1. Re-validates invite code
    2. Checks email uniqueness
    3. Creates user account with user_id = player_id
    4. Updates player record with profile data
    5. Marks player as linked
    6. Returns user data and JWT token

    All operations are performed in a single database transaction.

    **Errors:**
    - 404: Invalid invite code
    - 409: Invite code already used or email already exists
    - 400: Validation error
    """
    # Check if email already exists
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # Link player to user account
    try:
        player = link_player_to_user(
            db=db,
            invite_code=request.invite_code,
            player_name=request.player_name,
            email=request.email,
            password=request.password,
            birth_date=request.birth_date,
            height=request.height,
            profile_image_url=str(
                request.profile_image_url) if request.profile_image_url else None
        )

        db.commit()

    except ValueError as e:
        db.rollback()
        # ValueError from link_player_to_user (invalid code or already used)
        if "Invalid invite code" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invite code. Please check with your coach."
            )
        elif "already been used" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This invite code has already been used."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create player account: {str(e)}"
        )

    # Get user via player relationship
    user = player.user

    # Generate JWT token
    token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "user_type": user.user_type
    })

    # Build response with player and club data
    user_response = PlayerUserResponse(
        user_id=user.user_id,
        email=user.email,
        user_type=user.user_type,
        full_name=user.full_name,
        jersey_number=player.jersey_number,
        position=player.position,
        birth_date=player.birth_date,
        profile_image_url=player.profile_image_url,
        club=ClubResponse(
            club_id=player.club.club_id,
            club_name=player.club.club_name,
            age_group=player.club.age_group,
            stadium=player.club.stadium,
            logo_url=player.club.logo_url
        )
    )

    return TokenResponse(user=user_response, token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and return JWT token."
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return JWT token.

    This endpoint:
    1. Looks up user by email
    2. Verifies password hash
    3. Generates JWT token
    4. Returns minimal user data and token

    **Security:**
    - Same error message for "user not found" and "wrong password"
      (prevents email enumeration)
    - Consider rate limiting: 5 failed attempts per IP per 15 minutes

    **Errors:**
    - 401: Invalid email or password
    """
    # Get user by email
    user = get_user_by_email(db, request.email)

    # Verify user exists and password is correct
    # Use same error message for both to prevent email enumeration
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Generate JWT token
    token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "user_type": user.user_type
    })

    # Build minimal response (no club/player data for login)
    user_response = MinimalUserResponse(
        user_id=user.user_id,
        email=user.email,
        user_type=user.user_type,
        full_name=user.full_name
    )

    return TokenResponse(user=user_response, token=token)
