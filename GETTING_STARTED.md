# Getting Started with Spinta Backend

## 📁 Project Structure Created

```
Spinta_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              ✅ FastAPI application entry point
│   ├── config.py            ✅ Configuration management
│   ├── database.py          ✅ Database connection and dependencies
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           └── health.py    ✅ Health check endpoint
├── tests/
│   ├── __init__.py
│   └── test_health.py       ✅ Health endpoint tests (TDD)
├── docs/                     (Your existing documentation)
├── .env.example             ✅ Configuration template
├── .env                     ✅ Your local configuration (not in git)
├── .gitignore               ✅ Git ignore file
├── requirements.txt         ✅ Python dependencies
├── pytest.ini               ✅ Test configuration
└── GETTING_STARTED.md       ✅ This file!
```

## 🔧 Important Changes & Fixes

During the initial setup, we encountered and resolved several issues. Here's what was fixed:

### 1. **pytest.ini Configuration Issue**
**Problem:** Inline comments in the `addopts` section caused pytest to fail with "ERROR: file or directory not found: #"

**Solution:** Moved all comments to separate lines above the options. Pytest configuration files don't support inline comments in multi-line option values.

```ini
# Before (broken):
addopts =
    -v  # Verbose output

# After (fixed):
# -v: Verbose output
addopts =
    -v
```

### 2. **CORS Origins Parsing Error**
**Problem:** Pydantic Settings tried to parse `cors_origins: List[str]` as JSON from the `.env` file, causing a JSON parsing error.

**Solution:** Changed the approach:
- Store as a string field: `cors_origins_str: str`
- Use `Field(validation_alias="CORS_ORIGINS")` to map the env var name
- Created a `@property` method that converts the comma-separated string to a list on-the-fly

**Why this works:**
- Pydantic doesn't try to parse strings as JSON
- The `.env` file can use simple comma-separated format: `CORS_ORIGINS=http://localhost:3000,http://localhost:8080`
- FastAPI gets a list when accessing `settings.cors_origins`

### 3. **Circular Import Issue**
**Problem:** `main.py` imported `health.py`, but `health.py` tried to import `get_db` from `main.py`, creating a circular dependency.

**Solution:** Created a new `database.py` module to centralize database-related code:
- Moved database engine setup to `database.py`
- Moved session factory to `database.py`
- Moved `get_db` dependency to `database.py`

**Import flow (now working):**
```
config.py → database.py → main.py → health.py
                ↑                      ↓
                └──────────────────────┘
```

**Key Learning:**
- Circular imports are a common issue in Python applications
- Solution: Extract shared code into a separate module
- This pattern (separate `database.py`) is standard in FastAPI projects

### 4. **New Files Created**
- **`database.py`**: Centralizes all database configuration, connection pooling, and the `get_db` dependency
- **`.gitignore`**: Prevents sensitive files (`.env`, `__pycache__`, etc.) from being committed to git

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies

Open your terminal in the `Spinta_Backend` directory and run:

```bash
pip install -r requirements.txt
```

**What this does:**
- Installs FastAPI, SQLAlchemy, pytest, and all other dependencies
- Takes about 1-2 minutes

### Step 2: Set Up Neon Database

1. **Get your Neon connection string:**
   - Go to your Neon dashboard
   - Copy the connection string (looks like: `postgresql://user:password@ep-xxxx.neon.tech/dbname`)

2. **Create `.env` file:**
   - Copy `.env.example` to `.env`
   - Replace the DATABASE_URL with your actual Neon connection string

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your actual Neon database URL
```

Your `.env` should look like:
```env
DATABASE_URL=postgresql://your-user:your-password@ep-xxxx.us-east-2.aws.neon.tech/spinta_db?sslmode=require
APP_NAME=Spinta Backend
DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Step 3: Run Tests (TDD Approach!)

**This is the TDD moment!** Let's see if our tests pass:

```bash
pytest tests/test_health.py -v
```

**Expected output:**
```
tests/test_health.py::TestHealthEndpoint::test_health_endpoint_exists PASSED
tests/test_health.py::TestHealthEndpoint::test_health_response_structure PASSED
tests/test_health.py::TestHealthEndpoint::test_health_status_value PASSED
tests/test_health.py::TestHealthEndpoint::test_health_database_connected PASSED
tests/test_health.py::TestHealthEndpoint::test_health_response_time PASSED

======================== 5 passed in 0.50s ========================
```

**If tests fail:**
- Check your DATABASE_URL in .env
- Make sure Neon database is accessible
- Read the error messages - they tell you what's wrong!

### Step 4: Run the Server

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

**What this does:**
- Starts the server on http://localhost:8000
- `--reload` automatically restarts when you change code
- You should see: "✅ Database connection successful!"

### Step 5: Test the API

#### Option 1: Browser
Open your browser and visit:
- http://localhost:8000/ (Root endpoint)
- http://localhost:8000/api/health (Health check)
- http://localhost:8000/docs (Interactive API documentation - Swagger UI)

#### Option 2: Command Line (curl)
```bash
curl http://localhost:8000/api/health
```

#### Option 3: Python
```python
import requests
response = requests.get("http://localhost:8000/api/health")
print(response.json())
```

**Expected response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## 📚 What You Built (Learning Summary)

### 1. **Project Structure**
- Organized code into packages (`app/`, `tests/`)
- Separation of concerns (config, database, routes, tests separate)
- Proper module organization to avoid circular imports

### 2. **Configuration Management** (`config.py`)
- Environment variables for secrets
- Type-safe configuration with Pydantic
- Database connection string handling
- Custom CORS origins parsing with `@property`
- Field aliases for flexible env var naming

### 3. **Database Layer** (`database.py`)
- SQLAlchemy engine with connection pooling
- Session factory for database operations
- `get_db` dependency for FastAPI endpoints
- Configured for Neon serverless PostgreSQL

### 4. **FastAPI Application** (`main.py`)
- App initialization with metadata
- Lifespan events (startup/shutdown)
- CORS middleware configuration
- Route registration
- Database connection testing on startup

### 5. **Health Check Endpoint** (`health.py`)
- API Router for organizing routes
- Database dependency injection
- Error handling with try/except
- Simple SQL query to test connection
- Detailed health check endpoint (bonus)

### 6. **Test-Driven Development** (`test_health.py`)
- Write tests FIRST
- Test client for FastAPI
- Multiple test cases for one endpoint
- Assertions to verify behavior

## 🎯 Key Concepts Learned

### FastAPI Concepts:
- **APIRouter**: Group related endpoints
- **Depends()**: Dependency injection system
- **Lifespan**: Startup/shutdown events
- **TestClient**: Test endpoints without running server
- **CORS Middleware**: Allow cross-origin requests from frontends

### Database Concepts:
- **Connection String**: URL to connect to database
- **Connection Pooling**: Reuse database connections efficiently
- **Session**: A conversation with the database
- **SQL Query**: `SELECT 1` tests if database is alive
- **pool_pre_ping**: Essential for serverless databases like Neon

### Pydantic Concepts:
- **Settings Management**: Type-safe configuration from env vars
- **Field Aliases**: Map different names between code and env vars
- **@property**: Computed values that look like regular attributes
- **Custom Validators**: Transform data before validation

### Python/Architecture Concepts:
- **Circular Imports**: When Module A imports B and B imports A
- **Module Separation**: Breaking code into focused modules
- **Dependency Management**: `requirements.txt` for reproducibility

### Testing Concepts:
- **TDD**: Write tests before code
- **Assertions**: Verify expected behavior
- **Test Organization**: Group tests in classes
- **Test Coverage**: Multiple tests for different aspects

## 🔍 Common Issues & Solutions

### Issue 1: pytest ERROR: file or directory not found: #
**Problem:** pytest fails to collect tests with "ERROR: file or directory not found: #"
**Cause:** Inline comments in `pytest.ini` `addopts` section
**Solution:** Already fixed! We moved comments to separate lines above the options.

### Issue 2: CORS Origins JSON Parsing Error
**Problem:** `pydantic_settings.sources.SettingsError: error parsing value for field "cors_origins"`
**Cause:** Pydantic tries to parse `List[str]` as JSON from `.env` file
**Solution:** Already fixed! We use a string field with `@property` to convert comma-separated values.

### Issue 3: Circular Import Error
**Problem:** `ImportError: cannot import name 'get_db' from partially initialized module 'app.main'`
**Cause:** `main.py` imports `health.py`, but `health.py` imports from `main.py`
**Solution:** Already fixed! We created `database.py` to centralize database code.

### Issue 4: ModuleNotFoundError
**Problem:** Python can't find `app` module
**Solution:** Make sure you're in `Spinta_Backend` directory when running commands

### Issue 5: Database Connection Failed
**Problem:** Can't connect to Neon
**Solutions:**
- Check DATABASE_URL in `.env` is correct
- Verify Neon database is running
- Check your internet connection
- Ensure `?sslmode=require` is at the end of URL

### Issue 6: Tests Failing
**Problem:** pytest shows errors
**Solutions:**
- Read the error message carefully
- Check if server dependencies are installed
- Verify DATABASE_URL is set
- Try running one test at a time: `pytest tests/test_health.py::TestHealthEndpoint::test_health_endpoint_exists -v`

### Issue 7: Port Already in Use
**Problem:** `uvicorn` says port 8000 is busy
**Solution:** Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## 🎓 Next Steps

Now that you have a working foundation, here are the next learning steps:

### Phase 2: Database Models (Next Session)
- Create SQLAlchemy models for `users`, `coaches`, `clubs` tables
- Learn about ORM (Object-Relational Mapping)
- Set up Alembic for database migrations
- Create tables in Neon database

### Phase 3: Authentication (After Database)
- Implement user registration endpoint
- Password hashing with bcrypt
- JWT token generation
- Login endpoint with token

### Phase 4: First Real Endpoint
- Create coach registration endpoint
- Link to database models
- Write tests for registration
- Validate input data with Pydantic

## 📖 Helpful Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_health.py -v

# Run server
uvicorn app.main:app --reload

# Run server on different port
uvicorn app.main:app --reload --port 8001

# Check code formatting
black app/ tests/

# Check code style
flake8 app/ tests/
```

## 🤔 Questions to Explore

1. **What happens if Neon database goes down?**
   - Try stopping your database and call /api/health
   - Notice how the endpoint handles errors gracefully

2. **How does Depends() work?**
   - Read the `get_db()` function in `database.py`
   - Notice how FastAPI automatically calls it and provides a session

3. **Why separate database code into database.py?**
   - Prevents circular imports
   - Makes testing easier (can mock database separately)
   - Standard pattern in FastAPI projects

4. **Why separate routes into files?**
   - Imagine 50 endpoints in one file vs organized folders
   - Better organization = easier maintenance

5. **Why write tests before code?**
   - Tests define expected behavior
   - Code implements to meet those expectations
   - Confidence that code works as intended

6. **How does the @property decorator work?**
   - Look at `cors_origins` in `config.py`
   - It converts a string to a list automatically when accessed
   - No duplicate data stored!

## 🎉 Congratulations!

You've built:
✅ A structured FastAPI project with proper module separation
✅ Database connection with connection pooling (Neon-ready!)
✅ A tested health check endpoint (TDD approach)
✅ Configuration management with Pydantic
✅ Resolved real-world issues (circular imports, CORS parsing)

**You now understand:**
- FastAPI basics (routing, middleware, dependencies)
- Database connections and SQLAlchemy
- Dependency injection with `Depends()`
- Testing with pytest (TDD workflow)
- Project organization and avoiding circular imports
- Pydantic Settings with custom validators
- Environment variable management

**Real-World Skills Gained:**
- Debugging configuration issues
- Understanding and fixing circular imports
- Working with serverless databases (Neon)
- Test-driven development approach
- Reading and understanding error messages

Ready for Phase 2 (Database Models & Migrations)? Let me know!
