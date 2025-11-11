"""
Security utilities for password hashing and JWT token management.

This module provides functions for:
- Password hashing using bcrypt
- Password verification
- JWT token creation and validation

Usage:
    from app.core.security import get_password_hash, verify_password, create_access_token

    # Hash a password
    hashed = get_password_hash("my_password")

    # Verify a password
    is_valid = verify_password("my_password", hashed)

    # Create JWT token
    token = create_access_token({"user_id": "123", "email": "user@example.com"})

    # Decode JWT token
    payload = decode_access_token(token)
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password to hash

    Returns:
        Hashed password string (bcrypt format: $2b$12$...)

    Example:
        >>> hashed = get_password_hash("mypassword123")
        >>> hashed.startswith("$2b$")
        True
    """
    # Convert password to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        plain_password: Plain-text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    # Convert to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # Verify
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims to encode in the token.
              Typically includes: user_id, email, user_type
        expires_delta: Optional custom expiration time.
                      Defaults to 30 days if not specified.

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({
        ...     "user_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "email": "user@example.com",
        ...     "user_type": "coach"
        ... })
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()

    # Set expiration time (default: 30 days)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=30)

    to_encode.update({"exp": expire})

    # Encode the JWT token
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, str]]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing the token payload if valid, None if invalid/expired

    Example:
        >>> token = create_access_token({"user_id": "123", "email": "user@test.com"})
        >>> payload = decode_access_token(token)
        >>> payload["user_id"]
        '123'
        >>> decode_access_token("invalid_token")
        None
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        # Token is invalid or expired
        return None
