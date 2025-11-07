"""
Database Configuration and Dependencies

This module handles database connection and provides database sessions.

Key Concepts:
- Engine: Manages the connection pool to PostgreSQL
- SessionLocal: Factory for creating database sessions
- get_db: Dependency that provides sessions to endpoints

Why a separate file?
- Avoids circular imports (main.py imports routes, routes need get_db)
- Centralizes database configuration
- Makes testing easier (can mock database separately)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_database_url, settings


# Database Engine Setup
# The engine manages connections to the database
# echo=True prints all SQL queries (useful for learning/debugging)
engine = create_engine(
    get_database_url(),
    echo=settings.debug,  # Print SQL queries when DEBUG=True
    pool_pre_ping=True,   # Test connections before using them (important for Neon!)
    pool_size=5,          # Keep 5 connections ready
    max_overflow=10       # Allow up to 10 additional connections when busy
)

# Session Factory
# Creates database sessions for running queries
# autocommit=False: Transactions must be explicitly committed
# autoflush=False: Changes aren't automatically flushed to DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency: Get Database Session
def get_db():
    """
    Database Session Dependency

    This is a FastAPI dependency that provides a database session to endpoints.
    FastAPI will automatically:
    1. Create a session before the request
    2. Pass it to the endpoint function
    3. Close it after the request (even if there's an error)

    Usage in endpoints:
    ```python
    @router.get("/some-endpoint")
    def my_endpoint(db: Session = Depends(get_db)):
        # Use db here to query the database
        pass
    ```

    Why use Depends()?
    - Automatic session management (no need to manually open/close)
    - FastAPI handles cleanup even if endpoint raises an exception
    - Can be easily mocked in tests
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the endpoint
    finally:
        db.close()  # Always close the session
