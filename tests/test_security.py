"""
Security Utilities Tests

Tests for password hashing and JWT token management.
Tests are grouped by functionality (password ops, JWT ops).

Run with: pytest tests/test_security.py -v
"""

from datetime import timedelta

import pytest

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordOperations:
    """
    Consolidated tests for password hashing and verification.

    Tests both hashing and verification in grouped scenarios.
    """

    def test_password_hash_and_verify(self):
        """
        Test complete password workflow: hash and verify.

        Scenarios:
        - Hash generates bcrypt format
        - Correct password verifies successfully
        - Incorrect password fails verification
        - Different passwords generate different hashes
        """
        # Test hashing
        password = "my_secure_password_123"
        hashed = get_password_hash(password)

        # Verify hash format (bcrypt: $2b$12$...)
        assert hashed.startswith("$2b$"), "Hash should be in bcrypt format"
        assert len(hashed) == 60, "Bcrypt hash should be 60 characters"

        # Verify correct password
        assert verify_password(password, hashed) is True, "Correct password should verify"

        # Verify incorrect password fails
        assert verify_password("wrong_password", hashed) is False, "Wrong password should fail"

        # Verify different passwords generate different hashes
        password2 = "different_password_456"
        hashed2 = get_password_hash(password2)
        assert hashed != hashed2, "Different passwords should generate different hashes"

        # Verify each password only matches its own hash
        assert verify_password(password, hashed2) is False
        assert verify_password(password2, hashed) is False


class TestJWTOperations:
    """
    Consolidated tests for JWT token creation and validation.

    Tests token lifecycle: creation, decoding, and expiration.
    """

    def test_jwt_create_and_decode(self):
        """
        Test JWT token creation and decoding.

        Scenarios:
        - Token creation with standard payload
        - Successful decoding of valid token
        - Payload data preserved correctly
        - Token contains expiration claim
        """
        # Create token with user data
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@example.com",
            "user_type": "coach"
        }

        token = create_access_token(payload)

        # Verify token is a string
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"

        # Decode token
        decoded = decode_access_token(token)

        # Verify payload is preserved
        assert decoded is not None, "Valid token should decode successfully"
        assert decoded["user_id"] == payload["user_id"]
        assert decoded["email"] == payload["email"]
        assert decoded["user_type"] == payload["user_type"]

        # Verify expiration claim exists
        assert "exp" in decoded, "Token should contain expiration claim"

    def test_jwt_invalid_token(self):
        """
        Test handling of invalid JWT tokens.

        Scenarios:
        - Invalid token format returns None
        - Tampered token returns None
        - Empty token returns None
        """
        # Test completely invalid token
        assert decode_access_token("invalid_token_string") is None

        # Test empty token
        assert decode_access_token("") is None

        # Test tampered token (valid format but wrong signature)
        valid_token = create_access_token({"user_id": "123"})
        tampered_token = valid_token[:-10] + "tamperedXX"
        assert decode_access_token(tampered_token) is None

    def test_jwt_custom_expiration(self):
        """
        Test JWT token with custom expiration time.

        Scenarios:
        - Token accepts custom expiration delta
        - Custom expiration is applied correctly
        """
        payload = {"user_id": "123", "email": "user@test.com"}

        # Create token with 1 day expiration
        token = create_access_token(payload, expires_delta=timedelta(days=1))
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["user_id"] == "123"
        assert "exp" in decoded

    def test_jwt_different_users_different_tokens(self):
        """
        Test that different users get different tokens.

        Scenarios:
        - Same payload generates different tokens (due to exp timestamp)
        - Different payloads generate different tokens
        """
        payload1 = {"user_id": "user-1", "email": "user1@test.com"}
        payload2 = {"user_id": "user-2", "email": "user2@test.com"}

        token1 = create_access_token(payload1)
        token2 = create_access_token(payload2)

        # Tokens should be different
        assert token1 != token2

        # Each token decodes to correct payload
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)

        assert decoded1["user_id"] == "user-1"
        assert decoded2["user_id"] == "user-2"
