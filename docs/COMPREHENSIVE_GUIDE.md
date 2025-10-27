# 📚 SPINTA Backend - Complete Technical Deep Dive

## Table of Contents
1. [Database Tables - Complete Breakdown](#database-tables)
2. [Database Indexes - Performance Optimization](#database-indexes)
3. [API Endpoints - UI Screen Mapping](#api-endpoints)
4. [Data Flow - Queries & Operations](#data-flow)

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
| `profile_image_url` | TEXT | URL to profile picture | `https://...image.jpg` |

**Why these columns:**
- `coach_id`: Primary key that also references users table (one-to-one relationship)
- `birth_date`: For age verification, demographics
- `profile_image_url`: Stores link to image (stored in cloud storage like S3, not in DB)

**UI Usage:**
- Profile screen shows this info
- Coach signup screen collects this data

---

### Table: `players`
**Purpose:** Stores player-specific information. Extends users table with athlete details.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `player_id` | UUID (PK, FK→users) | Links to users table | Same as user_id |
| `jersey_number` | INTEGER | Player's jersey/shirt number | `10` |
| `height` | VARCHAR(20) | Player height | `5'11"` |
| `weight` | VARCHAR(20) | Player weight | `165 lbs` |
| `birth_date` | DATE | Player's date of birth | `2008-03-20` |
| `position` | VARCHAR(50) | Playing position | `Forward` |
| `profile_image_url` | TEXT | URL to profile picture | `https://...image.jpg` |
| `club_id` | UUID (FK→clubs) | Which club they belong to | Links to clubs table |
| `is_linked` | BOOLEAN | Whether player is linked to a club | `true` or `false` |
| `linked_at` | TIMESTAMP | When they joined the club | `2025-01-15 10:30:00` |

**Why these columns:**
- Athletic measurements (`height`, `weight`, `position`) are essential for player profiles
- `jersey_number`: Displayed on player cards, match lineups
- `is_linked`: Players can create accounts before joining a club (orphaned accounts)
- `linked_at`: Audit trail for when they joined

**UI Usage:**
- Player profile screen displays all this info
- Player signup collects this data
- Players list screen shows jersey number, name, position
- "Link player" functionality sets `is_linked` to true

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
| `invite_code` | VARCHAR(10) UNIQUE | Code for players to join | `ABC123XYZ` |
| `created_at` | TIMESTAMP | When club was created | `2025-01-15 10:30:00` |

**Why these columns:**
- `club_name`: Main identifier displayed everywhere
- `coach_id`: One club has one coach (one-to-one relationship)
- `invite_code`: Allows players to find and join the club without manual approval
- `age_group`: Important for youth football - teams are organized by age
- `logo_url`: Displayed on dashboard, match cards, everywhere

**UI Usage:**
- Club overview screen shows club name, logo, statistics
- Club signup screen collects this data
- Invite code is generated and shown to coach to share with players

---

### Table: `teams`
**Purpose:** Represents opponent teams. Separate from clubs because opponents don't have accounts.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `team_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `team_name` | VARCHAR(255) | Opponent team name | `City Strikers` |
| `logo_url` | TEXT | Opponent team logo (optional) | `https://...logo.png` |
| `created_at` | TIMESTAMP | When added to system | `2025-01-15 10:30:00` |

**Why separate from clubs:**
- Opponent teams don't have coaches in the system
- Don't need all the club metadata (age group, stadium, etc.)
- Simpler structure for opponents

**UI Usage:**
- Match cards show opponent name and logo
- Match detail screen shows opponent info
- When coach adds a match, they type opponent name (creates team record if new)

---

## 3. MATCH MANAGEMENT TABLES

### Table: `matches`
**Purpose:** Represents a single football match between the club and an opponent.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `match_id` | UUID (PK) | Unique identifier for match | `a1b2c3d4-...` |
| `club_id` | UUID (FK→clubs) | Which club played this match | Links to clubs |
| `opponent_team_id` | UUID (FK→teams) | Reference to opponent in teams table | Links to teams |
| `opponent_name` | VARCHAR(255) | Opponent name (denormalized for speed) | `City Strikers` |
| `match_date` | DATE | Date of match | `2025-10-08` |
| `match_time` | TIME | Kickoff time | `15:30:00` |
| `location` | VARCHAR(255) | Where match was played | `City Stadium` |
| `home_score` | INTEGER | Goals scored by home team | `3` |
| `away_score` | INTEGER | Goals scored by away team | `2` |
| `is_home_match` | BOOLEAN | True if club was home team | `true` |
| `match_status` | VARCHAR(20) | Current status of match | `completed` |
| `video_url` | TEXT | Link to match video (for CV processing) | `https://...video.mp4` |
| `statsbomb_match_id` | VARCHAR(50) | Original StatsBomb ID if from their data | `15946` |
| `created_at` | TIMESTAMP | When match record was created | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last update (e.g., when CV processed) | `2025-01-15 16:45:00` |

**Why these columns:**
- `opponent_name`: Denormalized (duplicated from teams table) for faster queries - avoids JOIN
- `match_status`: Tracks processing pipeline:
  - `scheduled`: Match created but not played yet
  - `processing`: Video uploaded, CV is analyzing
  - `completed`: All data processed and available
  - `cancelled`: Match didn't happen
- `video_url`: Coach uploads video, CV system processes it
- `is_home_match`: Determines which team's stats go in "home" vs "away" columns

**UI Usage:**
- Match list screen: Shows opponent, date, score, result (W/D/L)
- Match detail screen: Shows all match info
- Add match screen: Creates new record with status='scheduled'
- CV processing: Updates status to 'processing' → 'completed'

**Data Flow Example:**
1. Coach creates match → `match_status = 'scheduled'`
2. Coach uploads video → `video_url` populated, `match_status = 'processing'`
3. CV processes video → Creates events, calculates stats, `match_status = 'completed'`

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
| `team_id` | INTEGER | StatsBomb team ID | `217` |
| `team_name` | VARCHAR(255) | Team that performed the event | `Barcelona` |
| `player_id` | INTEGER | StatsBomb player ID | `5470` |
| `player_name` | VARCHAR(255) | Player who performed the event | `Ivan Rakitić` |
| `position_id` | INTEGER | StatsBomb position ID | `11` |
| `position_name` | VARCHAR(100) | Player's position during event | `Left Defensive Midfield` |
| `duration` | DECIMAL(8,6) | How long event lasted (seconds) | `1.412834` |
| `possession` | INTEGER | Possession sequence number | `19` |
| `play_pattern_id` | INTEGER | Type of play | `1` |
| `play_pattern_name` | VARCHAR(50) | Description of play type | `Regular Play`, `Corner`, etc. |
| `outcome` | VARCHAR(100) | General outcome | `Complete`, `Incomplete`, `Goal` |
| `outcome_type` | VARCHAR(50) | Specific outcome type | For shots: `Goal`, `Saved` |

**Pass-Specific Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `pass_recipient_id` | INTEGER | Who received the pass | `5211` |
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
- **Timestamp fields** (`period`, `minute`, `second`, `timestamp`): Enable chatbot to answer "when" questions
- **Event-specific fields** (pass_*, shot_*, etc.): Make common queries fast without JSON parsing
- **JSONB `event_data`**: Preserves complete original data for:
  - Complex queries not covered by extracted fields
  - Future feature additions
  - Data verification
  - Debugging

**UI Usage:**
- Chatbot queries: "When did player X shoot?" → Queries this table filtered by `event_type_name = 'Shot'`
- Match timeline: Chronological list of key events
- Player performance: All events by a player

**Storage Example:**
For a pass event from StatsBomb JSON:
```json
{
  "id": "abb2c888-a3c9-424e-a26a-4b8377475ccf",
  "type": {"id": 30, "name": "Pass"},
  "timestamp": "00:12:41.736",
  "minute": 12,
  "second": 41,
  "player": {"id": 5470, "name": "Ivan Rakitić"},
  "pass": {
    "recipient": {"id": 5211, "name": "Jordi Alba Ramos"},
    "length": 14.58,
    "height": {"name": "Ground Pass"}
  }
}
```

Stored as:
- `event_id` = "abb2c888-..."
- `event_type_name` = "Pass"
- `player_name` = "Ivan Rakitić"
- `pass_recipient_name` = "Jordi Alba Ramos"
- `pass_length` = 14.58
- `event_data` = entire JSON object

---

### Table: `goals`
**Purpose:** Extracted goals for easy access. Subset of events table but optimized for quick goal queries.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `goal_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `match_id` | UUID (FK→matches) | Which match | Links to matches |
| `event_id` | UUID (FK→events) | Reference to shot event | Links to events |
| `scorer_player_id` | INTEGER | StatsBomb player ID | `5470` |
| `scorer_name` | VARCHAR(255) | Who scored | `Ivan Rakitić` |
| `assist_player_id` | INTEGER | StatsBomb player ID of assister | `5211` |
| `assist_name` | VARCHAR(255) | Who assisted (if any) | `Jordi Alba Ramos` |
| `period` | INTEGER | Which half | `1` or `2` |
| `minute` | INTEGER | Minute of goal | `12` |
| `second` | INTEGER | Second within minute | `45` |
| `timestamp` | VARCHAR(20) | Exact time | `00:12:45.123` |
| `goal_type` | VARCHAR(50) | How goal was scored | `Open Play`, `Penalty`, `Free Kick` |
| `body_part` | VARCHAR(50) | Body part used | `Right Foot`, `Head` |
| `team_id` | INTEGER | StatsBomb team ID | `217` |
| `team_name` | VARCHAR(255) | Which team scored | `Barcelona` |
| `created_at` | TIMESTAMP | When stored | `2025-01-15 10:30:00` |

**Why separate goals table:**
- **Performance**: Much faster to query 5 goals than search through 3000+ events
- **Assist detection**: Pre-calculated by finding the pass before the shot
- **UI convenience**: Match detail screen shows goals without complex queries
- **Chatbot**: "Show me all goals" is instant without filtering events

**How assists are found:**
When processing a goal event, the system looks backwards through recent events to find the last pass to the scorer. That pass's player becomes the assist.

**UI Usage:**
- Match detail screen: Shows goals timeline
- Goals list in match summary
- Chatbot: "When did we score?" queries this table directly

---

## 4. STATISTICS TABLES

### Table: `match_statistics`
**Purpose:** Aggregated team-level statistics for a match. Pre-calculated from events table.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `match_id` | UUID (FK→matches) | Which match | Links to matches |
| `team_type` | VARCHAR(10) | 'home' or 'away' | `home` |

**Possession & Passing:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `possession_percentage` | DECIMAL(5,2) | % of time with ball | `58.50` (58.5%) |
| `total_passes` | INTEGER | Total pass attempts | `487` |
| `completed_passes` | INTEGER | Successful passes | `423` |
| `pass_accuracy` | DECIMAL(5,2) | Success rate | `86.86` (86.86%) |
| `short_passes` | INTEGER | Passes < 15m | `350` |
| `long_passes` | INTEGER | Passes > 15m | `137` |
| `final_third_passes` | INTEGER | Passes in attacking third | `145` |
| `crosses` | INTEGER | Cross attempts | `18` |
| `key_passes` | INTEGER | Passes leading to shots | `12` |

**Shooting:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_shots` | INTEGER | Total shot attempts | `14` |
| `shots_on_target` | INTEGER | Shots on goal | `8` |
| `shots_off_target` | INTEGER | Shots missing goal | `3` |
| `blocked_shots` | INTEGER | Shots blocked by defenders | `3` |
| `goals` | INTEGER | Goals scored | `3` |
| `expected_goals` | DECIMAL(5,3) | xG metric | `2.450` |
| `shot_conversion_rate` | DECIMAL(5,2) | Goals/shots * 100 | `21.43` (21.43%) |

**Dribbling:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_dribbles` | INTEGER | Dribble attempts | `25` |
| `successful_dribbles` | INTEGER | Successful dribbles | `18` |
| `dribble_success_rate` | DECIMAL(5,2) | Success percentage | `72.00` |

**Defensive:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `tackles` | INTEGER | Tackle attempts | `16` |
| `tackles_won` | INTEGER | Successful tackles | `12` |
| `tackle_success_rate` | DECIMAL(5,2) | Success percentage | `75.00` |
| `interceptions` | INTEGER | Interceptions made | `11` |
| `blocks` | INTEGER | Shots/passes blocked | `8` |
| `clearances` | INTEGER | Clearances made | `15` |

**Discipline:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `fouls_committed` | INTEGER | Fouls made | `8` |
| `fouls_won` | INTEGER | Fouls suffered | `12` |
| `yellow_cards` | INTEGER | Yellow cards received | `2` |
| `red_cards` | INTEGER | Red cards received | `0` |
| `created_at` | TIMESTAMP | When calculated | `2025-01-15 10:30:00` |

**Why these statistics:**
- All statistics shown in match detail screen
- Calculated once after match, not every query (performance)
- Two records per match: one for home team, one for away team

**How calculated:**
After CV processes match and stores events:
1. Count events by type: `SELECT COUNT(*) FROM events WHERE event_type_name = 'Pass' AND team_id = X`
2. Count successful events: `WHERE event_type_name = 'Pass' AND outcome = 'Complete'`
3. Calculate percentages: `completed_passes / total_passes * 100`
4. Store in this table

**UI Usage:**
- Match detail screen "Statistics" tab displays these
- Comparison bars show home vs away stats

---

### Table: `player_match_statistics`
**Purpose:** Individual player performance in a specific match. Pre-calculated from events table.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `match_id` | UUID (FK→matches) | Which match | Links to matches |
| `player_id` | UUID (FK→players) | Which player | Links to players |
| `minutes_played` | INTEGER | Time on pitch | `90` |
| `rating` | DECIMAL(3,1) | Performance rating (1-10) | `9.2` |

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
| `touches_in_box` | INTEGER | Touches in penalty area | `9` |

**Ball Retention:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_passes` | INTEGER | Pass attempts | `52` |
| `completed_passes` | INTEGER | Successful passes | `46` |
| `pass_accuracy` | DECIMAL(5,2) | Success rate | `88.46` |
| `short_passes` | INTEGER | Short pass attempts | `38` |
| `long_passes` | INTEGER | Long pass attempts | `14` |
| `final_third_passes` | INTEGER | Passes in attacking third | `18` |
| `crosses` | INTEGER | Cross attempts | `5` |
| `key_passes` | INTEGER | Passes leading to shots | `3` |
| `dispossessed` | INTEGER | Times lost ball | `2` |

**Defensive Work:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `tackles` | INTEGER | Tackle attempts | `5` |
| `tackles_won` | INTEGER | Successful tackles | `4` |
| `tackles_lost` | INTEGER | Failed tackles | `1` |
| `tackle_success_rate` | DECIMAL(5,2) | Success percentage | `80.00` |
| `interceptions` | INTEGER | Interceptions made | `5` |
| `blocks` | INTEGER | Shots/passes blocked | `2` |
| `clearances` | INTEGER | Clearances made | `1` |
| `fouls_committed` | INTEGER | Fouls made | `1` |
| `fouls_won` | INTEGER | Fouls won | `3` |

**Physical:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `distance_covered` | DECIMAL(5,2) | Kilometers run | `11.20` |
| `sprints` | INTEGER | Number of sprints | `45` |
| `duels_won` | INTEGER | Physical duels won | `11` |
| `duels_lost` | INTEGER | Physical duels lost | `4` |
| `aerial_duels_won` | INTEGER | Headers won | `5` |
| `aerial_duels_lost` | INTEGER | Headers lost | `2` |

**Discipline:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `yellow_cards` | INTEGER | Yellow cards | `0` |
| `red_cards` | INTEGER | Red cards | `0` |
| `created_at` | TIMESTAMP | When calculated | `2025-01-15 10:30:00` |

**Unique Constraint:** `(match_id, player_id)` - Each player appears once per match

**Why these statistics:**
- Shown in "Match Player Stats" screen
- Comparison with team averages
- Historical player performance tracking

**How calculated:**
Similar to match statistics but filtered by player:
```sql
SELECT COUNT(*) FROM events 
WHERE match_id = X AND player_name = 'Marcus Silva' AND event_type_name = 'Shot'
```

**UI Usage:**
- "Match Player Stats" screen shows all these stats
- Coach clicks on player from match detail → sees these stats
- Player views their own match performance

---

### Table: `player_season_statistics`
**Purpose:** Aggregated player statistics across an entire season.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `player_id` | UUID (FK→players) | Which player | Links to players |
| `club_id` | UUID (FK→clubs) | Which club | Links to clubs |
| `season` | VARCHAR(20) | Season identifier | `2024-2025` |

**Summary:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `matches_played` | INTEGER | Total matches | `22` |
| `minutes_played` | INTEGER | Total minutes | `1850` |
| `goals` | INTEGER | Total goals | `12` |
| `assists` | INTEGER | Total assists | `7` |
| `average_rating` | DECIMAL(3,1) | Average match rating | `8.5` |

**Averages & Totals:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `total_passes` | INTEGER | Season total | `1144` |
| `completed_passes` | INTEGER | Successful passes | `995` |
| `pass_accuracy` | DECIMAL(5,2) | Overall accuracy | `87.00` |
| `total_shots` | INTEGER | Total shots | `92` |
| `shots_on_target` | INTEGER | Shots on goal | `62` |
| `expected_goals` | DECIMAL(6,3) | Season xG | `10.800` |
| `shot_conversion_rate` | DECIMAL(5,2) | Goals/shots % | `13.04` |
| `total_dribbles` | INTEGER | Total dribbles | `158` |
| `successful_dribbles` | INTEGER | Successful dribbles | `118` |
| `tackles` | INTEGER | Total tackles | `45` |
| `tackle_success_rate` | DECIMAL(5,2) | Tackle success % | `78.00` |
| `interceptions` | INTEGER | Total interceptions | `32` |
| `total_distance` | DECIMAL(8,2) | Total km covered | `246.40` |
| `average_distance` | DECIMAL(5,2) | Avg km per match | `11.20` |
| `yellow_cards` | INTEGER | Total yellows | `3` |
| `red_cards` | INTEGER | Total reds | `0` |

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

**Unique Constraint:** `(player_id, season)` - One record per player per season

**Why these statistics:**
- Player profile screen shows season stats
- Comparison with other players
- Track player development over time

**How calculated:**
After each match, this record is updated:
```sql
-- Sum all player_match_statistics for this season
UPDATE player_season_statistics SET
  matches_played = matches_played + 1,
  goals = goals + NEW.goals,
  assists = assists + NEW.assists,
  ... etc
WHERE player_id = X AND season = '2024-2025'
```

**Attribute ratings calculated from performance:**
- `attacking_rating`: Based on goals, shots, xG
- `technique_rating`: Based on pass accuracy, dribble success
- `tactical_rating`: Based on positioning, key passes
- `defending_rating`: Based on tackles, interceptions
- `creativity_rating`: Based on assists, key passes, successful dribbles

**UI Usage:**
- Player profile "Summary" tab
- Player comparison screens
- Radar chart visualization (uses attribute ratings)

---

### Table: `club_season_statistics`
**Purpose:** Aggregated team-level statistics for entire season.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `stat_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `club_id` | UUID (FK→clubs) | Which club | Links to clubs |
| `season` | VARCHAR(20) | Season identifier | `2024-2025` |

**Record:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `matches_played` | INTEGER | Total matches | `22` |
| `wins` | INTEGER | Matches won | `14` |
| `draws` | INTEGER | Matches drawn | `4` |
| `losses` | INTEGER | Matches lost | `4` |
| `standing` | VARCHAR(10) | League position | `3rd` |

**Goals:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `goals_scored` | INTEGER | Total goals scored | `45` |
| `goals_conceded` | INTEGER | Total goals conceded | `23` |
| `goal_difference` | INTEGER | Difference | `+22` |
| `clean_sheets` | INTEGER | Matches without conceding | `8` |

**Form:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `team_form` | JSONB | Last 10 results | `["W","W","D","W","L"]` |

**Averages (per match):**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `avg_possession` | DECIMAL(5,2) | Average possession % | `58.00` |
| `avg_passes` | INTEGER | Average passes | `487` |
| `avg_pass_completion_rate` | DECIMAL(5,2) | Pass accuracy | `87.00` |
| `avg_shots` | INTEGER | Average shots | `14` |
| `avg_shots_on_target` | DECIMAL(5,2) | Avg shots on target | `8.20` |
| `avg_expected_goals` | DECIMAL(5,3) | Average xG | `1.900` |
| `avg_dribbles` | DECIMAL(5,2) | Average dribbles | `12.50` |
| `avg_successful_dribbles` | DECIMAL(5,2) | Avg successful dribbles | `8.20` |
| `avg_final_third_passes` | INTEGER | Avg passes in final third | `145` |
| `avg_crosses` | INTEGER | Average crosses | `18` |
| `avg_tackles` | DECIMAL(5,2) | Average tackles | `16.30` |
| `tackle_success_rate` | DECIMAL(5,2) | Overall tackle success | `72.00` |
| `avg_interceptions` | DECIMAL(5,2) | Average interceptions | `11.80` |
| `interception_success_rate` | DECIMAL(5,2) | Interception success | `85.00` |
| `avg_ball_recoveries` | DECIMAL(5,2) | Avg ball recoveries | `48.50` |

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `created_at` | TIMESTAMP | When first calculated | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last update | `2025-10-20 14:22:00` |

**Unique Constraint:** `(club_id, season)` - One record per club per season

**Why these statistics:**
- Club overview dashboard shows all these
- Track team performance over season
- Compare seasons

**How team_form works:**
JSONB array storing last 10 results: `["W", "W", "D", "W", "L", "W", "W", "D", "L", "W"]`
- After each match, prepend result to array
- Keep only last 10 results
- UI displays as colored badges

**UI Usage:**
- Club overview screen shows all these stats
- "Team Form" section shows form array
- Statistics tab shows averages

---

## 5. TRAINING MANAGEMENT TABLES

### Table: `training_plans`
**Purpose:** Templates for training routines created by coaches.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `plan_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `club_id` | UUID (FK→clubs) | Which club owns this plan | Links to clubs |
| `plan_name` | VARCHAR(255) | Name of training plan | `Sprint Training` |
| `duration` | VARCHAR(50) | How long plan lasts | `2 weeks` |
| `created_by` | UUID (FK→coaches) | Which coach created it | Links to coaches |
| `created_at` | TIMESTAMP | When created | `2025-01-15 10:30:00` |

**Why these columns:**
- Training plans are reusable templates
- Can be assigned to multiple players
- Coach can create library of training plans

**UI Usage:**
- "Create Training Plan" screen creates this
- Coach can view list of all their plans
- Plans can be assigned to players

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

**Why exercise_order:**
- Exercises must be performed in specific order
- UI displays exercises sorted by this field

**UI Usage:**
- "Create Training Plan" screen adds exercises
- Training detail screen shows exercises in order
- Player sees exercises list when viewing assignment

---

### Table: `player_training_assignments`
**Purpose:** Tracks which players are assigned which training plans.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `assignment_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `plan_id` | UUID (FK→training_plans) | Which plan is assigned | Links to training_plans |
| `player_id` | UUID (FK→players) | Which player | Links to players |
| `assigned_by` | UUID (FK→coaches) | Which coach assigned it | Links to coaches |
| `assigned_date` | DATE | When assigned | `2025-10-14` |
| `status` | VARCHAR(20) | Current status | `pending`, `in_progress`, `completed` |
| `progress_percentage` | INTEGER | % complete (0-100) | `60` |
| `coach_notes` | TEXT | Instructions from coach | `Focus on form...` |
| `created_at` | TIMESTAMP | When assigned | `2025-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last progress update | `2025-01-17 18:30:00` |

**Unique Constraint:** `(plan_id, player_id, assigned_date)` - Can't assign same plan twice on same day

**Status values:**
- `pending`: Assigned but player hasn't started
- `in_progress`: Player has completed some exercises
- `completed`: All exercises done

**Progress calculation:**
```
progress_percentage = (completed_exercises / total_exercises) * 100
```

**UI Usage:**
- Coach: "Assign Training" screen creates this
- Coach: "Training Assignments" list shows all assignments
- Player: "Training" tab shows their assignments
- Player: Training detail screen shows progress

---

### Table: `training_exercise_completion`
**Purpose:** Tracks which exercises within an assignment are completed.

**Columns:**
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `completion_id` | UUID (PK) | Unique identifier | `a1b2c3d4-...` |
| `assignment_id` | UUID (FK→player_training_assignments) | Which assignment | Links to assignments |
| `exercise_id` | UUID (FK→training_exercises) | Which exercise | Links to exercises |
| `completed` | BOOLEAN | Is it done? | `true` or `false` |
| `completed_at` | TIMESTAMP | When completed | `2025-01-16 14:30:00` |
| `created_at` | TIMESTAMP | When record created | `2025-01-15 10:30:00` |

**Unique Constraint:** `(assignment_id, exercise_id)` - Each exercise appears once per assignment

**How it works:**
1. When plan is assigned to player, create one completion record per exercise with `completed = false`
2. Player checks off exercise → Update `completed = true`, set `completed_at`
3. After each update, recalculate `progress_percentage` in assignments table

**UI Usage:**
- Player training detail screen shows checkboxes
- Checking exercise calls API to update this table
- Progress bar updates based on completed count

---

# 🔍 DATABASE INDEXES - PERFORMANCE OPTIMIZATION

## What are indexes?
Indexes are like a book's index - they help find data quickly without scanning every row. But they take up space and slow down writes (inserts/updates).

## Index Strategy:
- Add indexes for frequently queried columns
- Add composite indexes for common filter combinations
- Don't over-index (slows down writes)

---

## Events Table Indexes

```sql
CREATE INDEX idx_events_match ON events(match_id);
```
**Purpose:** Find all events for a specific match  
**Used in queries:** `WHERE match_id = X`  
**Use cases:**
- Loading match timeline
- Calculating match statistics
- Chatbot queries about a specific match

---

```sql
CREATE INDEX idx_events_player ON events(player_name);
```
**Purpose:** Find all events by a specific player  
**Used in queries:** `WHERE player_name = 'Marcus Silva'`  
**Use cases:**
- Player performance analysis
- Chatbot: "What did Marcus Silva do?"
- Season statistics calculation

---

```sql
CREATE INDEX idx_events_type ON events(event_type_name);
```
**Purpose:** Find all events of a specific type  
**Used in queries:** `WHERE event_type_name = 'Shot'`  
**Use cases:**
- Counting shots, passes, tackles
- Event type filtering
- Statistics calculation

---

```sql
CREATE INDEX idx_events_match_player ON events(match_id, player_name);
```
**Purpose:** Find all events by a player in a specific match (composite index)  
**Used in queries:** `WHERE match_id = X AND player_name = 'Marcus Silva'`  
**Use cases:**
- Player match statistics
- Chatbot: "What did Marcus do in this match?"
- Player timeline for specific match

**Why composite:** More efficient than using two separate indexes for this common query pattern

---

```sql
CREATE INDEX idx_events_match_type ON events(match_id, event_type_name);
```
**Purpose:** Find all events of a type in a match  
**Used in queries:** `WHERE match_id = X AND event_type_name = 'Shot'`  
**Use cases:**
- Chatbot: "Show all shots in this match"
- Match statistics calculation
- Event filtering

---

```sql
CREATE INDEX idx_events_player_type ON events(player_name, event_type_name);
```
**Purpose:** Find all events of a type by a player  
**Used in queries:** `WHERE player_name = 'Marcus Silva' AND event_type_name = 'Shot'`  
**Use cases:**
- Chatbot: "Show all of Marcus' shots this season"
- Player statistics by event type
- Performance analysis

---

```sql
CREATE INDEX idx_events_timestamp ON events(match_id, minute, second);
```
**Purpose:** Find events in a time range within a match  
**Used in queries:** `WHERE match_id = X AND minute BETWEEN 10 AND 20`  
**Use cases:**
- Chatbot: "What happened in the first 20 minutes?"
- Timeline queries
- Time-based filtering

---

```sql
CREATE INDEX idx_events_data ON events USING GIN (event_data);
```
**Purpose:** Efficiently query JSON data  
**Used in queries:** `WHERE event_data @> '{"type": {"name": "Shot"}}'` (JSON contains query)  
**Use cases:**
- Complex queries on event data
- Future feature queries
- Data analysis

**GIN Index:** Special type of index for JSONB columns that enables fast JSON queries

---

## Matches Table Index

```sql
CREATE INDEX idx_matches_club_date ON matches(club_id, match_date DESC);
```
**Purpose:** Get matches for a club ordered by date (newest first)  
**Used in queries:** `WHERE club_id = X ORDER BY match_date DESC`  
**Use cases:**
- Match list screen (shows recent matches first)
- Finding latest match
- Historical match queries

**DESC:** Index is ordered descending so newest matches are found first

---

## Goals Table Indexes

```sql
CREATE INDEX idx_goals_match ON goals(match_id);
```
**Purpose:** Find all goals in a match  
**Used in queries:** `WHERE match_id = X`  
**Use cases:**
- Match detail showing goals timeline
- Chatbot: "Show all goals in this match"
- Goals list

---

```sql
CREATE INDEX idx_goals_scorer ON goals(scorer_name);
```
**Purpose:** Find all goals by a player  
**Used in queries:** `WHERE scorer_name = 'Marcus Silva'`  
**Use cases:**
- Player goal history
- Chatbot: "How many goals did Marcus score?"
- Season goal statistics

---

## Heatmap/Pass/Shot Data Indexes

```sql
CREATE INDEX idx_heatmap_match_player ON match_heatmap_data(match_id, player_id);
CREATE INDEX idx_pass_match_player ON match_pass_data(match_id, player_id);
CREATE INDEX idx_shot_match_player ON match_shot_data(match_id, player_id);
```
**NOTE:** These are in the V1 strategy but REMOVED in V2 since visualizations are removed.

---

# 🌐 API ENDPOINTS - UI SCREEN MAPPING

## Authentication Endpoints

### `POST /api/auth/register/coach`
**Purpose:** Create a new coach account  
**UI Screen:** Coach Signup Screen  
**Request Body:**
```json
{
  "full_name": "John Smith",
  "email": "john@email.com",
  "password": "SecurePassword123",
  "birth_date": "1985-06-15",
  "gender": "Male"
}
```
**Response:**
```json
{
  "user_id": "uuid",
  "email": "john@email.com",
  "user_type": "coach",
  "token": "jwt_token_here"
}
```
**Data Flow:**
1. Hash password
2. Insert into `users` table (`user_type = 'coach'`)
3. Insert into `coaches` table
4. Generate JWT token
5. Return token to client

---

### `POST /api/auth/register/player`
**Purpose:** Create a new player account  
**UI Screen:** Player Signup Screen  
**Request Body:**
```json
{
  "full_name": "Marcus Silva",
  "email": "marcus@email.com",
  "password": "SecurePassword123",
  "birth_date": "2008-03-20",
  "jersey_number": 10,
  "height": "5'11\"",
  "weight": "165 lbs",
  "position": "Forward"
}
```
**Response:** Same as coach registration  
**Data Flow:**
1. Hash password
2. Insert into `users` table (`user_type = 'player'`)
3. Insert into `players` table (`is_linked = false` initially)
4. Generate JWT token
5. Return token

---

### `POST /api/auth/login`
**Purpose:** Login existing user  
**UI Screen:** Login Screen  
**Request Body:**
```json
{
  "email": "john@email.com",
  "password": "SecurePassword123"
}
```
**Response:**
```json
{
  "user_id": "uuid",
  "email": "john@email.com",
  "user_type": "coach",
  "token": "jwt_token_here"
}
```
**Data Flow:**
1. Query `users` table: `SELECT * FROM users WHERE email = ?`
2. Verify password hash matches
3. Generate JWT token with user info
4. Return token

---

### `POST /api/auth/verify-invite`
**Purpose:** Check if invite code is valid for a club  
**UI Screen:** Enter Invite Code Screen (Player)  
**Request Body:**
```json
{
  "invite_code": "ABC123XYZ"
}
```
**Response:**
```json
{
  "valid": true,
  "club_id": "uuid",
  "club_name": "Thunder United FC",
  "coach_name": "John Smith"
}
```
**Data Flow:**
1. Query `clubs` table: `SELECT * FROM clubs WHERE invite_code = ?`
2. If found, join with `users`/`coaches` to get coach name
3. Return club info

---

## Club Management Endpoints

### `POST /api/clubs`
**Purpose:** Create a new club  
**UI Screen:** Club Info Screen (after coach signup)  
**Request Body:**
```json
{
  "club_name": "Thunder United FC",
  "logo_url": "https://...logo.png",
  "country": "United States",
  "age_group": "U16",
  "stadium": "City Stadium"
}
```
**Response:**
```json
{
  "club_id": "uuid",
  "club_name": "Thunder United FC",
  "invite_code": "ABC123XYZ"
}
```
**Data Flow:**
1. Generate unique invite code
2. Insert into `clubs` table with coach_id from JWT
3. Initialize `club_season_statistics` record
4. Return club info with invite code

---

### `GET /api/clubs/{club_id}/statistics`
**Purpose:** Get club's season statistics  
**UI Screen:** Club Overview Screen  
**Response:**
```json
{
  "clubName": "Thunder United FC",
  "coachName": "John Smith",
  "standing": "3rd",
  "goalsScored": 45,
  "goalsConceded": 23,
  "cleanSheets": 8,
  "teamForm": ["W", "W", "D", "W", "L"],
  "basicStats": {
    "matchesPlayed": 22,
    "wins": 14,
    "losses": 4,
    "draws": 4,
    ...
  },
  "advancedStats": [...]
}
```
**Data Flow:**
1. Get club info: `SELECT * FROM clubs WHERE club_id = ?`
2. Get season stats: `SELECT * FROM club_season_statistics WHERE club_id = ? AND season = 'current'`
3. Get coach name: JOIN `users` and `coaches` tables
4. Combine and format response

---

### `GET /api/clubs/{club_id}/matches`
**Purpose:** Get all matches for a club  
**UI Screen:** Match list on Club Overview  
**Response:**
```json
{
  "matches": [
    {
      "id": "uuid",
      "opponent": "City Strikers",
      "date": "2025-10-08",
      "score": "3-2",
      "result": "win",
      "status": "completed"
    },
    ...
  ]
}
```
**Data Flow:**
1. Query matches: `SELECT * FROM matches WHERE club_id = ? ORDER BY match_date DESC`
2. Calculate result (win/draw/loss) from home_score and away_score
3. Format and return

---

## Match Management Endpoints

### `POST /api/matches`
**Purpose:** Create a new match  
**UI Screen:** Add Match Screen  
**Request Body:**
```json
{
  "opponent_name": "City Strikers",
  "match_date": "2025-10-08",
  "match_time": "15:30",
  "location": "City Stadium",
  "home_score": 3,
  "away_score": 2,
  "is_home_match": true,
  "video_url": "https://...video.mp4"
}
```
**Response:**
```json
{
  "match_id": "uuid",
  "opponent_name": "City Strikers",
  "match_status": "processing"
}
```
**Data Flow:**
1. Check if opponent exists in `teams` table
2. If not, create team record
3. Insert into `matches` table with `match_status = 'scheduled'`
4. If video_url provided, set status to 'processing' and trigger CV processing
5. Return match info

---

### `GET /api/matches/{match_id}`
**Purpose:** Get detailed match information  
**UI Screen:** Match Detail Screen  
**Response:**
```json
{
  "match_id": "uuid",
  "opponent": "City Strikers",
  "date": "2025-10-08",
  "time": "15:30",
  "location": "City Stadium",
  "home_score": 3,
  "away_score": 2,
  "result": "win",
  "status": "completed"
}
```
**Data Flow:**
1. Query match: `SELECT * FROM matches WHERE match_id = ?`
2. Calculate result from scores
3. Return match info

---

### `GET /api/matches/{match_id}/statistics`
**Purpose:** Get match statistics for both teams  
**UI Screen:** Match Detail Screen - Statistics Tab  
**Response:**
```json
{
  "home": {
    "possession": 58,
    "total_passes": 487,
    "pass_accuracy": 87,
    "total_shots": 14,
    "shots_on_target": 8,
    ...
  },
  "away": {
    "possession": 42,
    ...
  }
}
```
**Data Flow:**
1. Query stats: `SELECT * FROM match_statistics WHERE match_id = ?`
2. Get both home and away records (team_type = 'home' and 'away')
3. Format and return

---

### `GET /api/matches/{match_id}/goals`
**Purpose:** Get all goals in a match with timestamps  
**UI Screen:** Match Detail Screen - Shows goal timeline  
**Chatbot:** "Show me all goals in the match"  
**Response:**
```json
{
  "match_id": "uuid",
  "total_goals": 5,
  "goals": [
    {
      "goal_id": "uuid",
      "timestamp": "00:12:45.123",
      "minute": 12,
      "second": 45,
      "period": 1,
      "scorer": "Marcus Silva",
      "assist": "Jake Thompson",
      "team": "Thunder United FC",
      "goal_type": "Open Play"
    },
    ...
  ]
}
```
**Data Flow:**
1. Query goals: `SELECT * FROM goals WHERE match_id = ? ORDER BY minute, second`
2. Format and return chronologically

---

## Player Management Endpoints

### `GET /api/clubs/{club_id}/players`
**Purpose:** Get all players in a club  
**UI Screen:** Players List Screen  
**Response:**
```json
{
  "players": [
    {
      "id": "uuid",
      "jersey_number": 10,
      "name": "Marcus Silva",
      "position": "Forward",
      "is_linked": true,
      "goals": 12,
      "assists": 7
    },
    ...
  ]
}
```
**Data Flow:**
1. Query players: `SELECT * FROM players WHERE club_id = ? ORDER BY jersey_number`
2. For each player, get season stats: `SELECT goals, assists FROM player_season_statistics WHERE player_id = ? AND season = 'current'`
3. Format and return

---

### `GET /api/players/{player_id}`
**Purpose:** Get detailed player information  
**UI Screen:** Player Detail Screen  
**Response:**
```json
{
  "id": "uuid",
  "jersey_number": 10,
  "name": "Marcus Silva",
  "position": "Forward",
  "height": "5'11\"",
  "weight": "165 lbs",
  "is_linked": true,
  "seasonStats": {
    "matches_played": 22,
    "goals": 12,
    "assists": 7,
    ...
  },
  "attributes": {
    "attacking": 82,
    "technique": 64,
    "tactical": 52,
    "defending": 28,
    "creativity": 85
  }
}
```
**Data Flow:**
1. Query player: `SELECT * FROM players WHERE player_id = ?`
2. Query season stats: `SELECT * FROM player_season_statistics WHERE player_id = ? AND season = 'current'`
3. Combine and return

---

### `GET /api/players/{player_id}/statistics`
**Purpose:** Get player's season statistics  
**UI Screen:** Player Profile - Summary Tab  
**Response:** Same as season stats in player detail above  
**Data Flow:**
1. Query: `SELECT * FROM player_season_statistics WHERE player_id = ? AND season = 'current'`
2. Return stats

---

### `GET /api/players/{player_id}/matches`
**Purpose:** Get player's match history  
**UI Screen:** Player Detail - Matches Tab  
**Response:**
```json
{
  "matches": [
    {
      "match_id": "uuid",
      "opponent": "City Strikers",
      "date": "2025-10-08",
      "minutes_played": 90,
      "goals": 2,
      "assists": 1,
      "rating": 9.2
    },
    ...
  ]
}
```
**Data Flow:**
1. Query: 
```sql
SELECT m.*, pms.* 
FROM matches m
JOIN player_match_statistics pms ON m.match_id = pms.match_id
WHERE pms.player_id = ?
ORDER BY m.match_date DESC
```
2. Format and return

---

## Player Match Statistics Endpoint

### `GET /api/matches/{match_id}/players/{player_id}/stats`
**Purpose:** Get player's performance in a specific match  
**UI Screen:** Match Player Stats Screen  
**Response:**
```json
{
  "match": {
    "opponent": "City Strikers",
    "date": "2025-10-08",
    "home_score": 3,
    "away_score": 2
  },
  "player": {
    "name": "Marcus Silva",
    "jersey_number": 10
  },
  "stats": {
    "minutes_played": 90,
    "rating": 9.2,
    "goals": 2,
    "assists": 1,
    "shots": 6,
    "shots_on_target": 4,
    "total_passes": 52,
    "pass_accuracy": 89,
    ...
  }
}
```
**Data Flow:**
1. Query match: `SELECT * FROM matches WHERE match_id = ?`
2. Query player: `SELECT * FROM players WHERE player_id = ?`
3. Query stats: `SELECT * FROM player_match_statistics WHERE match_id = ? AND player_id = ?`
4. Combine and return

---

## Training Endpoints

### `POST /api/training-plans`
**Purpose:** Create a new training plan  
**UI Screen:** Create Training Plan Screen  
**Request Body:**
```json
{
  "plan_name": "Sprint Training",
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
  "plan_name": "Sprint Training",
  "duration": "2 weeks"
}
```
**Data Flow:**
1. Insert into `training_plans` table
2. For each exercise, insert into `training_exercises` table with `exercise_order`
3. Return plan info

---

### `POST /api/training-assignments`
**Purpose:** Assign a training plan to a player  
**UI Screen:** Assign Training Screen  
**Request Body:**
```json
{
  "plan_id": "uuid",
  "player_id": "uuid",
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
1. Insert into `player_training_assignments` table
2. Get all exercises for plan: `SELECT * FROM training_exercises WHERE plan_id = ?`
3. For each exercise, create completion record in `training_exercise_completion` with `completed = false`
4. Return assignment info

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
      "plan_name": "Sprint Training",
      "assigned_date": "2025-10-14",
      "status": "in_progress",
      "progress_percentage": 60,
      "coach_notes": "Focus on form..."
    },
    ...
  ]
}
```
**Data Flow:**
1. Query:
```sql
SELECT pta.*, tp.plan_name
FROM player_training_assignments pta
JOIN training_plans tp ON pta.plan_id = tp.plan_id
WHERE pta.player_id = ?
ORDER BY pta.assigned_date DESC
```
2. Return assignments

---

### `GET /api/training-assignments/{assignment_id}`
**Purpose:** Get detailed training assignment with exercises  
**UI Screen:** Training Detail Screen  
**Response:**
```json
{
  "assignment_id": "uuid",
  "plan_name": "Sprint Training",
  "status": "in_progress",
  "progress_percentage": 60,
  "coach_notes": "Focus on form...",
  "exercises": [
    {
      "exercise_id": "uuid",
      "exercise_name": "40m Sprints",
      "description": "Maximum effort...",
      "sets": "6",
      "reps": "1",
      "duration_minutes": "5",
      "completed": true,
      "completed_at": "2025-10-15T14:30:00Z"
    },
    ...
  ]
}
```
**Data Flow:**
1. Query assignment: `SELECT * FROM player_training_assignments WHERE assignment_id = ?`
2. Query plan: `SELECT * FROM training_plans WHERE plan_id = ?`
3. Query exercises with completion status:
```sql
SELECT te.*, tec.completed, tec.completed_at
FROM training_exercises te
JOIN training_exercise_completion tec ON te.exercise_id = tec.exercise_id
WHERE tec.assignment_id = ?
ORDER BY te.exercise_order
```
4. Combine and return

---

### `POST /api/training-assignments/{assignment_id}/complete-exercise/{exercise_id}`
**Purpose:** Mark an exercise as completed  
**UI Screen:** Training Detail Screen (player checks off exercise)  
**Request Body:** None (just POST to endpoint)  
**Response:**
```json
{
  "completed": true,
  "completed_at": "2025-10-15T14:30:00Z",
  "progress_percentage": 70
}
```
**Data Flow:**
1. Update completion: `UPDATE training_exercise_completion SET completed = true, completed_at = NOW() WHERE assignment_id = ? AND exercise_id = ?`
2. Recalculate progress:
```sql
SELECT 
  COUNT(CASE WHEN completed THEN 1 END) * 100.0 / COUNT(*) as progress
FROM training_exercise_completion
WHERE assignment_id = ?
```
3. Update assignment: `UPDATE player_training_assignments SET progress_percentage = ?, updated_at = NOW() WHERE assignment_id = ?`
4. If progress = 100, set status = 'completed'
5. Return updated progress

---

## Computer Vision Integration Endpoint

### `POST /api/cv/ingest`
**Purpose:** Receive and process StatsBomb JSON from CV system  
**UI Screen:** None (automated backend process)  
**Request Body:**
```json
{
  "match_id": "uuid",
  "statsbomb_data": [...] // Array of events from 15946.json format
}
```
**Response:**
```json
{
  "success": true,
  "match_id": "uuid",
  "events_processed": 3247,
  "goals_extracted": 5,
  "match_status": "completed"
}
```
**Data Flow:** (This is complex, see detailed section below)
1. Validate JSON format
2. Insert all events into `events` table
3. Extract goals into `goals` table
4. Calculate match statistics → `match_statistics`
5. Calculate player statistics → `player_match_statistics`
6. Update season statistics → `club_season_statistics`, `player_season_statistics`
7. Update match status to 'completed'
8. Return summary

---

## Chatbot Query Endpoints

### `GET /api/chatbot/match/{match_id}/shots`
**Purpose:** Get all shots in a match with timestamps  
**Chatbot Query:** "When did Marcus Silva shoot?"  
**Query Parameters:**
- `player_name` (optional): Filter by player
**Response:**
```json
{
  "match_id": "uuid",
  "player": "Marcus Silva",
  "total_shots": 6,
  "shots": [
    {
      "event_id": "uuid",
      "timestamp": "00:12:45.123",
      "minute": 12,
      "second": 45,
      "period": 1,
      "outcome": "Goal",
      "body_part": "Right Foot",
      "shot_type": "Open Play"
    },
    ...
  ]
}
```
**Data Flow:**
1. Query events:
```sql
SELECT *
FROM events
WHERE match_id = ? 
  AND event_type_name = 'Shot'
  AND (player_name = ? OR ? IS NULL)
ORDER BY minute, second
```
2. Format and return

---

### `GET /api/chatbot/match/{match_id}/passes`
**Purpose:** Get all passes in a match  
**Chatbot Query:** "How many passes did Jake complete?"  
**Query Parameters:**
- `player_name` (optional)
- `outcome` (optional): 'Complete' or 'Incomplete'
**Response:**
```json
{
  "match_id": "uuid",
  "player": "Jake Thompson",
  "total_passes": 52,
  "completed_passes": 46,
  "pass_accuracy": 88.46,
  "passes": [
    {
      "event_id": "uuid",
      "timestamp": "00:02:15.123",
      "minute": 2,
      "second": 15,
      "period": 1,
      "outcome": "Complete",
      "recipient": "Marcus Silva",
      "length": 12.5,
      "height": "Ground Pass",
      "body_part": "Right Foot"
    },
    ...
  ]
}
```
**Data Flow:**
1. Query events:
```sql
SELECT *
FROM events
WHERE match_id = ?
  AND event_type_name = 'Pass'
  AND (player_name = ? OR ? IS NULL)
  AND (outcome = ? OR ? IS NULL)
ORDER BY minute, second
```
2. Calculate totals and accuracy
3. Return

---

### `GET /api/chatbot/player/{player_name}/timeline`
**Purpose:** Get chronological timeline of all player events in a match  
**Chatbot Query:** "Show me everything Marcus Silva did in the match"  
**Query Parameters:**
- `match_id` (required)
**Response:**
```json
{
  "player": "Marcus Silva",
  "match_id": "uuid",
  "total_events": 234,
  "events": [
    {
      "timestamp": "00:01:30.123",
      "minute": 1,
      "second": 30,
      "period": 1,
      "event_type": "Pass",
      "outcome": "Complete",
      "details": "Pass to Jake Thompson"
    },
    {
      "timestamp": "00:12:45.123",
      "minute": 12,
      "second": 45,
      "period": 1,
      "event_type": "Shot",
      "outcome": "Goal",
      "details": "Right foot shot from open play"
    },
    ...
  ]
}
```
**Data Flow:**
1. Query all events for player:
```sql
SELECT *
FROM events
WHERE match_id = ?
  AND player_name = ?
ORDER BY minute, second
```
2. Format each event with human-readable details
3. Return chronologically

---

# 🔄 DATA FLOW - DETAILED QUERY OPERATIONS

## CV Data Ingestion - Complete Flow

This is the most complex operation, so here's the detailed breakdown:

### Input: StatsBomb JSON (like 15946.json)

```json
[
  {
    "id": "abb2c888-a3c9-424e-a26a-4b8377475ccf",
    "index": 601,
    "period": 1,
    "timestamp": "00:12:41.736",
    "minute": 12,
    "second": 41,
    "type": {"id": 30, "name": "Pass"},
    "possession": 19,
    "team": {"id": 217, "name": "Barcelona"},
    "player": {"id": 5470, "name": "Ivan Rakitić"},
    "position": {"id": 11, "name": "Left Defensive Midfield"},
    "location": [79.2, 8.9],
    "pass": {
      "recipient": {"id": 5211, "name": "Jordi Alba Ramos"},
      "length": 14.579781,
      "height": {"id": 1, "name": "Ground Pass"},
      "body_part": {"id": 40, "name": "Right Foot"},
      "end_location": [92.3, 2.5]
    }
  },
  // ... 3000+ more events
]
```

### Step 1: Store Events

**For each event in JSON:**

```sql
INSERT INTO events (
  event_id,
  match_id,
  event_index,
  event_type_id,
  event_type_name,
  period,
  timestamp,
  minute,
  second,
  team_id,
  team_name,
  player_id,
  player_name,
  position_id,
  position_name,
  duration,
  possession,
  play_pattern_id,
  play_pattern_name,
  -- Pass specific
  pass_recipient_id,
  pass_recipient_name,
  pass_length,
  pass_height,
  pass_body_part,
  pass_type,
  -- Shot specific
  shot_outcome,
  shot_body_part,
  shot_type,
  shot_technique,
  -- Defensive
  dribble_outcome,
  tackle_outcome,
  interception_outcome,
  -- Full data
  event_data,
  created_at
) VALUES (
  'abb2c888-a3c9-424e-a26a-4b8377475ccf',
  'match_uuid_here',
  601,
  30,
  'Pass',
  1,
  '00:12:41.736',
  12,
  41,
  217,
  'Barcelona',
  5470,
  'Ivan Rakitić',
  11,
  'Left Defensive Midfield',
  1.315766,
  19,
  1,
  'Regular Play',
  -- Pass data
  5211,
  'Jordi Alba Ramos',
  14.579781,
  'Ground Pass',
  'Right Foot',
  NULL,
  -- Shot data (NULL for pass event)
  NULL, NULL, NULL, NULL,
  -- Defensive (NULL for pass event)
  NULL, NULL, NULL,
  -- Full JSON
  '{"id": "abb2c888-...", ...}'::jsonb,
  NOW()
);
```

**Result:** 3000+ events inserted into `events` table

---

### Step 2: Extract Goals

**Find all shot events that resulted in goals:**

```sql
SELECT *
FROM events
WHERE match_id = 'match_uuid_here'
  AND event_type_name = 'Shot'
  AND shot_outcome IN ('Goal', 'Kick Off Goal', 'Corner Goal')
ORDER BY minute, second;
```

**For each goal, find the assist:**

```sql
-- Look backwards for the last pass to the scorer
SELECT *
FROM events
WHERE match_id = 'match_uuid_here'
  AND event_type_name = 'Pass'
  AND pass_recipient_name = 'Goal Scorer Name'
  AND minute <= goal_minute
  AND second <= goal_second
ORDER BY minute DESC, second DESC
LIMIT 1;
```

**Insert into goals table:**

```sql
INSERT INTO goals (
  match_id,
  event_id,
  scorer_player_id,
  scorer_name,
  assist_player_id,
  assist_name,
  period,
  minute,
  second,
  timestamp,
  goal_type,
  body_part,
  team_id,
  team_name
) VALUES (...);
```

**Result:** 5 goals extracted and stored in `goals` table

---

### Step 3: Calculate Match Statistics

**For home team and away team separately:**

**Count passes:**
```sql
SELECT
  COUNT(*) as total_passes,
  SUM(CASE WHEN outcome = 'Complete' THEN 1 ELSE 0 END) as completed_passes,
  SUM(CASE WHEN pass_length < 15 THEN 1 ELSE 0 END) as short_passes,
  SUM(CASE WHEN pass_length >= 15 THEN 1 ELSE 0 END) as long_passes
FROM events
WHERE match_id = 'match_uuid'
  AND team_id = 217  -- Barcelona
  AND event_type_name = 'Pass';
```

**Count shots:**
```sql
SELECT
  COUNT(*) as total_shots,
  SUM(CASE WHEN shot_outcome IN ('Goal', 'Saved', 'Saved To Post') THEN 1 ELSE 0 END) as shots_on_target,
  SUM(CASE WHEN shot_outcome IN ('Off Target', 'Wayward', 'Off T') THEN 1 ELSE 0 END) as shots_off_target,
  SUM(CASE WHEN shot_outcome = 'Blocked' THEN 1 ELSE 0 END) as blocked_shots,
  SUM(CASE WHEN shot_outcome LIKE '%Goal%' THEN 1 ELSE 0 END) as goals
FROM events
WHERE match_id = 'match_uuid'
  AND team_id = 217
  AND event_type_name = 'Shot';
```

**Count dribbles:**
```sql
SELECT
  COUNT(*) as total_dribbles,
  SUM(CASE WHEN dribble_outcome = 'Complete' THEN 1 ELSE 0 END) as successful_dribbles
FROM events
WHERE match_id = 'match_uuid'
  AND team_id = 217
  AND event_type_name = 'Dribble';
```

**Count tackles:**
```sql
SELECT
  COUNT(*) as tackles,
  SUM(CASE WHEN tackle_outcome IN ('Won', 'Success') THEN 1 ELSE 0 END) as tackles_won
FROM events
WHERE match_id = 'match_uuid'
  AND team_id = 217
  AND event_type_name = 'Tackle';
```

**Calculate possession:**
```sql
-- Count events by team
SELECT
  team_id,
  COUNT(*) as event_count
FROM events
WHERE match_id = 'match_uuid'
  AND event_type_name IN ('Pass', 'Carry', 'Dribble', 'Shot')
GROUP BY team_id;

-- Possession % = team_events / total_events * 100
```

**Insert statistics:**
```sql
INSERT INTO match_statistics (
  match_id,
  team_type,
  possession_percentage,
  total_passes,
  completed_passes,
  pass_accuracy,
  short_passes,
  long_passes,
  total_shots,
  shots_on_target,
  goals,
  total_dribbles,
  successful_dribbles,
  tackles,
  tackles_won,
  ...
) VALUES (
  'match_uuid',
  'home',
  58.50,
  487,
  423,
  86.86,
  350,
  137,
  14,
  8,
  3,
  25,
  18,
  16,
  12,
  ...
);

-- Insert again for away team with their stats
```

**Result:** 2 records in `match_statistics` (home and away)

---

### Step 4: Calculate Player Match Statistics

**For each player who participated:**

**Get player's events:**
```sql
SELECT
  player_name,
  COUNT(*) as total_events,
  -- Pass stats
  SUM(CASE WHEN event_type_name = 'Pass' THEN 1 ELSE 0 END) as total_passes,
  SUM(CASE WHEN event_type_name = 'Pass' AND outcome = 'Complete' THEN 1 ELSE 0 END) as completed_passes,
  -- Shot stats
  SUM(CASE WHEN event_type_name = 'Shot' THEN 1 ELSE 0 END) as shots,
  SUM(CASE WHEN event_type_name = 'Shot' AND shot_outcome LIKE '%Goal%' THEN 1 ELSE 0 END) as goals,
  -- Dribble stats
  SUM(CASE WHEN event_type_name = 'Dribble' THEN 1 ELSE 0 END) as total_dribbles,
  SUM(CASE WHEN event_type_name = 'Dribble' AND dribble_outcome = 'Complete' THEN 1 ELSE 0 END) as successful_dribbles,
  -- Tackle stats
  SUM(CASE WHEN event_type_name = 'Tackle' THEN 1 ELSE 0 END) as tackles,
  SUM(CASE WHEN event_type_name = 'Tackle' AND tackle_outcome IN ('Won', 'Success') THEN 1 ELSE 0 END) as tackles_won,
  -- ... more stats
FROM events
WHERE match_id = 'match_uuid'
  AND player_name IS NOT NULL
GROUP BY player_name;
```

**Count assists for player:**
```sql
SELECT COUNT(*) as assists
FROM goals
WHERE match_id = 'match_uuid'
  AND assist_name = 'Marcus Silva';
```

**Calculate minutes played:**
```sql
-- Find player's first and last event
SELECT
  MIN(minute * 60 + second) as first_event_seconds,
  MAX(minute * 60 + second) as last_event_seconds
FROM events
WHERE match_id = 'match_uuid'
  AND player_name = 'Marcus Silva';

-- minutes_played = (last - first) / 60
```

**Calculate rating (simplified formula):**
```
rating = 6.0 (base)
  + (goals * 0.5)
  + (assists * 0.3)
  + (pass_accuracy / 100 * 1.5)
  + (successful_dribbles * 0.1)
  + (tackles_won * 0.05)
  - (dispossessed * 0.2)
  - (fouls * 0.1)
```

**Insert player stats:**
```sql
INSERT INTO player_match_statistics (
  match_id,
  player_id,
  minutes_played,
  rating,
  goals,
  assists,
  shots,
  shots_on_target,
  total_passes,
  completed_passes,
  pass_accuracy,
  total_dribbles,
  successful_dribbles,
  tackles,
  tackles_won,
  ...
) VALUES (...);
```

**Result:** 22 records in `player_match_statistics` (11 players per team)

---

### Step 5: Update Season Statistics

**For club statistics:**

```sql
-- Get or create season record
INSERT INTO club_season_statistics (club_id, season, ...)
VALUES ('club_uuid', '2024-2025', 0, 0, ...)
ON CONFLICT (club_id, season) DO NOTHING;

-- Update statistics
UPDATE club_season_statistics SET
  matches_played = matches_played + 1,
  wins = wins + CASE WHEN home_score > away_score THEN 1 ELSE 0 END,
  draws = draws + CASE WHEN home_score = away_score THEN 1 ELSE 0 END,
  losses = losses + CASE WHEN home_score < away_score THEN 1 ELSE 0 END,
  goals_scored = goals_scored + home_score,
  goals_conceded = goals_conceded + away_score,
  clean_sheets = clean_sheets + CASE WHEN away_score = 0 THEN 1 ELSE 0 END,
  -- Update team_form array
  team_form = (
    CASE 
      WHEN home_score > away_score THEN '"W"'
      WHEN home_score = away_score THEN '"D"'
      ELSE '"L"'
    END || COALESCE(team_form, '[]')::jsonb
  )::jsonb,
  updated_at = NOW()
WHERE club_id = 'club_uuid' AND season = '2024-2025';

-- Recalculate averages
UPDATE club_season_statistics SET
  avg_possession = (
    SELECT AVG(possession_percentage)
    FROM match_statistics
    WHERE match_id IN (
      SELECT match_id FROM matches WHERE club_id = 'club_uuid'
    )
  ),
  avg_passes = (
    SELECT AVG(total_passes)
    FROM match_statistics
    WHERE match_id IN (
      SELECT match_id FROM matches WHERE club_id = 'club_uuid'
    )
  ),
  -- ... recalculate all averages
WHERE club_id = 'club_uuid' AND season = '2024-2025';
```

**For player season statistics:**

```sql
-- Update for each player
UPDATE player_season_statistics SET
  matches_played = matches_played + 1,
  minutes_played = minutes_played + NEW.minutes_played,
  goals = goals + NEW.goals,
  assists = assists + NEW.assists,
  total_passes = total_passes + NEW.total_passes,
  completed_passes = completed_passes + NEW.completed_passes,
  total_shots = total_shots + NEW.shots,
  shots_on_target = shots_on_target + NEW.shots_on_target,
  -- ... update all stats
  updated_at = NOW()
WHERE player_id = 'player_uuid' AND season = '2024-2025';

-- Recalculate averages
UPDATE player_season_statistics SET
  pass_accuracy = (completed_passes * 100.0 / NULLIF(total_passes, 0)),
  average_rating = (
    SELECT AVG(rating)
    FROM player_match_statistics
    WHERE player_id = 'player_uuid'
  ),
  average_distance = total_distance / NULLIF(matches_played, 0),
  -- ... recalculate all averages and percentages
WHERE player_id = 'player_uuid' AND season = '2024-2025';

-- Recalculate attribute ratings
UPDATE player_season_statistics SET
  attacking_rating = LEAST(100, GREATEST(0,
    (goals * 5) + (shots * 0.5) + (expected_goals * 3)
  )),
  technique_rating = LEAST(100, GREATEST(0,
    pass_accuracy + (successful_dribbles * 0.3)
  )),
  -- ... calculate other attributes
WHERE player_id = 'player_uuid' AND season = '2024-2025';
```

---

### Step 6: Update Match Status

```sql
UPDATE matches
SET
  match_status = 'completed',
  updated_at = NOW()
WHERE match_id = 'match_uuid';
```

---

## Summary of CV Ingestion Data Flow

**Input:** StatsBomb JSON with ~3000 events  
**Processing Time:** ~30-60 seconds  
**Database Operations:**
- ~3000 INSERTs into `events` table
- ~5 INSERTs into `goals` table
- 2 INSERTs into `match_statistics` table (home + away)
- ~22 INSERTs into `player_match_statistics` table
- ~1 UPDATE or INSERT into `club_season_statistics` table
- ~22 UPDATEs into `player_season_statistics` table
- 1 UPDATE to `matches` table

**Total:** ~3050 database operations

**Result:** Complete match data available for:
- Match detail screens
- Player statistics
- Season statistics
- Chatbot queries

---

# 📊 SUMMARY

This guide covered:

✅ **17 database tables** with every column explained  
✅ **9 database indexes** with query optimization details  
✅ **30+ API endpoints** mapped to UI screens  
✅ **Complete data flows** with SQL examples  
✅ **CV ingestion pipeline** with step-by-step process  

You now have a complete understanding of:
- What each table stores and why
- How data flows from UI → API → Database
- How CV data is processed and stored
- How chatbot queries work
- How statistics are calculated

Ready to provide feedback or suggest changes!
