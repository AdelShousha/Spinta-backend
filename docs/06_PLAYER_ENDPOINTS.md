# Player Endpoints

## Overview

This document details all API endpoints for the player-facing features of the Spinta platform. All endpoints require authentication with a valid JWT token and `user_type = "player"`.

## Authentication

All endpoints require:
- **Header:** `Authorization: Bearer <jwt_token>`
- **Token payload:** `user_type = "player"`

## Endpoints Organized by UI Screens

---

## 1. Player Dashboard Screen

**UI Purpose:** Display player's profile summary, club info, season stats, attributes, recent matches, and active training plans.

### GET /api/player/dashboard

**Description:** Returns all data needed for the player dashboard screen.

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
    "profile_image_url": "https://storage.example.com/players/marcus.jpg"
  },
  "club": {
    "club_id": "club-uuid-1",
    "club_name": "Thunder United FC",
    "logo_url": "https://storage.example.com/clubs/thunder-logo.png",
    "age_group": "U16",
    "coach_name": "John Smith"
  },
  "season_summary": {
    "matches_played": 22,
    "goals": 12,
    "assists": 7,
    "avg_shots_per_game": 4.18
  },
  "attributes": {
    "attacking_rating": 82,
    "technique_rating": 64,
    "tactical_rating": 52,
    "defending_rating": 28,
    "creativity_rating": 85
  },
  "recent_matches": [
    {
      "match_id": "match-uuid-1",
      "opponent_name": "City Strikers",
      "match_date": "2025-10-08",
      "result": "W",
      "goals": 2,
      "assists": 1
    },
    {
      "match_id": "match-uuid-2",
      "opponent_name": "North Athletic",
      "match_date": "2025-10-01",
      "result": "D",
      "goals": 1,
      "assists": 0
    },
    {
      "match_id": "match-uuid-3",
      "opponent_name": "West United",
      "match_date": "2025-09-24",
      "result": "W",
      "goals": 0,
      "assists": 2
    }
  ],
  "active_training": [
    {
      "plan_id": "plan-uuid-1",
      "plan_name": "Sprint Training",
      "status": "in_progress",
      "progress_percentage": 60
    },
    {
      "plan_id": "plan-uuid-2",
      "plan_name": "Finishing Drills",
      "status": "pending",
      "progress_percentage": 0
    }
  ]
}
```

**Database Queries:**

```sql
-- 1. Player and club info
SELECT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.height,
  p.profile_image_url,
  c.club_id,
  c.club_name,
  c.logo_url,
  c.age_group,
  u.full_name as coach_name
FROM players p
JOIN clubs c ON p.club_id = c.club_id
JOIN coaches co ON c.coach_id = co.coach_id
JOIN users u ON co.coach_id = u.user_id
WHERE p.player_id = :player_id_from_jwt;

-- 2. Season stats and attributes
SELECT
  matches_played,
  goals,
  assists,
  shots_per_game,
  attacking_rating,
  technique_rating,
  tactical_rating,
  defending_rating,
  creativity_rating
FROM player_season_statistics
WHERE player_id = :player_id_from_jwt;

-- 3. Recent matches (last 3)
SELECT
  m.match_id,
  m.opponent_name,
  m.match_date,
  CASE
    WHEN m.is_home_match AND m.home_score > m.away_score THEN 'W'
    WHEN m.is_home_match AND m.home_score < m.away_score THEN 'L'
    WHEN m.is_home_match AND m.home_score = m.away_score THEN 'D'
    WHEN NOT m.is_home_match AND m.away_score > m.home_score THEN 'W'
    WHEN NOT m.is_home_match AND m.away_score < m.home_score THEN 'L'
    ELSE 'D'
  END as result,
  pms.goals,
  pms.assists
FROM player_match_statistics pms
JOIN matches m ON pms.match_id = m.match_id
WHERE pms.player_id = :player_id_from_jwt
ORDER BY m.match_date DESC
LIMIT 3;

-- 4. Active training (pending or in_progress)
SELECT
  tp.plan_id,
  tp.plan_name,
  tp.status,
  (COUNT(CASE WHEN te.completed THEN 1 END) * 100.0 /
   NULLIF(COUNT(te.exercise_id), 0)) as progress_percentage
FROM training_plans tp
LEFT JOIN training_exercises te ON tp.plan_id = te.plan_id
WHERE tp.player_id = :player_id_from_jwt
  AND tp.status IN ('pending', 'in_progress')
GROUP BY tp.plan_id;
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

## 2. Player Matches List Screen

**UI Purpose:** Display all matches the player participated in with their personal stats.

### GET /api/player/matches

**Description:** Returns paginated list of matches with player's statistics for each match.

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
  "total_matches": 22,
  "matches": [
    {
      "match_id": "match-uuid-1",
      "opponent_name": "City Strikers",
      "opponent_logo_url": "https://storage.example.com/opponents/city-strikers.png",
      "match_date": "2025-10-08",
      "match_time": "15:30",
      "result": "W",
      "home_score": 3,
      "away_score": 2,
      "player_stats": {
        "goals": 2,
        "assists": 1,
        "shots": 6,
        "shots_on_target": 4,
        "total_passes": 52,
        "completed_passes": 46
      }
    },
    {
      "match_id": "match-uuid-2",
      "opponent_name": "North Athletic",
      "opponent_logo_url": null,
      "match_date": "2025-10-01",
      "match_time": "14:00",
      "result": "D",
      "home_score": 1,
      "away_score": 1,
      "player_stats": {
        "goals": 1,
        "assists": 0,
        "shots": 5,
        "shots_on_target": 3,
        "total_passes": 48,
        "completed_passes": 41
      }
    }
  ]
}
```

**Database Query:**

```sql
SELECT
  m.match_id,
  m.opponent_name,
  oc.logo_url as opponent_logo_url,
  m.match_date,
  m.match_time,
  m.home_score,
  m.away_score,
  CASE
    WHEN m.is_home_match AND m.home_score > m.away_score THEN 'W'
    WHEN m.is_home_match AND m.home_score < m.away_score THEN 'L'
    WHEN m.is_home_match AND m.home_score = m.away_score THEN 'D'
    WHEN NOT m.is_home_match AND m.away_score > m.home_score THEN 'W'
    WHEN NOT m.is_home_match AND m.away_score < m.home_score THEN 'L'
    ELSE 'D'
  END as result,
  pms.goals,
  pms.assists,
  pms.shots,
  pms.shots_on_target,
  pms.total_passes,
  pms.completed_passes,
  COUNT(*) OVER() as total_count
FROM player_match_statistics pms
JOIN matches m ON pms.match_id = m.match_id
LEFT JOIN opponent_clubs oc ON m.opponent_club_id = oc.opponent_club_id
WHERE pms.player_id = :player_id_from_jwt
ORDER BY m.match_date DESC
LIMIT :limit OFFSET :offset;
```

---

## 3. Player Match Detail Screen

**UI Purpose:** Display detailed statistics for a specific match, comparing player's performance to season averages.

### GET /api/player/matches/{match_id}

**Description:** Returns detailed player statistics for a specific match.

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
    "opponent_name": "City Strikers",
    "opponent_logo_url": "https://storage.example.com/opponents/city-strikers.png",
    "match_date": "2025-10-08",
    "match_time": "15:30",
    "result": "W",
    "home_score": 3,
    "away_score": 2
  },
  "player_stats": {
    "goals": 2,
    "assists": 1,
    "expected_goals": 1.800,
    "shots": 6,
    "shots_on_target": 4,
    "total_dribbles": 9,
    "successful_dribbles": 7,
    "total_passes": 52,
    "completed_passes": 46,
    "short_passes": 38,
    "long_passes": 14,
    "final_third_passes": 18,
    "crosses": 5,
    "tackles": 5,
    "tackle_success_rate": 80.00,
    "interceptions": 5,
    "interception_success_rate": 83.00
  },
  "season_averages": {
    "goals_per_game": 0.55,
    "assists_per_game": 0.32,
    "shots_per_game": 4.18,
    "pass_accuracy": 86.90
  }
}
```

**Database Queries:**

```sql
-- 1. Match info
SELECT
  m.match_id,
  m.opponent_name,
  oc.logo_url as opponent_logo_url,
  m.match_date,
  m.match_time,
  m.home_score,
  m.away_score,
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
WHERE m.match_id = :match_id;

-- 2. Player match stats
SELECT
  goals,
  assists,
  expected_goals,
  shots,
  shots_on_target,
  total_dribbles,
  successful_dribbles,
  total_passes,
  completed_passes,
  short_passes,
  long_passes,
  final_third_passes,
  crosses,
  tackles,
  tackle_success_rate,
  interceptions,
  interception_success_rate
FROM player_match_statistics
WHERE match_id = :match_id
  AND player_id = :player_id_from_jwt;

-- 3. Season averages
SELECT
  (goals::decimal / NULLIF(matches_played, 0)) as goals_per_game,
  (assists::decimal / NULLIF(matches_played, 0)) as assists_per_game,
  shots_per_game,
  (passes_completed * 100.0 / NULLIF(total_passes, 0)) as pass_accuracy
FROM player_season_statistics
WHERE player_id = :player_id_from_jwt;
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
  "detail": "You did not play in this match."
}
```

---

## 4. Player Training List Screen

**UI Purpose:** Display all training plans assigned to the player with filtering by status.

### GET /api/player/training

**Description:** Returns all training plans for the player with progress information.

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
      "plan_name": "Sprint Training for Marcus",
      "duration": "2 weeks",
      "status": "in_progress",
      "coach_notes": "Focus on maintaining form during maximum effort sprints.",
      "progress_percentage": 60,
      "total_exercises": 5,
      "completed_exercises": 3,
      "created_at": "2025-10-14T10:00:00Z"
    },
    {
      "plan_id": "plan-uuid-2",
      "plan_name": "Finishing Drills",
      "duration": "1 week",
      "status": "pending",
      "coach_notes": "Practice different finishing techniques in the box.",
      "progress_percentage": 0,
      "total_exercises": 4,
      "completed_exercises": 0,
      "created_at": "2025-10-20T10:00:00Z"
    },
    {
      "plan_id": "plan-uuid-3",
      "plan_name": "Agility Training",
      "duration": "1 week",
      "status": "completed",
      "coach_notes": "Great work on the cone drills!",
      "progress_percentage": 100,
      "total_exercises": 3,
      "completed_exercises": 3,
      "created_at": "2025-09-15T10:00:00Z"
    }
  ],
  "counts": {
    "pending": 2,
    "in_progress": 1,
    "completed": 5
  }
}
```

**Database Queries:**

```sql
-- 1. Training plans
SELECT
  tp.plan_id,
  tp.plan_name,
  tp.duration,
  tp.status,
  tp.coach_notes,
  tp.created_at,
  COUNT(te.exercise_id) as total_exercises,
  COUNT(CASE WHEN te.completed THEN 1 END) as completed_exercises,
  (COUNT(CASE WHEN te.completed THEN 1 END) * 100.0 /
   NULLIF(COUNT(te.exercise_id), 0)) as progress_percentage
FROM training_plans tp
LEFT JOIN training_exercises te ON tp.plan_id = te.plan_id
WHERE tp.player_id = :player_id_from_jwt
  AND (tp.status = :status OR :status = 'all')
GROUP BY tp.plan_id
ORDER BY
  CASE tp.status
    WHEN 'in_progress' THEN 1
    WHEN 'pending' THEN 2
    WHEN 'completed' THEN 3
  END,
  tp.created_at DESC;

-- 2. Status counts
SELECT
  status,
  COUNT(*) as count
FROM training_plans
WHERE player_id = :player_id_from_jwt
GROUP BY status;
```

---

## 5. Player Training Detail Screen

**UI Purpose:** Display detailed training plan with exercises, checkboxes to mark completion, and coach notes.

### GET /api/player/training/{plan_id}

**Description:** Returns complete training plan details with all exercises and completion status.

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
    "plan_name": "Sprint Training for Marcus",
    "duration": "2 weeks",
    "status": "in_progress",
    "coach_notes": "Focus on maintaining form during maximum effort sprints. Rest 2 minutes between sets.",
    "created_at": "2025-10-14T10:00:00Z"
  },
  "exercises": [
    {
      "exercise_id": "exercise-uuid-1",
      "exercise_name": "40m Sprints",
      "description": "Maximum effort sprints from standing start. Focus on explosive first step.",
      "sets": "6",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 1,
      "completed": true,
      "completed_at": "2025-10-15T14:30:00Z"
    },
    {
      "exercise_id": "exercise-uuid-2",
      "exercise_name": "Flying 30m Sprints",
      "description": "20m build-up, then 30m at maximum speed.",
      "sets": "4",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 2,
      "completed": true,
      "completed_at": "2025-10-16T15:00:00Z"
    },
    {
      "exercise_id": "exercise-uuid-3",
      "exercise_name": "Resistance Band Sprints",
      "description": "Sprint against resistance band tension.",
      "sets": "5",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 3,
      "completed": true,
      "completed_at": "2025-10-17T14:45:00Z"
    },
    {
      "exercise_id": "exercise-uuid-4",
      "exercise_name": "Hill Sprints",
      "description": "Sprint uphill for power development.",
      "sets": "4",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 4,
      "completed": false,
      "completed_at": null
    },
    {
      "exercise_id": "exercise-uuid-5",
      "exercise_name": "Cool Down Jog",
      "description": "Light jog to cool down muscles.",
      "sets": "1",
      "reps": "1",
      "duration_minutes": "10",
      "exercise_order": 5,
      "completed": false,
      "completed_at": null
    }
  ],
  "progress": {
    "total_exercises": 5,
    "completed_exercises": 3,
    "progress_percentage": 60
  }
}
```

**Database Query:**

```sql
SELECT
  tp.plan_id,
  tp.plan_name,
  tp.duration,
  tp.status,
  tp.coach_notes,
  tp.created_at,
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

**UI Purpose:** Allow player to mark exercise as complete/incomplete (checkbox toggle).

### PUT /api/player/training/exercises/{exercise_id}/toggle

**Description:** Toggle the completion status of a training exercise.

**Authentication:** Required (Player only)

**Path Parameters:**
- `exercise_id` (required): UUID of the exercise

**Request:**
```json
PUT /api/player/training/exercises/exercise-uuid-4/toggle HTTP/1.1
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
  "exercise_id": "exercise-uuid-4",
  "completed": true,
  "completed_at": "2025-10-26T16:30:00Z",
  "plan_progress": {
    "plan_id": "plan-uuid-1",
    "total_exercises": 5,
    "completed_exercises": 4,
    "progress_percentage": 80,
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

## 7. Player Profile Screen

**UI Purpose:** Display player's profile information (read-only view).

### GET /api/player/profile

**Description:** Returns player's profile information, club details, and season summary.

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
    "logo_url": "https://storage.example.com/clubs/thunder-logo.png",
    "coach_name": "John Smith"
  },
  "season_summary": {
    "matches_played": 22,
    "goals": 12,
    "assists": 7
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
  c.logo_url as club_logo,
  coach_user.full_name as coach_name
FROM players p
JOIN users u ON p.player_id = u.user_id
JOIN clubs c ON p.club_id = c.club_id
JOIN coaches co ON c.coach_id = co.coach_id
JOIN users coach_user ON co.coach_id = coach_user.user_id
WHERE p.player_id = :player_id_from_jwt;

-- 2. Season summary and attributes
SELECT
  matches_played,
  goals,
  assists,
  attacking_rating,
  technique_rating,
  tactical_rating,
  defending_rating,
  creativity_rating
FROM player_season_statistics
WHERE player_id = :player_id_from_jwt;
```

---

## 8. Update Player Profile

**UI Purpose:** Allow player to update their profile information.

### PUT /api/player/profile

**Description:** Update player's editable profile fields.

**Authentication:** Required (Player only)

**Request:**
```json
PUT /api/player/profile HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "player_name": "Marcus Silva",
  "height": 182,
  "profile_image_url": "https://storage.example.com/players/marcus-updated.jpg"
}
```

**Editable Fields:**
- `player_name`: Player's name (optional, 2-255 characters)
- `height`: Player height in cm (optional, integer 100-250)
- `profile_image_url`: Profile photo URL (optional, valid URL)

**Non-editable Fields** (controlled by admin/system):
- `jersey_number`
- `position`
- `birth_date`
- `email` (requires separate email change flow)

**Response (200 OK):**
```json
{
  "success": true,
  "player": {
    "player_id": "player-uuid-1",
    "player_name": "Marcus Silva",
    "email": "marcus@email.com",
    "jersey_number": 10,
    "position": "Forward",
    "height": 182,
    "birth_date": "2008-03-20",
    "profile_image_url": "https://storage.example.com/players/marcus-updated.jpg"
  }
}
```

**Database Queries:**

```sql
-- Start transaction
BEGIN;

-- 1. Update player record
UPDATE players SET
  player_name = COALESCE(:player_name, player_name),
  height = COALESCE(:height, height),
  profile_image_url = COALESCE(:profile_image_url, profile_image_url),
  updated_at = NOW()
WHERE player_id = :player_id_from_jwt;

-- 2. Update user full_name if player_name changed
UPDATE users SET
  full_name = :player_name,
  updated_at = NOW()
WHERE user_id = :player_id_from_jwt
  AND :player_name IS NOT NULL;

COMMIT;

-- 3. Return updated player data
SELECT
  p.player_id,
  p.player_name,
  u.email,
  p.jersey_number,
  p.position,
  p.height,
  p.birth_date,
  p.profile_image_url
FROM players p
JOIN users u ON p.player_id = u.user_id
WHERE p.player_id = :player_id_from_jwt;
```

**Validation:**
- `player_name`: 2-255 characters if provided
- `height`: Integer 100-250 if provided
- `profile_image_url`: Valid URL if provided

**Error Responses:**

Validation Error (400):
```json
{
  "detail": "Validation failed",
  "errors": {
    "height": "Height must be between 100 and 250 cm",
    "profile_image_url": "Invalid URL format"
  }
}
```

---

## Summary

### Player Endpoints

| Endpoint | Method | Purpose | Screen |
|----------|--------|---------|--------|
| `/api/player/dashboard` | GET | Player dashboard | Dashboard |
| `/api/player/matches` | GET | List all matches | Matches List |
| `/api/player/matches/{match_id}` | GET | Match details | Match Detail |
| `/api/player/training` | GET | List training plans | Training List |
| `/api/player/training/{plan_id}` | GET | Training plan details | Training Detail |
| `/api/player/training/exercises/{exercise_id}/toggle` | PUT | Toggle exercise completion | Training Detail |
| `/api/player/profile` | GET | View profile | Profile |
| `/api/player/profile` | PUT | Update profile | Edit Profile |

**Total: 8 endpoints (GET /api/player/profile counted once)**

### Authorization Rules

1. **Player-only access:** All endpoints require `user_type = "player"` in JWT token
2. **Resource ownership:** Players can only access their own data:
   - Matches must include the player
   - Training plans must be assigned to the player
   - Profile is their own
3. **Validation on every request:** Backend must verify player_id matches before returning data

### Key Features

1. **Read-Only Fields:** Players cannot edit:
   - Jersey number (set by admin)
   - Position (set by admin)
   - Birth date (set during signup)
   - Email (requires separate verification flow)

2. **Editable Fields:** Players can edit:
   - Name (synced with users.full_name)
   - Height
   - Profile photo

3. **Training Progress:**
   - Automatic status updates based on exercise completion
   - Progress percentage calculated in real-time
   - Players can toggle exercises on/off

4. **Statistics:**
   - Match-level stats show individual performance
   - Season averages for comparison
   - Attributes displayed as radar chart in UI
