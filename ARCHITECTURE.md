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
