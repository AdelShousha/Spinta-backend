"""
FastAPI Application Entry Point

This is the main file that creates and configures the FastAPI application.

Key Concepts:
- FastAPI app instance is created here
- Middleware (CORS, error handling) is configured
- Routes are registered
- Database connection is initialized on startup
"""

from app.api.routes import health, auth, coach, player
from app import __version__
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.config import settings
from app.database import engine  # Import engine from database module

# has the code to run when the app starts up and shuts down


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan Events Handler

    This function runs code:
    - On startup (before yield)
    - On shutdown (after yield)

    Why?
    - Test database connection on startup
    - Close connections gracefully on shutdown
    - Initialize any resources needed
    """
    # STARTUP
    print("🔄 Testing database connection...")
    try:
        # Test the database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

    yield  # Application runs here

    # SHUTDOWN
    print("👋 Shutting down gracefully...")
    engine.dispose()  # Close all database connections


# Create FastAPI Application
app = FastAPI(
    title=settings.app_name,
    description="Youth soccer analytics platform API",  # shown in Swagger UI
    version=__version__,
    lifespan=lifespan,  # Register lifespan handler
    docs_url="/docs",    # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"   # ReDoc at http://localhost:8000/redoc
)


# CORS Middleware
# Allows frontend applications to call our API from different domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Which origins can access the API
    allow_credentials=True,                # Allow cookies
    # Allow all HTTP methods (GET, POST, etc.)
    allow_methods=["*"],
    allow_headers=["*"],                   # Allow all headers
)


# Register Routes
# We'll import and include route modules here

@app.get("/", tags=["Root"])  # tags is used in API docs to group endpoints
async def root():
    """
    Root endpoint - Simple welcome message

    This is useful to verify the API is running.
    Try accessing: http://localhost:8000/
    """
    return {
        "message": "Welcome to Spinta Backend API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Include routes from other modules
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(coach.router, prefix="/api/coach", tags=["Coach"])
app.include_router(player.router, prefix="/api/player", tags=["Player"])
