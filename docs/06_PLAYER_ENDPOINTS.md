# Player Endpoints

## Overview

This document details all API endpoints for the player-facing features of the Spinta platform. All endpoints require authentication with a valid JWT token and `user_type = "player"`.

The player mobile app uses a bottom navigation bar with 4 tabs:

- **My Stats**: Player's attributes and season statistics
- **Matches**: List and details of all matches
- **Training**: List and details of training plans
- **Profile**: Player profile information

## Authentication

All endpoints require:

- **Header:** `Authorization: Bearer <jwt_token>`
- **Token payload:** `user_type = "player"`

## Navigation Structure

Unlike the coach view which uses top tabs within screens, the player view uses a bottom navigation bar to switch between main sections. Each section may have its own internal tabs.

---

## 1. My Stats Tab (Player Dashboard)

**UI Reference:** Page 25 in Spinta UI.pdf

**UI Purpose:** Display player's attributes (radar chart) and season statistics organized by categories.

### GET /api/player/dashboard

**Description:** Returns player's attributes and season statistics for the "My Stats" tab.

**Authentication:** Required (Player only)

**Request:**

```
GET /api/player/dashboard HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "player": {
    "player_id": "player-uuid-1",
    "player_name": "Marcus Silva",
    "jersey_number": 10,
    "position": "Forward",
    "height": 180,
    "age": "23 years",
    "profile_image_url": "https://storage.example.com/players/marcus.jpg"
  },
  "attributes": {
    "attacking_rating": 82,
    "technique_rating": 64,
    "creativity_rating": 85,
    "tactical_rating": 52,
    "defending_rating": 28
  },
  "season_statistics": {
    "general": {
      "matches_played": 22
    },
    "attacking": {
      "goals": 12,
      "assists": 7,
      "expected_goals": 10.8,
      "shots_per_game": 4.2,
      "shots_on_target_per_game": 2.8,
      "goals_per_game": 0.55
    },
    "passing": {
      "total_passes": 1144,
      "passes_completed": 995,
      "pass_accuracy": 86.9,
      "key_passes": 58,
      "crosses_completed": 23
    },
    "dribbling": {
      "total_dribbles": 158,
      "successful_dribbles": 118,
      "dribble_success_rate": 74.7
    },
    "defending": {
      "tackles": 45,
      "tackle_success_rate": 78,
      "interceptions": 32,
      "interception_success_rate": 81
    }
  }
}
```

**Database Queries:**

```sql
-- 1. Player basic info
SELECT
  player_id,
  player_name,
  jersey_number,
  position,
  height,
  birth_date,
  profile_image_url
FROM players
WHERE player_id = :player_id_from_jwt;

-- 2. Attributes and season statistics
SELECT
  -- Attributes
  attacking_rating,
  technique_rating,
  creativity_rating,
  tactical_rating,
  defending_rating,

  -- General
  matches_played,

  -- Attacking
  goals,
  assists,
  expected_goals,
  shots_per_game,
  shots_on_target_per_game,
  (goals::decimal / NULLIF(matches_played, 0)) as goals_per_game,

  -- Passing
  total_passes,
  passes_completed,
  (passes_completed * 100.0 / NULLIF(total_passes, 0)) as pass_accuracy,
  key_passes,
  crosses_completed,

  -- Dribbling
  total_dribbles,
  successful_dribbles,
  (successful_dribbles * 100.0 / NULLIF(total_dribbles, 0)) as dribble_success_rate,

  -- Defending
  tackles,
  tackle_success_rate,
  interceptions,
  interception_success_rate
FROM player_season_statistics
WHERE player_id = :player_id_from_jwt;

-- Calculate age from birth_date (in application layer):
-- age = FLOOR(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) || ' years'
```

**Error Responses:**

Unauthorized (401):

```json
{
  "detail": "Authentication credentials were not provided."
}
```

Forbidden (403):

```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 2. Matches Tab - Matches List Screen

**UI Reference:** Page 26 in Spinta UI.pdf

**UI Purpose:** Display all matches the player participated in with their personal stats.

**TODO:** Update this endpoint for new matches schema (`our_score`/`opponent_score`/`result` instead of `home_score`/`away_score`/`is_home_match`, no `match_time` field). Will be updated when we validate this endpoint.

### GET /api/player/matches

**Description:** Returns paginated list of all matches with player's statistics for each match.

**Authentication:** Required (Player only)

**Query Parameters:**

- `limit` (optional): Number of matches to return (default: 20, max: 100)
- `offset` (optional): Number of matches to skip for pagination (default: 0)

**Request:**

```
GET /api/player/matches?limit=20&offset=0 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "total_count": 22,
  "matches": [
    {
      "match_id": "match-uuid-1",
      "opponent_name": "City Strikers",
      "match_date": "2025-10-08",
      "match_time": "15:30",
      "home_score": 3,
      "away_score": 2,
      "is_home_match": true,
      "result": "W"
    },
    {
      "match_id": "match-uuid-2",
      "opponent_name": "North Athletic",
      "match_date": "2025-10-01",
      "match_time": "14:00",
      "home_score": 1,
      "away_score": 1,
      "is_home_match": true,
      "result": "D"
    }
  ]
}
```

**Database Query:**

```sql
SELECT
  m.match_id,
  m.opponent_name,
  m.match_date,
  m.match_time,
  m.home_score,
  m.away_score,
  m.is_home_match,
  CASE
    WHEN m.is_home_match AND m.home_score > m.away_score THEN 'W'
    WHEN m.is_home_match AND m.home_score < m.away_score THEN 'L'
    WHEN m.is_home_match AND m.home_score = m.away_score THEN 'D'
    WHEN NOT m.is_home_match AND m.away_score > m.home_score THEN 'W'
    WHEN NOT m.is_home_match AND m.away_score < m.home_score THEN 'L'
    ELSE 'D'
  END as result,
  COUNT(*) OVER() as total_count
FROM player_match_statistics pms
JOIN matches m ON pms.match_id = m.match_id
WHERE pms.player_id = :player_id_from_jwt
ORDER BY m.match_date DESC
LIMIT :limit OFFSET :offset;
```

---

## 3. Matches Tab - Match Detail Screen

**UI Reference:** Page 27 in Spinta UI.pdf

**UI Purpose:** Display player's individual performance in a specific match - simple page showing match header, player summary (goals/assists), and statistics sections. This is identical to the coach's view of player match detail (Page 15).

**TODO:** Update this endpoint for new matches schema (`our_score`/`opponent_score`/`result` instead of `home_score`/`away_score`/`is_home_match`, no `match_time` field). Will be updated when we validate this endpoint.

### GET /api/player/matches/{match_id}

**Description:** Returns player's detailed statistics for a specific match. This is a simple page format (not tabbed) showing match info, player summary, and categorized statistics.

**Authentication:** Required (Player only)

**Path Parameters:**

- `match_id` (required): UUID of the match

**Request:**

```
GET /api/player/matches/match-uuid-1 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "match": {
    "match_id": "match-uuid-1",
    "match_date": "2025-10-08",
    "match_time": "15:30",
    "home_score": 3,
    "away_score": 2,
    "is_home_match": true,
    "result": "W"
  },
  "teams": {
    "our_club": {
      "club_name": "Thunder United FC",
      "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
    },
    "opponent": {
      "opponent_name": "City Strikers",
      "logo_url": "https://storage.example.com/opponents/city-strikers.png"
    }
  },
  "player_summary": {
    "player_name": "Marcus Silva",
    "goals": 2,
    "assists": 1
  },
  "statistics": {
    "attacking": {
      "goals": 2,
      "assists": 1,
      "xg": 1.8,
      "total_shots": 6,
      "shots_on_target": 4,
      "total_dribbles": 9,
      "successful_dribbles": 7
    },
    "passing": {
      "total_passes": 52,
      "passes_completed": 46,
      "short_passes": 38,
      "long_passes": 14,
      "final_third": 18,
      "crosses": 5
    },
    "defending": {
      "tackles": 5,
      "tackle_success_rate": 80,
      "interceptions": 5,
      "interception_success_rate": 83
    }
  }
}
```

**Database Queries:**

```sql
-- 1. Match info and team details
SELECT
  m.match_id,
  m.match_date,
  m.match_time,
  m.home_score,
  m.away_score,
  m.is_home_match,
  c.club_name as our_club_name,
  c.logo_url as our_logo_url,
  m.opponent_name,
  oc.logo_url as opponent_logo_url,
  CASE
    WHEN m.is_home_match AND m.home_score > m.away_score THEN 'W'
    WHEN m.is_home_match AND m.home_score < m.away_score THEN 'L'
    WHEN m.is_home_match AND m.home_score = m.away_score THEN 'D'
    WHEN NOT m.is_home_match AND m.away_score > m.home_score THEN 'W'
    WHEN NOT m.is_home_match AND m.away_score < m.home_score THEN 'L'
    ELSE 'D'
  END as result
FROM matches m
LEFT JOIN opponent_clubs oc ON m.opponent_club_id = oc.opponent_club_id
JOIN clubs c ON m.club_id = c.club_id
WHERE m.match_id = :match_id
  AND m.club_id = (SELECT club_id FROM players WHERE player_id = :player_id_from_jwt);

-- 2. Player match stats
SELECT
  p.player_name,
  pms.goals,
  pms.assists,
  pms.expected_goals as xg,
  pms.shots as total_shots,
  pms.shots_on_target,
  pms.total_dribbles,
  pms.successful_dribbles,
  pms.total_passes,
  pms.completed_passes as passes_completed,
  pms.short_passes,
  pms.long_passes,
  pms.final_third_passes as final_third,
  pms.crosses,
  pms.tackles,
  pms.tackle_success_rate,
  pms.interceptions,
  pms.interception_success_rate
FROM player_match_statistics pms
JOIN players p ON pms.player_id = p.player_id
WHERE pms.match_id = :match_id
  AND pms.player_id = :player_id_from_jwt;
```

**Error Responses:**

Not Found (404):

```json
{
  "detail": "Match not found."
}
```

Forbidden (403):

```json
{
  "detail": "This match does not belong to your club or you did not play in this match."
}
```

---

## 4. Training Tab - Training Plans List Screen

**UI Reference:** Page 28 in Spinta UI.pdf

**UI Purpose:** Display all training plans assigned to the player with their status.

### GET /api/player/training

**Description:** Returns all training plans for the player showing name, date, and status.

**Authentication:** Required (Player only)

**Query Parameters:**

- `status` (optional): Filter by status ('all', 'pending', 'in_progress', 'completed'). Default: 'all'

**Request:**

```
GET /api/player/training?status=all HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "training_plans": [
    {
      "plan_id": "plan-uuid-1",
      "plan_name": "Speed & Agility Development",
      "created_at": "2025-10-14",
      "status": "in_progress"
    },
    {
      "plan_id": "plan-uuid-2",
      "plan_name": "Shooting Accuracy Program",
      "created_at": "2025-10-20",
      "status": "pending"
    },
    {
      "plan_id": "plan-uuid-3",
      "plan_name": "Strength & Conditioning",
      "created_at": "2025-09-15",
      "status": "completed"
    }
  ]
}
```

**Database Query:**

```sql
SELECT
  plan_id,
  plan_name,
  created_at,
  status
FROM training_plans
WHERE player_id = :player_id_from_jwt
  AND (status = :status OR :status = 'all')
ORDER BY
  CASE status
    WHEN 'in_progress' THEN 1
    WHEN 'pending' THEN 2
    WHEN 'completed' THEN 3
  END,
  created_at DESC;
```

---

## 5. Training Tab - Training Plan Detail Screen

**UI Reference:** Page 29 in Spinta UI.pdf

**UI Purpose:** Display detailed training plan with exercises that player can check/uncheck to mark completion.

### GET /api/player/training/{plan_id}

**Description:** Returns complete training plan details with all exercises and checkboxes for completion.

**Authentication:** Required (Player only)

**Path Parameters:**

- `plan_id` (required): UUID of the training plan

**Request:**

```
GET /api/player/training/plan-uuid-1 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "plan": {
    "plan_id": "plan-uuid-1",
    "plan_name": "Shooting Accuracy Program",
    "player_name": "Marcus Silva",
    "player_jersey": 10,
    "status": "in_progress",
    "created_at": "2025-10-14"
  },
  "progress": {
    "percentage": 60,
    "completed_exercises": 6,
    "total_exercises": 10
  },
  "exercises": [
    {
      "exercise_id": "exercise-uuid-1",
      "exercise_name": "Target Shooting Drill",
      "description": "Practice shooting at designated target zones in the goal. Focus on accuracy over power.",
      "sets": "3",
      "reps": "10",
      "duration_minutes": "20",
      "exercise_order": 1,
      "completed": true,
      "completed_at": "2025-10-15T14:30:00Z"
    },
    {
      "exercise_id": "exercise-uuid-2",
      "exercise_name": "One-Touch Finishing",
      "description": "Receive pass and shoot in one motion. Work on both feet.",
      "sets": "4",
      "reps": "8",
      "duration_minutes": "15",
      "exercise_order": 2,
      "completed": true,
      "completed_at": "2025-10-16T15:00:00Z"
    },
    {
      "exercise_id": "exercise-uuid-3",
      "exercise_name": "Power Shooting",
      "description": "Focus on generating maximum power while maintaining accuracy.",
      "sets": "3",
      "reps": "12",
      "duration_minutes": "20",
      "exercise_order": 3,
      "completed": false,
      "completed_at": null
    }
  ],
  "coach_notes": "Remember to follow through with your shooting motion and keep your body over the ball. Great progress so far!"
}
```

**Database Query:**

```sql
SELECT
  tp.plan_id,
  tp.plan_name,
  p.player_name,
  p.jersey_number as player_jersey,
  tp.status,
  tp.created_at,
  tp.coach_notes,
  COUNT(te.exercise_id) as total_exercises,
  COUNT(CASE WHEN te.completed THEN 1 END) as completed_exercises,
  (COUNT(CASE WHEN te.completed THEN 1 END) * 100.0 /
   NULLIF(COUNT(te.exercise_id), 0)) as percentage,
  te.exercise_id,
  te.exercise_name,
  te.description,
  te.sets,
  te.reps,
  te.duration_minutes,
  te.exercise_order,
  te.completed,
  te.completed_at
FROM training_plans tp
JOIN players p ON tp.player_id = p.player_id
LEFT JOIN training_exercises te ON tp.plan_id = te.plan_id
WHERE tp.plan_id = :plan_id
  AND tp.player_id = :player_id_from_jwt
ORDER BY te.exercise_order;
```

**Error Responses:**

Not Found (404):

```json
{
  "detail": "Training plan not found."
}
```

Forbidden (403):

```json
{
  "detail": "This training plan is not assigned to you."
}
```

---

## 6. Toggle Exercise Completion

**UI Reference:** Page 29 in Spinta UI.pdf (checkbox interaction)

**UI Purpose:** Allow player to mark exercise as complete/incomplete by checking/unchecking checkbox.

### PUT /api/player/training/exercises/{exercise_id}/toggle

**Description:** Toggle the completion status of a training exercise.

**Authentication:** Required (Player only)

**Path Parameters:**

- `exercise_id` (required): UUID of the exercise

**Request:**

```json
PUT /api/player/training/exercises/exercise-uuid-3/toggle HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "completed": true
}
```

**Response (200 OK):**

```json
{
  "exercise_id": "exercise-uuid-3",
  "completed": true,
  "completed_at": "2025-10-26T16:30:00Z",
  "plan_progress": {
    "plan_id": "plan-uuid-1",
    "total_exercises": 10,
    "completed_exercises": 7,
    "progress_percentage": 70,
    "plan_status": "in_progress"
  }
}
```

**Database Queries:**

```sql
-- Start transaction
BEGIN;

-- 1. Verify exercise belongs to player
SELECT te.exercise_id, te.plan_id
FROM training_exercises te
JOIN training_plans tp ON te.plan_id = tp.plan_id
WHERE te.exercise_id = :exercise_id
  AND tp.player_id = :player_id_from_jwt
FOR UPDATE;  -- Lock row for update
-- If no result, return 403

-- 2. Update exercise completion
UPDATE training_exercises SET
  completed = :completed,
  completed_at = CASE WHEN :completed THEN NOW() ELSE NULL END
WHERE exercise_id = :exercise_id;

-- 3. Calculate plan progress
SELECT
  plan_id,
  COUNT(*) as total_exercises,
  COUNT(CASE WHEN completed THEN 1 END) as completed_exercises,
  (COUNT(CASE WHEN completed THEN 1 END) * 100.0 /
   NULLIF(COUNT(*), 0)) as progress_percentage
FROM training_exercises
WHERE plan_id = (SELECT plan_id FROM training_exercises WHERE exercise_id = :exercise_id)
GROUP BY plan_id;

-- 4. Update plan status based on progress
UPDATE training_plans SET
  status = CASE
    WHEN :completed_exercises = :total_exercises THEN 'completed'
    WHEN :completed_exercises > 0 THEN 'in_progress'
    ELSE 'pending'
  END
WHERE plan_id = :plan_id;

COMMIT;
```

**Notes:**

- Player can toggle exercises on and off (check/uncheck)
- When exercise is marked complete: `completed = TRUE`, `completed_at = NOW()`
- When exercise is unmarked: `completed = FALSE`, `completed_at = NULL`
- Plan status automatically updates:
  - `pending`: No exercises completed
  - `in_progress`: At least one exercise completed
  - `completed`: All exercises completed

**Error Responses:**

Not Found (404):

```json
{
  "detail": "Exercise not found."
}
```

Forbidden (403):

```json
{
  "detail": "This exercise is not part of your training plan."
}
```

---

## 7. Profile Tab - Player Profile Screen

**UI Reference:** Page 30 in Spinta UI.pdf

**UI Purpose:** Display player's profile information.

### GET /api/player/profile

**Description:** Returns player's profile information, club details, and basic statistics.

**Authentication:** Required (Player only)

**Request:**

```
GET /api/player/profile HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "player": {
    "player_id": "player-uuid-1",
    "player_name": "Marcus Silva",
    "email": "marcus@email.com",
    "jersey_number": 10,
    "position": "Forward",
    "height": 180,
    "birth_date": "2008-03-20",
    "profile_image_url": "https://storage.example.com/players/marcus.jpg"
  },
  "club": {
    "club_name": "Thunder United FC",
    "coach_name": "John Smith"
  },
  "season_summary": {
    "matches_played": 22,
    "goals": 12,
    "assists": 7
  }
}
```

**Database Queries:**

```sql
-- 1. Player and club info
SELECT
  p.player_id,
  p.player_name,
  u.email,
  p.jersey_number,
  p.position,
  p.height,
  p.birth_date,
  p.profile_image_url,
  c.club_name,
  coach_user.full_name as coach_name
FROM players p
JOIN users u ON p.player_id = u.user_id
JOIN clubs c ON p.club_id = c.club_id
JOIN coaches co ON c.coach_id = co.coach_id
JOIN users coach_user ON co.coach_id = coach_user.user_id
WHERE p.player_id = :player_id_from_jwt;

-- 2. Season summary
SELECT
  matches_played,
  goals,
  assists
FROM player_season_statistics
WHERE player_id = :player_id_from_jwt;
```

---

## Summary

### Player Endpoints

| Endpoint                                              | Method | Purpose                                  | Screen Reference |
| ----------------------------------------------------- | ------ | ---------------------------------------- | ---------------- |
| `/api/player/dashboard`                               | GET    | My Stats tab (attributes + season stats) | Page 25          |
| `/api/player/matches`                                 | GET    | Matches list                             | Page 26          |
| `/api/player/matches/{match_id}`                      | GET    | Player match detail (simple page)        | Page 27          |
| `/api/player/training`                                | GET    | Training plans list                      | Page 28          |
| `/api/player/training/{plan_id}`                      | GET    | Training plan detail                     | Page 29          |
| `/api/player/training/exercises/{exercise_id}/toggle` | PUT    | Toggle exercise completion               | Page 29          |
| `/api/player/profile`                                 | GET    | View profile                             | Page 30          |

**Total: 7 endpoints**

### Authorization Rules

1. **Player-only access:** All endpoints require `user_type = "player"` in JWT token
2. **Resource ownership:** Players can only access their own data:
   - Matches must include the player
   - Training plans must be assigned to the player
   - Profile is their own
3. **Validation on every request:** Backend must verify player_id from JWT matches resource ownership

### Key Features

1. **Bottom Navigation Structure:**

   - My Stats: Attributes and season statistics by categories
   - Matches: List and detail views with 3 internal tabs
   - Training: List and detail views with checkboxes
   - Profile: Personal information and club details

2. **Statistics Categories:**

   - GENERAL: Matches played
   - ATTACKING: Goals, assists, xG, shots
   - PASSING: Total passes, accuracy, key passes, crosses
   - DRIBBLING: Total dribbles, success rate
   - DEFENDING: Tackles, interceptions, success rates

3. **Training Progress:**

   - Automatic status updates based on exercise completion
   - Progress percentage calculated in real-time
   - Players can toggle exercises on/off with checkboxes

4. **Match Detail Format:**
   - Simple page showing match header, player summary (goals/assists), and categorized statistics
   - Identical structure to coach's view of player match detail (Page 15)

### Key Differences from Coach View

1. **Navigation:** Bottom nav bar instead of top tabs within screens
2. **No AI Generation:** Players cannot create training plans (no "Create Training Plan Using AI" button)
3. **Checkbox Toggles:** Players can check/uncheck exercises to mark completion
4. **Simplified Dashboard:** Only "My Stats" content (no mixed content like club info or recent matches)
