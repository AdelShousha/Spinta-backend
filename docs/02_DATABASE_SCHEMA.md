# Database Schema

## Overview

This document provides the complete database schema for the Spinta platform. All tables are PostgreSQL-compatible with UUID primary keys.

## Schema Diagram

```
users
  ↓ (1:1 via user_id)
  ├─→ coaches ──→ clubs
  │                ↓ (1:N)
  └─→ players ←────┘
         ↓
    training_plans ←──── training_exercises

players ←──── matches ──→ opponent_clubs
  ↓ (N:N via matches)     ↓
  │                   opponent_players
  ↓
match_statistics
  ↓           ↓
  goals     events

Statistics Tables (aggregated):
- club_season_statistics (from match_statistics)
- player_season_statistics (from player_match_statistics)
- player_match_statistics (from events)

Key relationships:
- users.user_id → coaches.user_id (1:1, always linked)
- users.user_id → players.user_id (1:1, NULL before signup, linked after)
- coaches.coach_id → clubs.coach_id (1:1)
- clubs.club_id → players.club_id (1:N)
```

## Tables

### 1. users

Stores all user accounts (both coaches and players).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email (login) |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| full_name | VARCHAR(255) | NOT NULL | User's full name |
| user_type | VARCHAR(20) | NOT NULL | 'coach' or 'player' |
| created_at | TIMESTAMP | NOT NULL | Account creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- `idx_users_email` on `email`
- `idx_users_user_type` on `user_type`

**Relationships:**
- One-to-one with `coaches` table (via coaches.user_id)
- One-to-one with `players` table (via players.user_id, when player signs up)

**Notes:**
- `user_id` is referenced by both coaches and players tables via their user_id foreign keys
- For coaches: Created during coach registration, coach record immediately linked via user_id
- For players: Created during player signup, player.user_id is set to link to the user account
- `password_hash` should use bcrypt or similar
- `user_type` used for role-based access control ('coach' or 'player')

---

### 2. coaches

Stores coach-specific information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| coach_id | UUID | PRIMARY KEY | Unique coach identifier |
| user_id | UUID | FOREIGN KEY → users(user_id), UNIQUE, NOT NULL | Reference to user account |
| birth_date | DATE | NULL | Coach's birth date |
| gender | VARCHAR(20) | NULL | Coach's gender |
| created_at | TIMESTAMP | NOT NULL | Record creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- `idx_coaches_user_id` on `user_id`

**Relationships:**
- One-to-one with `users` table (via user_id)
- One-to-one with `clubs` table (coach creates one club)

**Notes:**
- `coach_id` is a separate primary key (auto-generated UUID)
- `user_id` is a foreign key to users table with UNIQUE constraint (one coach per user)
- When a user registers as a coach, a coach record is created with their user_id
- Profile image removed (not needed per requirements)

---

### 3. clubs

Stores club/team information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| club_id | UUID | PRIMARY KEY | Unique club identifier |
| coach_id | UUID | FOREIGN KEY → coaches(coach_id), UNIQUE | Owner coach |
| club_name | VARCHAR(255) | NOT NULL | Club name |
| statsbomb_team_id | INTEGER | UNIQUE, NULL | StatsBomb team ID |
| country | VARCHAR(100) | NULL | Club country |
| age_group | ENUM | NULL | Team age group: U6, U8, U10, U12, U14, U16, U18, U21, or Senior (18+) |
| stadium | VARCHAR(255) | NULL | Home stadium name |
| logo_url | TEXT | NULL | Club logo image URL |
| created_at | TIMESTAMP | NOT NULL | Club creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- `idx_clubs_coach_id` on `coach_id`

**Relationships:**
- One-to-one with `coaches` table
- One-to-many with `players` table
- One-to-many with `matches` table

**Notes:**
- Each coach can only create one club (enforced by UNIQUE constraint on coach_id)
- `invite_code` removed (moved to players table)
- `statsbomb_team_id` is NULL initially, automatically populated from first match upload
- Used to match club to StatsBomb event data

---

### 4. players

Stores player profiles, including incomplete players (before signup).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| player_id | UUID | PRIMARY KEY | Unique player identifier |
| user_id | UUID | FOREIGN KEY → users(user_id), UNIQUE, NULL | Reference to user account (NULL before signup) |
| club_id | UUID | FOREIGN KEY → clubs(club_id), NOT NULL | Player's club |
| player_name | VARCHAR(255) | NOT NULL | Player name (before and after signup) |
| statsbomb_player_id | INTEGER | NULL | StatsBomb player ID from data |
| jersey_number | INTEGER | NOT NULL | Player's jersey number |
| position | VARCHAR(50) | NOT NULL | Player position |
| invite_code | VARCHAR(10) | UNIQUE, NOT NULL | Unique signup code |
| is_linked | BOOLEAN | NOT NULL, DEFAULT FALSE | Has player signed up? |
| linked_at | TIMESTAMP | NULL | When player completed signup |
| birth_date | DATE | NULL | Player's birth date (filled on signup) |
| height | INTEGER | NULL | Player height in cm (filled on signup) |
| profile_image_url | TEXT | NULL | Profile photo URL (filled on signup) |
| created_at | TIMESTAMP | NOT NULL | Record creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- `idx_players_user_id` on `user_id`
- `idx_players_club_id` on `club_id`
- `idx_players_invite_code` on `invite_code`
- `idx_players_is_linked` on `is_linked`
- `idx_players_statsbomb_player_id` on `statsbomb_player_id`

**Unique Constraints:**
- `invite_code` must be unique across all players
- `user_id` must be unique when not NULL (one player per user account)

**Relationships:**
- Many-to-one with `clubs` table
- One-to-one with `users` table (after signup, via user_id)
- One-to-many with `training_plans` table

**Notes:**
- **player_id vs user_id**:
  - `player_id` is a separate primary key (auto-generated UUID)
  - `user_id` is NULL for incomplete players (before signup)
  - `user_id` is set when player completes signup, linking to their user account
  - UNIQUE constraint on user_id ensures one player per user account

- **Incomplete players** (before signup):
  - Created by admin during match processing
  - Have `player_name`, `statsbomb_player_id`, `jersey_number`, `position`, `invite_code`
  - `is_linked = FALSE`, `user_id = NULL`
  - `birth_date`, `height`, `profile_image_url` are NULL

- **Complete players** (after signup):
  - User account created and `user_id` field is set
  - `is_linked = TRUE`, `linked_at = NOW()`
  - `user_id` links to users table
  - All profile fields filled

- **Player name handling**:
  - Stored in both `players.player_name` and `users.full_name` after signup
  - Player can change name during signup
  - `player_name` is the source of truth for display (even before signup)

- **StatsBomb integration**:
  - `statsbomb_player_id` provided by admin from CV/StatsBomb data
  - Used to link events to players
  - Can be NULL for players added manually

---

### 5. opponent_clubs

Stores opponent team information (not managed by our coaches).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| opponent_club_id | UUID | PRIMARY KEY | Opponent club identifier |
| opponent_name | VARCHAR(255) | NOT NULL | Opponent team name |
| statsbomb_team_id | INTEGER | UNIQUE, NULL | StatsBomb team ID |
| logo_url | TEXT | NULL | Opponent logo URL |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Relationships:**
- One-to-many with `matches` table
- One-to-many with `opponent_players` table

**Notes:**
- Replaces the old `teams` table
- Only stores basic info (name, logo, StatsBomb ID)
- Not linked to user accounts
- Created automatically when processing matches
- `statsbomb_team_id` extracted from match event data

---

### 6. matches

Stores match records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| match_id | UUID | PRIMARY KEY | Unique match identifier |
| club_id | UUID | FOREIGN KEY → clubs(club_id), NOT NULL | Our club |
| opponent_club_id | UUID | FOREIGN KEY → opponent_clubs(opponent_club_id) | Opponent team |
| opponent_name | VARCHAR(255) | NOT NULL | Opponent name (denormalized) |
| match_date | DATE | NOT NULL | Match date |
| match_time | TIME | NULL | Match kickoff time |
| is_home_match | BOOLEAN | NOT NULL | Is this a home match? |
| home_score | INTEGER | NULL | Final home team score |
| away_score | INTEGER | NULL | Final away team score |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Indexes:**
- `idx_matches_club_id` on `club_id`
- `idx_matches_match_date` on `match_date`

**Relationships:**
- Many-to-one with `clubs` table
- Many-to-one with `opponent_clubs` table
- One-to-many with `goals` table
- One-to-many with `events` table
- One-to-one with `match_statistics` table

**Notes:**
- Removed: `match_status`, `video_url`, `statsbomb_match_id` (not needed)
- `opponent_name` is denormalized for easier queries
- Scores are NULL until match is completed
- Created by coach uploading match video and StatsBomb data

---

### 7. opponent_players

Stores opponent team players for lineup display purposes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| opponent_player_id | UUID | PRIMARY KEY | Opponent player identifier |
| opponent_club_id | UUID | FOREIGN KEY → opponent_clubs(opponent_club_id), NOT NULL | Opponent club |
| player_name | VARCHAR(255) | NOT NULL | Player name from event data |
| statsbomb_player_id | INTEGER | NULL | StatsBomb player ID |
| jersey_number | INTEGER | NULL | Player's jersey number |
| position | VARCHAR(50) | NULL | Player position |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Indexes:**
- `idx_opponent_players_opponent_club_id` on `opponent_club_id`
- `idx_opponent_players_statsbomb_player_id` on `statsbomb_player_id`

**Relationships:**
- Many-to-one with `opponent_clubs` table

**Notes:**
- Created automatically from match Starting XI events
- Used ONLY for lineup display in match details
- No individual statistics tracked (only team-level stats in match_statistics)
- Duplicate checking: Match by (opponent_club_id, statsbomb_player_id) or (opponent_club_id, player_name, jersey_number)

---

### 8. goals

Stores goal events from matches.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| goal_id | UUID | PRIMARY KEY | Unique goal identifier |
| match_id | UUID | FOREIGN KEY → matches(match_id), NOT NULL | Match reference |
| team_name | VARCHAR(255) | NOT NULL | Team that scored |
| scorer_name | VARCHAR(255) | NOT NULL | Player who scored |
| assist_name | VARCHAR(255) | NULL | Player who assisted |
| minute | INTEGER | NOT NULL | Match minute |
| second | INTEGER | NULL | Second within minute |
| period | INTEGER | NOT NULL | Match period (1, 2, etc.) |
| goal_type | VARCHAR(50) | NULL | Type of goal (Open Play, Penalty, etc.) |
| body_part | VARCHAR(50) | NULL | Body part used (Right Foot, Header, etc.) |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Indexes:**
- `idx_goals_match_id` on `match_id`

**Relationships:**
- Many-to-one with `matches` table

**Notes:**
- Extracted from StatsBomb events
- `team_name` can be our club or opponent
- Used for goals timeline display in match details

---

### 9. events

Stores raw StatsBomb event data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| event_id | UUID | PRIMARY KEY | Unique event identifier |
| match_id | UUID | FOREIGN KEY → matches(match_id), NOT NULL | Match reference |
| statsbomb_player_id | INTEGER | NULL | StatsBomb player ID |
| statsbomb_team_id | INTEGER | NULL | StatsBomb team ID |
| player_name | VARCHAR(255) | NULL | Player name from event |
| team_name | VARCHAR(255) | NULL | Team name from event |
| event_type_name | VARCHAR(100) | NULL | Event type (Pass, Shot, etc.) |
| position_name | VARCHAR(50) | NULL | Player position |
| minute | INTEGER | NULL | Match minute |
| second | INTEGER | NULL | Second within minute |
| period | INTEGER | NULL | Match period |
| event_data | JSONB | NULL | Full event JSON data |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Indexes:**
- `idx_events_match_id` on `match_id`
- `idx_events_statsbomb_player_id` on `statsbomb_player_id`
- `idx_events_event_type_name` on `event_type_name`
- `idx_events_event_data` on `event_data` using GIN

**Relationships:**
- Many-to-one with `matches` table

**Notes:**
- Raw StatsBomb data stored for processing
- `event_data` contains full JSON for flexibility
- Used to calculate player and match statistics
- Links to players via `statsbomb_player_id`

**JSONB Query Examples (Efficient Use of GIN Index):**

```sql
-- ✓ GOOD: Uses GIN index efficiently (containment operator @>)
SELECT * FROM events
WHERE event_data @> '{"type": {"name": "Shot"}}'::jsonb;

SELECT * FROM events
WHERE event_data @> '{"shot": {"outcome": {"name": "Goal"}}}'::jsonb;

-- ✓ GOOD: Uses existence operator (?)
SELECT * FROM events
WHERE event_data->'pass' ? 'goal_assist';

-- ✓ GOOD: Combined containment checks
SELECT * FROM events
WHERE event_data @> '{"type": {"name": "Pass"}}'::jsonb
  AND event_data->'pass' ? 'goal_assist';

-- ✗ BAD: Full table scan (doesn't use GIN index properly)
SELECT * FROM events
WHERE event_data->>'type' = 'Shot';

SELECT * FROM events
WHERE event_data->'shot'->'outcome'->>'name' = 'Goal';

-- Extract nested values efficiently (use after filtering with @>)
SELECT
  event_data->>'player_name' as player,
  (event_data->'shot'->>'statsbomb_xg')::numeric as xg
FROM events
WHERE event_data @> '{"type": {"name": "Shot"}}'::jsonb
  AND event_data @> '{"shot": {"outcome": {"name": "Goal"}}}'::jsonb;
```

---

### 10. match_statistics

Stores aggregated statistics per match (for both teams).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| statistics_id | UUID | PRIMARY KEY | Unique statistics record ID |
| match_id | UUID | FOREIGN KEY → matches(match_id), NOT NULL | Match reference |
| team_type | VARCHAR(20) | NOT NULL | 'our_team' or 'opponent_team' |
| possession_percentage | DECIMAL(5,2) | NULL | Ball possession % |
| expected_goals | DECIMAL(8,6) | NULL | xG (StatsBomb uses up to 8 decimal places) |
| total_shots | INTEGER | NULL | Total shots |
| shots_on_target | INTEGER | NULL | Shots on target |
| shots_off_target | INTEGER | NULL | Shots off target |
| goalkeeper_saves | INTEGER | NULL | Saves by goalkeeper |
| total_passes | INTEGER | NULL | Total passes |
| passes_completed | INTEGER | NULL | Completed passes |
| pass_completion_rate | DECIMAL(5,2) | NULL | Pass accuracy % |
| passes_in_final_third | INTEGER | NULL | Passes in final third |
| long_passes | INTEGER | NULL | Long passes |
| crosses | INTEGER | NULL | Crosses |
| total_dribbles | INTEGER | NULL | Dribbles attempted |
| successful_dribbles | INTEGER | NULL | Successful dribbles |
| total_tackles | INTEGER | NULL | Tackles attempted |
| tackle_success_percentage | DECIMAL(5,2) | NULL | Tackle success % |
| interceptions | INTEGER | NULL | Interceptions |
| ball_recoveries | INTEGER | NULL | Ball recoveries |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Indexes:**
- `idx_match_statistics_match_id` on `match_id`
- Unique constraint on (`match_id`, `team_type`)

**Relationships:**
- Many-to-one with `matches` table (2 records per match: our team + opponent)

**Notes:**
- One record for our team (`team_type = 'our_team'`)
- One record for opponent (`team_type = 'opponent_team'`)
- Calculated from `events` table after match processing
- Used for match detail screen statistics comparison

---

### 11. player_match_statistics

Stores individual player statistics per match.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| player_match_stats_id | UUID | PRIMARY KEY | Unique record ID |
| player_id | UUID | FOREIGN KEY → players(player_id), NOT NULL | Player reference |
| match_id | UUID | FOREIGN KEY → matches(match_id), NOT NULL | Match reference |
| goals | INTEGER | DEFAULT 0 | Goals scored |
| assists | INTEGER | DEFAULT 0 | Assists |
| expected_goals | DECIMAL(8,6) | NULL | Player xG (StatsBomb uses up to 8 decimal places) |
| shots | INTEGER | NULL | Total shots |
| shots_on_target | INTEGER | NULL | Shots on target |
| total_dribbles | INTEGER | NULL | Dribbles attempted |
| successful_dribbles | INTEGER | NULL | Successful dribbles |
| total_passes | INTEGER | NULL | Total passes |
| completed_passes | INTEGER | NULL | Completed passes |
| short_passes | INTEGER | NULL | Short passes |
| long_passes | INTEGER | NULL | Long passes |
| final_third_passes | INTEGER | NULL | Passes in final third |
| crosses | INTEGER | NULL | Crosses |
| tackles | INTEGER | NULL | Tackles |
| tackle_success_rate | DECIMAL(5,2) | NULL | Tackle success % |
| interceptions | INTEGER | NULL | Interceptions |
| interception_success_rate | DECIMAL(5,2) | NULL | Interception success % |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Indexes:**
- `idx_player_match_statistics_player_id` on `player_id`
- `idx_player_match_statistics_match_id` on `match_id`
- Unique constraint on (`player_id`, `match_id`)

**Relationships:**
- Many-to-one with `players` table
- Many-to-one with `matches` table

**Notes:**
- One record per player per match
- Calculated from `events` table using `statsbomb_player_id`
- Used for player match detail screen
- Aggregated into `player_season_statistics`

---

### 12. club_season_statistics

Aggregated season statistics for clubs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| club_stats_id | UUID | PRIMARY KEY | Unique record ID |
| club_id | UUID | FOREIGN KEY → clubs(club_id), UNIQUE, NOT NULL | Club reference |
| matches_played | INTEGER | DEFAULT 0 | Total matches played |
| wins | INTEGER | DEFAULT 0 | Wins |
| draws | INTEGER | DEFAULT 0 | Draws |
| losses | INTEGER | DEFAULT 0 | Losses |
| goals_scored | INTEGER | DEFAULT 0 | Total goals scored |
| goals_conceded | INTEGER | DEFAULT 0 | Total goals conceded |
| total_clean_sheets | INTEGER | DEFAULT 0 | Clean sheets |
| avg_goals_per_match | DECIMAL(5,2) | NULL | Avg goals per match |
| avg_possession_percentage | DECIMAL(5,2) | NULL | Avg possession % |
| avg_total_shots | DECIMAL(5,2) | NULL | Avg shots per match |
| avg_shots_on_target | DECIMAL(5,2) | NULL | Avg shots on target |
| avg_xg_per_match | DECIMAL(5,2) | NULL | Avg xG per match |
| avg_goals_conceded_per_match | DECIMAL(5,2) | NULL | Avg goals conceded |
| avg_total_passes | DECIMAL(5,2) | NULL | Avg passes per match |
| pass_completion_rate | DECIMAL(5,2) | NULL | Overall pass accuracy % |
| avg_final_third_passes | DECIMAL(5,2) | NULL | Avg final third passes |
| avg_crosses | DECIMAL(5,2) | NULL | Avg crosses per match |
| avg_dribbles | DECIMAL(5,2) | NULL | Avg dribbles per match |
| avg_successful_dribbles | DECIMAL(5,2) | NULL | Avg successful dribbles |
| avg_tackles | DECIMAL(5,2) | NULL | Avg tackles per match |
| tackle_success_rate | DECIMAL(5,2) | NULL | Overall tackle success % |
| avg_interceptions | DECIMAL(5,2) | NULL | Avg interceptions |
| interception_success_rate | DECIMAL(5,2) | NULL | Overall interception success % |
| avg_ball_recoveries | DECIMAL(5,2) | NULL | Avg ball recoveries |
| avg_saves_per_match | DECIMAL(5,2) | NULL | Avg goalkeeper saves |
| created_at | TIMESTAMP | NOT NULL | Record creation time |
| updated_at | TIMESTAMP | NOT NULL | Last calculation time |

**Indexes:**
- `idx_club_season_statistics_club_id` on `club_id` (UNIQUE)

**Relationships:**
- One-to-one with `clubs` table

**Notes:**
- One record per club (UNIQUE constraint on club_id)
- Recalculated after each new match
- Aggregated from `match_statistics` table
- Used for coach dashboard display
- Team form calculated from recent match results (not stored, calculated on-the-fly)

---

### 13. player_season_statistics

Aggregated season statistics for players.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| player_stats_id | UUID | PRIMARY KEY | Unique record ID |
| player_id | UUID | FOREIGN KEY → players(player_id), UNIQUE, NOT NULL | Player reference |
| matches_played | INTEGER | DEFAULT 0 | Matches played |
| goals | INTEGER | DEFAULT 0 | Total goals |
| assists | INTEGER | DEFAULT 0 | Total assists |
| expected_goals | DECIMAL(8,6) | NULL | Total xG (StatsBomb uses up to 8 decimal places) |
| shots_per_game | DECIMAL(5,2) | NULL | Avg shots per game |
| shots_on_target_per_game | DECIMAL(5,2) | NULL | Avg shots on target |
| total_passes | INTEGER | NULL | Total passes |
| passes_completed | INTEGER | NULL | Completed passes |
| total_dribbles | INTEGER | NULL | Total dribbles |
| successful_dribbles | INTEGER | NULL | Successful dribbles |
| tackles | INTEGER | NULL | Total tackles |
| tackle_success_rate | DECIMAL(5,2) | NULL | Tackle success % |
| interceptions | INTEGER | NULL | Total interceptions |
| interception_success_rate | DECIMAL(5,2) | NULL | Interception success % |
| attacking_rating | INTEGER | NULL | Attacking attribute (0-100) |
| technique_rating | INTEGER | NULL | Technique attribute (0-100) |
| tactical_rating | INTEGER | NULL | Tactical attribute (0-100) |
| defending_rating | INTEGER | NULL | Defending attribute (0-100) |
| creativity_rating | INTEGER | NULL | Creativity attribute (0-100) |
| created_at | TIMESTAMP | NOT NULL | Record creation time |
| updated_at | TIMESTAMP | NOT NULL | Last calculation time |

**Indexes:**
- `idx_player_season_statistics_player_id` on `player_id` (UNIQUE)

**Relationships:**
- One-to-one with `players` table

**Notes:**
- One record per player (UNIQUE constraint on player_id)
- Recalculated after each new match
- Aggregated from `player_match_statistics` table
- Attributes calculated from season stats using formulas
- Used for player dashboard and profile screens
- Exists for all players (both linked and unlinked players)

---

### 14. training_plans

Stores training plans assigned to players.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| plan_id | UUID | PRIMARY KEY | Unique plan ID |
| player_id | UUID | FOREIGN KEY → players(player_id), NOT NULL | Assigned player |
| plan_name | VARCHAR(255) | NOT NULL | Plan name |
| duration | VARCHAR(50) | NULL | Duration (e.g., "2 weeks") |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 'pending', 'in_progress', 'completed' |
| coach_notes | TEXT | NULL | Instructions from coach |
| created_by | UUID | FOREIGN KEY → coaches(coach_id), NOT NULL | Coach who created plan |
| created_at | TIMESTAMP | NOT NULL | Plan creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- `idx_training_plans_player_id` on `player_id`
- `idx_training_plans_status` on `status`

**Relationships:**
- Many-to-one with `players` table
- Many-to-one with `coaches` table
- One-to-many with `training_exercises` table

**Notes:**
- Status automatically updated based on exercise completion:
  - `pending`: No exercises completed
  - `in_progress`: At least one exercise completed
  - `completed`: All exercises completed
- Progress percentage calculated from exercises (not stored)
- Training plans are NOT reused (no assignments table)

---

### 15. training_exercises

Stores individual exercises within training plans.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| exercise_id | UUID | PRIMARY KEY | Unique exercise ID |
| plan_id | UUID | FOREIGN KEY → training_plans(plan_id), NOT NULL | Parent plan |
| exercise_name | VARCHAR(255) | NOT NULL | Exercise name |
| description | TEXT | NULL | Exercise description |
| sets | VARCHAR(20) | NULL | Number of sets |
| reps | VARCHAR(20) | NULL | Number of reps |
| duration_minutes | VARCHAR(20) | NULL | Duration in minutes |
| exercise_order | INTEGER | NOT NULL | Display order |
| completed | BOOLEAN | NOT NULL, DEFAULT FALSE | Has player completed this? |
| completed_at | TIMESTAMP | NULL | When player marked complete |
| created_at | TIMESTAMP | NOT NULL | Exercise creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- `idx_training_exercises_plan_id` on `plan_id`

**Relationships:**
- Many-to-one with `training_plans` table

**Notes:**
- Player toggles `completed` flag from mobile app
- When `completed` changes to TRUE:
  - `completed_at` set to NOW()
  - Parent plan status updated to 'in_progress' (if was 'pending')
- When all exercises completed:
  - Parent plan status updated to 'completed'
- Player can uncheck exercises (toggle back to FALSE)
- `sets`, `reps`, `duration_minutes` stored as strings for flexibility

---

## Database Changes Summary

### Tables Added
1. `player_season_statistics` - Player attributes and aggregated stats
2. `opponent_players` - Opponent team players for lineup display

### Tables Removed
1. `player_invite_codes` - Invite codes now in players table
2. `player_training_assignments` - Not needed (plans not reused)
3. `training_exercise_completion` - Completion tracked in exercises table

### Tables Modified

#### players
- **Added**: `player_name`, `statsbomb_player_id`, `invite_code`, `linked_at`
- **Removed**: `weight`
- **Modified**: `height` changed to INTEGER (cm)

#### training_plans
- **Added**: `status`, `coach_notes`

#### training_exercises
- **Added**: `completed`, `completed_at`

#### events
- **Renamed**: `player_id` → `statsbomb_player_id`, `team_id` → `statsbomb_team_id`

#### matches
- **Removed**: `match_status`, `video_url`, `statsbomb_match_id`

#### coaches
- **Removed**: `profile_image_url`

#### clubs
- **Added**: `statsbomb_team_id`
- **Removed**: `invite_code`

#### opponent_clubs
- **Added**: `statsbomb_team_id`
- **Renamed from**: `teams`

---

## Relationships Summary

### One-to-One Relationships
- `users` ↔ `coaches` (user_id = coach_id)
- `users` ↔ `players` (user_id = player_id, after signup)
- `coaches` ↔ `clubs` (one coach, one club)
- `clubs` ↔ `club_season_statistics`
- `players` ↔ `player_season_statistics`

### One-to-Many Relationships
- `clubs` → `players`
- `clubs` → `matches`
- `opponent_clubs` → `matches`
- `opponent_clubs` → `opponent_players`
- `matches` → `goals`
- `matches` → `events`
- `matches` → `match_statistics` (2 per match)
- `players` → `player_match_statistics`
- `matches` → `player_match_statistics`
- `players` → `training_plans`
- `coaches` → `training_plans`
- `training_plans` → `training_exercises`

---

## Data Integrity Constraints

### Foreign Key Constraints
All foreign keys should be enforced with `ON DELETE` rules:

- `coaches.coach_id` → `users.user_id` ON DELETE CASCADE
- `clubs.coach_id` → `coaches.coach_id` ON DELETE CASCADE
- `players.player_id` → `users.user_id` ON DELETE CASCADE (only after signup)
- `players.club_id` → `clubs.club_id` ON DELETE CASCADE
- `matches.club_id` → `clubs.club_id` ON DELETE CASCADE
- `matches.opponent_club_id` → `opponent_clubs.opponent_club_id` ON DELETE SET NULL
- `opponent_players.opponent_club_id` → `opponent_clubs.opponent_club_id` ON DELETE CASCADE
- `goals.match_id` → `matches.match_id` ON DELETE CASCADE
- `events.match_id` → `matches.match_id` ON DELETE CASCADE
- `match_statistics.match_id` → `matches.match_id` ON DELETE CASCADE
- `player_match_statistics.player_id` → `players.player_id` ON DELETE CASCADE
- `player_match_statistics.match_id` → `matches.match_id` ON DELETE CASCADE
- `club_season_statistics.club_id` → `clubs.club_id` ON DELETE CASCADE
- `player_season_statistics.player_id` → `players.player_id` ON DELETE CASCADE
- `training_plans.player_id` → `players.player_id` ON DELETE CASCADE
- `training_plans.created_by` → `coaches.coach_id` ON DELETE SET NULL
- `training_exercises.plan_id` → `training_plans.plan_id` ON DELETE CASCADE

### Unique Constraints
- `users.email` - No duplicate emails
- `players.invite_code` - Unique invite codes
- `clubs.coach_id` - One club per coach
- `clubs.statsbomb_team_id` - One StatsBomb team ID per club (if not NULL)
- `opponent_clubs.statsbomb_team_id` - One StatsBomb team ID per opponent club (if not NULL)
- `match_statistics (match_id, team_type)` - One record per team per match
- `player_match_statistics (player_id, match_id)` - One record per player per match
- `club_season_statistics.club_id` - One record per club
- `player_season_statistics.player_id` - One record per player

### Check Constraints
- `users.user_type` IN ('coach', 'player')
- `match_statistics.team_type` IN ('our_team', 'opponent_team')
- `training_plans.status` IN ('pending', 'in_progress', 'completed')
- `players.height` > 0 (if not NULL)
- `players.jersey_number` > 0

---

## Sample Data Flow

### Creating a Player (Admin Match Processing)

```sql
-- 1. Insert incomplete player
INSERT INTO players (
  player_id,
  club_id,
  player_name,
  statsbomb_player_id,
  jersey_number,
  position,
  invite_code,
  is_linked,
  created_at,
  updated_at
) VALUES (
  'uuid-here',
  'club-uuid',
  'Marcus Silva',
  5470,
  10,
  'Forward',
  'MRC-1827',
  FALSE,
  NOW(),
  NOW()
);
```

### Player Signup

```sql
-- 1. Validate invite code
SELECT * FROM players
WHERE invite_code = 'MRC-1827' AND is_linked = FALSE;

-- 2. Create user account (using player_id from step 1)
INSERT INTO users (
  user_id,        -- Same as player_id!
  email,
  password_hash,
  full_name,
  user_type,
  created_at,
  updated_at
) VALUES (
  'player-uuid',
  'marcus@email.com',
  'hashed_password',
  'Marcus Silva',
  'player',
  NOW(),
  NOW()
);

-- 3. Update player record
UPDATE players SET
  player_name = 'Marcus Silva',  -- Can be different if player changed it
  birth_date = '2008-03-20',
  height = 180,
  profile_image_url = 'https://...',
  is_linked = TRUE,
  linked_at = NOW(),
  updated_at = NOW()
WHERE player_id = 'player-uuid';
```

### Training Progress

```sql
-- 1. Player completes exercise
UPDATE training_exercises SET
  completed = TRUE,
  completed_at = NOW()
WHERE exercise_id = 'exercise-uuid';

-- 2. Check if plan should update status
SELECT
  plan_id,
  COUNT(*) as total_exercises,
  COUNT(CASE WHEN completed THEN 1 END) as completed_exercises
FROM training_exercises
WHERE plan_id = 'plan-uuid'
GROUP BY plan_id;

-- 3. Update plan status if needed
UPDATE training_plans SET
  status = CASE
    WHEN (completed_exercises = total_exercises) THEN 'completed'
    WHEN (completed_exercises > 0) THEN 'in_progress'
    ELSE 'pending'
  END
WHERE plan_id = 'plan-uuid';
```

---

## Notes for Implementation

1. **UUID Generation**: Use PostgreSQL's `gen_random_uuid()` or generate in application code

2. **Timestamps**: Use `NOW()` or application-level timestamp generation

3. **Invite Code Generation**: Use cryptographically secure random (e.g., Python's `secrets` module)

4. **Password Hashing**: Use bcrypt with cost factor 12

5. **Statistics Calculation**: Triggered after match processing, aggregated from events table

6. **Attributes Calculation**: Calculated from season statistics using proprietary formulas

7. **Player Name Sync**: When player updates name, update both `players.player_name` and `users.full_name`

8. **Training Status**: Automatically updated when exercises are marked complete/incomplete
