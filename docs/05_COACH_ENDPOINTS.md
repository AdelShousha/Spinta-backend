# Coach Endpoints

## Overview

This document details all API endpoints for the coach-facing features of the Spinta platform. All endpoints require authentication with a valid JWT token and `user_type = "coach"`.

## Authentication

All endpoints require:

- **Header:** `Authorization: Bearer <jwt_token>`
- **Token payload:** `user_type = "coach"`

For detailed authentication flow and endpoints, see `04_AUTHENTICATION.md` and `03_PLAYER_SIGNUP_FLOW.md`.

## Endpoints Organized by UI Screens

---

## 1. Coach Dashboard Screen

**UI Purpose:** Display club overview with two tabs: Summary (season record, team form, matches) and Statistics (detailed team metrics).

**UI Reference:** Pages 6-7 in Spinta UI.pdf

### GET /api/coach/dashboard

**Description:** Returns all data needed for the coach dashboard screen including club info, season record, team form, all matches, and detailed statistics.

**Authentication:** Required (Coach only)

**Query Parameters:**

- `matches_limit` (optional): Number of matches to return in matches list (default: 20, max: 100)
- `matches_offset` (optional): Number of matches to skip for pagination (default: 0)

**Request:**

```
GET /api/coach/dashboard?matches_limit=20&matches_offset=0 HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "coach": {
    "full_name": "John Smith"
  },
  "club": {
    "club_id": "550e8400-e29b-41d4-a716-446655440000",
    "club_name": "Thunder United FC",
    "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
  },
  "season_record": {
    "wins": 14,
    "draws": 4,
    "losses": 4
  },
  "team_form": "WWDLW",
  "matches": {
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
        "is_home_match": false,
        "result": "D"
      }
    ]
  },
  "statistics": {
    "season_summary": {
      "matches_played": 22,
      "goals_scored": 45,
      "goals_conceded": 23,
      "total_assists": 32
    },
    "attacking": {
      "avg_goals_per_match": 2.0,
      "avg_xg_per_match": 1.9,
      "avg_total_shots": 14,
      "avg_shots_on_target": 2.8,
      "avg_dribbles": 12.5,
      "avg_successful_dribbles": 8.2
    },
    "passes": {
      "avg_possession_percentage": 58,
      "avg_passes": 487,
      "pass_completion_percentage": 87,
      "avg_final_third_passes": 145,
      "avg_crosses": 18
    },
    "defending": {
      "total_clean_sheets": 8,
      "avg_goals_conceded_per_match": 1.0,
      "avg_tackles": 16.3,
      "tackle_success_percentage": 72,
      "avg_interceptions": 11.8,
      "interception_success_percentage": 85,
      "avg_ball_recoveries": 48.5,
      "avg_saves_per_match": 3.2
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

-- 2. Get season record from club_season_statistics
SELECT
  (wins + losses + draws) as matches_played,
  wins,
  draws,
  losses,
  goals_scored,
  goals_conceded,
  total_clean_sheets
FROM club_season_statistics
WHERE club_id = :club_id;

-- 3. Calculate team form (last 5 results as "WWDLW")
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
  LIMIT 5
) m;

-- 4. Get ALL matches with pagination
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
LIMIT :matches_limit OFFSET :matches_offset;

-- 5. Get detailed statistics from club_season_statistics
-- (All the avg fields are already pre-calculated in the table)
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

## 2. Match Detail Screen

**UI Purpose:** Display full match details with 3 tabs: Summary (goal scorers), Statistics (comparison bars), and Lineup (both teams' starting XI).

**UI Reference:** Pages 8-10 in Spinta UI.pdf

### GET /api/coach/matches/{match_id}

**Description:** Returns complete match details including goal scorers, team statistics comparisons, and lineups for both teams.

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
  "summary": {
    "goal_scorers": [
      {
        "goal_id": "goal-uuid-1",
        "scorer_name": "Marcus Silva",
        "assist_name": "Jake Thompson",
        "team_name": "Thunder United FC",
        "minute": 23,
        "second": 0,
        "period": 1,
        "goal_type": "Open Play",
        "body_part": "Right Foot"
      },
      {
        "goal_id": "goal-uuid-2",
        "scorer_name": "D. Martinez",
        "assist_name": null,
        "team_name": "City Strikers",
        "minute": 34,
        "second": 0,
        "period": 1,
        "goal_type": "Penalty",
        "body_part": "Right Foot"
      },
      {
        "goal_id": "goal-uuid-3",
        "scorer_name": "Jake Thompson",
        "assist_name": "Marcus Silva",
        "team_name": "Thunder United FC",
        "minute": 45,
        "second": 0,
        "period": 1,
        "goal_type": "Open Play",
        "body_part": "Head"
      },
      {
        "goal_id": "goal-uuid-4",
        "scorer_name": "R. Johnson",
        "assist_name": "P. Thompson",
        "team_name": "City Strikers",
        "minute": 67,
        "second": 0,
        "period": 2,
        "goal_type": "Open Play",
        "body_part": "Left Foot"
      },
      {
        "goal_id": "goal-uuid-5",
        "scorer_name": "Marcus Silva",
        "assist_name": "David Chen",
        "team_name": "Thunder United FC",
        "minute": 78,
        "second": 0,
        "period": 2,
        "goal_type": "Open Play",
        "body_part": "Right Foot"
      }
    ]
  },
  "statistics": {
    "match_overview": {
      "ball_possession": {
        "our_team": 55,
        "opponent": 45
      },
      "expected_goals": {
        "our_team": 2.4,
        "opponent": 1.8
      },
      "total_shots": {
        "our_team": 15,
        "opponent": 11
      },
      "goalkeeper_saves": {
        "our_team": 3,
        "opponent": 5
      },
      "total_passes": {
        "our_team": 487,
        "opponent": 412
      },
      "total_dribbles": {
        "our_team": 12,
        "opponent": 8
      }
    },
    "attacking": {
      "total_shots": {
        "our_team": 15,
        "opponent": 11
      },
      "shots_on_target": {
        "our_team": 8,
        "opponent": 5
      },
      "shots_off_target": {
        "our_team": 7,
        "opponent": 6
      },
      "total_dribbles": {
        "our_team": 12,
        "opponent": 8
      },
      "successful_dribbles": {
        "our_team": 9,
        "opponent": 5
      }
    },
    "passing": {
      "total_passes": {
        "our_team": 487,
        "opponent": 412
      },
      "passes_completed": {
        "our_team": 409,
        "opponent": 338
      },
      "passes_in_final_third": {
        "our_team": 142,
        "opponent": 98
      },
      "long_passes": {
        "our_team": 52,
        "opponent": 48
      },
      "crosses": {
        "our_team": 18,
        "opponent": 12
      }
    },
    "defending": {
      "tackle_success_percentage": {
        "our_team": 77.8,
        "opponent": 68.2
      },
      "total_tackles": {
        "our_team": 18,
        "opponent": 22
      },
      "interceptions": {
        "our_team": 12,
        "opponent": 8
      },
      "ball_recoveries": {
        "our_team": 48,
        "opponent": 42
      },
      "goalkeeper_saves": {
        "our_team": 3,
        "opponent": 5
      }
    }
  },
  "lineup": {
    "our_team": [
      {
        "player_id": "player-uuid-1",
        "jersey_number": 1,
        "player_name": "Alex Rodriguez",
        "position": "GK"
      },
      {
        "player_id": "player-uuid-2",
        "jersey_number": 3,
        "player_name": "Ryan Miller",
        "position": "DF"
      },
      {
        "player_id": "player-uuid-3",
        "jersey_number": 6,
        "player_name": "Tom Wilson",
        "position": "DF"
      },
      {
        "player_id": "player-uuid-4",
        "jersey_number": 3,
        "player_name": "Chris Brown",
        "position": "DF"
      },
      {
        "player_id": "player-uuid-5",
        "jersey_number": 2,
        "player_name": "Sam Davis",
        "position": "DF"
      },
      {
        "player_id": "player-uuid-6",
        "jersey_number": 6,
        "player_name": "Mike Johnson",
        "position": "MF"
      },
      {
        "player_id": "player-uuid-7",
        "jersey_number": 8,
        "player_name": "Paul Martinez",
        "position": "MF"
      },
      {
        "player_id": "player-uuid-8",
        "jersey_number": 15,
        "player_name": "David Chen",
        "position": "MF"
      },
      {
        "player_id": "player-uuid-9",
        "jersey_number": 10,
        "player_name": "Marcus Silva",
        "position": "FW"
      },
      {
        "player_id": "player-uuid-10",
        "jersey_number": 7,
        "player_name": "Jake Thompson",
        "position": "FW"
      },
      {
        "player_id": "player-uuid-11",
        "jersey_number": 11,
        "player_name": "Kevin Lee",
        "position": "FW"
      }
    ],
    "opponent_team": [
      {
        "opponent_player_id": "opp-player-uuid-1",
        "jersey_number": 1,
        "player_name": "D. Martinez",
        "position": "GK"
      },
      {
        "opponent_player_id": "opp-player-uuid-2",
        "jersey_number": 2,
        "player_name": "R. Johnson",
        "position": "DF"
      },
      {
        "opponent_player_id": "opp-player-uuid-3",
        "jersey_number": 5,
        "player_name": "L. Garcia",
        "position": "DF"
      },
      {
        "opponent_player_id": "opp-player-uuid-4",
        "jersey_number": 4,
        "player_name": "K. White",
        "position": "DF"
      },
      {
        "opponent_player_id": "opp-player-uuid-5",
        "jersey_number": 3,
        "player_name": "T. Anderson",
        "position": "DF"
      },
      {
        "opponent_player_id": "opp-player-uuid-6",
        "jersey_number": 8,
        "player_name": "M. Taylor",
        "position": "MF"
      },
      {
        "opponent_player_id": "opp-player-uuid-7",
        "jersey_number": 6,
        "player_name": "J. Wilson",
        "position": "MF"
      },
      {
        "opponent_player_id": "opp-player-uuid-8",
        "jersey_number": 10,
        "player_name": "S. Brown",
        "position": "MF"
      },
      {
        "opponent_player_id": "opp-player-uuid-9",
        "jersey_number": 11,
        "player_name": "C. Davis",
        "position": "FW"
      },
      {
        "opponent_player_id": "opp-player-uuid-10",
        "jersey_number": 9,
        "player_name": "P. Thompson",
        "position": "FW"
      },
      {
        "opponent_player_id": "opp-player-uuid-11",
        "jersey_number": 7,
        "player_name": "A. Miller",
        "position": "FW"
      }
    ]
  }
}
```

**Database Queries:**

```sql
-- 1. Match info with teams
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
  AND m.club_id = :club_id_from_jwt;

-- 2. Goal scorers
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

-- 3. Match statistics for both teams
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

-- 4. Our team lineup (from players who participated)
SELECT DISTINCT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position
FROM events e
JOIN players p ON e.statsbomb_player_id = p.statsbomb_player_id
WHERE e.match_id = :match_id
  AND e.team_name = :our_club_name
  AND e.event_type_name = 'Starting XI'
  AND p.club_id = :club_id
ORDER BY p.jersey_number;

-- 5. Opponent lineup (from opponent_players table)
SELECT
  op.opponent_player_id,
  op.player_name,
  op.jersey_number,
  op.position
FROM opponent_players op
JOIN matches m ON m.opponent_club_id = op.opponent_club_id
WHERE m.match_id = :match_id
ORDER BY op.jersey_number;
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

## 3. Players List Screen

**UI Purpose:** Display all players in the club with summary counts (total, joined, pending).

**UI Reference:** Page 11 in Spinta UI.pdf

### GET /api/coach/players

**Description:** Returns all players in the coach's club with summary counts and basic info.

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
  "summary": {
    "total_players": 5,
    "joined": 3,
    "pending": 2
  },
  "players": [
    {
      "player_id": "player-uuid-1",
      "player_name": "Marcus Silva",
      "jersey_number": 10,
      "profile_image_url": "https://storage.example.com/players/marcus.jpg",
      "is_linked": true
    },
    {
      "player_id": "player-uuid-2",
      "player_name": "Jake Thompson",
      "jersey_number": 7,
      "profile_image_url": "https://storage.example.com/players/jake.jpg",
      "is_linked": true
    },
    {
      "player_id": "player-uuid-3",
      "player_name": "Player #23",
      "jersey_number": 23,
      "profile_image_url": null,
      "is_linked": false,
      "invite_code": "SP23TH003",
      "status": "Pending Invitation"
    },
    {
      "player_id": "player-uuid-4",
      "player_name": "David Chen",
      "jersey_number": 15,
      "profile_image_url": "https://storage.example.com/players/david.jpg",
      "is_linked": true
    },
    {
      "player_id": "player-uuid-5",
      "player_name": "Player #9",
      "jersey_number": 9,
      "profile_image_url": null,
      "is_linked": false,
      "invite_code": "PLY-9982",
      "status": "Pending Invitation"
    }
  ]
}
```

**Database Queries:**

```sql
-- 1. Get summary counts
SELECT
  COUNT(*) as total_players,
  COUNT(*) FILTER (WHERE is_linked = TRUE) as joined,
  COUNT(*) FILTER (WHERE is_linked = FALSE) as pending
FROM players
WHERE club_id = :club_id;

-- 2. Get all players
SELECT
  player_id,
  player_name,
  jersey_number,
  profile_image_url,
  is_linked,
  invite_code
FROM players
WHERE club_id = :club_id
ORDER BY jersey_number;
```

---

## 4. Player Detail Screen (Coach View)

**UI Purpose:** Display full player profile with 3 tabs: Summary (attributes + season stats), Matches (match history), and Training (training plans).

**UI Reference:** Pages 12-16 in Spinta UI.pdf

### GET /api/coach/players/{player_id}

**Description:** Returns complete player information including attributes, season statistics organized by categories, recent matches, and training plans.

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
    "age": "23 years",
    "profile_image_url": "https://storage.example.com/players/marcus.jpg",
    "is_linked": true
  },
  "invite_code": null,
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
      "shots_on_target_per_game": 2.8
    },
    "passing": {
      "total_passes": 1144,
      "passes_completed": 995
    },
    "dribbling": {
      "total_dribbles": 158,
      "successful_dribbles": 118
    },
    "defending": {
      "tackles": 45,
      "tackle_success_rate": 78,
      "interceptions": 32,
      "interception_success_rate": 81
    }
  },
  "recent_matches": [
    {
      "match_id": "match-uuid-1",
      "opponent_name": "City Strikers",
      "match_date": "2025-10-08",
      "result": "W"
    },
    {
      "match_id": "match-uuid-2",
      "opponent_name": "North Athletic",
      "match_date": "2025-10-01",
      "result": "D"
    },
    {
      "match_id": "match-uuid-3",
      "opponent_name": "Valley Rangers",
      "match_date": "2025-10-01",
      "result": "W"
    },
    {
      "match_id": "match-uuid-4",
      "opponent_name": "Harbor FC",
      "match_date": "2025-09-28",
      "result": "L"
    },
    {
      "match_id": "match-uuid-5",
      "opponent_name": "Phoenix United",
      "match_date": "2025-09-24",
      "result": "W"
    }
  ],
  "training_plans": [
    {
      "plan_id": "plan-uuid-1",
      "plan_name": "Speed & Agility Development",
      "created_at": "2025-10-07",
      "status": "completed"
    },
    {
      "plan_id": "plan-uuid-2",
      "plan_name": "Shooting Accuracy Program",
      "created_at": "2025-10-14",
      "status": "in_progress"
    }
  ]
}
```

**For Unlinked Player (with invite code):**

```json
{
  "player": {
    "player_id": "player-uuid-3",
    "player_name": "Player #23",
    "jersey_number": 23,
    "position": "Forward",
    "height": null,
    "age": null,
    "profile_image_url": null,
    "is_linked": false
  },
  "invite_code": "SP23TH003",
  "attributes": {
    "attacking_rating": 68,
    "technique_rating": 72,
    "creativity_rating": 70,
    "tactical_rating": 65,
    "defending_rating": 35
  },
  "season_statistics": {
    "general": {
      "matches_played": 12
    },
    "attacking": {
      "goals": 5,
      "assists": 3,
      "expected_goals": 4.8,
      "shots_per_game": 3.5,
      "shots_on_target_per_game": 2.3
    },
    "passing": {
      "total_passes": 456,
      "passes_completed": 342
    },
    "dribbling": {
      "total_dribbles": 88,
      "successful_dribbles": 62
    },
    "defending": {
      "tackles": 22,
      "tackle_success_rate": 68,
      "interceptions": 15,
      "interception_success_rate": 73
    }
  },
  "recent_matches": [],
  "training_plans": []
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
  p.invite_code,
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
  AND p.club_id = :club_id_from_jwt;

-- 2. Recent matches (last 5)
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
  END as result
FROM player_match_statistics pms
JOIN matches m ON pms.match_id = m.match_id
WHERE pms.player_id = :player_id
ORDER BY m.match_date DESC
LIMIT 5;

-- 3. Training plans
SELECT
  plan_id,
  plan_name,
  created_at,
  status
FROM training_plans
WHERE player_id = :player_id
ORDER BY created_at DESC;
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

## 5. Player Match Detail (Coach View)

**UI Purpose:** Display player's individual performance in a specific match.

**UI Reference:** Page 15 in Spinta UI.pdf

### GET /api/coach/players/{player_id}/matches/{match_id}

**Description:** Returns detailed player statistics for a specific match.

**Authentication:** Required (Coach only)

**Path Parameters:**

- `player_id` (required): UUID of the player
- `match_id` (required): UUID of the match

**Request:**

```
GET /api/coach/players/player-uuid-1/matches/match-uuid-1 HTTP/1.1
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
    "opponent_name": "City Strikers",
    "opponent_logo_url": "https://storage.example.com/opponents/city-strikers.png",
    "home_score": 3,
    "away_score": 2,
    "result": "W"
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
-- 1. Match info
SELECT
  m.match_id,
  m.match_date,
  m.match_time,
  m.opponent_name,
  oc.logo_url as opponent_logo_url,
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
  AND pms.player_id = :player_id
  AND p.club_id = :club_id_from_jwt;
```

---

## 6. Generate AI Training Plan

**UI Purpose:** When "Create Training Plan Using AI" button is clicked, generate a training plan using AI.

**UI Reference:** Page 16 (button) → Page 17 (pre-filled form)

### POST /api/coach/training-plans/generate-ai

**Description:** Generate a training plan using AI for a specific player. Returns AI-generated plan data to pre-fill the creation form.

**Authentication:** Required (Coach only)

**Request:**

```json
POST /api/coach/training-plans/generate-ai HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "player_id": "player-uuid-1"
}
```

**Response (200 OK):**

```json
{
  "player_name": "Marcus Silva",
  "jersey_number": 10,
  "plan_name": "Shooting Accuracy Improvement",
  "duration": "4 weeks",
  "exercises": [
    {
      "exercise_name": "Target Shooting Drill",
      "description": "Practice shooting at designated target zones in the goal from various angles",
      "sets": "3",
      "reps": "10",
      "duration_minutes": "20"
    },
    {
      "exercise_name": "First Touch & Finish",
      "description": "Receive passes and shoot on goal with maximum 2 touches",
      "sets": "4",
      "reps": "8",
      "duration_minutes": "15"
    },
    {
      "exercise_name": "Power Shot Training",
      "description": "Work on generating shot power while maintaining accuracy",
      "sets": "3",
      "reps": "12",
      "duration_minutes": "18"
    }
  ]
}
```

**Notes:**

- AI implementation details are not included in this documentation
- The endpoint will use AI to analyze player statistics and generate appropriate training recommendations
- Coach can then add more exercises and notes before submitting via the Create Training Plan endpoint

---

## 7. Create Training Plan

**UI Purpose:** Create a new training plan for a player (after coach reviews/edits AI-generated or manually creates).

**UI Reference:** Page 17 (form submission)

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
  "plan_name": "Shooting Accuracy Improvement",
  "duration": "4 weeks",
  "coach_notes": "Focus on weak foot technique. Remember to follow through on every shot.",
  "exercises": [
    {
      "exercise_name": "Target Shooting Drill",
      "description": "Practice shooting at designated target zones in the goal from various angles",
      "sets": "3",
      "reps": "10",
      "duration_minutes": "20",
      "exercise_order": 1
    },
    {
      "exercise_name": "First Touch & Finish",
      "description": "Receive passes and shoot on goal with maximum 2 touches",
      "sets": "4",
      "reps": "8",
      "duration_minutes": "15",
      "exercise_order": 2
    },
    {
      "exercise_name": "Power Shot Training",
      "description": "Work on generating shot power while maintaining accuracy",
      "sets": "3",
      "reps": "12",
      "duration_minutes": "18",
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
  "plan_name": "Shooting Accuracy Improvement",
  "duration": "4 weeks",
  "status": "pending",
  "coach_notes": "Focus on weak foot technique. Remember to follow through on every shot.",
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

## 8. Training Plan Detail (Coach View)

**UI Purpose:** Display detailed view of a training plan when clicking from the player's training tab.

**UI Reference:** Page 18 in Spinta UI.pdf

### GET /api/coach/training-plans/{plan_id}

**Description:** Get detailed training plan information including all exercises, progress, and coach notes.

**Authentication:** Required (Coach only)

**Path Parameters:**

- `plan_id` (required): UUID of the training plan

**Request:**

```
GET /api/coach/training-plans/plan-uuid-1 HTTP/1.1
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
      "exercise_name": "Target Practice",
      "description": "Shooting at specific zones in the goal from various distances",
      "sets": "3",
      "reps": "15",
      "duration_minutes": "20",
      "completed": true,
      "exercise_order": 1
    },
    {
      "exercise_id": "exercise-uuid-2",
      "exercise_name": "One-Touch-Finishing",
      "description": "Quick shots immediately after receiving pass",
      "sets": "4",
      "reps": "10",
      "duration_minutes": "15",
      "completed": true,
      "exercise_order": 2
    },
    {
      "exercise_id": "exercise-uuid-3",
      "exercise_name": "Power-Shots",
      "description": "Maximum power strikes from 18 yards",
      "sets": "3",
      "reps": "12",
      "duration_minutes": "18",
      "completed": true,
      "exercise_order": 3
    },
    {
      "exercise_id": "exercise-uuid-4",
      "exercise_name": "Defender-Finishing",
      "description": "Shooting under pressure with defender present",
      "sets": "5",
      "reps": "8",
      "duration_minutes": null,
      "completed": true,
      "exercise_order": 4
    },
    {
      "exercise_id": "exercise-uuid-5",
      "exercise_name": "Quick-Release",
      "description": "Rapid shooting technique with 2-second constraint",
      "sets": "4",
      "reps": "10",
      "duration_minutes": "2",
      "completed": true,
      "exercise_order": 5
    },
    {
      "exercise_id": "exercise-uuid-6",
      "exercise_name": "Weak-Foot-Practice",
      "description": "Exclusive left foot shooting drills",
      "sets": "3",
      "reps": "15",
      "duration_minutes": null,
      "completed": true,
      "exercise_order": 6
    },
    {
      "exercise_id": "exercise-uuid-7",
      "exercise_name": "Curved Shots",
      "description": "Bending the ball around obstacles",
      "sets": "3",
      "reps": "10",
      "duration_minutes": null,
      "completed": false,
      "exercise_order": 7
    },
    {
      "exercise_id": "exercise-uuid-8",
      "exercise_name": "Volleys",
      "description": "Shooting from aerial passes and crosses",
      "sets": "4",
      "reps": "8",
      "duration_minutes": null,
      "completed": false,
      "exercise_order": 8
    },
    {
      "exercise_id": "exercise-uuid-9",
      "exercise_name": "Penalty Practice",
      "description": "Spot kicks with goalkeeper",
      "sets": "2",
      "reps": "10",
      "duration_minutes": null,
      "completed": false,
      "exercise_order": 9
    },
    {
      "exercise_id": "exercise-uuid-10",
      "exercise_name": "Match Simulation",
      "description": "Game-realistic shooting scenarios",
      "sets": null,
      "reps": null,
      "duration_minutes": "30",
      "completed": false,
      "exercise_order": 10
    }
  ],
  "coach_notes": "Remember to follow through on every shot. Your weak foot technique needs more attention - dedicate extra time to those drills."
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
  p.player_name,
  p.jersey_number as player_jersey,
  te.exercise_id,
  te.exercise_name,
  te.description,
  te.sets,
  te.reps,
  te.duration_minutes,
  te.exercise_order,
  te.completed
FROM training_plans tp
JOIN players p ON tp.player_id = p.player_id
LEFT JOIN training_exercises te ON tp.plan_id = te.plan_id
WHERE tp.plan_id = :plan_id
  AND p.club_id = :club_id_from_jwt
ORDER BY te.exercise_order;

-- Calculate progress
SELECT
  COUNT(*) as total_exercises,
  COUNT(CASE WHEN completed THEN 1 END) as completed_exercises,
  (COUNT(CASE WHEN completed THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)) as percentage
FROM training_exercises
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

## 9. Update Training Plan

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

## 10. Delete Training Plan

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

| Endpoint                                            | Method | Purpose                                                 | Screen                   |
| --------------------------------------------------- | ------ | ------------------------------------------------------- | ------------------------ |
| `/api/coach/dashboard`                              | GET    | Coach dashboard with 2 tabs (Summary, Statistics)       | Dashboard                |
| `/api/coach/matches/{match_id}`                     | GET    | Match details with 3 tabs (Summary, Statistics, Lineup) | Match Detail             |
| `/api/coach/players`                                | GET    | List all players with summary counts                    | Players List             |
| `/api/coach/players/{player_id}`                    | GET    | Player details with 3 tabs (Summary, Matches, Training) | Player Detail            |
| `/api/coach/players/{player_id}/matches/{match_id}` | GET    | Player's performance in specific match                  | Player Match Detail      |
| `/api/coach/training-plans/generate-ai`             | POST   | Generate AI training plan                               | AI Generation            |
| `/api/coach/training-plans`                         | POST   | Create training plan                                    | Create Training Plan     |
| `/api/coach/training-plans/{plan_id}`               | GET    | Training plan details                                   | Training Plan Detail     |
| `/api/coach/training-plans/{plan_id}`               | PUT    | Update training plan                                    | Edit Training Plan       |
| `/api/coach/training-plans/{plan_id}`               | DELETE | Delete training plan                                    | Training Plan Management |

**Total: 10 endpoints**

### Authorization Rules

1. **Coach-only access:** All endpoints require `user_type = "coach"` in JWT token
2. **Club ownership:** Coaches can only access data belonging to their club:
   - Matches must belong to coach's club
   - Players must belong to coach's club
   - Training plans must be for players in coach's club
3. **Validation on every request:** Backend must verify club_id matches before returning data

### Key Features

1. **Dashboard with Tabs:**

   - Summary tab: Season record, team form, ALL matches (with pagination)
   - Statistics tab: Organized by categories (Season Summary, Attacking, Passes, Defending)

2. **Match Detail with Tabs:**

   - Summary tab: Goal scorers with team names for color coding
   - Statistics tab: Comparison bars for both teams
   - Lineup tab: Both teams' starting XI with jersey numbers

3. **Player Detail with Tabs:**

   - Summary tab: Attributes radar chart + season statistics by category
   - Matches tab: Recent 5 matches
   - Training tab: List of training plans with status

4. **AI Training Plan Generation:**

   - Generate button sends request to AI endpoint
   - Returns pre-filled form data (plan name, duration, exercises)
   - Coach can edit before final submission

5. **Statistics Organization:**
   - GENERAL (1 metric)
   - ATTACKING (6 metrics)
   - PASSING (2-5 metrics)
   - DRIBBLING (2 metrics)
   - DEFENDING (4-8 metrics)
