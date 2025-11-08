"""
Health Check Endpoint

This endpoint verifies that:
1. The API is running
2. The database connection is working

Why health checks?
- Monitoring tools can verify the API is alive
- Load balancers can remove unhealthy instances
- Quick way to diagnose issues

Concepts:
- APIRouter: Groups related endpoints together
- Depends: Dependency injection for database session
- try/except: Error handling for database checks
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db


# Create Router
# APIRouter groups endpoints and allows us to organize routes in separate files
router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health Check Endpoint

    Returns the health status of the API and database connection.

    **What happens here:**
    1. FastAPI calls get_db() to create a database session
    2. We execute a simple query (SELECT 1) to test the connection
    3. If successful, database status is "connected"
    4. If it fails, database status is "disconnected"
    5. Return JSON response with both statuses

    **Depends(get_db):**
    - get_db is a dependency that provides a database session
    - FastAPI automatically calls get_db() before this function
    - The session is passed as the 'db' parameter
    - FastAPI closes the session after the request completes

    Returns:
        dict: JSON response with status and database connection state

    Example Response:
        {
            "status": "healthy",
            "database": "connected"
        }
    """
    # Default database status
    database_status = "disconnected"

    # Test database connection
    try:
        # Execute a simple query to verify the connection works
        # SELECT 1 is the simplest possible query - just returns the number 1
        # text() is used to execute raw SQL (not an ORM query)
        result = db.execute(text("SELECT 1"))

        # If we got here without an exception, the database is connected!
        database_status = "connected"

    except Exception as e:
        # If any error occurs, the database is disconnected
        # In production, you might want to log this error
        print(f"Database health check failed: {e}")
        database_status = "disconnected"

    # Return the health status
    return {
        "status": "healthy",      # API is running
        "database": database_status  # Database connection state
    }
