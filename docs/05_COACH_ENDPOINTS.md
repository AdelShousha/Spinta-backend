# Coach Endpoints

## Overview

This document details all API endpoints for the coach-facing features of the Spinta platform. All endpoints require authentication with a valid JWT token and `user_type = "coach"`.

## Authentication

All endpoints require:
- **Header:** `Authorization: Bearer <jwt_token>`
- **Token payload:** `user_type = "coach"`

## Endpoints Organized by UI Screens

---

## 1. Coach Dashboard / Club Overview Screen

**UI Purpose:** Display welcome message, club info, season record, team form, recent matches, and statistics.

### GET /api/coach/dashboard

**Description:** Returns all data needed for the coach dashboard screen including club info, season statistics, recent matches, and team form.

**Authentication:** Required (Coach only)

**Request:**
```
GET /api/coach/dashboard HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "coach": {
    "full_name": "John Smith",
    "email": "john@email.com"
  },
  "club": {
    "club_id": "550e8400-e29b-41d4-a716-446655440000",
    "club_name": "Thunder United FC",
    "logo_url": "https://storage.example.com/clubs/thunder-logo.png",
    "age_group": "U16",
    "stadium": "City Stadium",
    "country": "United States"
  },
  "season_record": {
    "matches_played": 22,
    "wins": 14,
    "draws": 4,
    "losses": 4,
    "goals_scored": 45,
    "goals_conceded": 23,
    "total_clean_sheets": 8
  },
  "team_form": "WWDWLWWDLW",
  "recent_matches": [
    {
      "match_id": "match-uuid-1",
      "opponent_name": "City Strikers",
      "opponent_logo_url": "https://storage.example.com/opponents/city-strikers.png",
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
      "opponent_logo_url": null,
      "match_date": "2025-10-01",
      "match_time": "14:00",
      "home_score": 1,
      "away_score": 1,
      "is_home_match": false,
      "result": "D"
    }
  ],
  "statistics": {
    "summary": {
      "avg_goals_per_match": 2.05,
      "avg_possession_percentage": 58.00,
      "avg_total_shots": 14.50,
      "avg_shots_on_target": 8.20
    },
    "detailed": {
      "avg_xg_per_match": 1.90,
      "avg_goals_conceded_per_match": 1.05,
      "avg_total_passes": 487.00,
      "pass_completion_rate": 87.00,
      "avg_final_third_passes": 145.00,
      "avg_crosses": 18.00,
      "avg_dribbles": 12.50,
      "avg_successful_dribbles": 8.20,
      "avg_tackles": 16.30,
      "tackle_success_rate": 72.00,
      "avg_interceptions": 11.80,
      "interception_success_rate": 85.00,
      "avg_ball_recoveries": 48.50,
      "avg_saves_per_match": 3.20
    }
  }
}
```

**Database Queries:**

```sql
-- 1. Get coach and club info
SELECT
  u.full_name as coach_name,
  u.email as coach_email,
  c.club_id,
  c.club_name,
  c.logo_url,
  c.age_group,
  c.stadium,
  c.country
FROM users u
JOIN coaches co ON u.user_id = co.coach_id
JOIN clubs c ON co.coach_id = c.coach_id
WHERE u.user_id = :user_id_from_jwt;

-- 2. Get season statistics
SELECT * FROM club_season_statistics
WHERE club_id = :club_id;

-- 3. Get recent matches (last 5)
SELECT
  m.match_id,
  m.opponent_name,
  oc.logo_url as opponent_logo_url,
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
  END as result
FROM matches m
LEFT JOIN opponent_clubs oc ON m.opponent_club_id = oc.opponent_club_id
WHERE m.club_id = :club_id
  AND m.home_score IS NOT NULL  -- Only completed matches
ORDER BY m.match_date DESC, m.match_time DESC
LIMIT 5;

-- 4. Calculate team form (last 10 results)
-- Get last 10 match results and concatenate as string "WWDLWWDLWD"
SELECT
  STRING_AGG(
    CASE
      WHEN m.is_home_match AND m.home_score > m.away_score THEN 'W'
      WHEN m.is_home_match AND m.home_score < m.away_score THEN 'L'
      WHEN m.is_home_match AND m.home_score = m.away_score THEN 'D'
      WHEN NOT m.is_home_match AND m.away_score > m.home_score THEN 'W'
      WHEN NOT m.is_home_match AND m.away_score < m.home_score THEN 'L'
      ELSE 'D'
    END,
    ''
    ORDER BY m.match_date DESC, m.match_time DESC
  ) as team_form
FROM (
  SELECT * FROM matches
  WHERE club_id = :club_id
    AND home_score IS NOT NULL
  ORDER BY match_date DESC, match_time DESC
  LIMIT 10
) m;
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

## 2. Matches List Screen

**UI Purpose:** Display all matches for the club with filtering and pagination.

### GET /api/coach/matches

**Description:** Returns paginated list of all matches for the coach's club.

**Authentication:** Required (Coach only)

**Query Parameters:**
- `limit` (optional): Number of matches to return (default: 20, max: 100)
- `offset` (optional): Number of matches to skip for pagination (default: 0)

**Request:**
```
GET /api/coach/matches?limit=20&offset=0 HTTP/1.1
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
      "is_home_match": true,
      "home_score": 3,
      "away_score": 2,
      "result": "W"
    },
    {
      "match_id": "match-uuid-2",
      "opponent_name": "North Athletic",
      "opponent_logo_url": null,
      "match_date": "2025-10-01",
      "match_time": "14:00",
      "is_home_match": false,
      "home_score": 1,
      "away_score": 1,
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
  oc.logo_url as opponent_logo_url,
  m.match_date,
  m.match_time,
  m.is_home_match,
  m.home_score,
  m.away_score,
  CASE
    WHEN m.home_score IS NULL THEN NULL
    WHEN m.is_home_match AND m.home_score > m.away_score THEN 'W'
    WHEN m.is_home_match AND m.home_score < m.away_score THEN 'L'
    WHEN m.is_home_match AND m.home_score = m.away_score THEN 'D'
    WHEN NOT m.is_home_match AND m.away_score > m.home_score THEN 'W'
    WHEN NOT m.is_home_match AND m.away_score < m.home_score THEN 'L'
    ELSE 'D'
  END as result,
  COUNT(*) OVER() as total_count
FROM matches m
LEFT JOIN opponent_clubs oc ON m.opponent_club_id = oc.opponent_club_id
WHERE m.club_id = :club_id
ORDER BY m.match_date DESC, m.match_time DESC
LIMIT :limit OFFSET :offset;
```

---

## 3. Match Detail Screen

**UI Purpose:** Display full match details including lineup, goals, and statistics with 3 tabs (Overview, Statistics, Goals).

### GET /api/coach/matches/{match_id}

**Description:** Returns complete match details including lineups, goals, and statistics for both teams.

**Authentication:** Required (Coach only)

**Path Parameters:**
- `match_id` (required): UUID of the match

**Request:**
```
GET /api/coach/matches/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "match": {
    "match_id": "550e8400-e29b-41d4-a716-446655440000",
    "opponent_name": "City Strikers",
    "opponent_logo_url": "https://storage.example.com/opponents/city-strikers.png",
    "match_date": "2025-10-08",
    "match_time": "15:30",
    "is_home_match": true,
    "home_score": 3,
    "away_score": 2,
    "result": "W"
  },
  "our_club": {
    "club_name": "Thunder United FC",
    "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
  },
  "lineups": {
    "our_team": [
      {
        "player_id": "player-uuid-1",
        "player_name": "Marcus Silva",
        "jersey_number": 10,
        "position": "Forward",
        "is_linked": true,
        "profile_image_url": "https://storage.example.com/players/marcus.jpg"
      },
      {
        "player_id": "player-uuid-2",
        "player_name": "Jake Thompson",
        "jersey_number": 7,
        "position": "Midfielder",
        "is_linked": true,
        "profile_image_url": null
      }
    ],
    "opponent_team": [
      {
        "player_name": "John Doe",
        "jersey_number": 9,
        "position": "Forward"
      },
      {
        "player_name": "Mike Smith",
        "jersey_number": 11,
        "position": "Midfielder"
      }
    ]
  },
  "goals": [
    {
      "goal_id": "goal-uuid-1",
      "scorer_name": "Marcus Silva",
      "assist_name": "Jake Thompson",
      "team_name": "Thunder United FC",
      "minute": 12,
      "second": 45,
      "period": 1,
      "goal_type": "Open Play",
      "body_part": "Right Foot"
    },
    {
      "goal_id": "goal-uuid-2",
      "scorer_name": "John Doe",
      "assist_name": null,
      "team_name": "City Strikers",
      "minute": 25,
      "second": 10,
      "period": 1,
      "goal_type": "Penalty",
      "body_part": "Right Foot"
    }
  ],
  "statistics": {
    "our_team": {
      "possession_percentage": 58.50,
      "expected_goals": 2.450,
      "total_shots": 14,
      "shots_on_target": 8,
      "shots_off_target": 3,
      "goalkeeper_saves": 4,
      "total_passes": 487,
      "passes_completed": 423,
      "pass_completion_rate": 86.86,
      "passes_in_final_third": 145,
      "long_passes": 137,
      "crosses": 18,
      "total_dribbles": 25,
      "successful_dribbles": 18,
      "total_tackles": 16,
      "tackle_success_percentage": 75.00,
      "interceptions": 11,
      "ball_recoveries": 48
    },
    "opponent_team": {
      "possession_percentage": 41.50,
      "expected_goals": 1.890,
      "total_shots": 10,
      "shots_on_target": 6,
      "shots_off_target": 2,
      "goalkeeper_saves": 5,
      "total_passes": 365,
      "passes_completed": 298,
      "pass_completion_rate": 81.64,
      "passes_in_final_third": 98,
      "long_passes": 102,
      "crosses": 12,
      "total_dribbles": 18,
      "successful_dribbles": 11,
      "total_tackles": 20,
      "tackle_success_percentage": 70.00,
      "interceptions": 15,
      "ball_recoveries": 52
    }
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
  m.is_home_match,
  m.home_score,
  m.away_score,
  c.club_name as our_club_name,
  c.logo_url as our_logo_url,
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
  AND m.club_id = :club_id_from_jwt;  -- Authorization check

-- 2. Our team lineup
-- Get distinct players who participated in this match
SELECT DISTINCT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.is_linked,
  p.profile_image_url
FROM events e
JOIN players p ON e.statsbomb_player_id = p.statsbomb_player_id
WHERE e.match_id = :match_id
  AND e.team_name = :our_club_name
  AND p.club_id = :club_id
ORDER BY p.jersey_number;

-- Alternative if no StatsBomb ID match:
SELECT DISTINCT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.is_linked,
  p.profile_image_url
FROM events e
JOIN players p ON e.player_name = p.player_name
WHERE e.match_id = :match_id
  AND e.team_name = :our_club_name
  AND p.club_id = :club_id
ORDER BY p.jersey_number;

-- 3. Opponent lineup (from events)
SELECT DISTINCT
  player_name,
  -- Extract jersey from events if available
  -- Otherwise default to sequential numbering
  position_name as position
FROM events
WHERE match_id = :match_id
  AND team_name != :our_club_name
  AND event_type_name = 'Starting XI'
ORDER BY player_name;

-- 4. Goals
SELECT
  goal_id,
  team_name,
  scorer_name,
  assist_name,
  minute,
  second,
  period,
  goal_type,
  body_part
FROM goals
WHERE match_id = :match_id
ORDER BY period, minute, second;

-- 5. Statistics (both teams)
SELECT
  team_type,
  possession_percentage,
  expected_goals,
  total_shots,
  shots_on_target,
  shots_off_target,
  goalkeeper_saves,
  total_passes,
  passes_completed,
  pass_completion_rate,
  passes_in_final_third,
  long_passes,
  crosses,
  total_dribbles,
  successful_dribbles,
  total_tackles,
  tackle_success_percentage,
  interceptions,
  ball_recoveries
FROM match_statistics
WHERE match_id = :match_id;
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
  "detail": "This match does not belong to your club."
}
```

---

## 4. Players List Screen

**UI Purpose:** Display all players in the club, separated into linked (signed up) and unlinked (pending signup) players.

### GET /api/coach/players

**Description:** Returns all players in the coach's club with their basic info and season stats.

**Authentication:** Required (Coach only)

**Request:**
```
GET /api/coach/players HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "linked_players": [
    {
      "player_id": "player-uuid-1",
      "player_name": "Marcus Silva",
      "jersey_number": 10,
      "position": "Forward",
      "height": 180,
      "profile_image_url": "https://storage.example.com/players/marcus.jpg",
      "season_stats": {
        "matches_played": 22,
        "goals": 12,
        "assists": 7
      }
    },
    {
      "player_id": "player-uuid-2",
      "player_name": "Jake Thompson",
      "jersey_number": 7,
      "position": "Midfielder",
      "height": 175,
      "profile_image_url": null,
      "season_stats": {
        "matches_played": 20,
        "goals": 5,
        "assists": 10
      }
    }
  ],
  "unlinked_players": [
    {
      "player_id": "player-uuid-3",
      "player_name": "John Smith",
      "jersey_number": 15,
      "position": "Defender",
      "invite_code": "JHN-4523",
      "season_stats": {
        "matches_played": 5,
        "goals": 2,
        "assists": 1
      }
    },
    {
      "player_id": "player-uuid-4",
      "player_name": "Alex Brown",
      "jersey_number": 3,
      "position": "Goalkeeper",
      "invite_code": "ALX-8821",
      "season_stats": {
        "matches_played": 0,
        "goals": 0,
        "assists": 0
      }
    }
  ],
  "totals": {
    "linked_count": 15,
    "unlinked_count": 8
  }
}
```

**Database Queries:**

```sql
-- 1. Linked players with season stats
SELECT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.height,
  p.profile_image_url,
  pss.matches_played,
  pss.goals,
  pss.assists
FROM players p
LEFT JOIN player_season_statistics pss ON p.player_id = pss.player_id
WHERE p.club_id = :club_id
  AND p.is_linked = TRUE
ORDER BY p.jersey_number;

-- 2. Unlinked players with season stats
SELECT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.invite_code,
  pss.matches_played,
  pss.goals,
  pss.assists
FROM players p
LEFT JOIN player_season_statistics pss ON p.player_id = pss.player_id
WHERE p.club_id = :club_id
  AND p.is_linked = FALSE
ORDER BY p.jersey_number;

-- 3. Counts
SELECT
  COUNT(*) FILTER (WHERE is_linked = TRUE) as linked_count,
  COUNT(*) FILTER (WHERE is_linked = FALSE) as unlinked_count
FROM players
WHERE club_id = :club_id;
```

---

## 5. Player Detail Screen (Coach View)

**UI Purpose:** Display full player profile with statistics, attributes, recent matches, and training plans. Has 3 tabs: Summary (stats + attributes), Matches, Training.

### GET /api/coach/players/{player_id}

**Description:** Returns complete player information including stats, attributes, recent matches, and training plans.

**Authentication:** Required (Coach only)

**Path Parameters:**
- `player_id` (required): UUID of the player

**Request:**
```
GET /api/coach/players/player-uuid-1 HTTP/1.1
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
    "birth_date": "2008-03-20",
    "profile_image_url": "https://storage.example.com/players/marcus.jpg",
    "is_linked": true
  },
  "season_statistics": {
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
  },
  "recent_matches": [
    {
      "match_id": "match-uuid-1",
      "opponent_name": "City Strikers",
      "match_date": "2025-10-08",
      "goals": 2,
      "assists": 1,
      "shots": 6,
      "shots_on_target": 4
    },
    {
      "match_id": "match-uuid-2",
      "opponent_name": "North Athletic",
      "match_date": "2025-10-01",
      "goals": 1,
      "assists": 0,
      "shots": 5,
      "shots_on_target": 3
    }
  ],
  "training_plans": [
    {
      "plan_id": "plan-uuid-1",
      "plan_name": "Sprint Training for Marcus",
      "duration": "2 weeks",
      "status": "in_progress",
      "progress_percentage": 60,
      "created_at": "2025-10-14T10:00:00Z"
    },
    {
      "plan_id": "plan-uuid-2",
      "plan_name": "Finishing Drills",
      "duration": "1 week",
      "status": "completed",
      "progress_percentage": 100,
      "created_at": "2025-09-20T10:00:00Z"
    }
  ]
}
```

**Database Queries:**

```sql
-- 1. Player info and season stats
SELECT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.height,
  p.birth_date,
  p.profile_image_url,
  p.is_linked,
  pss.matches_played,
  pss.goals,
  pss.assists,
  pss.expected_goals,
  pss.shots_per_game,
  pss.shots_on_target_per_game,
  pss.total_passes,
  pss.passes_completed,
  pss.total_dribbles,
  pss.successful_dribbles,
  pss.tackles,
  pss.tackle_success_rate,
  pss.interceptions,
  pss.interception_success_rate,
  pss.attacking_rating,
  pss.technique_rating,
  pss.tactical_rating,
  pss.defending_rating,
  pss.creativity_rating
FROM players p
LEFT JOIN player_season_statistics pss ON p.player_id = pss.player_id
WHERE p.player_id = :player_id
  AND p.club_id = :club_id_from_jwt;  -- Authorization check

-- 2. Recent matches (last 5)
SELECT
  m.match_id,
  m.opponent_name,
  m.match_date,
  pms.goals,
  pms.assists,
  pms.shots,
  pms.shots_on_target
FROM player_match_statistics pms
JOIN matches m ON pms.match_id = m.match_id
WHERE pms.player_id = :player_id
ORDER BY m.match_date DESC
LIMIT 5;

-- 3. Training plans
SELECT
  tp.plan_id,
  tp.plan_name,
  tp.duration,
  tp.status,
  tp.created_at,
  COUNT(te.exercise_id) as total_exercises,
  COUNT(CASE WHEN te.completed THEN 1 END) as completed_exercises,
  (COUNT(CASE WHEN te.completed THEN 1 END) * 100.0 /
   NULLIF(COUNT(te.exercise_id), 0)) as progress_percentage
FROM training_plans tp
LEFT JOIN training_exercises te ON tp.plan_id = te.plan_id
WHERE tp.player_id = :player_id
GROUP BY tp.plan_id
ORDER BY tp.created_at DESC;
```

**Error Responses:**

Not Found (404):
```json
{
  "detail": "Player not found."
}
```

Forbidden (403):
```json
{
  "detail": "This player does not belong to your club."
}
```

---

## 6. Create Training Plan

**UI Purpose:** Form to create new training plan for a player with exercises.

### POST /api/coach/training-plans

**Description:** Create a new training plan for a player with exercises.

**Authentication:** Required (Coach only)

**Request:**
```json
POST /api/coach/training-plans HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "player_id": "player-uuid-1",
  "plan_name": "Sprint Training for Marcus",
  "duration": "2 weeks",
  "coach_notes": "Focus on maintaining form during maximum effort sprints. Rest 2 minutes between sets.",
  "exercises": [
    {
      "exercise_name": "40m Sprints",
      "description": "Maximum effort sprints from standing start. Focus on explosive first step.",
      "sets": "6",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 1
    },
    {
      "exercise_name": "Flying 30m Sprints",
      "description": "20m build-up, then 30m at maximum speed.",
      "sets": "4",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 2
    },
    {
      "exercise_name": "Cool Down Jog",
      "description": "Light jog to cool down muscles.",
      "sets": "1",
      "reps": "1",
      "duration_minutes": "10",
      "exercise_order": 3
    }
  ]
}
```

**Validation:**
- `player_id`: Required, must exist and belong to coach's club
- `plan_name`: Required, 2-255 characters
- `duration`: Optional, string
- `coach_notes`: Optional, text
- `exercises`: Required, array with at least 1 exercise
- `exercise.exercise_name`: Required, 2-255 characters
- `exercise.description`: Optional
- `exercise.sets`: Optional, string
- `exercise.reps`: Optional, string
- `exercise.duration_minutes`: Optional, string
- `exercise.exercise_order`: Required, integer (for ordering)

**Response (201 Created):**
```json
{
  "plan_id": "plan-uuid-1",
  "player_id": "player-uuid-1",
  "plan_name": "Sprint Training for Marcus",
  "duration": "2 weeks",
  "status": "pending",
  "coach_notes": "Focus on maintaining form during maximum effort sprints. Rest 2 minutes between sets.",
  "exercise_count": 3,
  "created_at": "2025-10-26T15:30:00Z"
}
```

**Database Queries:**

```sql
-- Start transaction
BEGIN;

-- 1. Verify player belongs to coach's club
SELECT p.club_id
FROM players p
JOIN clubs c ON p.club_id = c.club_id
WHERE p.player_id = :player_id
  AND c.coach_id = :coach_id_from_jwt;
-- If no result, return 403

-- 2. Insert training plan
INSERT INTO training_plans (
  plan_id,
  player_id,
  plan_name,
  duration,
  status,
  coach_notes,
  created_by,
  created_at
) VALUES (
  gen_random_uuid(),
  :player_id,
  :plan_name,
  :duration,
  'pending',
  :coach_notes,
  :coach_id_from_jwt,
  NOW()
) RETURNING plan_id;

-- 3. Insert exercises
FOR EACH exercise IN exercises:
  INSERT INTO training_exercises (
    exercise_id,
    plan_id,
    exercise_name,
    description,
    sets,
    reps,
    duration_minutes,
    exercise_order,
    completed,
    created_at
  ) VALUES (
    gen_random_uuid(),
    :plan_id,
    :exercise_name,
    :description,
    :sets,
    :reps,
    :duration_minutes,
    :exercise_order,
    FALSE,
    NOW()
  );

COMMIT;
```

**Error Responses:**

Player Not Found (404):
```json
{
  "detail": "Player not found."
}
```

Forbidden (403):
```json
{
  "detail": "This player does not belong to your club."
}
```

Validation Error (400):
```json
{
  "detail": "Validation failed",
  "errors": {
    "plan_name": "Plan name is required",
    "exercises": "At least one exercise is required"
  }
}
```

---

## 7. Update Training Plan

**UI Purpose:** Edit existing training plan.

### PUT /api/coach/training-plans/{plan_id}

**Description:** Update an existing training plan and its exercises.

**Authentication:** Required (Coach only)

**Path Parameters:**
- `plan_id` (required): UUID of the training plan

**Request:**
```json
PUT /api/coach/training-plans/plan-uuid-1 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "plan_name": "Updated Sprint Training",
  "duration": "3 weeks",
  "coach_notes": "Updated notes: Added one more exercise.",
  "exercises": [
    {
      "exercise_id": "exercise-uuid-1",
      "exercise_name": "40m Sprints",
      "description": "Updated description",
      "sets": "8",
      "reps": "1",
      "duration_minutes": "5",
      "exercise_order": 1
    },
    {
      "exercise_name": "New Exercise",
      "description": "New exercise description",
      "sets": "3",
      "reps": "10",
      "duration_minutes": "5",
      "exercise_order": 2
    }
  ]
}
```

**Notes:**
- Exercises with `exercise_id` are updated
- Exercises without `exercise_id` are created
- Exercises not in the request are deleted

**Response (200 OK):**
```json
{
  "plan_id": "plan-uuid-1",
  "player_id": "player-uuid-1",
  "plan_name": "Updated Sprint Training",
  "duration": "3 weeks",
  "status": "pending",
  "updated": true
}
```

**Database Queries:**

```sql
-- Start transaction
BEGIN;

-- 1. Verify plan belongs to coach's club
SELECT tp.plan_id
FROM training_plans tp
JOIN players p ON tp.player_id = p.player_id
JOIN clubs c ON p.club_id = c.club_id
WHERE tp.plan_id = :plan_id
  AND c.coach_id = :coach_id_from_jwt;
-- If no result, return 403

-- 2. Update plan
UPDATE training_plans SET
  plan_name = :plan_name,
  duration = :duration,
  coach_notes = :coach_notes
WHERE plan_id = :plan_id;

-- 3. Update existing exercises
FOR EACH exercise WITH exercise_id:
  UPDATE training_exercises SET
    exercise_name = :exercise_name,
    description = :description,
    sets = :sets,
    reps = :reps,
    duration_minutes = :duration_minutes,
    exercise_order = :exercise_order
  WHERE exercise_id = :exercise_id;

-- 4. Insert new exercises
FOR EACH exercise WITHOUT exercise_id:
  INSERT INTO training_exercises (...) VALUES (...);

-- 5. Delete exercises not in request
DELETE FROM training_exercises
WHERE plan_id = :plan_id
  AND exercise_id NOT IN (:list_of_exercise_ids_in_request);

COMMIT;
```

---

## 8. Delete Training Plan

**UI Purpose:** Allow coach to delete training plan.

### DELETE /api/coach/training-plans/{plan_id}

**Description:** Delete a training plan and all its exercises.

**Authentication:** Required (Coach only)

**Path Parameters:**
- `plan_id` (required): UUID of the training plan

**Request:**
```
DELETE /api/coach/training-plans/plan-uuid-1 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "deleted": true,
  "plan_id": "plan-uuid-1"
}
```

**Database Queries:**

```sql
-- Verify plan belongs to coach's club
SELECT tp.plan_id
FROM training_plans tp
JOIN players p ON tp.player_id = p.player_id
JOIN clubs c ON p.club_id = c.club_id
WHERE tp.plan_id = :plan_id
  AND c.coach_id = :coach_id_from_jwt;
-- If no result, return 403

-- Delete plan (exercises cascade delete)
DELETE FROM training_plans
WHERE plan_id = :plan_id;
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
  "detail": "This training plan does not belong to your club."
}
```

---

## Summary

### Coach Endpoints

| Endpoint | Method | Purpose | Screen |
|----------|--------|---------|--------|
| `/api/coach/dashboard` | GET | Coach dashboard with club overview | Dashboard |
| `/api/coach/matches` | GET | List all matches | Matches List |
| `/api/coach/matches/{match_id}` | GET | Match details | Match Detail |
| `/api/coach/players` | GET | List all players | Players List |
| `/api/coach/players/{player_id}` | GET | Player details | Player Detail |
| `/api/coach/training-plans` | POST | Create training plan | Create Training Plan |
| `/api/coach/training-plans/{plan_id}` | PUT | Update training plan | Edit Training Plan |
| `/api/coach/training-plans/{plan_id}` | DELETE | Delete training plan | Training Plan Management |

**Total: 8 endpoints**

### Authorization Rules

1. **Coach-only access:** All endpoints require `user_type = "coach"` in JWT token
2. **Club ownership:** Coaches can only access data belonging to their club:
   - Matches must belong to coach's club
   - Players must belong to coach's club
   - Training plans must be for players in coach's club
3. **Validation on every request:** Backend must verify club_id matches before returning data
