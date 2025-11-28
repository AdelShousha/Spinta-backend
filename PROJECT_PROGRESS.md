# Spinta Backend - Project Progress Tracker

**Last Updated:** 2025-11-16
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

### ✅ Phase 2.5: Endpoint & Schema Validation (COMPLETED)

**Status:** All endpoints validated and schema changes applied successfully

**Goal:** For each endpoint, validate UI → API → Database in one pass, making corrections immediately.

**Progress:** 18/18 endpoints validated ✅

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
4. [X] GET /api/coach/players/{player_id} (Pages 12-16)
5. [X] GET /api/coach/players/{player_id}/matches/{match_id} (Page 15)
6. [X] GET /api/coach/profile (Page 20)
7. [X] POST /api/coach/training-plans/generate-ai (Pages 16-17)
8. [X] POST /api/coach/training-plans (Page 17)
9. [X] GET /api/coach/training-plans/{plan_id} (Page 18)
10. [X] PUT /api/coach/training-plans/{plan_id}
11. [X] DELETE /api/coach/training-plans/{plan_id}

#### Then Repeat for Player Endpoints (7 endpoints):

1. [X] GET /api/player/dashboard (Page 25)
2. [X] GET /api/player/matches (Page 26)
3. [X] GET /api/player/matches/{match_id} (Page 27)
4. [X] GET /api/player/training (Page 28)
5. [X] GET /api/player/training/{plan_id} (Page 29)
6. [X] PUT /api/player/training/exercises/{exercise_id}/toggle (Page 29)
7. [X] GET /api/player/profile (Page 30)

#### Final Step: Apply Schema Changes to Models ✅

After all endpoints validated:

- [x] Review all changes in `docs/MODEL_CHANGES.md`
- [x] Update model files in `app/models/` accordingly
- [x] Generate Alembic migrations
- [x] Apply migrations
- [x] Update tests if needed

**Schema Changes Applied:**

- **Match Model** (app/models/match.py):
  - Removed: `match_time`, `is_home_match`, `home_score`, `away_score`
  - Added: `our_score`, `opponent_score`, `result` (W/D/L)
  - Added relationship: `lineups` (one-to-many with MatchLineup)

- **Goal Model** (app/models/goal.py):
  - Removed: `team_name`, `assist_name`, `period`, `goal_type`, `body_part`
  - Added: `is_our_goal` (Boolean)
  - Retained: `scorer_name`, `minute`, `second`

- **NEW: MatchLineup Model** (app/models/match_lineup.py):
  - Created new model to track match lineups for both teams
  - Fields: `lineup_id`, `match_id`, `team_type`, `player_id`, `opponent_player_id`, `player_name`, `jersey_number`, `position`
  - Supports both our team and opponent team players

- **ClubSeasonStatistics Model** (app/models/club_season_statistics.py):
  - Added: `total_assists` (Integer)
  - Added: `team_form` (String, e.g., "WWDLW")

**Migration Applied:**
- `90388be62f06_apply_phase_2_5_schema_changes.py` - Applied successfully

**Testing:**
- Updated all affected tests in `tests/test_models.py`
- All 26 model tests pass ✅

**Benefits of Endpoint-by-Endpoint Approach:**

1. **Immediate Fixes:** Changes applied right away, not held in memory
2. **Clear Progress:** Can track exactly which endpoints are validated
3. **No Context Loss:** Complete one endpoint before moving to next
4. **Easier Review:** Changes grouped by endpoint, not by type
5. **Flexible:** Can pause/resume at any endpoint boundary

---

### ❌ Phase 3: Match Upload Processing - Iterative TDD (NOT STARTED)

**Goal:** Build StatsBomb data processing incrementally with test-driven development, ensuring each component is thoroughly tested before integration.

**Approach:** 12 iterations following strict TDD methodology (Red → Green → Refactor)

---

#### Iteration Overview

Each iteration follows this workflow:
1. **Red**: Write failing tests first
2. **Green**: Write minimal code to pass tests
3. **Refactor**: Clean up and optimize code
4. **Manual Test**: Verify with sample StatsBomb data
5. **Integrate**: Ensure compatibility with previous iterations

**Test Data:**
- Minimal JSON samples for unit tests
- Subsets of `docs/15946.json` for integration tests
- Full `docs/15946.json` (~3000 events) for end-to-end test

---

#### Iteration 1: Team Identification ✅ COMPLETED

**Goal:** Extract team information from StatsBomb events with smart matching (pure processing logic)

**Function:** `identify_teams(club_name: str, events: List[dict], club_statsbomb_team_id: Optional[int] = None) → dict`

**Input:**
- `club_name`: Our club's name from database
- `events`: StatsBomb events array
- `club_statsbomb_team_id`: Our club's StatsBomb team ID (None for first match, int for subsequent matches)

**Output:**
```python
{
  'our_club_statsbomb_team_id': int,
  'our_club_name': str,
  'opponent_statsbomb_team_id': int,
  'opponent_name': str,
  'should_update_statsbomb_id': bool,    # True if first match
  'new_statsbomb_team_id': int or None   # ID to save if first match
}
```

**Processing:**
- Extract 2 Starting XI events (type.id = 35)
- Validate each has exactly 11 players
- **If club_statsbomb_team_id is None (first match):**
  - Use fuzzy matching: exact → substring → 80% similarity
  - Return `should_update_statsbomb_id = True` and `new_statsbomb_team_id`
- **If club_statsbomb_team_id exists (subsequent matches):**
  - Use direct ID matching (faster and more reliable)
  - Return `should_update_statsbomb_id = False`

**Tests:** 24 tests (all passing)
- 7 fuzzy matching tests
- 5 team identification tests (first match)
- 5 subsequent match tests (direct ID matching)
- 4 validation error tests
- 3 end-to-end tests

**Manual Testing:**
```bash
python app/services/team_identifier.py
# Interactive prompts for:
# 1. JSON file path
# 2. Club name
# 3. Club StatsBomb team ID (press Enter for None/first match)
```

**Files:**
- `app/services/team_identifier.py` ✅
- `tests/services/test_team_identifier.py` ✅

**Key Notes:**
- Pure processing logic only (no database operations)
- Smart matching: fuzzy for first match, direct ID for subsequent matches
- Uses exact naming convention: our_club_*, opponent_*
- Returns flag to indicate if database update needed

---

#### Iteration 2: Opponent Club Creation ✅ COMPLETED

**Goal:** Get or create opponent club record

**Function:** `get_or_create_opponent_club(db: Session, opponent_statsbomb_team_id: int, opponent_name: str, logo_url: Optional[str] = None) → UUID`

**Input:**
- `db`: Database session
- `opponent_statsbomb_team_id`: StatsBomb team ID
- `opponent_name`: Opponent name
- `logo_url`: Opponent logo URL (optional, defaults to None)

**Output:** `opponent_club_id` (UUID)

**Processing:**
- Check if exists by `statsbomb_team_id`
- If exists: update `opponent_name` and `logo_url` if changed
- If not found: create new opponent_clubs record
- Return `opponent_club_id`

**Tests:** 6 tests (all passing)
- Test create new opponent club
- Test retrieve existing by statsbomb_team_id
- Test logo_url is optional (None)
- Test update opponent_name if changed
- Test update logo_url if changed
- Test multiple calls return same ID

**Files:**
- `app/services/opponent_service.py` ✅
- `tests/services/test_opponent_service.py` ✅

**Key Features:**
- Get-or-create pattern (idempotent)
- Updates opponent_name and logo_url if StatsBomb data changes
- Handles optional logo_url (defaults to None)
- Returns UUID type (compatible with both PostgreSQL and SQLite)

---

#### Iteration 3: Match Record Creation ✅ COMPLETED

**Goal:** Create match record with score validation from StatsBomb events

**Functions:**

1. **Helper Function (for validation & manual testing):**
   ```python
   count_goals_from_events(
       events: List[dict],
       our_club_statsbomb_team_id: int,
       opponent_statsbomb_team_id: int
   ) → dict
   ```

2. **Main Function:**
   ```python
   create_match_record(
       db: Session,
       club_id: UUID,
       opponent_club_id: UUID,
       match_date: str,
       our_score: int,
       opponent_score: int,
       opponent_name: str,
       events: List[dict]
   ) → UUID
   ```

**Parameter Sources:**
- `club_id`: Query clubs table using `our_club_statsbomb_team_id` from Iteration 1
- `opponent_club_id`: Output from `get_or_create_opponent_club()` (Iteration 2)
- `match_date`: From request body
- `our_score`: From request body (user input)
- `opponent_score`: From request body (user input)
- `opponent_name`: From request body
- `events`: From request body (StatsBomb events array)

**Output:** `match_id` (UUID)

**Processing:**

1. **Get StatsBomb Team IDs:**
   - Query clubs table: get `statsbomb_team_id` using `club_id`
   - Query opponent_clubs table: get `statsbomb_team_id` using `opponent_club_id`

2. **Count Goals from Events (Helper Function Logic):**
   - **IMPORTANT:** Skip penalty shootout (period 5) - match result based on regular/extra time only
   - Filter events where `event['type']['id'] == 16` (Shot)
   - Filter where `event['shot']['outcome']['id'] == 97` (Goal)
   - Filter where `event['period']` is 1-4 (exclude period 5 penalty shootout)
   - Use `event['possession_team']['id']` to determine which team scored
   - Count goals for our_club vs opponent
   - Return `{'our_goals': int, 'opponent_goals': int}`

3. **Validate Scores:**
   - Compare counted goals with user input (our_score, opponent_score)
   - If mismatch: raise ValueError with clear message
   - If match: proceed

4. **Calculate Result:**
   - 'W' if our_score > opponent_score
   - 'D' if our_score == opponent_score
   - 'L' if our_score < opponent_score

5. **Insert Match Record:**
   - Insert into matches table with all fields
   - Return match_id

**Example Goal Event Structure:**
```json
{
  "type": {"id": 16, "name": "Shot"},
  "possession_team": {"id": 779, "name": "Argentina"},
  "shot": {
    "outcome": {"id": 97, "name": "Goal"}
  }
}
```

**Tests:** 11 tests (all passing)
- ✅ Test count_goals_from_events with both teams scoring
- ✅ Test count_goals_from_events with no goals (0-0)
- ✅ Test count_goals_from_events with only our team scoring
- ✅ Test count_goals_from_events with only opponent scoring
- ✅ Test count_goals_from_events with empty events array
- ✅ Test count_goals_from_events excludes penalty shootout (period 5)
- ✅ Test create_match_record with Win result
- ✅ Test create_match_record with Draw result
- ✅ Test create_match_record with Loss result
- ✅ Test score validation error when mismatch
- ✅ Test score validation success when match

**Manual Testing:**
Interactive CLI to test goal counting:
```bash
python -m app.services.match_service
# Prompts for:
# 1. JSON file path (default: docs/15946.json)
# 2. Our team StatsBomb ID
# 3. Opponent team StatsBomb ID
# Output: Goal counts for both teams
```

**Files:**
- `app/services/match_service.py` ✅
- `tests/services/test_match_service.py` ✅

**Key Features:**
- **Goal Validation**: Counts goals from Shot events (type 16) with Goal outcome (id 97)
- **Penalty Shootout Exclusion**: Period 5 goals are NOT counted - match result based on regular/extra time only
- **Score Verification**: User-provided scores must match event data exactly
- **Automatic Result Calculation**: W/D/L based on scores
- **Clear Error Messages**: Detailed mismatch information if validation fails
- **Reusable Helper**: `count_goals_from_events()` can be used independently
- **Manual Testing CLI**: Quick verification with real StatsBomb data

**Important Note:**
Penalty shootout goals (period 5) are excluded from the final score. Match results are determined by the score at the end of regular time and extra time (periods 1-4) only, as per standard football rules.

---

#### Iteration 4: Player Extraction (Our Team) ✅ COMPLETED

**Goal:** Extract our club's players from Starting XI and create incomplete player records

**Functions:**

1. **Helper Function (for parsing & manual testing):**
   ```python
   parse_our_lineup_from_events(
       events: List[dict],
       our_club_statsbomb_team_id: int
   ) → List[dict]
   ```

2. **Main Function:**
   ```python
   extract_our_players(
       db: Session,
       club_id: UUID,
       events: List[dict]
   ) → dict
   ```

**Parameter Sources:**
- `db`: Database session
- `club_id`: Query clubs table using `our_club_statsbomb_team_id` from Iteration 1
- `events`: StatsBomb events array from request body

**Output:**
```python
{
    'players_processed': int,  # Total (created + updated + linked)
    'players_created': int,
    'players_updated': int,
    'players': [
        {
            'player_id': UUID,
            'player_name': str,
            'statsbomb_player_id': int,
            'jersey_number': int,
            'position': str,
            'invite_code': str
        },
        # ... 11 players total
    ]
}
```

**Processing:**

1. **Get StatsBomb Team ID:**
   - Query clubs table: get `statsbomb_team_id` using `club_id`

2. **Find Our Team's Starting XI Event (Helper Function):**
   - Filter events where `event['type']['id'] == 35` (Starting XI)
   - Should find exactly 2 Starting XI events
   - Check `event['team']['id']` to match our `statsbomb_team_id`
   - Extract our team's Starting XI event

3. **Validate and Extract Lineup:**
   - Extract `event['tactics']['lineup']`
   - Verify lineup has exactly 11 players
   - If not 11: raise ValueError

4. **Parse Player Data:**
   For each player in lineup:
   - Extract `player['player']['id']` → statsbomb_player_id
   - Extract `player['player']['name']` → player_name
   - Extract `player['jersey_number']` → jersey_number
   - Extract `player['position']['name']` → position

5. **Create or Update Players (Main Function):**
   For each player:
   - Check if exists by `(club_id, statsbomb_player_id)`
   - **If exists and is_linked=True (linked player):**
     - Skip update (preserve user account data)
     - Include existing data in results
   - **If exists and is_linked=False (incomplete player):**
     - Update `jersey_number` if changed
     - Update `position` if changed
     - **Preserve** `player_name` (don't update)
     - **Preserve** `invite_code` (critical - may be shared)
     - Track if actually updated (for count)
   - **If not exists (new player):**
     - Generate unique invite_code (format: XXX-####)
     - Create Player record with:
       - `club_id`: from parameter
       - `player_name`: from lineup
       - `statsbomb_player_id`: from lineup
       - `jersey_number`: from lineup
       - `position`: from lineup
       - `invite_code`: generated
       - `is_linked`: False
       - `user_id`: NULL (incomplete player)

6. **Return Results:**
   - Count of players processed (total)
   - Count of players created (new)
   - Count of players updated (incomplete only)
   - List of player data for response

**Example Starting XI Event Structure:**
```json
{
  "type": {"id": 35, "name": "Starting XI"},
  "team": {"id": 779, "name": "Argentina"},
  "tactics": {
    "lineup": [
      {
        "player": {"id": 5503, "name": "Lionel Andrés Messi Cuccittini"},
        "position": {"id": 17, "name": "Right Wing"},
        "jersey_number": 10
      }
      // ... 10 more players
    ]
  }
}
```

**Tests:** 14 tests (all passing)

**Helper Tests (5):**
- ✅ Test parse_lineup extracts 11 players
- ✅ Test parse_lineup finds correct team by team.id
- ✅ Test parse_lineup validation error if not 11 players
- ✅ Test parse_lineup validation error if no Starting XI events
- ✅ Test parse_lineup validation error if team not found

**Main Function Tests (9):**
- ✅ Test extract creates 11 incomplete Player records (with new return structure)
- ✅ Test extract generates unique invite codes with format XXX-####
- ✅ Test extract sets all fields correctly
- ✅ Test extract sets is_linked=False for all players
- ✅ **NEW:** Test updates existing incomplete player (jersey/position changed)
- ✅ **NEW:** Test preserves invite code on update (never regenerated)
- ✅ **NEW:** Test skips linked players (is_linked=True not updated)
- ✅ **NEW:** Test no update if same data (update count = 0)
- ✅ **NEW:** Test mixed create and update (some new, some existing)

**Manual Testing:**
Interactive CLI to test lineup parsing:
```bash
python -m app.services.player_service
# Prompts for:
# 1. JSON file path (default: docs/15946.json)
# 2. StatsBomb team ID
# Output: List of 11 players with:
#   - Player name
#   - StatsBomb player ID
#   - Jersey number
#   - Position
```

**Files:**
- `app/services/player_service.py` ✅
- `tests/services/test_player_service.py` ✅

**Key Features:**
- **Pure Processing Helper**: `parse_our_lineup_from_events()` extracts lineup without database
- **Team Identification**: Uses `team.id` to find our team's Starting XI
- **Update-or-Create Pattern**: Checks for existing players by `(club_id, statsbomb_player_id)`
  - **New players**: Create with unique invite code
  - **Incomplete players** (is_linked=False): Update jersey/position if changed
  - **Linked players** (is_linked=True): Skip (never modify)
- **Invite Code Preservation**: Never regenerates invite code (may be shared with player)
- **Selective Updates**: Only updates `jersey_number` and `position` (preserves `player_name`)
- **Invite Code Generation**: Cryptographically secure XXX-#### format (e.g., "ARG-1234")
- **Incomplete Players**: New players created with `is_linked=False`, `user_id=NULL`
- **Validation**: Ensures exactly 2 Starting XI events and 11 players per team
- **Unique Codes**: Checks database to ensure invite code uniqueness
- **Manual Testing**: Easy verification with real StatsBomb data

---

#### Iteration 5: Opponent Players Extraction ✅ COMPLETED

**Goal:** Create/update opponent players from Starting XI events

**Function:** `extract_opponent_players(db: Session, opponent_club_id: UUID, events: List[dict]) → dict`

**Input:**
- opponent_club_id (from Iteration 2)
- events (StatsBomb events array)

**Output:**
```python
{
    'players_processed': int,  # Total (created + updated)
    'players_created': int,
    'players_updated': int,
    'players': [
        {
            'opponent_player_id': UUID,
            'player_name': str,
            'statsbomb_player_id': int,
            'jersey_number': int,
            'position': str
        },
        ...
    ]
}
```

**Processing:**
1. Get opponent club and StatsBomb team ID
2. Parse lineup from events using `team.id` (same logic as Iteration 4)
3. For each opponent player:
   - Check if exists by `(opponent_club_id, statsbomb_player_id)` **only** (not name)
   - If exists: Update jersey/position if changed
   - Else: Create new opponent_players record

**Implementation Details:**
- Reuses `parse_our_lineup_from_events()` via `parse_opponent_lineup_from_events()`
- Update-or-create pattern (players can appear in multiple matches)
- Only increments `players_updated` if jersey/position actually changed
- Manual testing CLI supports both our team and opponent team parsing

**Tests (6 tests):**
- Helper: `test_extracts_11_opponent_players`, `test_finds_correct_opponent_team`
- Main: `test_creates_new_opponent_players`, `test_updates_existing_by_statsbomb_id`, `test_no_update_if_same_data`, `test_mixed_create_and_update`
- **Total player service tests: 15** (9 from Iteration 4 + 6 from Iteration 5)

**Manual Testing:**
```bash
python -m app.services.player_service
# Prompts:
# 1. JSON file path
# 2. Team type: (o)ur or (op)ponent
# 3. StatsBomb team ID
# Outputs: 11 players with name, ID, jersey, position
```

**Files:**
- `app/services/player_service.py` (extended with 2 functions)
- `tests/services/test_player_service.py` (extended with 6 tests)

---

#### Iteration 6: Match Lineups Creation ✅ COMPLETED

**Goal:** Create 22 match lineup records (11 our_team + 11 opponent_team) from Starting XI events

**Functions:**

1. **Helper (Pure Processing):** `parse_both_lineups_from_events(events, our_club_statsbomb_id, opponent_club_statsbomb_id) → dict`
2. **Main (Database):** `create_match_lineups(db, match_id, events) → dict`

**Parameter Sources:**
- `db`: Database session
- `match_id`: From match creation (Iteration 3)
- `events`: StatsBomb events array from request body

**Output:**
```python
{
    'lineups_created': 22,
    'our_team_count': 11,
    'opponent_team_count': 11
}
```

**Processing:**

**Helper Function:**
1. Extract Starting XI events (filter `type.id == 35`)
2. Validate exactly 2 Starting XI events
3. Use `team.id` to identify which lineup belongs to which team
4. Parse lineup data from both teams (11 players each)
5. Return both lineups with: player_name, statsbomb_player_id, jersey_number, position

**Main Function:**
1. **Get match and team IDs:**
   - Query matches table using `match_id` → get `club_id`, `opponent_club_id`
   - Query clubs table → get `our_club_statsbomb_id`
   - Query opponent_clubs table → get `opponent_club_statsbomb_id`

2. **Check for duplicates:**
   - Query MatchLineup by `match_id`
   - If exists → raise ValueError (prevent duplicates)

3. **Parse lineups:**
   - Call helper function: `parse_both_lineups_from_events()`
   - Get both lineups (11 + 11 players)

4. **Process our team (11 players):**
   - For each player in our_lineup:
     - Query players table: `WHERE club_id = ? AND statsbomb_player_id = ?`
     - If not found → raise ValueError
     - Create MatchLineup with:
       - `team_type='our_team'`
       - `player_id` from database
       - `opponent_player_id=NULL`
       - Denormalize: player_name, jersey_number, position from event

5. **Process opponent team (11 players):**
   - For each player in opponent_lineup:
     - Query opponent_players table: `WHERE opponent_club_id = ? AND statsbomb_player_id = ?`
     - If not found → raise ValueError
     - Create MatchLineup with:
       - `team_type='opponent_team'`
       - `player_id=NULL`
       - `opponent_player_id` from database
       - Denormalize: player_name, jersey_number, position from event

6. **Validate and commit:**
   - Count = 22 (raise error if not)
   - Commit all records
   - Return counts

**Tests:** 13 tests (all passing)

**Helper Function Tests (5):**
- ✅ Test extracts 11 our players
- ✅ Test extracts 11 opponent players
- ✅ Test uses team.id for our team
- ✅ Test uses team.id for opponent team
- ✅ Test raises error if not 2 Starting XI events

**Main Function Tests (8):**
- ✅ Test creates 22 lineup records (11 + 11)
- ✅ Test creates 11 our_team lineups
- ✅ Test creates 11 opponent_team lineups
- ✅ Test sets denormalized fields correctly (from events, not database)
- ✅ Test matches player_ids correctly by statsbomb_player_id
- ✅ Test raises error if match not found
- ✅ Test raises error if player not found in database
- ✅ Test raises error if lineups already exist (prevent duplicates)

**Manual Testing:**
Interactive CLI to test lineup parsing:
```bash
python -m app.services.lineup_service
# Prompts for:
# 1. JSON file path (default: data/3869685.json)
# 2. Our team StatsBomb ID (e.g., 779)
# 3. Opponent team StatsBomb ID (e.g., 771)
# Output: Two sections with 11 players each:
#   - Player name
#   - StatsBomb player ID
#   - Jersey number
#   - Position
```

**Files:**
- `app/services/lineup_service.py` ✅ (new file)
- `tests/services/test_lineup_service.py` ✅ (new file)

**Key Features:**
- **Pure Processing Helper**: `parse_both_lineups_from_events()` for easy manual testing
- **Team Identification**: Uses `team.id` to identify which lineup belongs to which team
- **Strict Validation**: Raises errors for missing players, duplicate lineups, invalid data
- **Denormalized Data**: Stores player_name, jersey_number, position in lineup records for query performance
- **Database Matching**: Matches players by `(club_id/opponent_club_id, statsbomb_player_id)`
- **Duplicate Prevention**: Checks if lineups already exist before creating
- **Manual Testing**: Interactive CLI for verifying lineup extraction with real data

---

#### Iteration 7: Events Storage ✅ COMPLETED

**Goal:** Store Pass, Shot, and Dribble events from StatsBomb data with extracted fields for indexing and full JSON for detailed analysis

**Functions:**

1. **Helper (Pure Processing):** `parse_events_for_storage(events: List[dict]) → dict`
2. **Main (Database):** `insert_events(db: Session, match_id: UUID, events: List[dict]) → int`

**Parameter Sources:**
- `db`: Database session
- `match_id`: From match creation (Iteration 3)
- `events`: StatsBomb events array from request body

**Event Types Stored (filter by type.id):**
- Pass: `type.id = 30`
- Shot: `type.id = 16`
- Dribble: `type.id = 14`

**All other event types are excluded** (e.g., Half Start, Starting XI, Substitution, etc.)

**Output:**
```python
# Helper function returns:
{
    'total_events': int,  # Total events in input
    'filtered_count': int,  # Events matching type filter (14, 16, 30)
    'first_shot': {
        'raw': dict,  # Full event JSON
        'extracted': {
            'player_name': str | None,
            'statsbomb_player_id': int | None,
            'team_name': str | None,
            'statsbomb_team_id': int | None,
            'event_type_name': str | None,
            'position_name': str | None,
            'minute': int | None,
            'second': int | None,
            'period': int | None
        }
    } | None,  # None if no shots found
    'first_pass': { ... } | None,
    'first_dribble': { ... } | None
}

# Main function returns:
int  # Count of events inserted
```

**Processing:**

**Helper Function:**
1. Filter events to only type.id in [14, 16, 30]
2. Find first occurrence of each type (shot, pass, dribble)
3. Extract database fields using safe `.get()` (handles missing fields)
4. Return raw JSON and extracted fields for manual verification

**Main Function:**
1. **Validate match exists:**
   - Query matches table using `match_id`
   - If not found → raise ValueError

2. **Filter events:**
   - Filter to only type.id in [14, 16, 30]
   - Store in filtered list

3. **Validate filtered count:**
   - If filtered count == 0 → raise ValueError("No Pass, Shot, or Dribble events found")

4. **Batch insert (500 events per batch):**
   - Loop through filtered events
   - For each event:
     - Extract all fields using safe `.get()`:
       - `player_name` = `event.get('player', {}).get('name')`
       - `statsbomb_player_id` = `event.get('player', {}).get('id')`
       - `team_name` = `event.get('team', {}).get('name')`
       - `statsbomb_team_id` = `event.get('team', {}).get('id')`
       - `event_type_name` = `event.get('type', {}).get('name')`
       - `position_name` = `event.get('position', {}).get('name')`
       - `minute` = `event.get('minute')`
       - `second` = `event.get('second')`
       - `period` = `event.get('period')`
       - `event_data` = event (full JSON)
     - Create Event record with all extracted fields
     - Add to session with `db.add()`
   - Every 500 events: `db.commit()`
   - After loop: Final `db.commit()` for remaining events

5. **Return count:**
   - Return total count of events inserted

**Field Extraction Strategy:**
- All fields are nullable in database (handles missing data)
- Use `.get()` with dict navigation for safe extraction
- Events without `player` field: player_name, statsbomb_player_id, position_name → None
- Events without `position` field: position_name → None
- Full event JSON preserved in `event_data` (JSONB) for future analysis

**Tests:** 13 tests (all passing)

**Helper Function Tests (6):**
- ✅ Test filters only 3 event types (Pass, Shot, Dribble)
- ✅ Test extracts all fields correctly from valid events
- ✅ Test handles events without player field (sets fields to None)
- ✅ Test handles events without position field (sets field to None)
- ✅ Test returns None for missing event types (e.g., 0 dribbles)
- ✅ Test counts filtered events correctly

**Main Function Tests (7):**
- ✅ Test inserts correct count of events (only 3 types)
- ✅ Test batch insert with >500 events (verifies batching works)
- ✅ Test event_data stored as JSON (full event preserved in JSONB)
- ✅ Test all extracted fields match database records
- ✅ Test handles events without player (nullable fields work)
- ✅ Test raises error if match not found
- ✅ Test raises error if zero filtered events

**Manual Testing:**
Interactive CLI to test event extraction:
```bash
python -m app.services.event_service
# Prompts for:
# 1. JSON file path (default: data/3869685.json)
# Output: Three sections showing first shot/pass/dribble:
#   - Raw event JSON (first 500 chars)
#   - Extracted fields for database
#   - Total events and filtered count
```

**Files:**
- `app/services/event_service.py` ✅ (new file)
- `tests/services/test_event_service.py` ✅ (new file)

**Key Features:**
- **Event Type Filtering**: Only stores Pass (30), Shot (16), Dribble (14) - reduces ~3000 events to ~500-800
- **Pure Processing Helper**: `parse_events_for_storage()` for easy manual testing
- **Safe Field Extraction**: Uses `.get()` to handle missing fields (all nullable)
- **Batch Inserts**: 500 events per batch for optimal performance
- **JSONB Storage**: Full event JSON preserved with GIN index for querying
- **Validation**: Raises errors for invalid match_id or zero filtered events
- **Allows Re-insertion**: No duplicate checking (simpler, allows re-processing)
- **Manual Testing**: Interactive CLI for verifying extraction with real data

**Performance:**
- Original: ~3000 events per match (all types)
- After filtering: ~500-800 events per match (Pass/Shot/Dribble only)
- Batch size: 500 events → typically 1-2 batches per match
- Storage: JSONB with GIN index for efficient JSON querying

---

#### Iteration 8: Goals Extraction ✅ COMPLETED

**Goal:** Extract goals from Shot events with scorer information and timing

**Function:** `insert_goals(db, match_id: UUID, events: List[dict], our_club_statsbomb_id: int, opponent_statsbomb_id: int) → int`

**Input:**
- `db`: Database session
- `match_id`: Match ID (UUID)
- `events`: StatsBomb events array
- `our_club_statsbomb_id`: StatsBomb team ID for our club (from Iteration 3 logic)
- `opponent_statsbomb_id`: StatsBomb team ID for opponent

**Output:**
- `int`: Count of goals inserted (0 or more, 0 is valid for goalless matches)

**Processing Logic:**

1. **Validate match exists:**
   - Query Match by match_id
   - Raise ValueError if not found

2. **Parse goals using helper function:**
   - Call `parse_goals_from_events()` to extract goal data
   - Returns list of goal dicts with scorer_name, minute, second, is_our_goal

3. **Insert goals into database:**
   - For each goal dict:
     - Create Goal record with all extracted fields
     - Add to session with `db.add()`
   - Single `db.commit()` after all goals

4. **Return count:**
   - Return total count of goals inserted

**Helper Function:** `parse_goals_from_events(events, our_club_statsbomb_id, opponent_statsbomb_id) → List[dict]`

**Purpose:** Pure processing function that extracts goal data from Shot events (no database).

**Processing:**
1. **Filter Shot events with Goal outcome:**
   - `event.get('type', {}).get('id') == 16` (Shot event)
   - `event.get('shot', {}).get('outcome', {}).get('id') == 97` (Goal outcome)
   - **EXCLUDE** `event.get('period') == 5` (penalty shootout goals)

2. **For each goal event, extract fields:**
   - `scorer_name`: `event.get('player', {}).get('name')` or `"Unknown"` if missing
   - `minute`: `event.get('minute')` (required)
   - `second`: `event.get('second')` (nullable - None if missing)
   - `is_our_goal`: Check if `event.get('team', {}).get('id') == our_club_statsbomb_id`
     - **Uses `team.id`** (not `possession_team.id` - avoids kick-off team issue)

3. **Return list of goal dicts:**
   ```python
   [
       {
           'scorer_name': str,      # Player name or "Unknown"
           'minute': int,           # Match minute
           'second': int | None,    # Match second (None if missing)
           'is_our_goal': bool      # True if our team scored
       },
       ...
   ]
   ```

**Tests:** 13 tests (all passing)

**Helper Function Tests (7):**
- ✅ Test extracts goals from Shot events with outcome 97 (Goal)
- ✅ Test excludes non-goal shots (Saved, Blocked, Off Target, Post, etc.)
- ✅ Test excludes penalty shootout goals (period 5)
- ✅ Test extracts all fields correctly (scorer_name, minute, second, is_our_goal)
- ✅ Test handles missing player field (uses "Unknown")
- ✅ Test handles missing second field (returns None)
- ✅ Test determines is_our_goal correctly for both teams

**Main Function Tests (6):**
- ✅ Test inserts goals into database with correct fields
- ✅ Test returns 0 for no goals (valid scenario - goalless matches)
- ✅ Test raises error if match not found
- ✅ Test excludes penalty shootout goals (period 5)
- ✅ Test handles missing player field (stores "Unknown" scorer)
- ✅ Test handles missing second field (stores None)

**Manual Testing:**
Interactive CLI to test goal extraction:
```bash
python -m app.services.goal_service
# Prompts for:
# 1. JSON file path (default: data/3869685.json)
# 2. Our club StatsBomb ID (default: 217 for Barcelona)
# 3. Opponent StatsBomb ID (default: 206 for Deportivo Alavés)
# Output: Summary and detailed list of all goals:
#   - Total events and total goals found
#   - Goal counts by team (our goals vs opponent goals)
#   - For each goal: scorer, time, team
```

**Files:**
- `app/services/goal_service.py` ✅ (new file)
- `tests/services/test_goal_service.py` ✅ (new file)

**Key Features:**
- **Uses Iteration 3 Logic**: Gets team IDs same way as `count_goals_from_events()`
- **Pure Processing Helper**: `parse_goals_from_events()` for easy manual testing
- **Excludes Penalty Shootouts**: Period 5 goals filtered out (only regular play)
- **Safe Field Extraction**: Uses `.get()` to handle missing fields
- **Team Identification**: Uses `team.id` (not `possession_team.id`) for accuracy
- **Handles Missing Data**: "Unknown" for missing player, None for missing second
- **Zero Goals Valid**: Returns 0 for goalless matches (not an error)
- **Validation**: Raises error for invalid match_id
- **Manual Testing**: Interactive CLI for verifying extraction with real data

**Field Mapping:**
- **Database Table**: `goals`
- **Fields Stored**:
  - `match_id`: UUID (from function parameter)
  - `scorer_name`: str (player.name or "Unknown")
  - `minute`: int (event.minute)
  - `second`: int | None (event.second, nullable)
  - `is_our_goal`: bool (team.id == our_club_statsbomb_id)

**Business Logic:**
- **Penalty Shootouts**: Excluded (period 5) - only regular play goals counted
- **Team Identification**: Uses `team.id` from event for correct team assignment
- **Missing Player**: Uses "Unknown" as scorer_name (e.g., own goals)
- **Missing Second**: Stored as None (some events lack precise timing)

---

**Tests:**
- Test filter Shot events with outcome="Goal"
- Test extract scorer, time correctly
- Test is_our_goal determination
- Test warning when count mismatch

**Files:**
- `app/services/goal_service.py`
- `tests/services/test_goal_service.py`

---

#### Iteration 9: Match Statistics Calculation ✅ COMPLETED

**Goal:** Calculate and store team statistics from StatsBomb events

**Functions:**

1. **Helper Function (Pure Processing):**
   ```python
   calculate_match_statistics_from_events(
       events: List[dict],
       our_club_statsbomb_id: int,
       opponent_statsbomb_id: int
   ) → Dict[str, Dict]
   ```

2. **Main Function (Database Insertion):**
   ```python
   insert_match_statistics(
       db: Session,
       match_id: UUID,
       events: List[dict],
       our_club_statsbomb_id: int,
       opponent_statsbomb_id: int
   ) → int
   ```

**Parameter Sources:**
- `db`: Database session
- `match_id`: Match ID (UUID) from Iteration 3
- `events`: StatsBomb events array from request body
- `our_club_statsbomb_id`: From Iteration 1 team identification
- `opponent_statsbomb_id`: From Iteration 1 team identification

**Output:**
```python
# Helper returns:
{
    'our_team': {...},      # 18 statistics fields
    'opponent_team': {...}  # 18 statistics fields
}

# Main function returns:
int  # Number of records inserted (always 2)
```

**Processing:**

**Helper Function:**
1. Initialize statistics dictionaries for both teams (all fields 0/None)
2. Filter out penalty shootout events (period 5)
3. Calculate possession by summing event durations where possession_team.id matches
4. Process each event by type:
   - **Shots (type.id = 16)**:
     - Sum xG (shot.statsbomb_xg)
     - Count total shots
     - On target: outcomes [97=Goal, 100=Saved, 116=Saved to Post]
     - Off target: outcomes [98=Off T, 99=Post, 101=Wayward]
     - GK saves: count opponent's shots with outcomes [100, 116]
   - **Passes (type.id = 30)**:
     - Count total and completed passes (no outcome field = completed)
     - Calculate completion rate
     - Count final third passes (location[0] > 80)
     - Count long passes (length > 30)
     - Count crosses (pass.cross = True)
   - **Dribbles (type.id = 14)**:
     - Count total and successful dribbles (outcome.name = "Complete")
   - **Duels (type.id = 4)**:
     - Count tackles (duel.type contains "Tackle")
     - Calculate success % (outcome.id in [4=Won, 15=Success, 16=Success In Play, 17=Success Out])
   - **Interceptions (type.id = 10)**
   - **Ball Recoveries (type.id = 2)**: Exclude recovery_failure = True
5. Calculate percentages (handle division by zero → None)
6. Return both team statistics

**Main Function:**
1. Validate match exists
2. Check for duplicate statistics (raise ValueError if exist)
3. Call helper function to calculate statistics
4. Create 2 MatchStatistics records (our_team + opponent_team)
5. Commit transaction
6. Return 2

**Statistics Calculated (18 total):**
- possession_percentage (Numeric 5,2)
- expected_goals (Numeric 8,6)
- total_shots, shots_on_target, shots_off_target
- goalkeeper_saves
- total_passes, passes_completed, pass_completion_rate (Numeric 5,2)
- passes_in_final_third, long_passes, crosses
- total_dribbles, successful_dribbles
- total_tackles, tackle_success_percentage (Numeric 5,2)
- interceptions, ball_recoveries

**Tests:** 23 tests (all passing)

**Helper Function Tests (15):**
- ✅ Test calculates possession percentage correctly (sum event durations)
- ✅ Test calculates expected goals sum
- ✅ Test categorizes shots by outcome (97, 100, 116 vs 98, 99, 101)
- ✅ Test counts goalkeeper saves from opponent shots (100, 116)
- ✅ Test counts total and completed passes
- ✅ Test counts passes in final third (location[0] > 80)
- ✅ Test counts long passes and crosses
- ✅ Test counts dribbles with success rate
- ✅ Test counts tackles with success percentage (outcome IDs 4, 15, 16, 17)
- ✅ Test counts interceptions and ball recoveries (excludes recovery_failure)
- ✅ Test handles empty events list
- ✅ Test handles division by zero for percentages (returns None)
- ✅ Test returns correct dict structure
- ✅ Test excludes penalty shootout events (period 5)
- ✅ Test handles missing optional fields

**Main Function Tests (8):**
- ✅ Test inserts 2 statistics records into database
- ✅ Test raises error if match not found
- ✅ Test raises error if statistics already exist
- ✅ Test handles empty events list (inserts with 0/None values)
- ✅ Test stores all 18 statistics fields correctly
- ✅ Test commits transaction successfully
- ✅ Test sets team_type correctly ('our_team', 'opponent_team')
- ✅ Test excludes penalty shootout events

**Manual Testing:**
Interactive CLI to test statistics calculation:
```bash
python -m app.services.match_statistics_service
# Prompts for:
# 1. JSON file path (default: data/france771.json)
# 2. Our club StatsBomb ID (default: 779 for Argentina)
# 3. Opponent StatsBomb ID (default: 771 for France)
# Output: Formatted statistics for both teams with all 18 fields
```

**Files:**
- `app/services/match_statistics_service.py` ✅ (helper + main + CLI)
- `tests/services/test_match_statistics_service.py` ✅ (23 tests)

**Key Features:**
- **Pure Processing Helper**: `calculate_match_statistics_from_events()` for easy manual testing
- **Possession Calculation**: Sums event durations (NOT count of sequences) - corrected from initial plan
- **Shot Categorization**: Uses correct outcome IDs [97, 100, 116] for on target vs [98, 99, 101] for off target
- **Goalkeeper Saves**: Counts BOTH outcomes [100=Saved, 116=Saved to Post] - corrected from initial plan
- **Ball Recoveries**: Excludes recovery_failure = True - corrected from initial plan
- **Tackle Success**: Uses outcome IDs [4, 15, 16, 17] - corrected from initial plan
- **Penalty Shootout Exclusion**: Period 5 events filtered out
- **Division by Zero Handling**: Returns None for percentages when denominator is 0
- **Duplicate Prevention**: Raises error if statistics already exist for match
- **Decimal Precision**: Numeric(5,2) for percentages, Numeric(8,6) for xG
- **Manual Testing**: Interactive CLI for verifying calculations with real data

**Critical Corrections from Initial Plan:**
1. **Possession**: Sum duration field (NOT count sequences) per user specification
2. **Shot outcomes**: Added missing outcome IDs 99 (Post) and 116 (Saved to Post)
3. **GK saves**: Count outcomes 100 AND 116 (initial plan only had 100)
4. **Ball recoveries**: Filter where recovery_failure is NOT True
5. **Tackle success**: Use outcome IDs [4, 15, 16, 17] instead of string matching

---

#### Iteration 10: Player Match Statistics ❌

**Goal:** Calculate per-player statistics

**Function:** `calculate_player_match_statistics(match_id: UUID, events: List[dict], players: List[dict]) → int`

**Input:**
- match_id
- Events array
- Our players (with player_id and statsbomb_player_id mapping)

**Output:** Count of player_match_statistics records created

**Processing:**
For each player:
- Filter events by statsbomb_player_id
- Count goals (Shot + outcome="Goal")
- Count assists (Pass + goal_assist=true)
- Sum xG
- Calculate shot statistics
- Calculate pass statistics
- Calculate dribble statistics
- Calculate defensive statistics
- Insert player_match_statistics record

**Tests:**
- Test goals counting per player
- Test assists counting
- Test xG per player
- Test all statistics calculations
- Test record per player in lineup

**Files:**
- `app/services/player_stats_service.py`
- `tests/services/test_player_stats_service.py`

---

#### Iteration 11: Club Season Statistics Update ❌

**Goal:** Recalculate club season aggregates

**Function:** `update_club_season_statistics(club_id: UUID) → UUID`

**Input:** club_id

**Output:** club_stats_id

**Processing:**
- Aggregate all matches for club
- Count wins/draws/losses from matches.result
- Sum goals_scored/goals_conceded
- Sum assists from player_match_statistics
- Count clean_sheets (opponent_score = 0)
- Calculate team_form (last 5 results, most recent first: "WWDLW")
- Calculate averages from match_statistics (team_type='our_team')
- Update club_season_statistics record

**Tests:**
- Test aggregate wins/draws/losses
- Test goals totals
- Test assists summation
- Test clean sheets
- Test team_form calculation
- Test averages calculation

**Files:**
- `app/services/season_stats_service.py`
- `tests/services/test_season_stats_service.py`

---

#### Iteration 12: Player Season Statistics Update ❌

**Goal:** Recalculate player season aggregates

**Function:** `update_player_season_statistics(player_ids: List[UUID]) → int`

**Input:** List of player_ids

**Output:** Count of players updated

**Processing:**
For each player:
- Aggregate all player_match_statistics
- Count matches_played
- Sum goals, assists, xG
- Calculate per-game averages
- Sum totals (passes, dribbles, tackles, etc.)
- Calculate success rates
- Calculate attribute ratings (attacking, technique, tactical, defending, creativity)
- Update player_season_statistics record

**Tests:**
- Test aggregate statistics
- Test per-game calculations
- Test attribute rating formulas
- Test update existing records

**Files:**
- `app/services/season_stats_service.py` (extend)
- `tests/services/test_season_stats_service.py` (extend)

---

#### Final Integration: Match Processor ❌

**Goal:** Orchestrate all iterations into single transaction

**Function:** `process_match_upload(coach_id: UUID, match_data: dict) → dict`

**Input:**
- coach_id (from JWT)
- match_data (opponent_name, match_date, our_score, opponent_score, statsbomb_events)

**Output:**
```python
{
  'success': bool,
  'match_id': UUID,
  'summary': {
    'events_processed': int,
    'goals_extracted': int,
    'players_created': int,
    'players_updated': int,
    'lineups_created': int,
    'warnings': List[str]
  },
  'new_players': List[dict]
}
```

**Processing:**
1. Authenticate coach and get club_id
2. Identify teams (Iteration 1)
3. Get/create opponent club (Iteration 2)
4. Create match record (Iteration 3)
5. Extract our players (Iteration 4)
6. Extract opponent players (Iteration 5)
7. Create match lineups (Iteration 6)
8. Insert events (Iteration 7)
9. Extract goals (Iteration 8)
10. Calculate match statistics (Iteration 9)
11. Calculate player statistics (Iteration 10)
12. Update club season stats (Iteration 11)
13. Update player season stats (Iteration 12)

All wrapped in database transaction (rollback on any error)

**Tests:**
- Integration test with sample data subset
- End-to-end test with full 15946.json
- Test transaction rollback on error
- Test all summary fields populated

**Files:**
- `app/services/match_processor.py`
- `tests/services/test_match_processor.py`
- `tests/test_admin_endpoint.py`

---

#### Admin Endpoint Implementation ❌

**Goal:** Create POST /api/coach/matches endpoint

**Route:** `POST /api/coach/matches`

**Handler:**
```python
@router.post("/matches")
async def upload_match(
    match_data: MatchUploadRequest,
    current_user = Depends(get_current_coach)
):
    result = process_match_upload(current_user.coach_id, match_data.dict())
    return result
```

**Files:**
- `app/api/routes/admin.py`
- `app/schemas/admin.py`

---

#### File Structure

```
app/services/
├── __init__.py
├── team_identifier.py          # Iteration 1
├── opponent_service.py          # Iteration 2
├── match_service.py             # Iteration 3
├── player_service.py            # Iterations 4-5
├── lineup_service.py            # Iteration 6
├── event_service.py             # Iteration 7
├── goal_service.py              # Iteration 8
├── match_stats_service.py       # Iteration 9
├── player_stats_service.py      # Iteration 10
├── season_stats_service.py      # Iterations 11-12
└── match_processor.py           # Final integration

tests/services/
├── __init__.py
├── test_team_identifier.py      # Unit tests for each service
├── test_opponent_service.py
├── test_match_service.py
├── test_player_service.py
├── test_lineup_service.py
├── test_event_service.py
├── test_goal_service.py
├── test_match_stats_service.py
├── test_player_stats_service.py
├── test_season_stats_service.py
└── test_match_processor.py      # Integration tests

app/api/routes/
└── admin.py                     # Endpoint implementation

app/schemas/
└── admin.py                     # Request/response schemas

tests/
└── test_admin_endpoint.py       # End-to-end test
```

---

**Benefits of Iterative TDD Approach:**

1. **Incremental Progress**: 12 clear milestones, each independently testable
2. **Early Validation**: Catch errors at smallest scope before integration
3. **Refactoring Safety**: Tests prevent regressions when improving code
4. **Clear Dependencies**: Each iteration builds on tested, working code
5. **Easier Debugging**: Isolated failures with clear boundaries
6. **Living Documentation**: Tests serve as usage examples
7. **Confidence**: Every feature proven correct before moving forward
8. **Manual Testing**: Verify with real data after each iteration

**Testing Pyramid:**
- **Unit Tests**: Fast, isolated tests for each service function
- **Integration Tests**: Combine related services (e.g., Iterations 1-3)
- **End-to-End Test**: Full match upload with 15946.json (~3000 events)

**Implementation Order:**
Complete Iterations 1-12 sequentially, ensuring all tests pass before proceeding to next iteration

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
│   │   ├── match_lineup.py ✅
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

### Immediate: Phase 3 - Admin Endpoint Processing Logic

**Current Task:** Build data processing incrementally from raw JSON to database tables

**Why this order makes sense:**

- ✅ Phase 1 (Foundation): Auth and core infrastructure complete
- ✅ Phase 2 (Models): All 15 database models created
- ✅ Phase 2.5 (Validation): Schema validated and updated to match UI/API requirements
- → Phase 3 (Admin Processing): Build data processing systematically
- → Phase 4-5 (Implementation): Implement validated endpoints with confidence

With all endpoints validated and schema finalized, we can now build the admin match upload processing logic with confidence that our database structure fully supports all UI requirements.

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
**Models Completed:** 15/15 tables (100%) ✅
**Endpoints Validated:** 18/18 endpoints (100%) ✅

### Phase Status

- **Phase 1 (Foundation):** ✅ COMPLETE
- **Phase 2 (Database Models):** ✅ COMPLETE - All 15 models created
- **Phase 2.5 (Endpoint & Schema Validation):** ✅ COMPLETE - 18/18 endpoints validated, schema changes applied
- **Phase 3 (Admin Endpoint Processing):** ❌ NOT STARTED - Data processing logic & implementation
- **Phase 4 (Coach Endpoints):** ❌ NOT STARTED - 11 endpoints to implement
- **Phase 5 (Player Endpoints):** ❌ NOT STARTED - 7 endpoints to implement

**Current State:** All database models finalized and validated against UI requirements. Schema changes applied successfully. Ready to implement admin match upload processing.

**Implementation Order:**

1. ✅ Phase 1: Foundation (auth, core models)
2. ✅ Phase 2: All database models (schema)
3. ✅ Phase 2.5: Validate endpoints & schema
4. → Phase 3: Admin data processing (current)
5. → Phase 4: Implement coach endpoints
6. → Phase 5: Implement player endpoints

---

**End of Progress Tracker**
