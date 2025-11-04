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
from typing import List


class Settings(BaseSettings):
    """
    Application Settings

    This class defines all configuration variables for the application.
    Pydantic automatically loads values from:
    1. Environment variables (highest priority)
    2. .env file (if it exists)
    3. Default values defined here (lowest priority)
    """

    # Application Metadata
    app_name: str = "Spinta Backend"
    debug: bool = True

    # Database Configuration
    # This is your Neon database connection string
    # Format: postgresql://user:password@host/database?sslmode=require
    database_url: str

    # JWT Authentication
    # SECRET_KEY must be a strong random string in production
    # Generate with: openssl rand -hex 32
    secret_key: str
    algorithm: str = "HS256"  # JWT algorithm (HS256 is standard)

    # CORS (Cross-Origin Resource Sharing)
    # Allows frontend apps from these origins to access the API
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8", # UTF-8 encoding
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
    print(f"📊 Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'Not configured'}")
    print(f"🔒 JWT Algorithm: {settings.algorithm}")
    print(f"🌐 CORS Origins: {settings.cors_origins}")
