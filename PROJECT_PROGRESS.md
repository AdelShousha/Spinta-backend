# Spinta Backend - Project Progress Tracker

**Last Updated:** 2025-11-13
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

### → Phase 2.5: Endpoint & Schema Validation (IN PROGRESS)

**Status:** Validating all endpoints and schema before implementation

**Goal:** For each endpoint, validate UI → API → Database in one pass, making corrections immediately.

**Progress:** 0/18 endpoints validated

#### Workflow (Repeat for Each Endpoint)

**For Each Coach Endpoint (11 endpoints):**

1. **Review Against UI**

   - Open corresponding UI page in `docs/Spinta UI.pdf`
   - Check request/response fields match UI exactly
   - Identify missing/extra fields

2. **Review Database Queries**

   - Check if schema supports all required fields
   - Verify JOINs work with current relationships
   - Identify missing columns/tables
   - Validate query logic correctness

3. **Document Changes**

   - Update endpoint in `docs/05_COACH_ENDPOINTS.md`:
     - Fix request/response schemas
     - Fix database queries
     - Add missing fields
     - Remove unnecessary fields
   - Update `docs/02_DATABASE_SCHEMA.md`:
     - Add missing columns
     - Modify field types
     - Add/update relationships
     - Update constraints

4. **Move to Next Endpoint**

#### Coach Endpoints Order:

1. [x] GET /api/coach/dashboard (Pages 6-7)
2. [x] GET /api/coach/matches/{match_id} (Pages 8-10)
3. [x] GET /api/coach/players (Page 11)
4. [ ] GET /api/coach/players/{player_id} (Pages 12-16)
5. [ ] GET /api/coach/players/{player_id}/matches/{match_id} (Page 15)
6. [ ] GET /api/coach/profile (Page 20)
7. [ ] POST /api/coach/training-plans/generate-ai (Pages 16-17)
8. [ ] POST /api/coach/training-plans (Page 17)
9. [ ] GET /api/coach/training-plans/{plan_id} (Page 18)
10. [ ] PUT /api/coach/training-plans/{plan_id}
11. [ ] DELETE /api/coach/training-plans/{plan_id}

#### Then Repeat for Player Endpoints (7 endpoints):

1. [ ] GET /api/player/dashboard (Page 25)
2. [ ] GET /api/player/matches (Page 26)
3. [ ] GET /api/player/matches/{match_id} (Page 27)
4. [ ] GET /api/player/training (Page 28)
5. [ ] GET /api/player/training/{plan_id} (Page 29)
6. [ ] PUT /api/player/training/exercises/{exercise_id}/toggle (Page 29)
7. [ ] GET /api/player/profile (Page 30)

#### Final Step: Apply Schema Changes to Models

After all endpoints validated:

- Review all changes in `docs/02_DATABASE_SCHEMA.md`
- Update model files in `app/models/` accordingly
- Generate Alembic migrations
- Apply migrations
- Update tests if needed

**Benefits of Endpoint-by-Endpoint Approach:**

1. **Immediate Fixes:** Changes applied right away, not held in memory
2. **Clear Progress:** Can track exactly which endpoints are validated
3. **No Context Loss:** Complete one endpoint before moving to next
4. **Easier Review:** Changes grouped by endpoint, not by type
5. **Flexible:** Can pause/resume at any endpoint boundary

---

### ❌ Phase 3: Admin Endpoint Processing Logic (NOT STARTED)

**Goal:** Build data processing incrementally from raw JSON to database tables.

#### Step 1: Granular Processing Logic Design

For each table in the final schema, document exact processing steps:

**Create file:** `docs/PROCESSING_LOGIC.md`

For each table, answer:

- Which raw JSON events contain this data?
- What filters/conditions extract the right events?
- How to calculate/derive each field?
- What validation rules apply?

**Example:**

```markdown
### Table: goals

#### Column: scorer_name

- Source: Shot events where outcome.name == "Goal"
- Extract: event['player']['name']
- Validation: Must exist in lineup
```

#### Step 2: Implement Processing Functions

Create modular processing functions:

```
app/services/
├── match_processor.py       # Main orchestrator
├── team_identifier.py       # Team matching logic
├── player_extractor.py      # Player creation logic
├── goal_extractor.py        # Goal extraction logic
├── statistics_calculator.py # Stats calculation
└── event_processor.py       # Event storage
```

#### Step 3: Consolidate into Main Processor

Create `app/services/match_processor.py` that:

- Orchestrates all extraction functions
- Handles transaction management
- Returns processing summary

#### Step 4: Integrate with Admin Endpoint

Create POST /api/coach/matches route that:

- Validates request
- Calls match processor
- Returns response

#### Step 5: Test with Real Data

- Test with `docs/15946.json`
- Verify all tables populated correctly
- Validate calculations

**Key Deliverables:**

- `docs/PROCESSING_LOGIC.md` - Detailed processing documentation
- `app/services/` - All processing functions
- `app/api/routes/admin.py` - Admin endpoint implementation
- `tests/test_admin_match_upload.py` - Integration tests

---

### ❌ Phase 4: Implement Coach Endpoints (NOT STARTED)

**Total: 11 endpoints**

For each endpoint:

- Create route handler
- Create schemas
- Create CRUD operations
- Write tests

**Endpoints to Implement:**

1. [ ] GET /api/coach/dashboard
2. [ ] GET /api/coach/matches/{match_id}
3. [ ] GET /api/coach/players
4. [ ] GET /api/coach/players/{player_id}
5. [ ] GET /api/coach/players/{player_id}/matches/{match_id}
6. [ ] GET /api/coach/profile
7. [ ] POST /api/coach/training-plans/generate-ai
8. [ ] POST /api/coach/training-plans
9. [ ] GET /api/coach/training-plans/{plan_id}
10. [ ] PUT /api/coach/training-plans/{plan_id}
11. [ ] DELETE /api/coach/training-plans/{plan_id}

**Files to Create:**

- `app/api/routes/coach.py` - Route handlers
- `app/schemas/coach_*.py` - Request/response schemas
- `app/crud/match.py`, `statistics.py`, `training.py` - CRUD operations
- `tests/test_coach_*.py` - Endpoint tests

---

### ❌ Phase 5: Implement Player Endpoints (NOT STARTED)

**Total: 7 endpoints**

For each endpoint:

- Create route handler
- Create schemas
- Reuse CRUD where possible
- Write tests

**Endpoints to Implement:**

1. [ ] GET /api/player/dashboard
2. [ ] GET /api/player/matches
3. [ ] GET /api/player/matches/{match_id}
4. [ ] GET /api/player/training
5. [ ] GET /api/player/training/{plan_id}
6. [ ] PUT /api/player/training/exercises/{exercise_id}/toggle
7. [ ] GET /api/player/profile

**Files to Create:**

- `app/api/routes/player.py` - Route handlers
- `app/schemas/player_*.py` - Request/response schemas
- Reuse CRUD from coach endpoints
- `tests/test_player_*.py` - Endpoint tests

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
│   │   ├── opponent_club.py ✅
│   │   ├── opponent_player.py ✅
│   │   ├── match.py ✅
│   │   ├── goal.py ✅
│   │   ├── event.py ✅
│   │   ├── match_statistics.py ✅
│   │   ├── player_match_statistics.py ✅
│   │   ├── club_season_statistics.py ✅
│   │   ├── player_season_statistics.py ✅
│   │   ├── training_plan.py ✅
│   │   └── training_exercise.py ✅
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

### Immediate: Phase 2.5 - Endpoint & Schema Validation

**Current Task:** Validate first coach endpoint (Dashboard - Pages 6-7)

**Workflow for Each Endpoint:**

1. **Review UI** - Check pages in `docs/Spinta UI.pdf`
2. **Compare API** - Verify request/response in endpoint docs
3. **Validate Queries** - Check database can support all fields
4. **Document Changes** - Update endpoint docs and schema docs immediately

**Why this order makes sense:**

- ✅ Phase 1 (Foundation): Auth and core infrastructure complete
- ✅ Phase 2 (Models): All 15 database models created
- → Phase 2.5 (Validation): Ensure schema matches UI/API requirements
- → Phase 3 (Admin Processing): Build data processing systematically
- → Phase 4-5 (Implementation): Implement validated endpoints with confidence

Validating everything first prevents rework later and ensures the schema supports all UI requirements.

### Approach for Phase 2.5

For each endpoint:

1. Open corresponding UI page
2. List all fields shown in UI
3. Compare against endpoint spec
4. Test if database queries work
5. Update docs immediately
6. Move to next endpoint

Track progress: Currently 0/18 endpoints validated

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
**Models Completed:** 15/15 tables (100%) - Pending revisions from Phase 2.5

### Phase Status

- **Phase 1 (Foundation):** ✅ COMPLETE
- **Phase 2 (Database Models):** ✅ COMPLETE - All 15 models created (pending revisions)
- **Phase 2.5 (Endpoint & Schema Validation):** → IN PROGRESS - 0/18 endpoints validated
- **Phase 3 (Admin Endpoint Processing):** ❌ NOT STARTED - Data processing logic & implementation
- **Phase 4 (Coach Endpoints):** ❌ NOT STARTED - 11 endpoints to implement
- **Phase 5 (Player Endpoints):** ❌ NOT STARTED - 7 endpoints to implement

**Current State:** All database models created. Now validating endpoints against UI and schema before implementation.

**Implementation Order:**

1. ✅ Phase 1: Foundation (auth, core models)
2. ✅ Phase 2: All database models (schema)
3. → Phase 2.5: Validate endpoints & schema (current)
4. → Phase 3: Admin data processing (systematic build)
5. → Phase 4: Implement coach endpoints
6. → Phase 5: Implement player endpoints

---

**End of Progress Tracker**
