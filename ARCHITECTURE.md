# Spinta Backend Architecture Guide

A comprehensive explanation of every file in the backend, how they work, and how they connect together.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [File-by-File Explanation](#file-by-file-explanation)
3. [How Files Connect](#how-files-connect)
4. [Request Flow](#request-flow)
5. [Data Flow Diagrams](#data-flow-diagrams)

---

## Project Overview

This FastAPI backend is built with a **modular architecture** that separates concerns into different files:

- **Configuration** → `config.py`
- **Database** → `database.py`
- **Application** → `main.py`
- **API Routes** → `api/routes/health.py`
- **Tests** → `tests/test_health.py`

**Key Design Principles:**
- Separation of concerns (each file has one responsibility)
- Dependency injection (FastAPI manages dependencies)
- Test-Driven Development (tests written first)
- Environment-based configuration (secrets in .env)

---

## File-by-File Explanation

### 1. `.env` - Environment Variables (Secrets)

**Location:** `D:\Spinta_Backend\.env`

**Purpose:** Store sensitive configuration data that should NOT be committed to git.

**Content:**
```env
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
APP_NAME=Spinta Backend
DEBUG=True
SECRET_KEY=your-secret-key-here-change-this-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Why This Exists:**
- **Security**: Keeps passwords and secrets out of source code
- **Flexibility**: Different values for development, staging, production
- **Best Practice**: Never commit `.env` to git (it's in `.gitignore`)

**What It Does:**
- Python's `python-dotenv` library reads this file on startup
- Pydantic Settings in `config.py` loads these values
- Each variable becomes an attribute of the `settings` object

**Connection to Other Files:**
- Read by: `config.py` (via Pydantic Settings)
- Used by: All files that import `settings`

---

### 2. `.env.example` - Configuration Template

**Location:** `D:\Spinta_Backend\.env.example`

**Purpose:** A template showing what variables are needed, without exposing real secrets.

**Content:**
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@ep-example.neon.tech/spinta_db?sslmode=require

# Application Settings
APP_NAME=Spinta Backend
DEBUG=True

# JWT Secret Key
SECRET_KEY=your-secret-key-here-change-this-in-production

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Why This Exists:**
- **Documentation**: Shows developers what variables to set
- **Onboarding**: New developers copy this to `.env` and fill in real values
- **Safety**: Can be committed to git (no real secrets)

**What It Does:**
- Serves as documentation only
- Not read by the application
- Developers manually copy it to create `.env`

**Connection to Other Files:**
- Template for: `.env`
- Referenced in: `GETTING_STARTED.md`

---

### 3. `.gitignore` - Git Ignore Rules

**Location:** `D:\Spinta_Backend\.gitignore`

**Purpose:** Tell Git which files should NOT be tracked or committed.

**Key Sections:**
```gitignore
# Environment Variables (CRITICAL - contains secrets!)
.env
.env.local

# Python cache
__pycache__/
*.pyc

# Virtual environments
venv/
.venv/
env/

# Testing
.pytest_cache/
.coverage

# IDE
.vscode/
.idea/
```

**Why This Exists:**
- **Security**: Prevents committing `.env` with database passwords
- **Cleanliness**: Excludes generated files (cache, builds)
- **Portability**: Excludes environment-specific files (venv, IDE config)

**What It Does:**
- Git reads this file to know what to ignore
- Listed files won't appear in `git status`
- Can't accidentally commit secrets

**Connection to Other Files:**
- Protects: `.env`, `__pycache__/`, `.venv/`, etc.

---

### 4. `requirements.txt` - Python Dependencies

**Location:** `D:\Spinta_Backend\requirements.txt`

**Purpose:** List all Python packages needed to run the application.

**Key Dependencies:**
```txt
# Core Framework
fastapi==0.109.0          # Web framework for building APIs
uvicorn[standard]==0.27.0 # ASGI server to run FastAPI

# Database
sqlalchemy==2.0.25        # ORM for database operations
psycopg2-binary==2.9.9    # PostgreSQL adapter
alembic==1.13.1           # Database migrations

# Configuration
python-dotenv==1.0.0      # Load .env files
pydantic-settings==2.1.0  # Settings management

# Authentication
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4            # Password hashing

# Testing
pytest==7.4.3             # Testing framework
httpx==0.26.0             # HTTP client for testing
```

**Why This Exists:**
- **Reproducibility**: Same versions on all machines
- **Easy Setup**: `pip install -r requirements.txt`
- **Documentation**: See all project dependencies

**What It Does:**
- When you run `pip install -r requirements.txt`, pip installs all listed packages
- Pinned versions (==) ensure consistency across environments

**Connection to Other Files:**
- Used by: All Python files (imports these packages)
- Read by: `pip` during installation

---

### 5. `pytest.ini` - Pytest Configuration

**Location:** `D:\Spinta_Backend\pytest.ini`

**Purpose:** Configure pytest behavior (test discovery, output format, markers).

**Content:**
```ini
[pytest]
# Test discovery patterns
python_files = test_*.py      # Files starting with test_
python_classes = Test*         # Classes starting with Test
python_functions = test_*      # Functions starting with test_

# Output options
addopts =
    -v                         # Verbose output
    --strict-markers           # Error on unknown markers
    --tb=short                 # Shorter traceback format
    --disable-warnings         # Hide deprecation warnings
    -p no:warnings            # Disable warning summary
    --color=yes               # Colored output

# Test paths
testpaths = tests              # Look for tests in tests/ directory

# Markers (for organizing tests)
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (use database)
    slow: Slow tests (> 1 second)

# Asyncio configuration
asyncio_mode = auto
```

**Why This Exists:**
- **Consistency**: All developers see same test output
- **Organization**: Define custom test markers
- **Configuration**: Centralize pytest settings

**What It Does:**
- pytest reads this file on startup
- Configures test discovery (how pytest finds tests)
- Sets output format (verbose, colors, traceback length)

**Connection to Other Files:**
- Read by: `pytest` command
- Affects: All test files in `tests/`

---

### 6. `app/__init__.py` - App Package Initializer

**Location:** `D:\Spinta_Backend\app\__init__.py`

**Purpose:** Mark `app/` directory as a Python package.

**Content:**
```python
"""
Spinta Backend Application

This package contains the main application code for the Spinta platform.
"""

__version__ = "0.1.0"
```

**Why This Exists:**
- **Python Requirement**: Directories need `__init__.py` to be importable as packages
- **Metadata**: Can define package-level variables like `__version__`
- **Imports**: Can expose specific items at package level (optional)

**What It Does:**
- Tells Python that `app/` is a package
- Allows `from app.config import settings`
- Defines the version string

**Connection to Other Files:**
- Makes importable: All files in `app/` directory
- Can be imported: `from app import __version__`

---

### 7. `app/config.py` - Configuration Management

**Location:** `D:\Spinta_Backend\app\config.py`

**Purpose:** Load and manage all application configuration from environment variables.

**Key Components:**

#### **Imports:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
```

#### **Settings Class:**
```python
class Settings(BaseSettings):
    # Application metadata
    app_name: str = "Spinta Backend"
    debug: bool = True

    # Database
    database_url: str  # Required, no default

    # JWT Authentication
    secret_key: str  # Required
    algorithm: str = "HS256"

    # CORS - stored as string, converted to list
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        validation_alias="CORS_ORIGINS"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in self.cors_origins_str.split(',')]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
```

#### **Global Instance:**
```python
settings = Settings()  # Created once on import
```

**Why This Exists:**
- **Centralization**: All config in one place
- **Type Safety**: Pydantic validates types on startup
- **Flexibility**: Different values per environment

**What It Does:**
1. **On Import:**
   - Reads `.env` file
   - Loads environment variables
   - Validates types (str, bool, etc.)
   - Creates global `settings` object

2. **CORS Property:**
   - Stores CORS origins as string (`cors_origins_str`)
   - Uses `Field(validation_alias="CORS_ORIGINS")` to map env var name
   - `@property` converts to list when accessed
   - Avoids Pydantic JSON parsing issue

3. **Validation:**
   - If `DATABASE_URL` is missing → Error on startup
   - If `DEBUG` is not a boolean → Error on startup

**Connection to Other Files:**
- Reads from: `.env`
- Imported by: `database.py`, `main.py`
- Used by: All files that need configuration

**Key Methods:**
```python
# Access configuration anywhere:
from app.config import settings

print(settings.app_name)      # "Spinta Backend"
print(settings.database_url)  # "postgresql://..."
print(settings.cors_origins)  # ["http://localhost:3000", "http://localhost:8080"]
```

---

### 8. `app/database.py` - Database Connection & Dependencies

**Location:** `D:\Spinta_Backend\app\database.py`

**Purpose:** Centralize all database-related code (engine, sessions, dependencies).

**Key Components:**

#### **Imports:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_database_url, settings
```

#### **Database Engine:**
```python
engine = create_engine(
    get_database_url(),
    echo=settings.debug,      # Print SQL queries when DEBUG=True
    pool_pre_ping=True,       # Test connections before using (important for Neon!)
    pool_size=5,              # Keep 5 connections ready
    max_overflow=10           # Allow up to 10 additional connections when busy
)
```

**What the engine does:**
- **Connection Pooling**: Reuses database connections (faster than creating new ones)
- **pool_pre_ping**: Tests connection before using (handles serverless database sleep)
- **echo**: Logs all SQL queries (learning tool!)

#### **Session Factory:**
```python
SessionLocal = sessionmaker(
    autocommit=False,    # Don't auto-commit transactions
    autoflush=False,     # Don't auto-flush changes
    bind=engine          # Bind to our engine
)
```

**What the session factory does:**
- Creates new database sessions
- Each session = one "conversation" with the database
- `autocommit=False`: Must explicitly call `db.commit()`

#### **Dependency Function:**
```python
def get_db():
    """
    FastAPI dependency that provides a database session.

    Usage:
    @app.get("/endpoint")
    def my_endpoint(db: Session = Depends(get_db)):
        # Use db here
        pass
    """
    db = SessionLocal()
    try:
        yield db  # Provide session to endpoint
    finally:
        db.close()  # Always close, even if endpoint raises error
```

**What get_db does:**
1. Creates a new session
2. Yields it to the endpoint (FastAPI injects it as parameter)
3. **Always closes** the session (in finally block)
4. Even if endpoint crashes, session gets closed

**Why This Exists:**
- **Separation of Concerns**: Database logic separate from app logic
- **Avoid Circular Imports**: Prevents main.py ↔ health.py import loop
- **Reusability**: Any route can use `Depends(get_db)`

**What It Does:**
- Creates database engine on import (happens once)
- Provides `get_db` dependency for FastAPI endpoints
- Manages connection pooling

**Connection to Other Files:**
- Reads config from: `config.py`
- Imported by: `main.py` (for engine), `health.py` (for get_db)
- Used by: All endpoints that need database access

---

### 9. `app/main.py` - FastAPI Application Entry Point

**Location:** `D:\Spinta_Backend\app\main.py`

**Purpose:** Create and configure the FastAPI application, register routes, set up middleware.

**Key Components:**

#### **Imports:**
```python
from app.api.routes import health
from app import __version__
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.config import settings
from app.database import engine
```

**Import Highlights:**
- `from app import __version__`: Imports version string from `app/__init__.py`
- Keeps version in single place (single source of truth)
- Used in FastAPI app metadata for documentation

#### **Lifespan Handler:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs code on startup and shutdown.

    Startup (before yield):
    - Test database connection

    Shutdown (after yield):
    - Close database connections
    """
    # STARTUP
    print("🔄 Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

    yield  # Application runs here

    # SHUTDOWN
    print("👋 Shutting down gracefully...")
    engine.dispose()  # Close all connections
```

**What the lifespan handler does:**
- Runs **BEFORE** the application starts accepting requests
- Tests database connection with `SELECT 1`
- If database is down → Application fails to start (fail fast!)
- Runs **AFTER** the application stops
- Closes all database connections gracefully

#### **FastAPI App Creation:**
```python
app = FastAPI(
    title=settings.app_name,
    description="Youth soccer analytics platform API",
    version=__version__,     # Uses version from app/__init__.py
    lifespan=lifespan,       # Register lifespan handler
    docs_url="/docs",        # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"       # ReDoc at http://localhost:8000/redoc
)
```

**What this creates:**
- The FastAPI application instance
- Automatic interactive documentation at `/docs`
- Alternative documentation at `/redoc`
- **Version from `__init__.py`**: Displayed in API docs (single source of truth)
- Lifespan events registered

#### **CORS Middleware:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Frontend URLs that can call API
    allow_credentials=True,                # Allow cookies
    allow_methods=["*"],                   # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],                   # Allow all headers
)
```

**What CORS middleware does:**
- Adds CORS headers to responses
- Allows frontend applications from different domains to call the API
- Without this, browsers block cross-origin requests

#### **Root Endpoint:**
```python
@app.get("/", tags=["Root"])
async def root():
    """Simple welcome message"""
    return {
        "message": "Welcome to Spinta Backend API",
        "docs": "/docs",
        "redoc": "/redoc"
    }
```

**What this does:**
- Provides a simple endpoint at `http://localhost:8000/`
- Returns JSON with helpful links to documentation
- `tags=["Root"]` groups it in API docs
- Points users to both Swagger UI (`/docs`) and ReDoc (`/redoc`)

#### **Route Registration:**
```python
# Import at top of file:
# from app.api.routes import health

app.include_router(health.router, prefix="/api", tags=["Health"])
```

**What this does:**
- Registers all routes from `health.router` (imported at top)
- Adds `/api` prefix (so `/health` becomes `/api/health`)
- Tags all health routes as "Health" in docs
- Router pattern allows organizing endpoints in separate files

**Why This Exists:**
- **Entry Point**: This is what `uvicorn` runs
- **Configuration**: Sets up middleware, CORS, docs
- **Route Registration**: Connects all API routes

**What It Does:**
1. On import: Creates FastAPI app, adds middleware
2. On startup: Tests database connection
3. During runtime: Handles HTTP requests
4. On shutdown: Closes database connections

**Connection to Other Files:**
- Reads config from: `config.py`
- Uses database from: `database.py`
- Registers routes from: `api/routes/health.py`
- Run by: `uvicorn` command

---

### 10. `app/api/__init__.py` - API Package Initializer

**Location:** `D:\Spinta_Backend\app\api\__init__.py`

**Purpose:** Mark `api/` directory as a Python package.

**Content:**
```python
"""
API Package

Contains all API routes and endpoints.
"""
```

**Why This Exists:**
- Makes `api/` importable as a package
- Allows `from app.api.routes import health`

**Connection to Other Files:**
- Makes importable: `app/api/routes/`

---

### 11. `app/api/routes/__init__.py` - Routes Package Initializer

**Location:** `D:\Spinta_Backend\app\api\routes\__init__.py`

**Purpose:** Mark `routes/` directory as a Python package.

**Content:**
```python
"""
API Routes Package

Contains all route handlers organized by feature.
"""
```

**Why This Exists:**
- Makes `routes/` importable as a package
- Allows `from app.api.routes import health`

**Connection to Other Files:**
- Makes importable: `app/api/routes/health.py`

---

### 12. `app/api/routes/health.py` - Health Check Endpoints

**Location:** `D:\Spinta_Backend\app\api\routes\health.py`

**Purpose:** Provide health check endpoints to verify API and database are working.

**Key Components:**

#### **Imports:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
```

#### **Router Creation:**
```python
router = APIRouter()
```

**What APIRouter does:**
- Groups related endpoints together
- Can be registered in main.py with `app.include_router()`
- Keeps route definitions separate from main app

#### **Health Check Endpoint:**
```python
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Check if API and database are healthy.

    Returns:
        {"status": "healthy", "database": "connected"}
    """
    database_status = "disconnected"

    try:
        # Execute simple query to test connection
        result = db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        print(f"Database health check failed: {e}")
        database_status = "disconnected"

    return {
        "status": "healthy",
        "database": database_status
    }
```

**What this endpoint does:**
1. FastAPI sees `db: Session = Depends(get_db)`
2. Calls `get_db()` to create a database session
3. Injects the session as the `db` parameter
4. Endpoint executes `SELECT 1` query
5. If successful: `database: "connected"`
6. If fails: `database: "disconnected"`
7. Returns JSON response
8. FastAPI calls `db.close()` (in get_db's finally block)

**Flow:**
```
Request → FastAPI → Depends(get_db) → get_db() creates session →
Inject session → health_check() runs → SELECT 1 →
Return JSON → get_db() closes session → Response
```

**Why This Exists:**
- **Monitoring**: External tools can check if API is alive
- **Debugging**: Quickly verify database connectivity
- **Load Balancers**: Can route traffic away from unhealthy instances
- **Simplicity**: Single endpoint, clear purpose

**What It Does:**
- Provides `/api/health` endpoint (after prefix from main.py)
- Tests database connection
- Returns status as JSON

**Connection to Other Files:**
- Uses dependency from: `database.py` (`get_db`)
- Registered in: `main.py`
- Tested by: `tests/test_health.py`

---

### 13. `tests/__init__.py` - Tests Package Initializer

**Location:** `D:\Spinta_Backend\tests\__init__.py`

**Purpose:** Mark `tests/` directory as a Python package.

**Content:**
```python
"""
Tests Package

Contains all test files for the Spinta backend.
"""
```

**Why This Exists:**
- Makes `tests/` importable as a package
- pytest can discover and run tests

**Connection to Other Files:**
- Makes importable: All test files in `tests/`

---

### 14. `tests/test_health.py` - Health Endpoint Tests

**Location:** `D:\Spinta_Backend\tests\test_health.py`

**Purpose:** Test the health check endpoint to ensure it works correctly.

**Key Components:**

#### **Imports:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
```

#### **Test Client:**
```python
client = TestClient(app)
```

**What TestClient does:**
- Simulates HTTP requests without running a real server
- Uses HTTPX under the hood
- Synchronous API (no async/await needed in tests)

#### **Test Class:**
```python
class TestHealthEndpoint:
    """
    Test Suite for Health Check Endpoint
    """

    def test_health_check_full_response(self):
        """
        Test 1: Check endpoint status, structure, and values in one call.

        This is the primary "happy path" test. It verifies:
        - The endpoint returns 200 OK.
        - The JSON keys ("status", "database") are correct.
        - The JSON values ("healthy", "connected") are correct.
        """
        response = client.get("/api/health")

        # Test 1: Endpoint exists and is OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Test 2: Response structure (contract)
        assert "status" in data, "Response missing 'status' key"
        assert "database" in data, "Response missing 'database' key"

        # Test 3 & 4: Response values (logic)
        assert data["status"] == "healthy", f"Expected 'healthy', got '{data['status']}'"
        assert data["database"] == "connected", f"Expected 'connected', got '{data['database']}'"
```

**What this test does:**

**test_health_check_full_response**:
   - **Comprehensive test**: Combines multiple assertions in one test
   - **Endpoint availability**: Verifies endpoint returns 200 OK
   - **Response structure**: Checks JSON has "status" and "database" keys
   - **Response values**: Verifies status is "healthy" and database is "connected"
   - **Efficient**: Single HTTP request tests all aspects
   - **Clear error messages**: Each assertion includes descriptive error message

**Why This Exists:**
- **Confidence**: Proves code works as expected
- **Regression**: Catches bugs when code changes
- **Documentation**: Tests show expected behavior

**What It Does:**
- Runs when you execute `pytest`
- Makes HTTP requests to the API
- Asserts that responses match expectations

**Connection to Other Files:**
- Imports app from: `main.py`
- Tests endpoints in: `health.py`
- Configured by: `pytest.ini`

---

### 15. `app/models/base.py` - Database Base & Utilities

**Location:** `D:\Spinta_Backend\app\models\base.py`

**Purpose:** Provide foundation for all SQLAlchemy models with shared utilities and base classes.

**Key Components:**

#### **Platform-Independent GUID Type:**
```python
class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    String(36) for SQLite and other databases.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(String(36))
```

**Why GUID exists:**
- **Production (PostgreSQL)**: Uses native UUID type (efficient, indexed)
- **Testing (SQLite)**: Uses String(36) (compatible, no errors)
- **Seamless**: Same code works with both databases
- **No changes needed**: Models work in production and tests

#### **Declarative Base:**
```python
Base = declarative_base()
```

**What this provides:**
- All models inherit from `Base`
- Tracks all model metadata
- Used by Alembic for migrations

#### **TimestampMixin:**
```python
class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
```

**What this provides:**
- Automatic `created_at` timestamp on insert
- Automatic `updated_at` timestamp on update
- DRY: Define once, use in all models
- Database-level defaults (server_default)

#### **UUID Generator:**
```python
def generate_uuid():
    return str(uuid.uuid4())
```

**What this does:**
- Generates globally unique identifiers
- Returns string (compatible with GUID type)
- Used as default for all primary keys

**Why This Exists:**
- **Consistency**: All models use same base
- **DRY**: Shared utilities avoid repetition
- **Flexibility**: Works with PostgreSQL and SQLite
- **Timestamps**: Automatic created_at/updated_at

**Connection to Other Files:**
- Imported by: All model files
- Used by: `user.py`, `coach.py`, `club.py`, `player.py`
- Provides: `Base`, `TimestampMixin`, `generate_uuid`, `GUID`

---

### 16. `app/models/user.py` - User Model

**Location:** `D:\Spinta_Backend\app\models\user.py`

**Purpose:** Store user accounts for both coaches and players.

**Schema (7 fields):**
```python
class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id = Column(GUID, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    user_type = Column(String(20), nullable=False, index=True)  # 'coach' or 'player'
    # created_at, updated_at from TimestampMixin
```

**Relationships:**
- One-to-one with Coach (via `coaches.user_id`)
- One-to-one with Player (via `players.user_id`, when linked)

**Helper Methods:**
```python
def is_coach(self) -> bool:
    return self.user_type == "coach"

def is_player(self) -> bool:
    return self.user_type == "player"
```

**Why This Exists:**
- **Authentication**: Single table for all users
- **Role-Based Access**: `user_type` determines permissions
- **Simplicity**: Password hashing in one place
- **Separation**: User account separate from role-specific data

**Constraints:**
- Email must be unique (UNIQUE index)
- user_type indexed for filtering
- Cascade delete to coach/player when user deleted

**Connection to Other Files:**
- Extended by: `coach.py` (one-to-one)
- Extended by: `player.py` (one-to-one)
- Tested in: `tests/test_models.py`

---

### 17. `app/models/coach.py` - Coach Model

**Location:** `D:\Spinta_Backend\app\models\coach.py`

**Purpose:** Store coach-specific information linked to user account.

**Schema (6 fields):**
```python
class Coach(Base, TimestampMixin):
    __tablename__ = "coaches"

    coach_id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(GUID, ForeignKey('users.user_id', ondelete='CASCADE'),
                     unique=True, nullable=False, index=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    # created_at, updated_at from TimestampMixin
```

**Relationships:**
- One-to-one with User (via `user_id`)
- One-to-one with Club (one coach owns one club)

**Convenience Properties:**
```python
@property
def email(self):
    return self.user.email if self.user else None

@property
def full_name(self):
    return self.user.full_name if self.user else None
```

**Why This Exists:**
- **Separation**: Coach data separate from user account
- **Flexibility**: Can add coach-specific fields without affecting users table
- **Design Pattern**: Separate PK (coach_id) from FK (user_id)

**Constraints:**
- user_id is UNIQUE (one coach per user)
- user_id is NOT NULL (coach must have user account)
- CASCADE delete from users

**Connection to Other Files:**
- Linked to: `user.py` (one-to-one)
- Extended by: `club.py` (one-to-one)
- Tested in: `tests/test_models.py`

---

### 18. `app/models/club.py` - Club Model

**Location:** `D:\Spinta_Backend\app\models\club.py`

**Purpose:** Store club/team information owned by coaches.

**Schema (10 fields):**
```python
class Club(Base, TimestampMixin):
    __tablename__ = "clubs"

    club_id = Column(GUID, primary_key=True, default=generate_uuid)
    coach_id = Column(GUID, ForeignKey('coaches.coach_id', ondelete='CASCADE'),
                      unique=True, nullable=False, index=True)
    club_name = Column(String(255), nullable=False)
    statsbomb_team_id = Column(Integer, unique=True, nullable=True)
    country = Column(String(100), nullable=True)
    age_group = Column(String(20), nullable=True)  # "U16", "U18", etc.
    stadium = Column(String(255), nullable=True)
    logo_url = Column(String, nullable=True)
    # created_at, updated_at from TimestampMixin
```

**Relationships:**
- One-to-one with Coach (via `coach_id`)
- One-to-many with Players (club has multiple players)

**Convenience Properties:**
```python
@property
def coach_name(self):
    return self.coach.full_name if self.coach else None

@property
def player_count(self):
    return len(self.players) if hasattr(self, 'players') else 0
```

**Why This Exists:**
- **Team Management**: Each coach manages one club
- **StatsBomb Integration**: `statsbomb_team_id` links to event data
- **Player Organization**: Groups players by club

**Constraints:**
- coach_id is UNIQUE (one club per coach)
- statsbomb_team_id is UNIQUE (each StatsBomb team maps to one club)
- CASCADE delete from coaches and to players

**Connection to Other Files:**
- Linked to: `coach.py` (one-to-one)
- Parent of: `player.py` (one-to-many)
- Tested in: `tests/test_models.py`

---

### 19. `app/models/player.py` - Player Model

**Location:** `D:\Spinta_Backend\app\models\player.py`

**Purpose:** Handle both incomplete players (before signup) and complete players (after signup).

**Schema (15 fields):**
```python
class Player(Base, TimestampMixin):
    __tablename__ = "players"

    player_id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(GUID, ForeignKey('users.user_id', ondelete='CASCADE'),
                     unique=True, nullable=True, index=True)  # NULL before signup
    club_id = Column(GUID, ForeignKey('clubs.club_id', ondelete='CASCADE'),
                     nullable=False, index=True)
    player_name = Column(String(255), nullable=False)
    statsbomb_player_id = Column(Integer, nullable=True, index=True)
    jersey_number = Column(Integer, nullable=False)
    position = Column(String(50), nullable=False)
    invite_code = Column(String(10), unique=True, nullable=False, index=True)
    is_linked = Column(Boolean, nullable=False, default=False, index=True)
    linked_at = Column(DateTime(timezone=True), nullable=True)
    birth_date = Column(Date, nullable=True)  # Filled on signup
    height = Column(Integer, nullable=True)  # Filled on signup
    profile_image_url = Column(String, nullable=True)  # Filled on signup
    # created_at, updated_at from TimestampMixin
```

**Two States:**

1. **Incomplete Player (before signup):**
   - Created by admin during match processing
   - `user_id = NULL`
   - `is_linked = FALSE`
   - Only basic fields filled

2. **Complete Player (after signup):**
   - Player completes signup using invite code
   - `user_id` set (links to users table)
   - `is_linked = TRUE`
   - `linked_at = NOW()`
   - All profile fields filled

**Relationships:**
- One-to-one with User (via `user_id`, NULL before signup)
- Many-to-one with Club (via `club_id`)

**Helper Methods:**
```python
@property
def email(self):
    return self.user.email if self.user else None

@property
def is_incomplete(self):
    return not self.is_linked

def complete_signup(self, user_id: str):
    self.user_id = user_id
    self.is_linked = True
    self.linked_at = datetime.utcnow()
```

**Why This Exists:**
- **Two-Phase Creation**: Admin creates players before they have accounts
- **Invite System**: Players sign up using unique invite codes
- **Flexible**: Handles incomplete state gracefully
- **StatsBomb Integration**: Links players to event data

**Constraints:**
- user_id is UNIQUE when set (one player per user)
- user_id is NULLABLE (incomplete players)
- invite_code is UNIQUE (each code is one-time use)
- CASCADE delete from both users and clubs

**Connection to Other Files:**
- Linked to: `user.py` (one-to-one, optional)
- Linked to: `club.py` (many-to-one)
- Tested in: `tests/test_models.py`

---

### 20. `app/models/__init__.py` - Models Package

**Location:** `D:\Spinta_Backend\app\models\__init__.py`

**Purpose:** Export all models for easy importing.

**Content:**
```python
from app.models.base import Base
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player

__all__ = [
    "Base",
    "User",
    "Coach",
    "Club",
    "Player",
]
```

**Why This Exists:**
- **Convenience**: Import all models from one place
- **Clean Imports**: `from app.models import User, Coach`
- **Alembic**: Ensures all models are imported for autogenerate

**Connection to Other Files:**
- Imports from: All model files
- Imported by: `alembic/env.py`, route handlers, tests

---

### 21. `alembic/env.py` - Alembic Configuration

**Location:** `D:\Spinta_Backend\alembic\env.py`

**Purpose:** Configure Alembic to detect models and run migrations.

**Key Configuration:**
```python
from app.config import get_database_url
from app.models.base import Base
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player

config = context.config
config.set_main_option('sqlalchemy.url', get_database_url())
target_metadata = Base.metadata
```

**Why This Exists:**
- **Database URL**: Loads from `.env` (no hardcoded credentials)
- **Model Discovery**: Imports all models so Alembic can detect them
- **Autogenerate**: Compares models with database to create migrations

**What It Does:**
1. Imports all models (registers them with Base.metadata)
2. Overrides sqlalchemy.url from .env
3. Provides metadata to Alembic
4. Enables autogenerate feature

**Connection to Other Files:**
- Reads config from: `app.config`
- Imports models from: `app.models`
- Used by: `alembic revision --autogenerate`

---

### 22. `alembic/versions/` - Migration Files

**Location:** `D:\Spinta_Backend\alembic\versions\cec718a67a72_initial_schema_with_users_coaches_clubs_.py`

**Purpose:** Version-controlled database schema changes.

**What Migration Files Contain:**
```python
def upgrade() -> None:
    # Create tables
    op.create_table('users', ...)
    op.create_table('coaches', ...)
    op.create_table('clubs', ...)
    op.create_table('players', ...)

    # Create indexes
    op.create_index(...)

def downgrade() -> None:
    # Reverse all changes
    op.drop_table('players')
    op.drop_table('clubs')
    op.drop_table('coaches')
    op.drop_table('users')
```

**Why This Exists:**
- **Version Control**: Track database schema changes over time
- **Reproducibility**: Apply same schema to all environments
- **Rollback**: Can undo changes with `alembic downgrade`
- **Team Collaboration**: Everyone gets same database structure

**Commands:**
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current
```

**Connection to Other Files:**
- Generated from: Model changes
- Applied to: Neon PostgreSQL database
- Configured by: `alembic.ini`, `alembic/env.py`

---

### 23. `tests/conftest.py` - Test Fixtures

**Location:** `D:\Spinta_Backend\tests\conftest.py`

**Purpose:** Provide reusable test fixtures for database testing.

**Key Fixtures:**

#### **Engine Fixture:**
```python
@pytest.fixture(scope="function")
def engine():
    """Create in-memory SQLite database for each test"""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
```

#### **Session Fixture:**
```python
@pytest.fixture(scope="function")
def session(engine):
    """Create database session that rolls back after test"""
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
```

#### **Data Fixtures:**
```python
@pytest.fixture
def sample_user(session):
    """Pre-created user for testing"""
    user = User(email="test@example.com", ...)
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def sample_coach(session, sample_user):
    """Pre-created coach linked to sample_user"""
    coach = Coach(user_id=sample_user.user_id, ...)
    session.add(coach)
    session.commit()
    return coach

# Similar fixtures for club, incomplete_player, complete_player
```

**Why This Exists:**
- **Test Isolation**: Each test gets clean database
- **Speed**: SQLite in-memory is fast
- **Reusability**: Fixtures avoid duplicate code
- **Dependencies**: Fixtures can depend on other fixtures

**Connection to Other Files:**
- Used by: `tests/test_models.py`
- Imports from: `app.models`

---

### 24. `tests/test_models.py` - Model Tests

**Location:** `D:\Spinta_Backend\tests\test_models.py`

**Purpose:** Comprehensively test all database models.

**Test Coverage:**

#### **User Model Tests (5 tests):**
- Create user with all fields
- Email uniqueness constraint
- `is_coach()` and `is_player()` methods
- String representation

#### **Coach Model Tests (7 tests):**
- Create coach with user_id
- user_id uniqueness constraint
- One-to-one relationship with user
- Convenience properties (email, full_name)
- Optional fields can be NULL
- CASCADE delete from user

#### **Club Model Tests (7 tests):**
- Create club with all fields
- coach_id uniqueness constraint
- statsbomb_team_id uniqueness constraint
- One-to-one relationship with coach
- Convenience properties
- Optional fields can be NULL
- CASCADE delete from coach

#### **Player Model Tests (12 tests):**
- Create incomplete player (user_id = NULL)
- Create complete player (user_id set)
- `complete_signup()` method
- invite_code uniqueness constraint
- user_id uniqueness when set
- Relationships with club and user
- Convenience properties
- CASCADE deletes

#### **Integration Tests (3 tests):**
- Coach registration flow (user → coach → club)
- Player signup flow (incomplete → signup → complete)
- Cascade delete through entire chain

**Total: 34 tests, all passing ✅**

**Why This Exists:**
- **Confidence**: Proves models work correctly
- **Regression Prevention**: Catches bugs when code changes
- **Documentation**: Tests show how models should be used
- **Coverage**: Tests all relationships, constraints, and methods

**Connection to Other Files:**
- Tests: All model files
- Uses fixtures from: `conftest.py`
- Configured by: `pytest.ini`

---

## How Files Connect

### Import Dependency Graph

```
.env
  ↓
config.py (reads .env, creates settings)
  ↓
database.py (uses settings, creates engine & get_db)
  ↓
main.py (uses settings & engine, creates app)
  ↓
health.py (uses get_db, defines routes)
  ↑
test_health.py (imports app, tests routes)
```

### Detailed Connection Flow

#### 1. **Configuration Flow**
```
.env file
  → python-dotenv loads variables
  → Pydantic Settings reads variables
  → settings object created
  → Available throughout application
```

#### 2. **Database Flow**
```
settings.database_url
  → create_engine() creates engine
  → SessionLocal factory created
  → get_db() function defined
  → FastAPI injects sessions into endpoints
```

#### 3. **Application Flow**
```
main.py imports
  → Creates FastAPI app
  → Adds CORS middleware
  → Registers lifespan handler
  → Imports and registers routes
  → uvicorn runs the app
```

#### 4. **Request Flow**
```
HTTP Request
  → CORS middleware (adds headers)
  → FastAPI routing (matches endpoint)
  → Dependency injection (calls get_db())
  → Endpoint function (uses db session)
  → Returns response
  → get_db() closes session (finally block)
  → Response sent to client
```

#### 5. **Test Flow**
```
pytest command
  → Reads pytest.ini
  → Discovers test_*.py files
  → Imports test_health.py
  → Creates TestClient(app)
  → Runs each test_* function
  → Makes HTTP requests via TestClient
  → Asserts response matches expectations
```

---

## Request Flow

### Detailed Request Flow for GET /api/health

Let's trace what happens when a client calls `GET http://localhost:8000/api/health`:

#### **Step 1: HTTP Request Arrives**
```
Client → HTTP Request → uvicorn (ASGI server) → FastAPI app
```

#### **Step 2: CORS Middleware**
```python
# In main.py
app.add_middleware(CORSMiddleware, ...)
```
- Middleware checks request origin
- Adds CORS headers to response
- Allows/blocks based on `settings.cors_origins`

#### **Step 3: Route Matching**
```python
# FastAPI router looks for matching route
"/api/health" → Found in health.router (registered with "/api" prefix)
```

#### **Step 4: Dependency Resolution**
```python
# In health.py
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
```

FastAPI sees `Depends(get_db)` and:
1. Calls `get_db()` from `database.py`
2. `get_db()` creates a session: `db = SessionLocal()`
3. Yields the session
4. FastAPI injects it as the `db` parameter

#### **Step 5: Endpoint Execution**
```python
# In health.py
database_status = "disconnected"

try:
    result = db.execute(text("SELECT 1"))
    database_status = "connected"
except Exception as e:
    database_status = "disconnected"

return {
    "status": "healthy",
    "database": database_status
}
```

- Executes `SELECT 1` query via the database session
- If successful: database = "connected"
- If fails: database = "disconnected"
- Returns Python dict

#### **Step 6: Response Serialization**
```
Python dict → FastAPI converts to JSON → HTTP Response
```

#### **Step 7: Cleanup (Finally Block)**
```python
# In database.py get_db()
try:
    yield db
finally:
    db.close()  # ← Always runs, even if endpoint crashed
```

- FastAPI returns to `get_db()` generator
- `finally` block executes
- Session closed
- Database connection returned to pool

#### **Step 8: Response Sent**
```
FastAPI → uvicorn → HTTP Response → Client
```

Client receives:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTTP Request                             │
│                  GET /api/health                                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         uvicorn                                  │
│                      (ASGI Server)                               │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI App                                 │
│                       (main.py)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CORS Middleware                               │
│          (adds headers, checks origin)                           │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Route Matching                                │
│     "/api/health" → health.router.get("/health")                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Dependency Injection                             │
│        Depends(get_db) → get_db() called                        │
│              SessionLocal() creates session                      │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Endpoint Function                              │
│         health_check(db) executes                                │
│         db.execute(text("SELECT 1"))                             │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Database Query                                 │
│        Connection from pool → Neon PostgreSQL                    │
│        Execute "SELECT 1" → Return result                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Build Response                                 │
│   {"status": "healthy", "database": "connected"}                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Cleanup (finally)                              │
│         db.close() → Return connection to pool                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   JSON Serialization                             │
│         Python dict → JSON string                                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      HTTP Response                               │
│    Status: 200 OK                                                │
│    Content-Type: application/json                                │
│    Body: {"status": "healthy", "database": "connected"}         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Configuration Loading (Startup)

```
Application Startup
       ↓
┌──────────────┐
│  import      │
│  main.py     │
└──────┬───────┘
       ↓
┌──────────────┐
│  import      │
│  config.py   │
└──────┬───────┘
       ↓
┌──────────────┐
│ Settings()   │  ← Pydantic Settings reads .env
└──────┬───────┘
       ↓
┌──────────────┐
│ .env file    │
│ DATABASE_URL │
│ SECRET_KEY   │
│ CORS_ORIGINS │
└──────┬───────┘
       ↓
┌──────────────┐
│ settings     │  ← Global object
│ object       │
└──────┬───────┘
       ↓
Used by database.py, main.py, etc.
```

### Database Connection Pool

```
Application Startup
       ↓
┌──────────────────┐
│ import           │
│ database.py      │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ create_engine()  │
│ - pool_size=5    │  ← Creates 5 connections
│ - max_overflow=10│  ← Can add 10 more if needed
└────────┬─────────┘
         ↓
┌──────────────────────────────────┐
│     Connection Pool              │
│  [Conn1] [Conn2] [Conn3]         │
│  [Conn4] [Conn5]                 │
└────────┬─────────────────────────┘
         ↓
    Neon PostgreSQL
         ↑
         │
    ┌────┴─────┐
    │  Reused  │
    │  by      │
    │  requests│
    └──────────┘
```

### Session Lifecycle

```
HTTP Request arrives
       ↓
┌──────────────────┐
│ FastAPI sees     │
│ Depends(get_db)  │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ get_db() called  │
│ db = SessionLocal()  ← Creates session
└────────┬─────────┘
         ↓
┌──────────────────┐
│ yield db         │  ← Session passed to endpoint
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Endpoint uses db │
│ db.execute(...)  │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Endpoint returns │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ finally:         │
│   db.close()     │  ← Always runs
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Connection       │
│ returned to pool │
└──────────────────┘
```

---

## Summary

### Key Takeaways

1. **Modular Architecture**: Each file has a single, clear responsibility
   - `config.py` → Configuration
   - `database.py` → Database
   - `main.py` → Application
   - `health.py` → Routes

2. **Dependency Injection**: FastAPI automatically manages dependencies
   - `Depends(get_db)` → Automatic session creation and cleanup
   - Clean, readable code
   - Easy to test (can mock dependencies)

3. **Connection Pooling**: Efficient database connection management
   - Reuse connections instead of creating new ones
   - Faster requests
   - Lower database load

4. **Environment-Based Config**: Secrets never in code
   - `.env` file for local development
   - Environment variables for production
   - Type-safe with Pydantic

5. **Test-Driven Development**: Tests prove code works
   - TestClient simulates requests
   - Multiple test cases cover different scenarios
   - CI/CD can run tests automatically

### File Responsibilities Summary

| File | Responsibility | Used By |
|------|---------------|---------|
| `.env` | Store secrets | `config.py` |
| `.env.example` | Document required config | Developers |
| `.gitignore` | Exclude files from git | Git |
| `requirements.txt` | List dependencies | pip |
| `pytest.ini` | Configure pytest | pytest |
| `config.py` | Load configuration | All files |
| `database.py` | Manage database | `main.py`, routes |
| `main.py` | Create FastAPI app | uvicorn |
| `health.py` | Health check routes | `main.py` |
| `test_health.py` | Test health routes | pytest |

### Communication Flow Summary

```
Environment (.env)
    ↓
Configuration (config.py)
    ↓
Database (database.py)
    ↓
Application (main.py)
    ↓
Routes (health.py)
    ↑
Tests (test_health.py)
```

All files work together to create a **scalable, maintainable, testable** FastAPI backend! 🚀
