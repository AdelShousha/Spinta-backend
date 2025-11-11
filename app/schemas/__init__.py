"""
Pydantic schemas for request/response validation.

This package contains all Pydantic models used for API request validation
and response serialization.
"""

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
)

__all__ = [
    "CoachRegisterRequest",
    "PlayerRegisterRequest",
    "LoginRequest",
    "VerifyInviteRequest",
    "TokenResponse",
    "CoachUserResponse",
    "PlayerUserResponse",
    "MinimalUserResponse",
    "InviteValidationResponse",
]
