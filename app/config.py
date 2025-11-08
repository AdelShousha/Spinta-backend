"""
Configuration Management

This module handles all application configuration using Pydantic Settings.
Settings are loaded from environment variables and .env file.

Key Concepts:
- Pydantic validates configuration on startup
- Environment variables override .env file values
- Type safety ensures correct configuration types
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """
    Application Settings

    This class defines all configuration variables for the application.
    Pydantic automatically loads values from:
    1. Environment variables (highest priority)
    2. .env file (if it exists)
    3. Default values defined here (lowest priority)

    In development, store sensitive info (DB URL, secret keys) in .env file.
    In production (on server), never put a .env file; Instead set the same variable names directly in the server's settings panel
    If non of them exist the app uses the default values defined below (if any).
    If a required variable has no default and is not set in env or .env, Pydantic raises a validation error on startup.
    """

    # Application Metadata
    app_name: str = "Spinta Backend"
    debug: bool = True

    # database_url, secret_key are required because they have no defaults (editor will warn about it)

    # Database Configuration
    database_url: str

    # JWT Authentication
    # Generate with: openssl rand -hex 32
    secret_key: str
    algorithm: str = "HS256"  # JWT algorithm (HS256 is standard)

    # CORS Configuration
    # Stored as comma-separated string in .env file
    # Example: CORS_ORIGINS=http://localhost:3000,http://localhost:8080
    # The validation_alias tells Pydantic to look for "CORS_ORIGINS" in .env
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        validation_alias="CORS_ORIGINS"
    )

    @property
    def cors_origins(self) -> List[str]:
        """
        Parse CORS origins from comma-separated string to list.

        This property converts the cors_origins_str (comma-separated string)
        into a list of origins that FastAPI's CORS middleware expects.

        Why use a property?
        - Pydantic Settings tries to parse List[str] fields as JSON from env vars
        - By using a string field + property, we avoid the JSON parsing issue
        - The property provides easy access as a list when needed
        """
        return [origin.strip() for origin in self.cors_origins_str.split(',')]

    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8",  # UTF-8 encoding
        case_sensitive=False       # DATABASE_URL and database_url both work
    )


# Create a global settings instance
# This is imported throughout the application
settings = Settings()


# Database connection configuration
def get_database_url() -> str:
    """
    Returns the database URL for SQLAlchemy

    Why a function?
    - Easy to modify URL if needed (e.g., add connection pooling parameters)
    - Can handle different database types in the future
    - Centralizes database URL logic
    """
    return settings.database_url


# Display loaded configuration (for debugging)
if settings.debug:
    print(f"🚀 {settings.app_name} starting...")
    print(
        f"📊 Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'Not configured'}")
    print(f"🔒 JWT Algorithm: {settings.algorithm}")
    print(f"🌐 CORS Origins: {settings.cors_origins}")
