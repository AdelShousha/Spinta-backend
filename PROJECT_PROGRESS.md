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

#### Iteration 2: Opponent Club Creation ❌

**Goal:** Get or create opponent club record

**Function:** `get_or_create_opponent_club(opponent_statsbomb_team_id: int, opponent_name: str, logo_url: str) → UUID`

**Input:**
- `opponent_statsbomb_team_id`: StatsBomb team ID
- `opponent_name`: Opponent name
- `logo_url`: Opponent logo URL (optional)

**Output:** `opponent_club_id` (UUID)

**Processing:**
- Check if exists by `statsbomb_team_id`
- If not found, create new opponent_clubs record
- Return `opponent_club_id`

**Tests:**
- Test create new opponent club
- Test retrieve existing by statsbomb_team_id

**Files:**
- `app/services/opponent_service.py`
- `tests/services/test_opponent_service.py`

---

#### Iteration 3: Match Record Creation ❌

**Goal:** Create match record with our_score/opponent_score/result

**Function:** `create_match_record(...) → UUID`

**Input:**
- club_id, opponent_club_id, match_date
- our_score, opponent_score, opponent_name

**Output:** `match_id` (UUID)

**Processing:**
- Calculate result: 'W' if our_score > opponent_score, 'L' if <, 'D' if =
- Insert into matches table
- Return match_id

**Tests:**
- Test create with Win result (our_score > opponent_score)
- Test create with Loss result (our_score < opponent_score)
- Test create with Draw result (our_score = opponent_score)
- Test opponent_name denormalization

**Files:**
- `app/services/match_service.py`
- `tests/services/test_match_service.py`

---

#### Iteration 4: Player Extraction (Our Team) ❌

**Goal:** Create/update our players from Starting XI lineup

**Function:** `extract_our_players(lineup: List[dict], club_id: UUID) → dict`

**Input:**
- Starting XI lineup (11 players)
- club_id

**Output:**
```python
{
  'player_ids': List[UUID],
  'new_players': List[{'name': str, 'jersey': int, 'invite_code': str}]
}
```

**Processing:**
- For each player in lineup:
  - Check if exists by (club_id, statsbomb_player_id)
  - If exists: update jersey/position
  - Else: check by (club_id, name OR jersey)
    - If exists: link statsbomb_player_id
    - Else: create new player with invite code
  - Initialize player_season_statistics if new

**Tests:**
- Test create new player with invite code
- Test update existing by statsbomb_player_id
- Test update existing by name/jersey
- Test invite code format (XXX-####)
- Test invite code uniqueness
- Test initialize season stats

**Files:**
- `app/services/player_service.py`
- `tests/services/test_player_service.py`

---

#### Iteration 5: Opponent Players Extraction ❌

**Goal:** Create/update opponent players

**Function:** `extract_opponent_players(lineup: List[dict], opponent_club_id: UUID) → List[UUID]`

**Input:**
- Opponent Starting XI lineup
- opponent_club_id

**Output:** List of opponent_player_ids

**Processing:**
- For each opponent player:
  - Check if exists by (opponent_club_id, statsbomb_player_id)
  - If not: check by (opponent_club_id, name, jersey)
  - If exists: update jersey/position
  - Else: create new opponent_players record

**Tests:**
- Test create new opponent player
- Test update existing by statsbomb_player_id
- Test update existing by name/jersey
- Test duplicate detection

**Files:**
- `app/services/player_service.py` (extend)
- `tests/services/test_player_service.py` (extend)

---

#### Iteration 6: Match Lineups Creation ❌

**Goal:** Create lineup entries for both teams

**Function:** `create_match_lineups(match_id: UUID, our_lineup: List, opp_lineup: List) → int`

**Input:**
- match_id
- Our team lineup data (11 players with player_ids)
- Opponent lineup data (11 players with opponent_player_ids)

**Output:** Count of lineups created (should be 22)

**Processing:**
- For each our player: insert with team_type='our_team', player_id set
- For each opponent player: insert with team_type='opponent_team', opponent_player_id set
- Denormalize player_name, jersey_number, position

**Tests:**
- Test create 11 our_team lineups
- Test create 11 opponent_team lineups
- Test denormalized fields populated
- Test total count = 22

**Files:**
- `app/services/lineup_service.py`
- `tests/services/test_lineup_service.py`

---

#### Iteration 7: Events Storage ❌

**Goal:** Bulk insert ~3000 events into database

**Function:** `insert_events(match_id: UUID, events: List[dict]) → int`

**Input:**
- match_id
- Full StatsBomb events array

**Output:** Count of events inserted

**Processing:**
- Batch events (500 per query for performance)
- For each event:
  - Extract key fields for indexing (player_id, team_id, type, minute, etc.)
  - Store full JSON in event_data (JSONB)
- Bulk insert

**Tests:**
- Test bulk insert performance
- Test JSONB storage of event_data
- Test extract key fields correctly
- Test handle events without player (Half Start, etc.)
- Test batch size = 500

**Files:**
- `app/services/event_service.py`
- `tests/services/test_event_service.py`

---

#### Iteration 8: Goals Extraction ❌

**Goal:** Extract goals from Shot events

**Function:** `extract_goals(match_id: UUID, events: List[dict], our_team_name: str) → dict`

**Input:**
- match_id
- Events array
- our_team_name (for determining is_our_goal)

**Output:**
```python
{
  'goals_count': int,
  'warnings': List[str]  # If extracted count != admin input
}
```

**Processing:**
- Filter Shot events where shot.outcome.name == "Goal"
- For each goal:
  - Extract scorer_name, minute, second
  - Determine is_our_goal (team_name == our_team_name)
  - Insert into goals table
- Validate count matches admin input scores

**Tests:**
- Test filter Shot events with outcome="Goal"
- Test extract scorer, time correctly
- Test is_our_goal determination
- Test warning when count mismatch

**Files:**
- `app/services/goal_service.py`
- `tests/services/test_goal_service.py`

---

#### Iteration 9: Match Statistics Calculation ❌

**Goal:** Calculate and store team statistics

**Function:** `calculate_match_statistics(match_id: UUID, events: List[dict], teams: dict) → List[UUID]`

**Input:**
- match_id
- Events array
- Team names (our_team_name, opponent_team_name)

**Output:** 2 statistics_ids (our_team, opponent_team)

**Processing:**
For each team:
- Calculate possession % (sum event durations / total)
- Sum xG (shot.statsbomb_xg)
- Count shots (total, on target, off target)
- Count goalkeeper saves (opponent shots with outcome="Saved")
- Calculate pass statistics (total, completed, completion %)
- Count passes in final third (location[0] > 80)
- Count long passes (length > 30)
- Count crosses
- Calculate dribble statistics
- Calculate tackle statistics
- Count interceptions
- Count ball recoveries
- Insert match_statistics record

**Tests:**
- Test possession calculation
- Test xG summation
- Test shots counting by outcome
- Test pass statistics
- Test defensive statistics
- Test create 2 records (our_team, opponent_team)

**Files:**
- `app/services/match_stats_service.py`
- `tests/services/test_match_stats_service.py`

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
