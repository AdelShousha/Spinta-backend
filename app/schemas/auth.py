"""
Pydantic schemas for authentication endpoints.

This module contains request and response schemas for:
- Coach registration
- Player registration (2-step: verify invite + complete signup)
- User login

All schemas follow the specification in docs/04_AUTHENTICATION.md
"""

from datetime import date
from typing import Optional, Union, Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl, ConfigDict


# ================================
# Request Schemas
# ================================

class ClubCreateData(BaseModel):
    """Nested schema for club data in coach registration."""
    club_name: str = Field(..., min_length=2, max_length=255, description="Club name")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    age_group: Optional[str] = Field(None, description="Team age group (e.g., U16, U18)")
    stadium: Optional[str] = Field(None, max_length=255, description="Stadium name")
    logo_url: Optional[HttpUrl] = Field(None, description="Club logo URL")

    class Config:
        json_schema_extra = {
            "example": {
                "club_name": "Thunder United FC",
                "country": "United States",
                "age_group": "U16",
                "stadium": "City Stadium",
                "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
            }
        }


class CoachRegisterRequest(BaseModel):
    """Request schema for coach registration (POST /api/auth/register/coach)."""
    email: EmailStr = Field(..., description="Coach email address (must be unique)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Coach full name")
    birth_date: Optional[date] = Field(None, description="Coach birth date (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, max_length=20, description="Coach gender")
    club: ClubCreateData = Field(..., description="Club information")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@email.com",
                "password": "SecurePass123!",
                "full_name": "John Smith",
                "birth_date": "1985-06-15",
                "gender": "Male",
                "club": {
                    "club_name": "Thunder United FC",
                    "country": "United States",
                    "age_group": "U16",
                    "stadium": "City Stadium",
                    "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
                }
            }
        }


class VerifyInviteRequest(BaseModel):
    """Request schema for verifying player invite code (POST /api/auth/verify-invite)."""
    invite_code: str = Field(..., min_length=3, max_length=20, description="Player invite code (e.g., MRC-1827)")

    class Config:
        json_schema_extra = {
            "example": {
                "invite_code": "MRC-1827"
            }
        }


class PlayerRegisterRequest(BaseModel):
    """Request schema for player registration (POST /api/auth/register/player)."""
    invite_code: str = Field(..., min_length=3, max_length=20, description="Player invite code")
    player_name: str = Field(..., min_length=2, max_length=255, description="Player full name")
    email: EmailStr = Field(..., description="Player email address (must be unique)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    birth_date: date = Field(..., description="Player birth date (YYYY-MM-DD)")
    height: int = Field(..., ge=100, le=250, description="Player height in cm (100-250)")
    profile_image_url: Optional[HttpUrl] = Field(None, description="Player profile image URL")

    class Config:
        json_schema_extra = {
            "example": {
                "invite_code": "MRC-1827",
                "player_name": "Marcus Silva",
                "email": "marcus@email.com",
                "password": "SecurePass123!",
                "birth_date": "2008-03-20",
                "height": 180,
                "profile_image_url": "https://storage.example.com/players/marcus.jpg"
            }
        }


class LoginRequest(BaseModel):
    """Request schema for user login (POST /api/auth/login)."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@email.com",
                "password": "SecurePass123!"
            }
        }


# ================================
# Response Schemas
# ================================

class ClubResponse(BaseModel):
    """Nested schema for club data in responses."""
    club_id: str = Field(..., description="Club UUID")
    club_name: str = Field(..., description="Club name")
    age_group: Optional[str] = Field(None, description="Team age group")
    stadium: Optional[str] = Field(None, description="Stadium name")
    logo_url: Optional[str] = Field(None, description="Club logo URL")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "club_id": "550e8400-e29b-41d4-a716-446655440000",
                "club_name": "Thunder United FC",
                "age_group": "U16",
                "stadium": "City Stadium",
                "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
            }
        }


class CoachUserResponse(BaseModel):
    """Response schema for coach user data (registration only)."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@email.com",
                "user_type": "coach",
                "full_name": "John Smith",
                "club": {
                    "club_id": "club-uuid-here",
                    "club_name": "Thunder United FC",
                    "age_group": "U16",
                    "stadium": "City Stadium",
                    "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
                }
            }
        }
    )

    user_id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    user_type: Literal["coach"] = Field(..., description="User type (always 'coach')")
    full_name: str = Field(..., description="User full name")
    club: ClubResponse = Field(..., description="Coach's club")


class PlayerUserResponse(BaseModel):
    """Response schema for player user data (registration only)."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "marcus@email.com",
                "user_type": "player",
                "full_name": "Marcus Silva",
                "jersey_number": 10,
                "position": "Forward",
                "birth_date": "2008-03-20",
                "profile_image_url": "https://storage.example.com/players/marcus.jpg",
                "club": {
                    "club_id": "club-uuid-here",
                    "club_name": "Thunder United FC",
                    "age_group": "U16",
                    "stadium": "City Stadium",
                    "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
                }
            }
        }
    )

    user_id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    user_type: Literal["player"] = Field(..., description="User type (always 'player')")
    full_name: str = Field(..., description="User full name")
    jersey_number: int = Field(..., description="Jersey number")
    position: str = Field(..., description="Player position")
    birth_date: date = Field(..., description="Birth date")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    club: ClubResponse = Field(..., description="Player's club")


class MinimalUserResponse(BaseModel):
    """Response schema for minimal user data (login only)."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@email.com",
                "user_type": "coach",
                "full_name": "John Smith"
            }
        }
    )

    user_id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    user_type: str = Field(..., description="User type (coach or player)")
    full_name: str = Field(..., description="User full name")


class TokenResponse(BaseModel):
    """Response schema for authentication endpoints that return a token."""
    user: Union[CoachUserResponse, PlayerUserResponse, MinimalUserResponse] = Field(
        ..., description="Authenticated user data"
    )
    token: str = Field(..., description="JWT access token")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "john@email.com",
                    "user_type": "coach",
                    "full_name": "John Smith"
                },
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PlayerDataResponse(BaseModel):
    """Nested schema for player data in invite verification response."""
    player_id: str = Field(..., description="Player UUID")
    player_name: str = Field(..., description="Player name")
    jersey_number: int = Field(..., description="Jersey number")
    position: str = Field(..., description="Player position")
    club_name: str = Field(..., description="Club name")
    club_logo_url: Optional[str] = Field(None, description="Club logo URL")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "player_id": "660e8400-e29b-41d4-a716-446655440001",
                "player_name": "Marcus Silva",
                "jersey_number": 10,
                "position": "Forward",
                "club_name": "Thunder United FC",
                "club_logo_url": "https://storage.example.com/clubs/thunder-logo.png"
            }
        }


class InviteValidationResponse(BaseModel):
    """Response schema for invite code verification (POST /api/auth/verify-invite)."""
    valid: bool = Field(..., description="Whether the invite code is valid")
    player_data: PlayerDataResponse = Field(..., description="Pre-filled player data")

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "player_data": {
                    "player_id": "660e8400-e29b-41d4-a716-446655440001",
                    "player_name": "Marcus Silva",
                    "jersey_number": 10,
                    "position": "Forward",
                    "club_name": "Thunder United FC",
                    "club_logo_url": "https://storage.example.com/clubs/thunder-logo.png"
                }
            }
        }
