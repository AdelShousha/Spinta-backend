# Getting Started with Spinta Backend

## 📁 Project Structure Created

```
Spinta_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              ✅ FastAPI application entry point
│   ├── config.py            ✅ Configuration management
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
├── requirements.txt         ✅ Python dependencies
└── pytest.ini               ✅ Test configuration
```

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
- Separation of concerns (config, routes, tests separate)

### 2. **Configuration Management** (`config.py`)
- Environment variables for secrets
- Type-safe configuration with Pydantic
- Database connection string handling

### 3. **FastAPI Application** (`main.py`)
- App initialization with metadata
- Database connection pooling
- Lifespan events (startup/shutdown)
- CORS middleware
- Dependency injection (`get_db`)

### 4. **Health Check Endpoint** (`health.py`)
- API Router for organizing routes
- Database dependency injection
- Error handling with try/except
- Simple SQL query to test connection

### 5. **Test-Driven Development** (`test_health.py`)
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

### Database Concepts:
- **Connection String**: URL to connect to database
- **Connection Pooling**: Reuse database connections
- **Session**: A conversation with the database
- **SQL Query**: `SELECT 1` tests if database is alive

### Testing Concepts:
- **TDD**: Write tests before code
- **Assertions**: Verify expected behavior
- **Test Organization**: Group tests in classes
- **Test Coverage**: Multiple tests for different aspects

## 🔍 Common Issues & Solutions

### Issue 1: ModuleNotFoundError
**Problem:** Python can't find `app` module
**Solution:** Make sure you're in `Spinta_Backend` directory when running commands

### Issue 2: Database Connection Failed
**Problem:** Can't connect to Neon
**Solutions:**
- Check DATABASE_URL in `.env` is correct
- Verify Neon database is running
- Check your internet connection
- Ensure `?sslmode=require` is at the end of URL

### Issue 3: Tests Failing
**Problem:** pytest shows errors
**Solutions:**
- Read the error message carefully
- Check if server dependencies are installed
- Verify DATABASE_URL is set
- Try running one test at a time: `pytest tests/test_health.py::TestHealthEndpoint::test_health_endpoint_exists -v`

### Issue 4: Port Already in Use
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
   - Read the `get_db()` function in `main.py`
   - Notice how FastAPI automatically calls it

3. **Why separate routes into files?**
   - Imagine 50 endpoints in one file vs organized folders
   - Better organization = easier maintenance

4. **Why write tests before code?**
   - Tests define expected behavior
   - Code implements to meet those expectations
   - Confidence that code works as intended

## 🎉 Congratulations!

You've built:
✅ A structured FastAPI project
✅ Database connection with connection pooling
✅ A tested health check endpoint
✅ Test-driven development workflow

**You now understand:**
- FastAPI basics
- Database connections
- Dependency injection
- Testing with pytest
- Project organization

Ready for Phase 2 (Database Models)? Let me know!
