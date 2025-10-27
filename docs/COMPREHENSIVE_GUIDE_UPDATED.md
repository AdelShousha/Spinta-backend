# 📚 SPINTA Backend - Complete Technical Deep Dive (UPDATED)

## ⚠️ MAJOR UPDATES IMPLEMENTED

This version includes significant architectural changes:
- ✅ Per-player unique invite codes system
- ✅ Admin panel-only match creation (coaches cannot create matches)
- ✅ Simplified statistics tables matching UI exactly
- ✅ Player-specific training plans
- ✅ Metric system (height in cm)
- ✅ Renamed teams → opponent_clubs for clarity

---

## Table of Contents
1. [Database Tables - Complete Breakdown](#database-tables)
2. [Database Indexes - Performance Optimization](#database-indexes)
3. [API Endpoints - UI Screen Mapping](#api-endpoints)
4. [Data Flow - Queries & Operations](#data-flow)
5. [Admin Panel Integration](#admin-panel-integration)

---

# 🗄️ DATABASE TABLES - COMPLETE BREAKDOWN

## 1. USER MANAGEMENT TABLES

### Table: `users`
**Purpose:** Central user table for both coaches and players. Stores authentication credentials and basic user information.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `user_id` | UUID (PK) | Unique identifier for each user | `a1b2c3d4-...` |
| `email` | VARCHAR(255) UNIQUE | Login email, must be unique | `john@email.com` |
| `password_hash` | VARCHAR(255) | Encrypted password (never store plain text) | `$2b$12$...` |
| `user_type` | VARCHAR(20) | Either 'coach' or 'player' | `coach` |
| `full_name` | VARCHAR(255) | User's full name | `John Smith` |
| `created_at` | TIMESTAMP | When account was created | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last time account was updated | `2025-01-20 14:22:00` |

**Why these columns:**
- `user_id`: UUID ensures global uniqueness, better than auto-incrementing integers for distributed systems
- `email`: Used for login, must be unique
- `password_hash`: Security best practice - never store plain passwords
- `user_type`: Determines if user sees coach or player interface
- Timestamps: Audit trail for when accounts are created/modified

**Relationships:**
- One user → One coach (via coaches.coach_id)
- One user → One player (via players.player_id)

---

### Table: `coaches`
**Purpose:** Stores coach-specific information. Extends the users table with coach details.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `coach_id` | UUID (PK, FK→users) | Links to users table, identifies coach | Same as user_id |
| `birth_date` | DATE | Coach's date of birth | `1985-06-15` |
| `gender` | VARCHAR(20) | Coach's gender | `Male` |

**REMOVED COLUMNS:**
- ❌ `profile_image_url` - Coach signup now only requires club logo, not coach photo

**Why these columns:**
- `coach_id`: Primary key that also references users table (one-to-one relationship)
- `birth_date`: For age verification, demographics
- No coach photo - club logo is used instead throughout the UI

**UI Usage:**
- Profile screen shows coach name, birth date, gender
- Club logo is shown (from clubs table), not coach photo
- Coach signup screen collects only basic info + club details

---

### Table: `players`
**Purpose:** Stores player-specific information. Extends users table with athlete details.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `player_id` | UUID (PK, FK→users) | Links to users table | Same as user_id |
| `jersey_number` | INTEGER | Player's jersey/shirt number | `10` |
| `height` | INTEGER | Player height in centimeters | `180` (180 cm) |
| `birth_date` | DATE | Player's date of birth | `2008-03-20` |
| `position` | VARCHAR(50) | Playing position | `Forward` |
| `profile_image_url` | TEXT | URL to profile picture | `https://...image.jpg` |
| `club_id` | UUID (FK→clubs) | Which club they belong to | Links to clubs table |
| `is_linked` | BOOLEAN | Whether player is linked via invite code | `true` or `false` |
| `linked_at` | TIMESTAMP | When they joined the club | `2025-01-15 10:30:00` |

**CHANGED COLUMNS:**
- ✅ `height`: Changed from VARCHAR(20) "5'11"" → INTEGER `180` (centimeters)
- ❌ `weight`: REMOVED - no longer collected

**Why these columns:**
- Athletic measurements (`height`, `position`) are essential for player profiles
- `height` in cm: Universal metric system, easier to validate and compare
- `jersey_number`: Critical for invite code matching system (see below)
- `is_linked`: Players exist in database before creating accounts (from match data)
- `linked_at`: Audit trail for when player claimed their invite code

**Player Linking System:**
1. Admin processes match → creates unlinked player records with invite codes
2. Real player signs up → enters unique invite code + jersey number
3. System validates jersey number match → links account to existing player data
4. All historical statistics now belong to authenticated player

**UI Usage:**
- Player profile screen displays: name, jersey #, height (in cm), position
- Player signup: collects height as integer (100-250 cm range validation)
- "Unlinked Players" list in coach view shows players waiting to join

---

## 2. CLUB MANAGEMENT TABLES

### Table: `clubs`
**Purpose:** Represents a football club/team managed by a coach.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `club_id` | UUID (PK) | Unique identifier for club | `a1b2c3d4-...` |
| `club_name` | VARCHAR(255) | Official club name | `Thunder United FC` |
| `coach_id` | UUID (FK→coaches) | Which coach manages this club | Links to coaches |
| `logo_url` | TEXT | URL to club logo/badge | `https://...logo.png` |
| `country` | VARCHAR(100) | Country where club is based | `United States` |
| `age_group` | VARCHAR(20) | Age category of team | `U16` (Under 16) |
| `stadium` | VARCHAR(255) | Home stadium name | `City Stadium` |
| `created_at` | TIMESTAMP | When club was created | `2025-01-15 10:30:00` |

**REMOVED COLUMNS:**
- ❌ `invite_code` - Moved to per-player system (see player_invite_codes table below)

**Why these columns:**
- `club_name`: Main identifier displayed everywhere
- `coach_id`: One club has one coach (one-to-one relationship)
- `logo_url`: Displayed on dashboard, match cards, everywhere (also used for coach profile)
- `age_group`: Important for youth football - teams are organized by age

**UI Usage:**
- Club overview screen shows club name, logo, statistics
- Club signup screen collects this data
- Club logo appears throughout app (dashboards, match cards, coach profile)

---

### Table: `player_invite_codes` ⭐ NEW TABLE
**Purpose:** Per-player unique invite codes for linking player accounts to match data.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `invite_code_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `club_id` | UUID (FK→clubs) | Which club this player belongs to | Links to clubs |
| `player_name` | VARCHAR(255) | Player name from match lineup data | `Marcus Silva` |
| `jersey_number` | INTEGER | Jersey number from match data | `10` |
| `position` | VARCHAR(50) | Position from match data | `Forward` |
| `invite_code` | VARCHAR(10) UNIQUE | Unique code for this player | `MRC-1827` |
| `is_used` | BOOLEAN | Has player claimed this code? | `false` |
| `linked_player_id` | UUID (FK→players) | Player account after linking | NULL or player_id |
| `created_at` | TIMESTAMP | When code was generated | `2025-01-15 10:30:00` |
| `linked_at` | TIMESTAMP | When player claimed code | NULL or timestamp |

**Unique Constraint:** `invite_code` must be globally unique

**Why this table:**
- **Per-player codes**: Each player gets their own unique invite code
- **Data pre-population**: Players exist in database before creating accounts
- **Jersey number validation**: Ensures correct player claims correct data
- **Statistics linking**: Connects StatsBomb player data to authenticated users

**Lifecycle:**
1. **Admin processes match:**
   - Extracts lineup (player names + jersey numbers)
   - FOR EACH player in coach's team:
     - Generate unique invite code (e.g., first 3 letters of name + 4 random digits)
     - INSERT INTO player_invite_codes with `is_used = FALSE`

2. **Coach views unlinked players:**
   - Query: `SELECT * FROM player_invite_codes WHERE club_id = ? AND is_used = FALSE`
   - Shows: Player name, jersey #, invite code
   - Coach shares code with that specific player

3. **Player signup:**
   - Player enters invite code
   - System validates code exists
   - Player enters jersey number
   - System validates: `jersey_number = player_invite_codes.jersey_number`
   - If match: Create player account, link to code
   - UPDATE: `is_used = TRUE`, `linked_player_id = new_player_id`

**UI Usage:**
- **Coach View - Unlinked Players List:**
```
┌──────────────────┬────────┬───────────┬────────────┐
│ Player Name      │ Jersey │ Code      │ Statistics │
├──────────────────┼────────┼───────────┼────────────┤
│ Marcus Silva     │ 10     │ MRC-1827  │ ✅ Visible │
│ John Smith       │ 7      │ JHN-4523  │ ✅ Visible │
│ Alex Johnson     │ 3      │ ALX-9012  │ ✅ Visible │
└──────────────────┴────────┴───────────┴────────────┘

⚠️ Training cannot be assigned to unlinked players
```

- **Player Signup Flow:**
```
Step 1: Enter Invite Code
  [MRC-1827]
  
Step 2: Confirm Your Details
  Name from match data: Marcus Silva
  Enter your jersey number: [10]
  
  ✅ Match! Proceeding to account creation...
```

---

### Table: `opponent_clubs`
**Purpose:** Represents opponent teams. Separate from clubs because opponents don't have accounts.

**RENAMED FROM:** `teams` → `opponent_clubs` for clarity

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `opponent_club_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `club_name` | VARCHAR(255) | Opponent club name | `City Strikers` |
| `logo_url` | TEXT | Opponent team logo (optional) | `https://...logo.png` |
| `stadium_name` | VARCHAR(255) | Opponent's home stadium | `Riverside Arena` |
| `created_at` | TIMESTAMP | When added to system | `2025-01-15 10:30:00` |

**ADDED COLUMNS:**
- ✅ `stadium_name` - Where opponent plays home matches

**Why separate from clubs:**
- Opponent teams don't have coaches in the system
- Don't need all the club metadata (age group, invite codes, etc.)
- Simpler structure for opponents

**UI Usage:**
- Match cards show opponent name and logo
- Match detail screen shows opponent info and stadium
- Admin panel: Creates opponent clubs when processing matches

---

## 3. MATCH MANAGEMENT TABLES

### Table: `matches`
**Purpose:** Represents a single football match between the club and an opponent.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `match_id` | UUID (PK) | Unique identifier for match | `a1b2c3d4-...` |
| `club_id` | UUID (FK→clubs) | Which club played this match | Links to clubs |
| `opponent_club_id` | UUID (FK→opponent_clubs) | Reference to opponent | Links to opponent_clubs |
| `opponent_name` | VARCHAR(255) | Opponent name (denormalized for speed) | `City Strikers` |
| `match_date` | DATE | Date of match | `2025-10-08` |
| `match_time` | TIME | Kickoff time | `15:30:00` |
| `location` | VARCHAR(255) | Where match was played | `City Stadium` |
| `stadium_name` | VARCHAR(255) | Stadium name (if away match) | `Riverside Arena` |
| `home_score` | INTEGER | Goals scored by home team | `3` |
| `away_score` | INTEGER | Goals scored by away team | `2` |
| `is_home_match` | BOOLEAN | True if club was home team | `true` |
| `created_at` | TIMESTAMP | When match record was created | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last update | `2025-01-15 16:45:00` |

**REMOVED COLUMNS:**
- ❌ `match_status` - No longer needed (matches only inserted after completion)
- ❌ `video_url` - Not stored in app database (handled by admin panel)
- ❌ `statsbomb_match_id` - Temporary field, removed

**ADDED COLUMNS:**
- ✅ `stadium_name` - For away matches, stores opponent's stadium

**Why these columns:**
- `opponent_name`: Denormalized (duplicated from opponent_clubs table) for faster queries - avoids JOIN
- `stadium_name`: Only populated if `is_home_match = FALSE`
- `is_home_match`: Determines which team's stats go in "home" vs "away" columns

**Critical Change - Match Creation:**
- **OLD:** Coaches create matches in mobile app
- **NEW:** Only admin panel can create matches
- **Result:** Matches appear as read-only in coach app

**UI Usage:**
- Match list screen: Shows opponent, date, score, result (W/D/L)
- Match detail screen: Shows all match info
- Coaches CANNOT create, edit, or delete matches

**Data Flow:**
1. Admin uploads video to admin panel
2. CV processes video → generates event data
3. Admin fills match details form (date, score, location, stadium if away)
4. Admin submits → INSERT into matches table
5. Match appears in coach's app automatically

---

### Table: `events`
**Purpose:** Stores every action/event that happens in a match (passes, shots, tackles, etc.) with timestamps. This is the raw event-level data from StatsBomb format.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `event_id` | UUID (PK) | Unique identifier (from StatsBomb JSON) | `f89cbb1a-16e9-...` |
| `match_id` | UUID (FK→matches) | Which match this event belongs to | Links to matches |
| `event_index` | INTEGER | Sequential order of events in match | `600` (600th event) |
| `event_type_id` | INTEGER | StatsBomb type ID | `30` |
| `event_type_name` | VARCHAR(50) | Human-readable event type | `Pass`, `Shot`, `Tackle` |
| `period` | INTEGER | Which half/period | `1` (first half), `2` (second half) |
| `timestamp` | VARCHAR(20) | Exact time in match | `00:12:45.123` |
| `minute` | INTEGER | Minute on the clock | `12` |
| `second` | INTEGER | Second within that minute | `45` |
| `statsbomb_team_id` | INTEGER | StatsBomb team ID | `217` |
| `team_name` | VARCHAR(255) | Team that performed the event | `Barcelona` |
| `statsbomb_player_id` | INTEGER | StatsBomb player ID | `5470` |
| `player_name` | VARCHAR(255) | Player who performed the event | `Ivan Rakitić` |
| `position_id` | INTEGER | StatsBomb position ID | `11` |
| `position_name` | VARCHAR(100) | Player's position during event | `Left Defensive Midfield` |
| `duration` | DECIMAL(8,6) | How long event lasted (seconds) | `1.412834` |
| `possession` | INTEGER | Possession sequence number | `19` |
| `play_pattern_id` | INTEGER | Type of play | `1` |
| `play_pattern_name` | VARCHAR(50) | Description of play type | `Regular Play`, `Corner`, etc. |
| `outcome` | VARCHAR(100) | General outcome | `Complete`, `Incomplete`, `Goal` |
| `outcome_type` | VARCHAR(50) | Specific outcome type | For shots: `Goal`, `Saved` |

**RENAMED COLUMNS:**
- ✅ `player_id` → `statsbomb_player_id` (eliminates confusion with players.player_id)
- ✅ `team_id` → `statsbomb_team_id` (clarifies this is StatsBomb's ID)

**Pass-Specific Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `pass_recipient_id` | INTEGER | StatsBomb ID of recipient | `5211` |
| `pass_recipient_name` | VARCHAR(255) | Recipient's name | `Jordi Alba Ramos` |
| `pass_length` | DECIMAL(6,2) | Distance in meters | `14.58` |
| `pass_height` | VARCHAR(50) | Height of pass | `Ground Pass`, `High Pass` |
| `pass_body_part` | VARCHAR(50) | Body part used | `Right Foot`, `Head` |
| `pass_type` | VARCHAR(50) | Type of pass | `Corner`, `Free Kick`, `Throw-in` |

**Shot-Specific Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `shot_outcome` | VARCHAR(50) | What happened to shot | `Goal`, `Saved`, `Off Target`, `Blocked` |
| `shot_body_part` | VARCHAR(50) | Body part used | `Right Foot`, `Head` |
| `shot_type` | VARCHAR(50) | Type of shot | `Open Play`, `Penalty`, `Free Kick` |
| `shot_technique` | VARCHAR(50) | How shot was taken | `Normal`, `Volley`, `Half Volley` |

**Defensive Event Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `dribble_outcome` | VARCHAR(50) | Result of dribble | `Complete`, `Incomplete` |
| `tackle_outcome` | VARCHAR(50) | Result of tackle | `Won`, `Lost` |
| `interception_outcome` | VARCHAR(50) | Result of interception | `Success`, `Lost` |

**Full Event Data:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `event_data` | JSONB | Complete original event JSON | Full StatsBomb event object |
| `created_at` | TIMESTAMP | When stored in database | `2025-01-15 10:30:00` |

**Why these columns:**
- **Extracted fields** (`event_type_name`, `player_name`, etc.): Pre-extracted for fast querying without parsing JSON
- **Renamed IDs**: `statsbomb_player_id` and `statsbomb_team_id` make it clear these are external IDs, not our database IDs
- **Timestamp fields** (`period`, `minute`, `second`, `timestamp`): Enable queries like "what happened in first 20 minutes?"
- **Event-specific fields** (pass_*, shot_*, etc.): Make common queries fast without JSON parsing
- **JSONB `event_data`**: Preserves complete original data for future features

**Linking Events to Players:**
- Events reference players by `player_name` (from StatsBomb)
- When player links account via invite code, we can query:
  ```sql
  -- Get player's real ID from invite code
  SELECT linked_player_id 
  FROM player_invite_codes 
  WHERE player_name = 'Marcus Silva' AND is_used = TRUE
  
  -- Then query events
  SELECT * FROM events WHERE player_name = 'Marcus Silva'
  ```

---

### Table: `goals`
**Purpose:** Extracted goals for easy access. Subset of events table but optimized for quick goal queries.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `goal_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `match_id` | UUID (FK→matches) | Which match | Links to matches |
| `event_id` | UUID (FK→events) | Reference to shot event | Links to events |
| `scorer_statsbomb_player_id` | INTEGER | StatsBomb player ID | `5470` |
| `scorer_name` | VARCHAR(255) | Who scored | `Ivan Rakitić` |
| `assist_statsbomb_player_id` | INTEGER | StatsBomb player ID of assister | `5211` |
| `assist_name` | VARCHAR(255) | Who assisted (if any) | `Jordi Alba Ramos` |
| `period` | INTEGER | Which half | `1` or `2` |
| `minute` | INTEGER | Minute of goal | `12` |
| `second` | INTEGER | Second within minute | `45` |
| `timestamp` | VARCHAR(20) | Exact time | `00:12:45.123` |
| `goal_type` | VARCHAR(50) | How goal was scored | `Open Play`, `Penalty`, `Free Kick` |
| `body_part` | VARCHAR(50) | Body part used | `Right Foot`, `Head` |
| `statsbomb_team_id` | INTEGER | StatsBomb team ID | `217` |
| `team_name` | VARCHAR(255) | Which team scored | `Barcelona` |
| `created_at` | TIMESTAMP | When stored | `2025-01-15 10:30:00` |

**RENAMED COLUMNS:**
- ✅ `scorer_player_id` → `scorer_statsbomb_player_id`
- ✅ `assist_player_id` → `assist_statsbomb_player_id`
- ✅ `team_id` → `statsbomb_team_id`

**Why separate goals table:**
- **Performance**: Much faster to query 5 goals than search through 3000+ events
- **Assist detection**: Pre-calculated by finding the pass before the shot
- **UI convenience**: Match detail screen shows goals without complex queries

**How assists are found:**
When processing a goal event, the system looks backwards through recent events to find the last pass to the scorer. That pass's player becomes the assist.

---

## 4. STATISTICS TABLES

### Table: `match_statistics`
**Purpose:** Aggregated team-level statistics for a match. Pre-calculated from events table. **UPDATED to match UI exactly.**

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `match_id` | UUID (FK→matches) | Which match | Links to matches |
| `team_type` | VARCHAR(10) | 'home' or 'away' | `home` |

**General Match Stats:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `possession_percentage` | DECIMAL(5,2) | % of time with ball | `58.50` (58.5%) |
| `expected_goals` | DECIMAL(5,3) | xG metric | `2.450` |
| `goalkeeper_saves` | INTEGER | Saves made by goalkeeper | `4` |

**Shooting Stats:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_shots` | INTEGER | Total shot attempts | `14` |
| `shots_on_target` | INTEGER | Shots on goal | `8` |
| `shots_off_target` | INTEGER | Shots missing goal | `3` |

**Passing Stats:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_passes` | INTEGER | Total pass attempts | `487` |
| `passes_completed` | INTEGER | Successful passes | `423` |
| `pass_completion_rate` | DECIMAL(5,2) | Success rate (calculated) | `86.86` (86.86%) |
| `passes_in_final_third` | INTEGER | Passes in attacking third | `145` |
| `long_passes` | INTEGER | Passes > 15m | `137` |
| `crosses` | INTEGER | Cross attempts | `18` |

**Dribbling Stats:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_dribbles` | INTEGER | Dribble attempts | `25` |
| `successful_dribbles` | INTEGER | Successful dribbles | `18` |
| `dribble_success_rate` | DECIMAL(5,2) | Success percentage (calculated) | `72.00` |

**Defensive Stats:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_tackles` | INTEGER | Tackle attempts | `16` |
| `tackle_success_percentage` | DECIMAL(5,2) | Success percentage | `75.00` |
| `interceptions` | INTEGER | Interceptions made | `11` |
| `ball_recoveries` | INTEGER | Ball recoveries | `48` |

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `created_at` | TIMESTAMP | When calculated | `2025-01-15 10:30:00` |

**REMOVED COLUMNS:**
- ❌ `fouls_committed`, `fouls_won`, `yellow_cards`, `red_cards` - Not shown in UI

**Unique Constraint:** `(match_id, team_type)` - One home, one away record per match

**Calculation Formula:**
```sql
-- Calculated fields (not stored, computed when needed):
pass_completion_rate = (passes_completed / total_passes) * 100
dribble_success_rate = (successful_dribbles / total_dribbles) * 100
tackle_success_percentage = (tackles_won / total_tackles) * 100
```

**UI Usage - Match Detail Screen Sections:**

1. **Overview Stats:**
   - Ball Possession, Expected Goals (xG), Total Shots, Goalkeeper Saves, Total Passes, Total Dribbles

2. **Shooting:**
   - Total Shots, Shots on Target, Shots off Target, Total Dribbles, Successful Dribbles

3. **Passing:**
   - Total Passes, Passes Completed, Passes in Final Third, Long Passes, Crosses

4. **Defense:**
   - Tackle Success %, Total Tackles, Interceptions, Ball Recoveries, Goalkeeper Saves

---

### Table: `player_match_statistics`
**Purpose:** Individual player performance in a specific match. Pre-calculated from events table. **SIMPLIFIED to essential stats only.**

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `match_id` | UUID (FK→matches) | Which match | Links to matches |
| `player_id` | UUID (FK→players) | Which player | Links to players |

**Match Summary:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `goals` | INTEGER | Goals scored | `2` |
| `assists` | INTEGER | Assists made | `1` |

**Attacking Threat:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `expected_goals` | DECIMAL(5,3) | xG for player | `1.800` |
| `shots` | INTEGER | Shot attempts | `6` |
| `shots_on_target` | INTEGER | Shots on goal | `4` |
| `total_dribbles` | INTEGER | Dribble attempts | `9` |
| `successful_dribbles` | INTEGER | Successful dribbles | `7` |

**Ball Retention:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_passes` | INTEGER | Pass attempts | `52` |
| `completed_passes` | INTEGER | Successful passes | `46` |
| `short_passes` | INTEGER | Short pass attempts | `38` |
| `long_passes` | INTEGER | Long pass attempts | `14` |
| `final_third_passes` | INTEGER | Passes in attacking third | `18` |
| `crosses` | INTEGER | Cross attempts | `5` |

**Defensive Work:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `tackles` | INTEGER | Tackle attempts | `5` |
| `tackle_success_rate` | DECIMAL(5,2) | Success percentage | `80.00` |
| `interceptions` | INTEGER | Interceptions made | `5` |
| `interception_success_rate` | DECIMAL(5,2) | Success percentage | `83.00` |

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `created_at` | TIMESTAMP | When calculated | `2025-01-15 10:30:00` |

**REMOVED COLUMNS:**
- ❌ `minutes_played`, `rating`, `touches_in_box`, `pass_accuracy`, `key_passes`, `dispossessed`
- ❌ **Physical section:** `distance_covered`, `sprints`, `duels_won`, `duels_lost`, `aerial_duels_won`, `aerial_duels_lost`
- ❌ **Discipline section:** `yellow_cards`, `red_cards`
- ❌ Defensive extras: `tackles_won`, `tackles_lost`, `blocks`, `clearances`, `fouls_committed`, `fouls_won`

**Unique Constraint:** `(match_id, player_id)` - Each player appears once per match

**Why simplified:**
- Matches exactly what UI displays
- Faster calculations (fewer stats to compute)
- Easier to maintain

---

### Table: `player_season_statistics`
**Purpose:** Aggregated player statistics across all matches. **NO SEASON TRACKING - single record per player.**

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `player_id` | UUID (FK→players) | Which player | Links to players |
| `club_id` | UUID (FK→clubs) | Which club | Links to clubs |

**Summary:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `matches_played` | INTEGER | Total matches | `22` |

**Core Stats:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `goals` | INTEGER | Total goals | `12` |
| `assists` | INTEGER | Total assists | `7` |
| `expected_goals` | DECIMAL(6,3) | Total xG | `10.800` |
| `shots_per_game` | DECIMAL(5,2) | Average shots per match | `4.18` |
| `shots_on_target_per_game` | DECIMAL(5,2) | Average shots on target | `2.82` |
| `total_passes` | INTEGER | Total passes | `1144` |
| `passes_completed` | INTEGER | Successful passes | `995` |
| `total_dribbles` | INTEGER | Total dribbles | `158` |
| `successful_dribbles` | INTEGER | Successful dribbles | `118` |
| `tackles` | INTEGER | Total tackles | `45` |
| `tackle_success_rate` | DECIMAL(5,2) | Tackle success % | `78.00` |
| `interceptions` | INTEGER | Total interceptions | `32` |
| `interception_success_rate` | DECIMAL(5,2) | Interception success % | `85.00` |

**Attributes (1-100 ratings):**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `attacking_rating` | INTEGER | Attacking ability | `82` |
| `technique_rating` | INTEGER | Technical skill | `64` |
| `tactical_rating` | INTEGER | Tactical awareness | `52` |
| `defending_rating` | INTEGER | Defensive ability | `28` |
| `creativity_rating` | INTEGER | Creative play | `85` |

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `created_at` | TIMESTAMP | When first calculated | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last update | `2025-10-20 14:22:00` |

**REMOVED COLUMNS:**
- ❌ `season` - No season tracking (app is single-season only)
- ❌ `average_rating`, `minutes_played`
- ❌ Many other stats (kept only those listed above)

**Unique Constraint:** `player_id` (only one record per player)

**Attribute Calculation (from stats):**
```javascript
attacking_rating = min(100, max(0, 
  (goals * 5) + (shots_per_game * 2) + (expected_goals * 3)
))

technique_rating = min(100, max(0,
  (passes_completed / total_passes * 100 * 0.6) + 
  (successful_dribbles / total_dribbles * 100 * 0.4)
))

tactical_rating = min(100, max(0,
  (assists * 8) + (shots_on_target_per_game * 5)
))

defending_rating = min(100, max(0,
  (tackle_success_rate * 0.5) + 
  (interception_success_rate * 0.3) +
  (tackles * 0.5)
))

creativity_rating = min(100, max(0,
  (assists * 10) + (successful_dribbles * 0.4)
))
```

**UI Usage:**
- Player profile "Summary" tab
- Radar chart visualization (uses 5 attribute ratings)
- Stats comparison between players

---

### Table: `club_season_statistics`
**Purpose:** Aggregated team-level statistics. **NO SEASON TRACKING - single record per club.**

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `club_id` | UUID (FK→clubs) | Which club | Links to clubs |

**Record:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `matches_played` | INTEGER | Total matches | `22` |
| `wins` | INTEGER | Matches won | `14` |
| `draws` | INTEGER | Matches drawn | `4` |
| `losses` | INTEGER | Matches lost | `4` |

**Goals:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `goals_scored` | INTEGER | Total goals scored | `45` |
| `goals_conceded` | INTEGER | Total goals conceded | `23` |
| `total_assists` | INTEGER | Total assists | `32` |
| `total_clean_sheets` | INTEGER | Matches without conceding | `8` |

**Form:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `team_form` | VARCHAR(50) | Last 10 results as string | `WWDWLWWDLW` |

**Averages (per match):**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `avg_goals_per_match` | DECIMAL(5,2) | Average goals scored | `2.05` |
| `avg_xg_per_match` | DECIMAL(5,2) | Average xG | `1.90` |
| `avg_goals_conceded_per_match` | DECIMAL(5,2) | Avg goals conceded | `1.05` |
| `avg_possession_percentage` | DECIMAL(5,2) | Average possession % | `58.00` |
| `avg_total_shots` | DECIMAL(5,2) | Average shots | `14.50` |
| `avg_shots_on_target` | DECIMAL(5,2) | Avg shots on target | `8.20` |
| `avg_total_passes` | DECIMAL(5,2) | Average passes | `487.00` |
| `pass_completion_rate` | DECIMAL(5,2) | Overall pass accuracy | `87.00` |
| `avg_final_third_passes` | DECIMAL(5,2) | Avg passes in final third | `145.00` |
| `avg_crosses` | DECIMAL(5,2) | Average crosses | `18.00` |
| `avg_dribbles` | DECIMAL(5,2) | Average dribbles | `12.50` |
| `avg_successful_dribbles` | DECIMAL(5,2) | Avg successful dribbles | `8.20` |
| `avg_tackles` | DECIMAL(5,2) | Average tackles | `16.30` |
| `tackle_success_rate` | DECIMAL(5,2) | Overall tackle success | `72.00` |
| `avg_interceptions` | DECIMAL(5,2) | Average interceptions | `11.80` |
| `interception_success_rate` | DECIMAL(5,2) | Interception success | `85.00` |
| `avg_ball_recoveries` | DECIMAL(5,2) | Avg ball recoveries | `48.50` |
| `avg_saves_per_match` | DECIMAL(5,2) | Avg goalkeeper saves | `3.20` |

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `created_at` | TIMESTAMP | When first calculated | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last update | `2025-10-20 14:22:00` |

**REMOVED COLUMNS:**
- ❌ `season` - No season tracking
- ❌ `standing` - League position not tracked
- ❌ `goal_difference` - Can be calculated from goals_scored - goals_conceded

**CHANGED:**
- ✅ `team_form`: Changed from JSONB array `["W","W","D"]` to VARCHAR `WWDWLWWDLW`
  - Simpler to work with
  - Easier to display in UI
  - Just a string of W/D/L characters

**Unique Constraint:** `club_id` (only one record per club)

**Why team_form as VARCHAR:**
- Easier string manipulation
- No JSON parsing needed
- Display directly in UI: `W W D W L W W D L W`
- Update logic: `team_form = 'W' + LEFT(team_form, 9)` (prepend new result, keep last 10)

**UI Usage:**
- Club overview dashboard shows all these stats
- "Team Form" section shows form string as colored badges
- Statistics tab shows all averages

---

## 5. TRAINING MANAGEMENT TABLES

### Table: `training_plans`
**Purpose:** Training routines created for specific players. **CHANGED: Player-specific, not club-wide templates.**

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `plan_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `player_id` | UUID (FK→players) | Which player this plan is for | Links to players |
| `plan_name` | VARCHAR(255) | Name of training plan | `Sprint Training for Marcus` |
| `duration` | VARCHAR(50) | How long plan lasts | `2 weeks` |
| `created_by` | UUID (FK→coaches) | Which coach created it | Links to coaches |
| `created_at` | TIMESTAMP | When created | `2025-01-15 10:30:00` |

**REMOVED COLUMNS:**
- ❌ `club_id` - Plans are player-specific, not club-wide

**ADDED COLUMNS:**
- ✅ `player_id` - Each plan belongs to ONE specific player

**Critical Change:**
- **OLD:** Plans were club-wide templates that could be assigned to multiple players
- **NEW:** Plans are created for ONE player only, cannot be reused

**Why this change:**
- Each player gets personalized training
- Coach can see all plans created for a player
- Cannot accidentally assign wrong plan to wrong player
- Simpler model - no need for separate assignment table (though we keep it for tracking)

**UI Changes:**
- **Create Training Plan Screen:**
  1. Select player FIRST → `player_id` set
  2. Fill plan name, duration
  3. Add exercises
  4. Submit → Plan created for that player only

- **Cannot:** Create generic plan and assign to multiple players
- **Can:** Copy existing plan to create new plan for different player (client-side feature)

**UI Usage:**
- Coach selects player → sees all training plans for that player
- "Create Training Plan" flow starts with player selection
- Each plan is unique to one player

---

### Table: `training_exercises`
**Purpose:** Individual exercises within a training plan.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `exercise_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `plan_id` | UUID (FK→training_plans) | Which plan this belongs to | Links to training_plans |
| `exercise_name` | VARCHAR(255) | Name of exercise | `40m Sprints` |
| `description` | TEXT | Detailed instructions | `Maximum effort sprints...` |
| `sets` | VARCHAR(20) | Number of sets | `6` |
| `reps` | VARCHAR(20) | Repetitions per set | `1` |
| `duration_minutes` | VARCHAR(20) | Time duration | `5` (5 min rest) |
| `exercise_order` | INTEGER | Order in the plan | `1` (first exercise) |
| `created_at` | TIMESTAMP | When added | `2025-01-15 10:30:00` |

**Relationships:**
- One training plan → Many exercises (one-to-many)
- Exercises are deleted if plan is deleted (CASCADE)

**No changes to this table**

---

### Table: `player_training_assignments`
**Purpose:** Tracks when training plans are assigned to players and their completion status.

**Note:** This table is still useful even though plans are player-specific, to track:
- When plan was assigned (different from when it was created)
- Completion status and progress
- Coach notes for the assignment

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `assignment_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `plan_id` | UUID (FK→training_plans) | Which plan is assigned | Links to training_plans |
| `player_id` | UUID (FK→players) | Which player (redundant but kept for queries) | Links to players |
| `assigned_by` | UUID (FK→coaches) | Which coach assigned it | Links to coaches |
| `assigned_date` | DATE | When assigned | `2025-10-14` |
| `status` | VARCHAR(20) | Current status | `pending`, `in_progress`, `completed` |
| `progress_percentage` | INTEGER | % complete (0-100) | `60` |
| `coach_notes` | TEXT | Instructions from coach | `Focus on form...` |
| `created_at` | TIMESTAMP | When assigned | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last progress update | `2025-01-17 18:30:00` |

**Note:** `player_id` here will always match the `player_id` in training_plans table, but we keep it for easier querying.

---

### Table: `training_exercise_completion`
**Purpose:** Tracks which exercises within an assignment are completed.

**No changes to this table**

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `completion_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `assignment_id` | UUID (FK→player_training_assignments) | Which assignment | Links to assignments |
| `exercise_id` | UUID (FK→training_exercises) | Which exercise | Links to exercises |
| `completed` | BOOLEAN | Is it done? | `true` or `false` |
| `completed_at` | TIMESTAMP | When completed | `2025-01-16 14:30:00` |
| `created_at` | TIMESTAMP | When record created | `2025-01-15 10:30:00` |

---

# 🔍 DATABASE INDEXES - PERFORMANCE OPTIMIZATION

**No changes to index structure, but column name updates:**

## Events Table Indexes

```sql
CREATE INDEX idx_events_match ON events(match_id);
CREATE INDEX idx_events_player ON events(player_name);
CREATE INDEX idx_events_type ON events(event_type_name);
CREATE INDEX idx_events_match_player ON events(match_id, player_name);
CREATE INDEX idx_events_match_type ON events(match_id, event_type_name);
CREATE INDEX idx_events_player_type ON events(player_name, event_type_name);
CREATE INDEX idx_events_timestamp ON events(match_id, minute, second);
CREATE INDEX idx_events_data ON events USING GIN (event_data);
```

**Note:** No changes needed for column renames (player_id→statsbomb_player_id) since these indexes use player_name

## Other Indexes

```sql
CREATE INDEX idx_matches_club_date ON matches(club_id, match_date DESC);
CREATE INDEX idx_goals_match ON goals(match_id);
CREATE INDEX idx_goals_scorer ON goals(scorer_name);
CREATE INDEX idx_player_invite_codes_club ON player_invite_codes(club_id, is_used);
CREATE INDEX idx_player_invite_codes_code ON player_invite_codes(invite_code);
```

**NEW INDEXES:**
```sql
-- For player invite code lookups
CREATE INDEX idx_player_invite_codes_club ON player_invite_codes(club_id, is_used);
CREATE INDEX idx_player_invite_codes_code ON player_invite_codes(invite_code);
```

---

# 🌐 API ENDPOINTS - UI SCREEN MAPPING

## Authentication Endpoints

### `POST /api/auth/register/coach`
**Purpose:** Create new coach account  
**UI Screen:** Coach Signup Screen  
**Request Body:**
```json
{
  "email": "john@email.com",
  "password": "securepass123",
  "full_name": "John Smith",
  "birth_date": "1985-06-15",
  "gender": "Male",
  "club": {
    "club_name": "Thunder United FC",
    "country": "United States",
    "age_group": "U16",
    "stadium": "City Stadium",
    "logo_url": "https://...logo.png"
  }
}
```
**Response:**
```json
{
  "user_id": "uuid",
  "coach_id": "uuid",
  "club_id": "uuid",
  "email": "john@email.com",
  "user_type": "coach"
}
```
**Changes:**
- ❌ Removed: `profile_image_url` from request
- ✅ Club logo required instead

---

### `POST /api/auth/register/player`
**Purpose:** Create new player account with invite code validation  
**UI Screen:** Player Signup Screen  
**Request Body:**
```json
{
  "email": "marcus@email.com",
  "password": "securepass123",
  "full_name": "Marcus Silva",
  "birth_date": "2008-03-20",
  "jersey_number": 10,
  "height": 180,
  "position": "Forward",
  "profile_image_url": "https://...image.jpg",
  "invite_code": "MRC-1827"
}
```
**Response:**
```json
{
  "user_id": "uuid",
  "player_id": "uuid",
  "club_id": "uuid",
  "email": "marcus@email.com",
  "user_type": "player",
  "linked": true
}
```
**Data Flow:**
1. Validate invite code: `SELECT * FROM player_invite_codes WHERE invite_code = ? AND is_used = FALSE`
2. Validate jersey number matches: `WHERE jersey_number = ?`
3. If match:
   - Create user account
   - Create player record with `is_linked = TRUE`
   - Update invite code: `UPDATE player_invite_codes SET is_used = TRUE, linked_player_id = ?, linked_at = NOW()`
4. If no match:
   - Return error: "Jersey number doesn't match. Contact your coach."

**Changes:**
- ✅ `height` now INTEGER (cm) instead of VARCHAR
- ❌ Removed: `weight`
- ✅ Added: `invite_code` validation with jersey number matching

---

### `POST /api/auth/verify-invite`
**Purpose:** Verify invite code before signup (optional pre-check)  
**UI Screen:** Player Signup Screen (Step 1)  
**Request Body:**
```json
{
  "invite_code": "MRC-1827"
}
```
**Response:**
```json
{
  "valid": true,
  "player_name": "Marcus Silva",
  "jersey_number": 10,
  "position": "Forward",
  "club_name": "Thunder United FC"
}
```
**Data Flow:**
1. Query: `SELECT * FROM player_invite_codes pic JOIN clubs c ON pic.club_id = c.club_id WHERE pic.invite_code = ? AND pic.is_used = FALSE`
2. If found, return player info
3. If not found or already used, return error

**NEW ENDPOINT**

---

## Club Management Endpoints

### `GET /api/clubs/{club_id}/unlinked-players`
**Purpose:** Get list of players with invite codes who haven't joined yet  
**UI Screen:** Coach Dashboard - Unlinked Players Section  
**Response:**
```json
{
  "unlinked_players": [
    {
      "player_name": "Marcus Silva",
      "jersey_number": 10,
      "position": "Forward",
      "invite_code": "MRC-1827",
      "has_statistics": true
    },
    {
      "player_name": "John Smith",
      "jersey_number": 7,
      "position": "Midfielder",
      "invite_code": "JHN-4523",
      "has_statistics": true
    }
  ],
  "total_unlinked": 8
}
```
**Data Flow:**
```sql
SELECT 
  pic.player_name,
  pic.jersey_number,
  pic.position,
  pic.invite_code,
  COUNT(e.event_id) as event_count
FROM player_invite_codes pic
LEFT JOIN events e ON e.player_name = pic.player_name
WHERE pic.club_id = ? 
  AND pic.is_used = FALSE
GROUP BY pic.invite_code_id
ORDER BY pic.jersey_number
```

**NEW ENDPOINT**

---

### `GET /api/clubs/{club_id}/statistics`
**Purpose:** Get club overview statistics  
**UI Screen:** Club Overview Screen  
**Response:**
```json
{
  "club": {
    "club_name": "Thunder United FC",
    "logo_url": "https://...logo.png",
    "age_group": "U16"
  },
  "record": {
    "matches_played": 22,
    "wins": 14,
    "draws": 4,
    "losses": 4,
    "goals_scored": 45,
    "goals_conceded": 23
  },
  "form": "WWDWLWWDLW",
  "averages": {
    "avg_goals_per_match": 2.05,
    "avg_possession": 58.00,
    "avg_shots": 14.50,
    ...
  }
}
```
**Changes:**
- ❌ Removed: `season`, `standing`, `goal_difference`
- ✅ `form` now string instead of JSON array

---

## Match Management Endpoints

**CRITICAL: Coaches CANNOT create, edit, or delete matches**

### `GET /api/clubs/{club_id}/matches`
**Purpose:** Get list of all matches for a club (READ-ONLY)  
**UI Screen:** Matches List Screen  
**Response:**
```json
{
  "matches": [
    {
      "match_id": "uuid",
      "opponent_name": "City Strikers",
      "match_date": "2025-10-08",
      "match_time": "15:30:00",
      "home_score": 3,
      "away_score": 2,
      "is_home_match": true,
      "result": "W"
    },
    ...
  ]
}
```
**Data Flow:**
```sql
SELECT * FROM matches
WHERE club_id = ?
ORDER BY match_date DESC, match_time DESC
```

---

### `GET /api/matches/{match_id}`
**Purpose:** Get detailed match information  
**UI Screen:** Match Detail Screen  
**Response:**
```json
{
  "match": {
    "match_id": "uuid",
    "opponent_name": "City Strikers",
    "opponent_logo_url": "https://...logo.png",
    "match_date": "2025-10-08",
    "match_time": "15:30:00",
    "location": "City Stadium",
    "stadium_name": null,
    "home_score": 3,
    "away_score": 2,
    "is_home_match": true
  },
  "lineup": {
    "home": [
      {
        "player_name": "Marcus Silva",
        "jersey_number": 10,
        "position": "Forward",
        "is_linked": true
      },
      ...
    ],
    "away": [
      {
        "player_name": "Opponent Player",
        "jersey_number": 9,
        "position": "Forward",
        "is_linked": false
      },
      ...
    ]
  }
}
```
**Data Flow:**
1. Query match: `SELECT * FROM matches WHERE match_id = ?`
2. Get lineup from events (Starting XI events):
   ```sql
   SELECT DISTINCT player_name, jersey_number, position_name
   FROM events
   WHERE match_id = ? AND event_type_name = 'Starting XI'
   ORDER BY jersey_number
   ```
3. Check if players are linked:
   ```sql
   SELECT linked_player_id FROM player_invite_codes
   WHERE player_name = ? AND is_used = TRUE
   ```

**Note:** Lineup data comes from events table, not stored separately

---

### `GET /api/matches/{match_id}/statistics`
**Purpose:** Get match statistics (team-level)  
**UI Screen:** Match Detail Screen - Statistics Tab  
**Response:**
```json
{
  "match_id": "uuid",
  "home_team": {
    "team_name": "Thunder United FC",
    "possession_percentage": 58.50,
    "expected_goals": 2.450,
    "total_shots": 14,
    "shots_on_target": 8,
    "shots_off_target": 3,
    "total_passes": 487,
    "passes_completed": 423,
    "pass_completion_rate": 86.86,
    "total_dribbles": 25,
    "successful_dribbles": 18,
    "total_tackles": 16,
    "tackle_success_percentage": 75.00,
    "interceptions": 11,
    "ball_recoveries": 48,
    "goalkeeper_saves": 4
  },
  "away_team": {
    "team_name": "City Strikers",
    ...
  }
}
```
**Changes:**
- Removed: fouls, cards
- Only includes stats shown in UI

---

### `GET /api/matches/{match_id}/goals`
**Purpose:** Get all goals scored in match  
**UI Screen:** Match Detail Screen - Goals Section  
**Response:**
```json
{
  "goals": [
    {
      "goal_id": "uuid",
      "scorer_name": "Marcus Silva",
      "assist_name": "Jake Thompson",
      "period": 1,
      "minute": 12,
      "timestamp": "00:12:45.123",
      "goal_type": "Open Play",
      "body_part": "Right Foot",
      "team_name": "Thunder United FC"
    },
    ...
  ],
  "total_goals": 5
}
```

---

## Player Management Endpoints

### `GET /api/clubs/{club_id}/players`
**Purpose:** Get all players in a club (linked AND unlinked)  
**UI Screen:** Players List Screen  
**Response:**
```json
{
  "linked_players": [
    {
      "player_id": "uuid",
      "full_name": "Marcus Silva",
      "jersey_number": 10,
      "position": "Forward",
      "height": 180,
      "profile_image_url": "https://...image.jpg",
      "is_linked": true
    },
    ...
  ],
  "unlinked_players": [
    {
      "player_name": "John Smith",
      "jersey_number": 7,
      "position": "Midfielder",
      "invite_code": "JHN-4523",
      "has_statistics": true
    },
    ...
  ]
}
```
**Data Flow:**
1. Get linked players:
   ```sql
   SELECT * FROM players
   WHERE club_id = ? AND is_linked = TRUE
   ORDER BY jersey_number
   ```
2. Get unlinked players:
   ```sql
   SELECT * FROM player_invite_codes
   WHERE club_id = ? AND is_used = FALSE
   ORDER BY jersey_number
   ```

---

### `GET /api/players/{player_id}/statistics`
**Purpose:** Get player season statistics  
**UI Screen:** Player Profile Screen  
**Response:**
```json
{
  "player": {
    "full_name": "Marcus Silva",
    "jersey_number": 10,
    "position": "Forward",
    "height": 180
  },
  "statistics": {
    "matches_played": 22,
    "goals": 12,
    "assists": 7,
    "expected_goals": 10.800,
    "shots_per_game": 4.18,
    "shots_on_target_per_game": 2.82,
    "total_passes": 1144,
    "passes_completed": 995,
    "total_dribbles": 158,
    "successful_dribbles": 118,
    "tackles": 45,
    "tackle_success_rate": 78.00,
    "interceptions": 32,
    "interception_success_rate": 85.00
  },
  "attributes": {
    "attacking_rating": 82,
    "technique_rating": 64,
    "tactical_rating": 52,
    "defending_rating": 28,
    "creativity_rating": 85
  }
}
```
**Changes:**
- No season field
- Simplified stats
- Height shown as integer (cm)

---

## Training Management Endpoints

### `POST /api/training-plans`
**Purpose:** Create a new training plan for a specific player  
**UI Screen:** Create Training Plan Screen  
**Request Body:**
```json
{
  "player_id": "uuid",
  "plan_name": "Sprint Training for Marcus",
  "duration": "2 weeks",
  "exercises": [
    {
      "exercise_name": "40m Sprints",
      "description": "Maximum effort sprints...",
      "sets": "6",
      "reps": "1",
      "duration_minutes": "5"
    },
    ...
  ]
}
```
**Response:**
```json
{
  "plan_id": "uuid",
  "player_id": "uuid",
  "plan_name": "Sprint Training for Marcus",
  "duration": "2 weeks"
}
```
**Changes:**
- ✅ `player_id` now required (plan belongs to one player)
- ❌ No `club_id`

---

### `POST /api/training-assignments`
**Purpose:** Assign a training plan to its player  
**UI Screen:** Assign Training Screen  
**Request Body:**
```json
{
  "plan_id": "uuid",
  "assigned_date": "2025-10-14",
  "coach_notes": "Focus on maintaining form..."
}
```
**Response:**
```json
{
  "assignment_id": "uuid",
  "status": "pending",
  "progress_percentage": 0
}
```
**Data Flow:**
1. Get plan: `SELECT * FROM training_plans WHERE plan_id = ?`
2. Verify player can receive training (is linked):
   ```sql
   SELECT is_linked FROM players WHERE player_id = (
     SELECT player_id FROM training_plans WHERE plan_id = ?
   )
   ```
3. If `is_linked = FALSE`, return error: "Cannot assign training to unlinked player"
4. Create assignment
5. Create completion records for each exercise

**Note:** `player_id` comes from training_plans table, doesn't need to be in request

---

### `GET /api/players/{player_id}/training-plans`
**Purpose:** Get all training plans created for a player  
**UI Screen:** Training Plans List  
**Response:**
```json
{
  "plans": [
    {
      "plan_id": "uuid",
      "plan_name": "Sprint Training for Marcus",
      "duration": "2 weeks",
      "exercise_count": 5,
      "created_at": "2025-10-14"
    },
    ...
  ]
}
```
**Data Flow:**
```sql
SELECT 
  tp.*,
  COUNT(te.exercise_id) as exercise_count
FROM training_plans tp
LEFT JOIN training_exercises te ON tp.plan_id = te.plan_id
WHERE tp.player_id = ?
GROUP BY tp.plan_id
ORDER BY tp.created_at DESC
```

**NEW ENDPOINT**

---

### `GET /api/players/{player_id}/training-assignments`
**Purpose:** Get all training assignments for a player  
**UI Screen:** Training List Screen (Player side)  
**Response:**
```json
{
  "assignments": [
    {
      "assignment_id": "uuid",
      "plan_name": "Sprint Training for Marcus",
      "assigned_date": "2025-10-14",
      "status": "in_progress",
      "progress_percentage": 60,
      "coach_notes": "Focus on form..."
    },
    ...
  ]
}
```

---

### `POST /api/training-assignments/{assignment_id}/complete-exercise/{exercise_id}`
**Purpose:** Mark an exercise as completed  
**UI Screen:** Training Detail Screen (player checks off exercise)  
**Response:**
```json
{
  "completed": true,
  "completed_at": "2025-10-15T14:30:00Z",
  "progress_percentage": 70
}
```

---

# 📊 ADMIN PANEL INTEGRATION

## Overview

**Admin Panel** is a separate application (not part of coach/player apps) used to:
1. Upload match videos
2. Process videos with Computer Vision
3. Input match details and lineups
4. Generate player invite codes
5. Insert complete match data into database

---

## Admin Panel Workflow

### Step 1: Upload Match Video

**UI:**
```
┌─────────────────────────────────────┐
│  Upload Match Video                 │
├─────────────────────────────────────┤
│  [Choose File] match_video.mp4      │
│                                     │
│  [Upload & Process]                 │
└─────────────────────────────────────┘
```

**Backend:**
1. Upload video to storage (S3, etc.)
2. Send video to Computer Vision system
3. CV returns StatsBomb JSON (~3000 events)

---

### Step 2: Match Details Form

**UI:**
```
┌─────────────────────────────────────┐
│  Match Details                      │
├─────────────────────────────────────┤
│  Select Club: [Dropdown]            │
│  → Thunder United FC                │
│                                     │
│  Match Date: [2025-10-08]           │
│  Match Time: [15:30]                │
│                                     │
│  Home/Away:  ⚪ Home  ⚫ Away        │
│                                     │
│  Score:                             │
│    Home: [3]  Away: [2]             │
│                                     │
│  Stadium Name: [City Stadium]       │
│  (only if Away match)               │
│                                     │
│  [Next: Opponent Details]           │
└─────────────────────────────────────┘
```

---

### Step 3: Opponent Details

**UI:**
```
┌─────────────────────────────────────┐
│  Opponent Details                   │
├─────────────────────────────────────┤
│  Existing Opponent: [Dropdown]      │
│  OR                                 │
│  Create New Opponent:               │
│    Name: [City Strikers]            │
│    Logo: [Upload]                   │
│    Stadium: [Riverside Arena]       │
│                                     │
│  [Next: Lineup]                     │
└─────────────────────────────────────┘
```

**Backend:**
- Check if opponent exists: `SELECT * FROM opponent_clubs WHERE club_name = ?`
- If not, create: `INSERT INTO opponent_clubs (...)`

---

### Step 4: Home Team Lineup

**UI:**
```
┌─────────────────────────────────────┐
│  Thunder United FC Lineup           │
├─────────────────────────────────────┤
│  Player 1:                          │
│    Name: [Marcus Silva]             │
│    Jersey: [10]                     │
│    Position: [Forward ▼]            │
│                                     │
│  Player 2:                          │
│    Name: [Jake Thompson]            │
│    Jersey: [7]                      │
│    Position: [Midfielder ▼]         │
│                                     │
│  ...  (repeat for all 11 players)   │
│                                     │
│  [Next: Away Team Lineup]           │
└─────────────────────────────────────┘
```

**Note:** Admin inputs lineup data, but we ALSO have lineup in StatsBomb events. We use StatsBomb data as source of truth, admin input is for verification.

---

### Step 5: Away Team Lineup

**UI:**
```
┌─────────────────────────────────────┐
│  City Strikers Lineup               │
├─────────────────────────────────────┤
│  Player 1:                          │
│    Name: [John Doe]                 │
│    Jersey: [9]                      │
│    Position: [Forward ▼]            │
│                                     │
│  ...  (repeat for all 11 players)   │
│                                     │
│  [Submit & Create Match]            │
└─────────────────────────────────────┘
```

---

### Step 6: Backend Processing

When admin clicks "Submit & Create Match":

1. **Insert Match Record:**
```sql
INSERT INTO matches (
  match_id, club_id, opponent_club_id, opponent_name,
  match_date, match_time, location, stadium_name,
  home_score, away_score, is_home_match,
  created_at, updated_at
) VALUES (...);
```

2. **Insert All Events:**
```sql
-- For each event in StatsBomb JSON (~3000 events)
INSERT INTO events (
  event_id, match_id, event_type_name, period, timestamp,
  minute, second, statsbomb_team_id, team_name,
  statsbomb_player_id, player_name, position_name,
  -- ... all other fields
  event_data
) VALUES (...);
```

3. **Generate Player Invite Codes:**
```sql
-- For each player in home team (Thunder United FC)
INSERT INTO player_invite_codes (
  invite_code_id, club_id, player_name, jersey_number,
  position, invite_code, is_used, created_at
) VALUES (
  gen_random_uuid(),
  'club_uuid',
  'Marcus Silva',
  10,
  'Forward',
  'MRC-' || floor(random() * 10000)::text, -- Generate code
  FALSE,
  NOW()
)
ON CONFLICT (invite_code) DO NOTHING; -- Ensure unique code
```

4. **Extract Goals:**
```sql
-- Find all shot events that resulted in goals
INSERT INTO goals (
  goal_id, match_id, event_id,
  scorer_statsbomb_player_id, scorer_name,
  assist_statsbomb_player_id, assist_name,
  period, minute, second, timestamp,
  goal_type, body_part, statsbomb_team_id, team_name
)
SELECT
  gen_random_uuid(),
  match_id,
  event_id,
  statsbomb_player_id,
  player_name,
  (SELECT statsbomb_player_id FROM events 
   WHERE match_id = e.match_id 
     AND event_type_name = 'Pass'
     AND pass_recipient_name = e.player_name
     AND minute <= e.minute
   ORDER BY minute DESC, second DESC
   LIMIT 1) as assist_player_id,
  (SELECT player_name FROM events 
   WHERE match_id = e.match_id 
     AND event_type_name = 'Pass'
     AND pass_recipient_name = e.player_name
     AND minute <= e.minute
   ORDER BY minute DESC, second DESC
   LIMIT 1) as assist_name,
  period, minute, second, timestamp,
  shot_type, shot_body_part,
  statsbomb_team_id, team_name
FROM events e
WHERE match_id = 'match_uuid'
  AND event_type_name = 'Shot'
  AND shot_outcome LIKE '%Goal%';
```

5. **Calculate Match Statistics:**
```sql
-- For home team
INSERT INTO match_statistics (
  stat_id, match_id, team_type,
  possession_percentage, expected_goals, goalkeeper_saves,
  total_shots, shots_on_target, shots_off_target,
  total_passes, passes_completed, pass_completion_rate,
  passes_in_final_third, long_passes, crosses,
  total_dribbles, successful_dribbles, dribble_success_rate,
  total_tackles, tackle_success_percentage,
  interceptions, ball_recoveries
)
SELECT
  gen_random_uuid(),
  'match_uuid',
  'home',
  
  -- Calculate possession
  (COUNT(CASE WHEN possession_team_id = home_team_id THEN 1 END) * 100.0 / COUNT(*)) as possession,
  
  -- Calculate xG (sum from events)
  SUM(CASE WHEN event_type_name = 'Shot' AND team_id = home_team_id 
      THEN COALESCE((event_data->'shot'->>'statsbomb_xg')::decimal, 0) 
      ELSE 0 END) as xg,
  
  -- Goalkeeper saves
  COUNT(CASE WHEN event_type_name = 'Goal Keeper' 
             AND team_id = away_team_id 
             AND (event_data->'goalkeeper'->>'type')::text = 'Save' 
        THEN 1 END) as gk_saves,
  
  -- Shots
  COUNT(CASE WHEN event_type_name = 'Shot' AND team_id = home_team_id THEN 1 END) as total_shots,
  COUNT(CASE WHEN event_type_name = 'Shot' AND team_id = home_team_id 
             AND shot_outcome IN ('Goal', 'Saved') THEN 1 END) as shots_on_target,
  COUNT(CASE WHEN event_type_name = 'Shot' AND team_id = home_team_id 
             AND shot_outcome = 'Off Target' THEN 1 END) as shots_off_target,
  
  -- Passes
  COUNT(CASE WHEN event_type_name = 'Pass' AND team_id = home_team_id THEN 1 END) as total_passes,
  COUNT(CASE WHEN event_type_name = 'Pass' AND team_id = home_team_id 
             AND outcome = 'Complete' THEN 1 END) as passes_completed,
  (COUNT(CASE WHEN event_type_name = 'Pass' AND team_id = home_team_id AND outcome = 'Complete' THEN 1 END) * 100.0 /
   NULLIF(COUNT(CASE WHEN event_type_name = 'Pass' AND team_id = home_team_id THEN 1 END), 0)) as pass_completion,
  
  -- ... continue for all other stats
  
FROM events
WHERE match_id = 'match_uuid';

-- Repeat for away team
```

6. **Calculate Player Match Statistics:**
```sql
-- For each player in the match
INSERT INTO player_match_statistics (
  stat_id, match_id, player_id,
  goals, assists, expected_goals,
  shots, shots_on_target,
  total_passes, completed_passes,
  short_passes, long_passes, final_third_passes, crosses,
  total_dribbles, successful_dribbles,
  tackles, tackle_success_rate,
  interceptions, interception_success_rate
)
SELECT
  gen_random_uuid(),
  'match_uuid',
  -- Try to find linked player, otherwise NULL
  (SELECT linked_player_id FROM player_invite_codes 
   WHERE player_name = e.player_name AND is_used = TRUE
   LIMIT 1),
  
  -- Goals
  COUNT(CASE WHEN event_type_name = 'Shot' AND shot_outcome LIKE '%Goal%' THEN 1 END),
  
  -- Assists
  (SELECT COUNT(*) FROM goals WHERE match_id = 'match_uuid' AND assist_name = e.player_name),
  
  -- xG
  SUM(CASE WHEN event_type_name = 'Shot' 
      THEN COALESCE((event_data->'shot'->>'statsbomb_xg')::decimal, 0) 
      ELSE 0 END),
  
  -- Shots
  COUNT(CASE WHEN event_type_name = 'Shot' THEN 1 END),
  COUNT(CASE WHEN event_type_name = 'Shot' AND shot_outcome IN ('Goal', 'Saved') THEN 1 END),
  
  -- ... continue for all stats
  
FROM events e
WHERE match_id = 'match_uuid'
  AND player_name IS NOT NULL
GROUP BY player_name;
```

7. **Update Club Season Statistics:**
```sql
-- Update or create club season record
INSERT INTO club_season_statistics (
  stat_id, club_id,
  matches_played, wins, draws, losses,
  goals_scored, goals_conceded, total_assists, total_clean_sheets,
  team_form, ...
) VALUES (
  gen_random_uuid(),
  'club_uuid',
  0, 0, 0, 0, 0, 0, 0, 0, '', ...
)
ON CONFLICT (club_id) DO UPDATE SET
  matches_played = club_season_statistics.matches_played + 1,
  wins = club_season_statistics.wins + CASE WHEN NEW.home_score > NEW.away_score THEN 1 ELSE 0 END,
  draws = club_season_statistics.draws + CASE WHEN NEW.home_score = NEW.away_score THEN 1 ELSE 0 END,
  losses = club_season_statistics.losses + CASE WHEN NEW.home_score < NEW.away_score THEN 1 ELSE 0 END,
  goals_scored = club_season_statistics.goals_scored + NEW.home_score,
  goals_conceded = club_season_statistics.goals_conceded + NEW.away_score,
  total_clean_sheets = club_season_statistics.total_clean_sheets + 
    CASE WHEN NEW.away_score = 0 THEN 1 ELSE 0 END,
  team_form = LEFT(
    CASE 
      WHEN NEW.home_score > NEW.away_score THEN 'W'
      WHEN NEW.home_score = NEW.away_score THEN 'D'
      ELSE 'L'
    END || club_season_statistics.team_form,
    10
  ), -- Prepend result, keep last 10
  
  -- Recalculate all averages
  avg_goals_per_match = (goals_scored + NEW.home_score) / (matches_played + 1),
  avg_goals_conceded_per_match = (goals_conceded + NEW.away_score) / (matches_played + 1),
  -- ... recalculate all other averages
  
  updated_at = NOW();
```

8. **Update Player Season Statistics:**
```sql
-- For each player in the match
UPDATE player_season_statistics SET
  matches_played = matches_played + 1,
  goals = goals + NEW.goals,
  assists = assists + NEW.assists,
  expected_goals = expected_goals + NEW.expected_goals,
  total_passes = total_passes + NEW.total_passes,
  passes_completed = passes_completed + NEW.completed_passes,
  total_dribbles = total_dribbles + NEW.total_dribbles,
  successful_dribbles = successful_dribbles + NEW.successful_dribbles,
  tackles = tackles + NEW.tackles,
  interceptions = interceptions + NEW.interceptions,
  
  -- Recalculate rates
  tackle_success_rate = (tackles_won_total * 100.0 / NULLIF(tackles, 0)),
  interception_success_rate = (interceptions_won_total * 100.0 / NULLIF(interceptions, 0)),
  
  -- Recalculate per-game stats
  shots_per_game = total_shots / NULLIF(matches_played, 0),
  shots_on_target_per_game = shots_on_target / NULLIF(matches_played, 0),
  
  -- Recalculate attributes
  attacking_rating = LEAST(100, GREATEST(0,
    (goals * 5) + (shots_per_game * 2) + (expected_goals * 3)
  )),
  -- ... recalculate all other attributes
  
  updated_at = NOW()
WHERE player_id = (
  SELECT linked_player_id FROM player_invite_codes
  WHERE player_name = ? AND is_used = TRUE
);

-- If player not linked yet, skip or create placeholder record
```

---

### Admin Panel API Endpoint

### `POST /api/admin/ingest-match`
**Purpose:** Insert complete match data from admin panel  
**Request Body:**
```json
{
  "club_id": "uuid",
  "match_details": {
    "opponent_club_id": "uuid",
    "opponent_name": "City Strikers",
    "match_date": "2025-10-08",
    "match_time": "15:30:00",
    "location": "City Stadium",
    "stadium_name": null,
    "home_score": 3,
    "away_score": 2,
    "is_home_match": true
  },
  "statsbomb_data": [...] // Complete StatsBomb JSON
}
```
**Response:**
```json
{
  "success": true,
  "match_id": "uuid",
  "events_processed": 3247,
  "goals_extracted": 5,
  "invite_codes_generated": 11,
  "invite_codes": [
    {
      "player_name": "Marcus Silva",
      "jersey_number": 10,
      "invite_code": "MRC-1827"
    },
    ...
  ]
}
```

**This endpoint handles all 8 steps above automatically.**

---

## Summary of Admin Panel Flow

```
┌──────────────┐
│ Upload Video │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ CV Processing│ (Returns StatsBomb JSON)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Match Details│ (Date, Score, Home/Away)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Opponent   │ (Select or Create)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Home Lineup  │ (11 players)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Away Lineup  │ (11 players)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Submit    │ → POST /api/admin/ingest-match
└──────┬───────┘
       │
       ▼
┌───────────────────────────────────────┐
│ Backend Processing:                   │
│ 1. Insert match                       │
│ 2. Insert ~3000 events                │
│ 3. Generate invite codes (11 players) │
│ 4. Extract goals (~5)                 │
│ 5. Calculate match statistics         │
│ 6. Calculate player statistics (~22)  │
│ 7. Update club season stats           │
│ 8. Update player season stats (~11)   │
└───────────────┬───────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ Match appears │
        │  in Coach App │
        │  (read-only)  │
        └───────────────┘
```

---

# 📋 SUMMARY OF ALL CHANGES

## Database Changes

### Modified Tables:
1. **coaches** - Removed profile_image_url
2. **players** - Removed weight, changed height to INTEGER (cm)
3. **clubs** - Removed invite_code
4. **teams** → **opponent_clubs** - Renamed, added stadium_name
5. **matches** - Removed match_status, video_url, statsbomb_match_id; added stadium_name
6. **events** - Renamed player_id → statsbomb_player_id, team_id → statsbomb_team_id
7. **goals** - Renamed ID columns for clarity
8. **match_statistics** - Removed fouls/cards, kept only UI-specific stats
9. **player_match_statistics** - Major simplification, removed Physical/Discipline
10. **player_season_statistics** - Removed season, simplified stats
11. **club_season_statistics** - Removed season/standing/goal_difference, changed form to VARCHAR
12. **training_plans** - Removed club_id, added player_id

### New Tables:
1. **player_invite_codes** - Per-player unique invite code system

### New Indexes:
```sql
CREATE INDEX idx_player_invite_codes_club ON player_invite_codes(club_id, is_used);
CREATE INDEX idx_player_invite_codes_code ON player_invite_codes(invite_code);
```

## API Changes

### New Endpoints:
- `POST /api/auth/verify-invite` - Verify invite code before signup
- `GET /api/clubs/{club_id}/unlinked-players` - List players without accounts
- `GET /api/players/{player_id}/training-plans` - Get player's training plans
- `POST /api/admin/ingest-match` - Admin panel match creation

### Removed Endpoints:
- `POST /api/matches` - Coaches cannot create matches
- `PUT /api/matches/{id}` - Coaches cannot edit matches
- `DELETE /api/matches/{id}` - Coaches cannot delete matches

### Modified Endpoints:
- All player-related endpoints now handle height as INTEGER (cm)
- Training endpoints now player-specific (require player_id)
- Statistics endpoints simplified to match UI exactly

## Workflow Changes

### Match Creation:
- **OLD:** Coach creates match in app → uploads video → CV processes
- **NEW:** Admin uploads video → CV processes → Admin inputs details → Match appears in coach app

### Player Onboarding:
- **OLD:** Player uses club invite code → joins club
- **NEW:** Admin processes match → generates per-player codes → Player uses their unique code + jersey# validation → linked to statistics

### Training Management:
- **OLD:** Create club-wide template → assign to multiple players
- **NEW:** Create plan for specific player → can only assign to that player

---

# ✅ IMPLEMENTATION CHECKLIST

Before deployment, ensure:


---

**Ready to implement! 🚀**

All changes documented and explained. Proceed with database migrations and API updates.
