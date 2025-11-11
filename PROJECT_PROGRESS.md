# Spinta Backend - Project Progress Tracker

**Last Updated:** 2025-11-11
**Approach:** Test-Driven Development (TDD)
**Database:** PostgreSQL (Neon) for production, SQLite for testing

---

## Project Overview

**Spinta** is a youth soccer analytics platform backend API that serves both coaches and players through a mobile application. The system processes StatsBomb match data, manages teams and players, calculates performance statistics, and provides training plan management.

### Key Technologies
- **Framework:** FastAPI
- **Database:** SQLAlchemy ORM with Alembic migrations
- **Authentication:** JWT tokens (no expiration)
- **Testing:** pytest with TDD approach
- **Production DB:** Neon PostgreSQL (serverless)
- **Test DB:** SQLite (in-memory)

### Architecture Patterns
- Screen-based API design (one endpoint per UI screen)
- Invite code-based player signup flow
- Automatic statistics calculation from StatsBomb events
- Pre-created player records (incomplete until signup)

---

## Documentation Structure

All specifications are in the `docs/` folder:

1. **01_OVERVIEW.md** - Project overview, workflows, and design decisions
2. **02_DATABASE_SCHEMA.md** - Complete 15-table database schema
3. **03_PLAYER_SIGNUP_FLOW.md** - Detailed 2-step player registration flow
4. **04_AUTHENTICATION.md** - JWT auth specification (4 endpoints)
5. **05_COACH_ENDPOINTS.md** - Coach API endpoints (11 endpoints)
6. **06_PLAYER_ENDPOINTS.md** - Player API endpoints (7 endpoints)
7. **07_ADMIN_ENDPOINTS.md** - Match upload endpoint (1 endpoint)

**Total API Endpoints:** 23 endpoints

---

## Database Schema (15 Tables)

### Core Tables (6 tables)
1. ✅ **users** - User accounts (coaches and players)
2. ✅ **coaches** - Coach-specific data
3. ✅ **clubs** - Club/team information
4. ✅ **players** - Player profiles with invite codes
5. ✅ **opponent_clubs** - Opponent team information
6. ✅ **opponent_players** - Opponent players (for lineups)

### Match Data Tables (3 tables)
7. ✅ **matches** - Match records
8. ✅ **goals** - Goal events
9. ✅ **events** - StatsBomb event data (~3000 per match)

### Statistics Tables (4 tables)
10. ✅ **match_statistics** - Team stats per match
11. ✅ **player_match_statistics** - Player stats per match
12. ✅ **club_season_statistics** - Aggregated club season stats
13. ✅ **player_season_statistics** - Aggregated player season stats + attributes

### Training Tables (2 tables)
14. ✅ **training_plans** - Training plans assigned to players
15. ✅ **training_exercises** - Individual exercises within plans

---

## Progress Summary

### ✅ Phase 1: Foundation (COMPLETED)

**Status:** All basic infrastructure completed successfully

#### 1.1 Project Setup ✅
- [x] FastAPI application structure
- [x] Configuration management (Pydantic Settings)
- [x] Database connection (SQLAlchemy + Neon)
- [x] CORS middleware
- [x] Health check endpoint with DB validation
- [x] pytest configuration
- [x] .gitignore setup

**Files Created:**
- `app/main.py` - FastAPI app entry point
- `app/config.py` - Environment configuration
- `app/database.py` - Database connection and session management
- `app/api/routes/health.py` - Health endpoint
- `tests/test_health.py` - Health endpoint tests
- `pytest.ini` - Test configuration
- `.env` - Local environment variables
- `GETTING_STARTED.md` - Setup documentation

**Key Solutions Implemented:**
- Fixed circular imports by separating `database.py`
- Resolved CORS origins parsing with `@property` decorator
- Fixed pytest.ini comment parsing issues

---

#### 1.2 Database Models (Core Tables) ✅
- [x] Base model with GUID type (PostgreSQL UUID / SQLite String compatibility)
- [x] TimestampMixin for created_at/updated_at
- [x] User model (polymorphic: coach/player)
- [x] Coach model (1:1 with users)
- [x] Club model (1:1 with coaches, includes AgeGroup enum)
- [x] Player model (includes invite code, incomplete/complete states)
- [x] Alembic migrations for all models
- [x] Model tests (test_models.py)

**Files Created:**
- `app/models/base.py` - Base class with GUID and TimestampMixin
- `app/models/user.py` - User model
- `app/models/coach.py` - Coach model
- `app/models/club.py` - Club model with AgeGroup enum
- `app/models/player.py` - Player model
- `app/models/__init__.py` - Model exports
- `alembic/` - Migration infrastructure
- `tests/test_models.py` - Model tests

**Key Features:**
- GUID type adapter for PostgreSQL/SQLite compatibility using `load_dialect_impl`
- Proper foreign key relationships with CASCADE rules
- Player model supports both incomplete (pre-signup) and complete (linked) states
- AgeGroup enum: U6, U8, U10, U12, U14, U16, U18, U21, Senior

---

#### 1.3 Authentication System ✅
- [x] Password hashing (bcrypt)
- [x] JWT token generation and validation
- [x] Auth dependency (`get_current_user`)
- [x] Role-based access control (coach/player)
- [x] Coach registration endpoint (creates user + coach + club)
- [x] Player invite verification endpoint
- [x] Player registration endpoint (links player to user)
- [x] Login endpoint
- [x] Pydantic schemas for all auth endpoints
- [x] CRUD operations for users, coaches, clubs, players
- [x] Complete test suite for all auth endpoints

**Files Created:**
- `app/core/security.py` - Password hashing, JWT generation/validation
- `app/core/deps.py` - Authentication dependencies
- `app/api/routes/auth.py` - All 4 auth endpoints
- `app/schemas/auth.py` - Request/response schemas
- `app/schemas/user.py` - User schemas
- `app/schemas/coach.py` - Coach schemas
- `app/schemas/club.py` - Club schemas
- `app/schemas/player.py` - Player schemas
- `app/crud/user.py` - User CRUD operations
- `app/crud/coach.py` - Coach CRUD operations
- `app/crud/club.py` - Club CRUD operations
- `app/crud/player.py` - Player CRUD operations
- `tests/test_auth.py` - Complete auth test suite

**Endpoints Implemented:**
1. `POST /api/auth/register/coach` - Coach registration with club creation
2. `POST /api/auth/verify-invite` - Validate player invite code
3. `POST /api/auth/register/player` - Complete player signup
4. `POST /api/auth/login` - User login (coach or player)

**Key Features:**
- JWT tokens without expiration (as per spec)
- Invite code generation with cryptographic randomness
- Transaction-safe registration (rollback on failure)
- Player pre-creation during match upload (incomplete players)
- Player linking during signup (user_id = player_id)

---

### ✅ Phase 2: Remaining Database Models (COMPLETED)

**Status:** All 11 remaining database models created with TDD approach

**Why Phase 2:** Must create all database models before we can populate or query the database.

#### 2.1 Match-Related Models ✅
- [x] Opponent clubs model
- [x] Opponent players model
- [x] Matches model
- [x] Goals model
- [x] Events model (with JSONB for event_data)
- [x] Alembic migration (grouped)
- [x] Model tests (compact grouped tests)

**Files Created:**
- `app/models/opponent_club.py` - Opponent team information
- `app/models/opponent_player.py` - Opponent player details
- `app/models/match.py` - Match records with FK relationships
- `app/models/goal.py` - Goal events from matches
- `app/models/event.py` - StatsBomb event data with JSONB storage
- `alembic/versions/59ce4e824ea4_add_match_related_models.py` - Migration
- `alembic/versions/fa912f5abb62_make_opponent_club_id_nullable.py` - Nullable fix
- `alembic/versions/aac509491515_change_club_id_to_cascade.py` - CASCADE fix
- Updated `tests/test_models.py` with `TestMatchRelatedModels` class

**Key Features Implemented:**
- JSONB storage with SQLite fallback (JSONBType adapter)
- CASCADE delete relationships (Club→Match→Goals/Events)
- GIN index on event_data for efficient JSONB queries
- Proper relationship back_populates for ORM cascade

---

#### 2.2 Statistics Models ✅
- [x] Match statistics model (2 records per match: our_team + opponent_team)
- [x] Player match statistics model (N records per match, one per player)
- [x] Club season statistics model (aggregated from match_statistics)
- [x] Player season statistics model (includes attribute ratings, aggregated from player_match_statistics)
- [x] Alembic migration (grouped)
- [x] Model tests (compact grouped tests)

**Files Created:**
- `app/models/match_statistics.py` - Team stats per match
- `app/models/player_match_statistics.py` - Player stats per match
- `app/models/club_season_statistics.py` - Season aggregated club stats
- `app/models/player_season_statistics.py` - Season aggregated player stats
- `alembic/versions/26261d486b2e_add_statistics_models.py` - Migration
- Updated `tests/test_models.py` with `TestStatisticsModels` class

**Key Features Implemented:**
- Numeric precision for statistics (DECIMAL 5,2 and 8,6 for xG)
- UNIQUE constraints for one-to-one relationships
- CASCADE delete on player/match deletion
- CheckConstraints for team_type validation

---

#### 2.3 Training Models ✅
- [x] Training plans model
- [x] Training exercises model
- [x] Alembic migration (grouped)
- [x] Model tests (compact grouped tests)

**Files Created:**
- `app/models/training_plan.py` - Training plans for players
- `app/models/training_exercise.py` - Exercises within plans
- `alembic/versions/2c84469970f0_add_training_models.py` - Migration
- Updated `tests/test_models.py` with `TestTrainingModels` class

**Key Features Implemented:**
- Status tracking (pending, in_progress, completed)
- Completion tracking per exercise
- SET NULL on coach deletion (preserve plans)
- CASCADE delete on player deletion
- Flexible exercise parameters (sets, reps, duration as strings)

---

### ❌ Phase 3: Admin Endpoint - Match Upload (NOT STARTED)

**Why Phase 3 (moved from Phase 5):** After models exist, we need to POPULATE the database with match data before coach/player endpoints have anything to display. This is the most complex endpoint that creates all the data.

**Total: 1 endpoint (most complex in the entire project)**

- [ ] `POST /api/coach/matches` - Upload match with StatsBomb events

**This endpoint must:**
1. Parse ~3000 StatsBomb events from JSON
2. Identify teams from Starting XI events (fuzzy match club name)
3. Create/update opponent club
4. Create match record
5. Insert all ~3000 events to database (bulk insert for performance)
6. Extract goals and find assists from events
7. Create/update players (your club) with invite codes
8. Create/update opponent players
9. Calculate match statistics (both teams) from events
10. Calculate player match statistics from events
11. Update club season statistics (aggregated)
12. Update player season statistics with attribute ratings

**Estimated Files:**
- Route: `app/api/routes/admin.py` or add to `coach.py`
- Schemas: `app/schemas/match_upload.py`
- Processing logic: `app/services/match_processor.py`
- Statistics calculator: `app/services/statistics.py`
- Invite code generator: `app/utils/invite_code.py`
- Team matcher: `app/utils/team_matcher.py`
- Tests: `tests/test_admin_match_upload.py` (integration test)

**Key Challenges:**
- Transaction management (rollback entire upload on failure)
- Bulk insert performance (~3000 events)
- Fuzzy team name matching
- Complex statistics aggregation from JSONB
- Attribute rating calculation formulas
- Goal validation vs final score

**Dependencies:**
- All match-related models
- All statistics models
- Comprehensive error handling
- Sample StatsBomb event JSON for testing

---

### ❌ Phase 4: Coach Endpoints (NOT STARTED)

**Why Phase 4 (moved from Phase 3):** After admin endpoint populates the database, coach endpoints can now display that data.

**Total: 11 endpoints**

#### 4.1 Dashboard & Matches
- [ ] `GET /api/coach/dashboard` - Dashboard with summary + statistics tabs
- [ ] `GET /api/coach/matches/{match_id}` - Match detail with 3 tabs (summary, stats, lineup)

#### 4.2 Players Management
- [ ] `GET /api/coach/players` - List all players (joined + pending)
- [ ] `GET /api/coach/players/{player_id}` - Player detail with 3 tabs
- [ ] `GET /api/coach/players/{player_id}/matches/{match_id}` - Player match detail

#### 4.3 Profile
- [ ] `GET /api/coach/profile` - Coach profile with club stats

#### 4.4 Training Plans
- [ ] `POST /api/coach/training-plans/generate-ai` - AI training plan generation
- [ ] `POST /api/coach/training-plans` - Create training plan
- [ ] `GET /api/coach/training-plans/{plan_id}` - Training plan detail
- [ ] `PUT /api/coach/training-plans/{plan_id}` - Update training plan
- [ ] `DELETE /api/coach/training-plans/{plan_id}` - Delete training plan

**Estimated Files Per Endpoint:**
- Route file: `app/api/routes/coach.py`
- Schemas: `app/schemas/coach_*.py`
- CRUD operations: `app/crud/match.py`, `app/crud/statistics.py`, etc.
- Tests: `tests/test_coach_*.py`

---

### ❌ Phase 5: Player Endpoints (NOT STARTED)

**Why Phase 5 (moved from Phase 4):** Player endpoints are similar to coach endpoints but filtered to player's own data.

**Total: 7 endpoints**

#### 5.1 Dashboard & Stats
- [ ] `GET /api/player/dashboard` - My Stats tab (attributes + season stats)

#### 5.2 Matches
- [ ] `GET /api/player/matches` - Matches list
- [ ] `GET /api/player/matches/{match_id}` - Player match detail

#### 5.3 Training
- [ ] `GET /api/player/training` - Training plans list
- [ ] `GET /api/player/training/{plan_id}` - Training plan detail
- [ ] `PUT /api/player/training/exercises/{exercise_id}/toggle` - Toggle exercise completion

#### 5.4 Profile
- [ ] `GET /api/player/profile` - Player profile

**Estimated Files Per Endpoint:**
- Route file: `app/api/routes/player.py`
- Schemas: `app/schemas/player_*.py`
- CRUD operations: Reuse from coach endpoints where applicable
- Tests: `tests/test_player_*.py`

---

## File Structure

```
Spinta_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py ✅
│   ├── config.py ✅
│   ├── database.py ✅
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py ✅
│   │       ├── auth.py ✅
│   │       ├── coach.py ❌
│   │       ├── player.py ❌
│   │       └── admin.py ❌
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py ✅
│   │   └── deps.py ✅
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py ✅
│   │   ├── coach.py ✅
│   │   ├── club.py ✅
│   │   ├── player.py ✅
│   │   ├── match.py ❌
│   │   ├── statistics.py ❌
│   │   └── training.py ❌
│   ├── models/
│   │   ├── __init__.py ✅
│   │   ├── base.py ✅
│   │   ├── user.py ✅
│   │   ├── coach.py ✅
│   │   ├── club.py ✅
│   │   ├── player.py ✅
│   │   ├── opponent_club.py ❌
│   │   ├── opponent_player.py ❌
│   │   ├── match.py ❌
│   │   ├── goal.py ❌
│   │   ├── event.py ❌
│   │   ├── match_statistics.py ❌
│   │   ├── player_match_statistics.py ❌
│   │   ├── club_season_statistics.py ❌
│   │   ├── player_season_statistics.py ❌
│   │   ├── training_plan.py ❌
│   │   └── training_exercise.py ❌
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py ✅
│   │   ├── user.py ✅
│   │   ├── coach.py ✅
│   │   ├── club.py ✅
│   │   ├── player.py ✅
│   │   ├── match.py ❌
│   │   ├── statistics.py ❌
│   │   └── training.py ❌
│   ├── services/ ❌
│   │   ├── __init__.py
│   │   ├── match_processor.py ❌
│   │   └── statistics.py ❌
│   └── utils/ ❌
│       ├── __init__.py
│       └── invite_code.py ❌
├── tests/
│   ├── __init__.py
│   ├── conftest.py ✅
│   ├── test_health.py ✅
│   ├── test_models.py ✅
│   ├── test_auth.py ✅
│   ├── test_coach_*.py ❌
│   ├── test_player_*.py ❌
│   └── test_admin_*.py ❌
├── alembic/ ✅
├── docs/ ✅ (specs provided by user)
├── .env ✅
├── .env.example ✅
├── .gitignore ✅
├── requirements.txt ✅
├── pytest.ini ✅
├── alembic.ini ✅
├── GETTING_STARTED.md ✅
└── PROJECT_PROGRESS.md ✅ (this file)
```

---

## Next Steps

### Immediate: Phase 2 - Database Models

**Logical Implementation Order:**

1. **Match-Related Models** (highest priority - required for Phase 3)
   - Start with: opponent_clubs, matches, opponent_players
   - Then: goals, events (with JSONB for event_data)
   - These are required for the admin endpoint

2. **Statistics Models** (required for Phase 3)
   - Start with: match_statistics, player_match_statistics
   - Then: club_season_statistics, player_season_statistics
   - These store calculated data from events table

3. **Training Models** (required for Phases 4-5)
   - Start with: training_plans, training_exercises
   - These are independent and can be done last

### After Phase 2: Phase 3 - Admin Endpoint

**Why this order makes sense:**
- ✅ Phase 2 creates the database schema (all 15 tables)
- ✅ Phase 3 (admin endpoint) POPULATES the database with match data
- ✅ Phase 4 (coach endpoints) reads and displays the populated data
- ✅ Phase 5 (player endpoints) reads and displays player-specific data

Without Phase 3 working first, Phases 4-5 would query empty tables, making testing difficult.

### Approach for Each Model

Using TDD:
1. Create model file in `app/models/`
2. Write tests in `tests/test_models.py`
3. Generate Alembic migration
4. Run tests (should pass)
5. Verify migration works on both PostgreSQL and SQLite

---

## Key Technical Challenges

### Solved ✅
1. **UUID Compatibility** - GUID type with `load_dialect_impl` handles PostgreSQL UUID and SQLite String
2. **Circular Imports** - Separated database.py from main.py
3. **CORS Parsing** - Used `@property` decorator for list conversion
4. **Player Linking** - User_id equals player_id during signup
5. **Invite Code Generation** - Cryptographically secure random codes

### To Solve ❌
1. **StatsBomb Event Processing** - Parse and insert ~3000 events per match efficiently
2. **Statistics Calculation** - Aggregate complex statistics from events JSONB
3. **Team Matching** - Fuzzy match club name to StatsBomb team names
4. **Attribute Ratings** - Calculate player attributes from season statistics
5. **Transaction Management** - Rollback entire match upload on any failure
6. **Performance** - Optimize bulk inserts for events table

---

## Testing Strategy

### Current Coverage ✅
- Health endpoint (5 tests)
- Database models (comprehensive tests)
- Authentication (all 4 endpoints with edge cases)

### Required Coverage ❌
- All coach endpoints (11 endpoints)
- All player endpoints (7 endpoints)
- Admin match upload (complex integration test)
- Statistics calculation accuracy
- Edge cases and error scenarios

---

## Dependencies

### Installed ✅
```
fastapi
uvicorn[standard]
sqlalchemy
alembic
psycopg2-binary
python-dotenv
pydantic[email]
pydantic-settings
python-multipart
python-jose[cryptography]
passlib[bcrypt]
pytest
pytest-asyncio
httpx
```

### May Need Later ❌
- `redis` - For rate limiting
- `celery` - For background jobs (if match processing is slow)
- `anthropic` - For AI training plan generation

---

## Notes & Decisions

### Design Patterns
- **Screen-based API**: One endpoint per UI screen with all required data
- **Stateless JWT**: No expiration, client-side logout
- **Incomplete Players**: Pre-created during match upload, completed during signup
- **Player Attributes**: Calculated from season statistics using proprietary formulas

### Database Decisions
- **User_id = Player_id**: Player's user_id matches their player_id after signup
- **JSONB for Events**: Full StatsBomb event JSON stored for flexibility
- **Opponent Separation**: Opponent clubs/players in separate tables
- **Statistics Pre-calculation**: All statistics calculated and stored (not on-the-fly)

### Future Enhancements (Not in Scope)
- Email verification
- Token refresh mechanism
- Password reset flow
- Profile image upload service
- AI training plan generation implementation
- Real-time match updates
- Push notifications

---

## Summary

**Completed:** 4/23 endpoints (17%)
**Models Completed:** 4/15 tables (27%)

### Phase Status
- **Phase 1 (Foundation):** ✅ COMPLETE
- **Phase 2 (Database Models):** ❌ NOT STARTED - 11 models remaining
- **Phase 3 (Admin Endpoint):** ❌ NOT STARTED - 1 complex endpoint to populate DB
- **Phase 4 (Coach Endpoints):** ❌ NOT STARTED - 11 endpoints to display data
- **Phase 5 (Player Endpoints):** ❌ NOT STARTED - 7 endpoints to display data

**Current State:** Foundation complete. Ready to build remaining database models using TDD approach.

**Implementation Order:**
1. ✅ Phase 1: Foundation (auth, core models)
2. → Phase 2: All database models (schema)
3. → Phase 3: Admin endpoint (populate database)
4. → Phase 4: Coach endpoints (read/display data)
5. → Phase 5: Player endpoints (read/display data)

---

**End of Progress Tracker**
