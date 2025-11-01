# Admin Endpoints

## Overview

This document details the admin panel endpoints for the Spinta platform. The admin panel is used by coaches to upload match videos with StatsBomb event data, which triggers automatic processing of matches, lineups, statistics, and player records.

**Note:** In the Spinta system, coaches serve as admins for their own clubs. All admin endpoints are authenticated coach endpoints.

## Authentication

All endpoints require:
- **Header:** `Authorization: Bearer <jwt_token>`
- **Token payload:** `user_type = "coach"`

---

## Match Upload and Processing

### POST /api/coach/matches

**Description:** Upload match data with StatsBomb events. This endpoint processes match video analysis results, creates match records, extracts lineups, calculates statistics, and generates player invite codes.

**Authentication:** Required (Coach only)

**Request:**
```json
POST /api/coach/matches HTTP/1.1
Host: api.spinta.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "opponent_name": "City Strikers",
  "opponent_logo_url": "https://storage.example.com/opponents/city-strikers.png",
  "match_date": "2025-10-08",
  "match_time": "15:30:00",
  "is_home_match": true,
  "home_score": 3,
  "away_score": 2,
  "statsbomb_events": [
    {
      "id": "a3f7e8c2-1234-5678-9abc-def012345678",
      "index": 1,
      "period": 1,
      "timestamp": "00:00:00.000",
      "minute": 0,
      "second": 0,
      "type": {
        "id": 35,
        "name": "Starting XI"
      },
      "possession": 1,
      "possession_team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "play_pattern": {
        "id": 1,
        "name": "Regular Play"
      },
      "team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "tactics": {
        "formation": 442,
        "lineup": [
          {
            "player": {
              "id": 5470,
              "name": "Marcus Silva"
            },
            "position": {
              "id": 23,
              "name": "Center Forward"
            },
            "jersey_number": 10
          },
          {
            "player": {
              "id": 5471,
              "name": "Jake Thompson"
            },
            "position": {
              "id": 13,
              "name": "Right Center Midfield"
            },
            "jersey_number": 7
          }
          // ... 9 more players (11 total in Starting XI)
        ]
      }
    },
    {
      "id": "b4e9f3d5-2345-6789-abcd-ef0123456789",
      "index": 2,
      "period": 1,
      "timestamp": "00:00:00.000",
      "minute": 0,
      "second": 0,
      "type": {
        "id": 35,
        "name": "Starting XI"
      },
      "possession": 1,
      "possession_team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "play_pattern": {
        "id": 1,
        "name": "Regular Play"
      },
      "team": {
        "id": 912,
        "name": "City Strikers"
      },
      "tactics": {
        "formation": 433,
        "lineup": [
          {
            "player": {
              "id": 8923,
              "name": "John Doe"
            },
            "position": {
              "id": 23,
              "name": "Center Forward"
            },
            "jersey_number": 9
          }
          // ... 10 more opponent players
        ]
      }
    },
    {
      "id": "c5fa04e6-3456-789a-bcde-f01234567890",
      "index": 15,
      "period": 1,
      "timestamp": "00:12:34.567",
      "minute": 12,
      "second": 34,
      "type": {
        "id": 16,
        "name": "Shot"
      },
      "possession": 2,
      "possession_team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "play_pattern": {
        "id": 1,
        "name": "Regular Play"
      },
      "team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "player": {
        "id": 5470,
        "name": "Marcus Silva"
      },
      "position": {
        "id": 23,
        "name": "Center Forward"
      },
      "location": [102.3, 34.5],
      "duration": 1.2,
      "shot": {
        "statsbomb_xg": 0.45,
        "end_location": [120.0, 38.2, 2.1],
        "outcome": {
          "id": 97,
          "name": "Goal"
        },
        "type": {
          "id": 87,
          "name": "Open Play"
        },
        "body_part": {
          "id": 40,
          "name": "Right Foot"
        }
      }
    },
    {
      "id": "d6gb15f7-4567-89ab-cdef-012345678901",
      "index": 16,
      "period": 1,
      "timestamp": "00:12:34.567",
      "minute": 12,
      "second": 34,
      "type": {
        "id": 34,
        "name": "Pass"
      },
      "possession": 2,
      "possession_team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "play_pattern": {
        "id": 1,
        "name": "Regular Play"
      },
      "team": {
        "id": 746,
        "name": "Thunder United FC"
      },
      "player": {
        "id": 5471,
        "name": "Jake Thompson"
      },
      "position": {
        "id": 13,
        "name": "Right Center Midfield"
      },
      "location": [95.2, 45.8],
      "duration": 0.8,
      "pass": {
        "recipient": {
          "id": 5470,
          "name": "Marcus Silva"
        },
        "length": 12.5,
        "angle": 0.45,
        "height": {
          "id": 1,
          "name": "Ground Pass"
        },
        "end_location": [102.3, 34.5],
        "outcome": {
          "id": 9,
          "name": "Complete"
        },
        "body_part": {
          "id": 40,
          "name": "Right Foot"
        },
        "type": {
          "id": 65,
          "name": "Through Ball"
        },
        "goal_assist": true
      }
    }
    // ... ~3000 more events
  ]
}
```

**Request Body Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `opponent_name` | String | Yes | Opponent team name (2-255 chars) |
| `opponent_logo_url` | String (URL) | No | Opponent team logo URL |
| `match_date` | Date (YYYY-MM-DD) | Yes | Match date |
| `match_time` | Time (HH:MM:SS) | Yes | Match kickoff time |
| `is_home_match` | Boolean | Yes | true = home match, false = away match |
| `home_score` | Integer | Yes | Final score for home team |
| `away_score` | Integer | Yes | Final score for away team |
| `statsbomb_events` | Array | Yes | Full StatsBomb event data (typically ~3000 events) |

**StatsBomb Events Array:**
- Complete JSON array from StatsBomb data
- Contains all event types: Starting XI, Pass, Shot, Dribble, Tackle, etc.
- See @docs\Open Data Events v4.0.0.pdf for full event schema
- Typical size: 160,000 lines / 10-20 MB JSON

---

## Backend Processing Logic

### Step 1: Authentication & Authorization

```python
# Verify coach is authenticated
coach_id = get_user_from_jwt(request.headers['Authorization'])
club_id = get_club_id_for_coach(coach_id)

if not club_id:
    return 403 Forbidden
```

---

### Step 2: Identify Teams from JSON

```python
# Extract team information from Starting XI events
starting_xi_events = filter_events_by_type(statsbomb_events, "Starting XI")

# Typically 2 Starting XI events (one per team)
team_1 = starting_xi_events[0]['team']  # {"id": 746, "name": "Thunder United FC"}
team_2 = starting_xi_events[1]['team']  # {"id": 912, "name": "City Strikers"}

# Determine which team is the coach's club
our_club = get_club(club_id)

if our_club.club_name == team_1['name']:
    our_team_id = team_1['id']
    our_team_name = team_1['name']
    opponent_team_id = team_2['id']
    opponent_team_name = team_2['name']
elif our_club.club_name == team_2['name']:
    our_team_id = team_2['id']
    our_team_name = team_2['name']
    opponent_team_id = team_1['id']
    opponent_team_name = team_1['name']
else:
    return 400 Bad Request - "Cannot match your club name to teams in event data"

# Set statsbomb_team_id if not already set
if our_club.statsbomb_team_id is NULL:
    UPDATE clubs SET statsbomb_team_id = our_team_id WHERE club_id = club_id
```

---

### Step 3: Create/Get Opponent Club

```sql
-- Check if opponent exists by statsbomb_team_id
SELECT opponent_club_id FROM opponent_clubs
WHERE statsbomb_team_id = :opponent_team_id;

-- If not found, check by name
SELECT opponent_club_id FROM opponent_clubs
WHERE opponent_name = :opponent_name;

-- If still not found, create new opponent club
INSERT INTO opponent_clubs (
  opponent_club_id,
  opponent_name,
  statsbomb_team_id,
  logo_url,
  created_at
) VALUES (
  gen_random_uuid(),
  :opponent_name,
  :opponent_team_id,
  :opponent_logo_url,
  NOW()
) RETURNING opponent_club_id;
```

---

### Step 4: Create Match Record

```sql
INSERT INTO matches (
  match_id,
  club_id,
  opponent_club_id,
  opponent_name,
  match_date,
  match_time,
  is_home_match,
  home_score,
  away_score,
  created_at,
  updated_at
) VALUES (
  gen_random_uuid(),
  :club_id,
  :opponent_club_id,
  :opponent_name,
  :match_date,
  :match_time,
  :is_home_match,
  :home_score,
  :away_score,
  NOW(),
  NOW()
) RETURNING match_id;
```

---

### Step 5: Insert All Events

```sql
-- For each event in statsbomb_events array (~3000 events)
INSERT INTO events (
  event_id,
  match_id,
  statsbomb_player_id,
  statsbomb_team_id,
  player_name,
  team_name,
  event_type_name,
  position_name,
  minute,
  second,
  period,
  event_data,  -- Store full event JSON as JSONB
  created_at
) VALUES (
  gen_random_uuid(),
  :match_id,
  event['player']['id'] if 'player' in event else NULL,
  event['team']['id'],
  event['player']['name'] if 'player' in event else NULL,
  event['team']['name'],
  event['type']['name'],
  event['position']['name'] if 'position' in event else NULL,
  event['minute'],
  event['second'],
  event['period'],
  event (as JSONB),
  NOW()
);
```

---

### Step 6: Extract and Create Goals

```python
# Filter Shot events where outcome is "Goal"
goal_events = [e for e in statsbomb_events
               if e['type']['name'] == 'Shot'
               and e.get('shot', {}).get('outcome', {}).get('name') == 'Goal']

# Find assist for each goal (Pass event immediately before with goal_assist=true)
for goal_event in goal_events:
    # Find the Pass event just before this Shot
    assist_event = find_pass_before_shot(statsbomb_events, goal_event)

    assist_name = None
    if assist_event and assist_event.get('pass', {}).get('goal_assist'):
        assist_name = assist_event['player']['name']

    INSERT INTO goals (
      goal_id,
      match_id,
      team_name,
      scorer_name,
      assist_name,
      minute,
      second,
      period,
      goal_type,  -- e.g., "Open Play", "Penalty", "Free Kick"
      body_part,   -- e.g., "Right Foot", "Left Foot", "Head"
      created_at
    ) VALUES (
      gen_random_uuid(),
      :match_id,
      goal_event['team']['name'],
      goal_event['player']['name'],
      assist_name,
      goal_event['minute'],
      goal_event['second'],
      goal_event['period'],
      goal_event['shot']['type']['name'],
      goal_event['shot']['body_part']['name'],
      NOW()
    );
```

**Goal Validation:**
```python
# Count goals from events
our_goals_from_json = count(goals where team_name == our_team_name)
opponent_goals_from_json = count(goals where team_name == opponent_team_name)

# Compare with admin's input
if is_home_match:
    our_score_input = home_score
    opponent_score_input = away_score
else:
    our_score_input = away_score
    opponent_score_input = home_score

warnings = []
if our_goals_from_json != our_score_input:
    warnings.append(f"Event data has {our_goals_from_json} goals for your team but score says {our_score_input}")

if opponent_goals_from_json != opponent_score_input:
    warnings.append(f"Event data has {opponent_goals_from_json} goals for opponent but score says {opponent_score_input}")

# Always use admin's input scores (home_score, away_score) as source of truth
```

---

### Step 7: Extract and Create/Update Players (Your Club)

```python
# Get Starting XI for our team
our_starting_xi = [e for e in statsbomb_events
                   if e['type']['name'] == 'Starting XI'
                   and e['team']['name'] == our_team_name][0]

lineup = our_starting_xi['tactics']['lineup']

for player_data in lineup:
    statsbomb_player_id = player_data['player']['id']
    player_name = player_data['player']['name']
    jersey_number = player_data['jersey_number']
    position = player_data['position']['name']

    # Check if player exists by statsbomb_player_id
    existing_player = SELECT * FROM players
                      WHERE club_id = :club_id
                      AND statsbomb_player_id = :statsbomb_player_id;

    if existing_player:
        # Player exists - update jersey number and position if changed
        UPDATE players SET
          jersey_number = :jersey_number,
          position = :position,
          updated_at = NOW()
        WHERE player_id = existing_player.player_id;

        player_id = existing_player.player_id

    else:
        # Check if player exists by name or jersey (without statsbomb_player_id)
        existing_player_by_name = SELECT * FROM players
                                  WHERE club_id = :club_id
                                  AND (player_name = :player_name OR jersey_number = :jersey_number);

        if existing_player_by_name:
            # Update existing player's statsbomb_player_id and other fields
            UPDATE players SET
              statsbomb_player_id = :statsbomb_player_id,
              player_name = :player_name,
              jersey_number = :jersey_number,
              position = :position,
              updated_at = NOW()
            WHERE player_id = existing_player_by_name.player_id;

            player_id = existing_player_by_name.player_id

        else:
            # Create new player (incomplete, not linked)
            invite_code = generate_invite_code(player_name)

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
              gen_random_uuid(),
              :club_id,
              :player_name,
              :statsbomb_player_id,
              :jersey_number,
              :position,
              :invite_code,
              FALSE,
              NOW(),
              NOW()
            ) RETURNING player_id;

            # Initialize player season statistics
            INSERT INTO player_season_statistics (
              player_stats_id,
              player_id,
              updated_at
            ) VALUES (
              gen_random_uuid(),
              :player_id,
              NOW()
            );

            new_players_created.append({
              "player_name": player_name,
              "jersey_number": jersey_number,
              "invite_code": invite_code
            })
```

**Invite Code Generation:**
```python
def generate_invite_code(player_name):
    import secrets
    import string

    # Extract prefix from name
    parts = player_name.split()
    if len(parts) >= 2:
        prefix = (parts[0][0] + parts[-1][:2]).upper()
    else:
        prefix = player_name[:3].upper()

    # Generate unique code
    while True:
        digits = ''.join(secrets.choice(string.digits) for _ in range(4))
        code = f"{prefix}-{digits}"

        # Check uniqueness
        exists = SELECT 1 FROM players WHERE invite_code = code;
        if not exists:
            return code
```

---

### Step 8: Extract and Create Opponent Players

```python
# Get Starting XI for opponent team
opponent_starting_xi = [e for e in statsbomb_events
                        if e['type']['name'] == 'Starting XI'
                        and e['team']['name'] == opponent_team_name][0]

opponent_lineup = opponent_starting_xi['tactics']['lineup']

for player_data in opponent_lineup:
    statsbomb_player_id = player_data['player']['id']
    player_name = player_data['player']['name']
    jersey_number = player_data['jersey_number']
    position = player_data['position']['name']

    # Check if opponent player exists
    existing = SELECT * FROM opponent_players
               WHERE opponent_club_id = :opponent_club_id
               AND statsbomb_player_id = :statsbomb_player_id;

    if not existing:
        # Check by name/jersey
        existing = SELECT * FROM opponent_players
                   WHERE opponent_club_id = :opponent_club_id
                   AND (player_name = :player_name OR jersey_number = :jersey_number);

    if existing:
        # Update existing opponent player
        UPDATE opponent_players SET
          jersey_number = :jersey_number,
          position = :position
        WHERE opponent_player_id = existing.opponent_player_id;
    else:
        # Create new opponent player
        INSERT INTO opponent_players (
          opponent_player_id,
          opponent_club_id,
          player_name,
          statsbomb_player_id,
          jersey_number,
          position,
          created_at
        ) VALUES (
          gen_random_uuid(),
          :opponent_club_id,
          :player_name,
          :statsbomb_player_id,
          :jersey_number,
          :position,
          NOW()
        );
```

---

### Step 9: Calculate and Store Match Statistics

**Concept:** Aggregate statistics from events table for both teams.

```python
# Calculate for our team
our_team_stats = calculate_team_stats(match_id, our_team_name)

INSERT INTO match_statistics (
  statistics_id,
  match_id,
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
  ball_recoveries,
  created_at
) VALUES (
  gen_random_uuid(),
  :match_id,
  'our_team',
  our_team_stats['possession_percentage'],
  our_team_stats['expected_goals'],
  our_team_stats['total_shots'],
  # ... all other stats
  NOW()
);

# Calculate for opponent team
opponent_team_stats = calculate_team_stats(match_id, opponent_team_name)

INSERT INTO match_statistics (
  # ... same fields as above
  team_type = 'opponent_team',
  # ... opponent stats
);
```

**Statistics Calculation Formulas:**

| Statistic | Calculation Method | Event Fields Used |
|-----------|-------------------|-------------------|
| **Possession %** | Time in possession / Total time | `possession_team`, `duration` |
| **Expected Goals (xG)** | Sum of shot xG values | `shot.statsbomb_xg` from Shot events |
| **Total Shots** | Count Shot events | `type.name == "Shot"` |
| **Shots on Target** | Count shots with outcome "Saved" or "Goal" | `shot.outcome.name IN ["Saved", "Goal"]` |
| **Shots off Target** | Count shots with outcome "Off T", "Wayward" | `shot.outcome.name IN ["Off T", "Wayward"]` |
| **Goalkeeper Saves** | Count opponent shots with outcome "Saved" | Opponent's Shot events with `outcome == "Saved"` |
| **Total Passes** | Count Pass events | `type.name == "Pass"` |
| **Passes Completed** | Count successful passes | `pass.outcome` is NULL or "Complete" |
| **Pass Completion Rate** | (Completed / Total) * 100 | Calculated from above |
| **Passes in Final Third** | Count passes with location x > 80 | `location[0] > 80` for Pass events |
| **Long Passes** | Count passes with length > 30 | `pass.length > 30` |
| **Crosses** | Count passes with type "Cross" | `pass.type.name == "Cross"` |
| **Total Dribbles** | Count Dribble events | `type.name == "Dribble"` |
| **Successful Dribbles** | Count dribbles with outcome "Complete" | `dribble.outcome.name == "Complete"` |
| **Total Tackles** | Count Duel events with type "Tackle" | `duel.type.name == "Tackle"` |
| **Tackle Success %** | (Won tackles / Total tackles) * 100 | `duel.outcome.name == "Success"` |
| **Interceptions** | Count Interception events | `type.name == "Interception"` |
| **Ball Recoveries** | Count Ball Recovery events | `type.name == "Ball Recovery"` |

---

### Step 10: Calculate and Store Player Match Statistics

**Concept:** Aggregate statistics from events table for each player in your club's lineup.

```python
# For each player in our Starting XI
for player in our_lineup:
    player_id = get_player_id_by_statsbomb_id(player['player']['id'], club_id)

    if not player_id:
        continue  # Skip if player not found (shouldn't happen)

    player_stats = calculate_player_stats(match_id, player['player']['id'])

    INSERT INTO player_match_statistics (
      player_match_stats_id,
      player_id,
      match_id,
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
      interception_success_rate,
      created_at
    ) VALUES (
      gen_random_uuid(),
      :player_id,
      :match_id,
      player_stats['goals'],
      player_stats['assists'],
      # ... all stats
      NOW()
    );
```

**Player Statistics Calculation:**

| Statistic | Calculation Method |
|-----------|-------------------|
| **Goals** | Count Shot events with outcome "Goal" for this player |
| **Assists** | Count Pass events with `goal_assist == true` for this player |
| **Expected Goals** | Sum of `shot.statsbomb_xg` for this player's shots |
| **Shots** | Count Shot events for this player |
| **Shots on Target** | Count shots with outcome "Saved" or "Goal" |
| **Total Dribbles** | Count Dribble events for this player |
| **Successful Dribbles** | Count dribbles with outcome "Complete" |
| **Total Passes** | Count Pass events for this player |
| **Completed Passes** | Count passes with outcome NULL or "Complete" |
| **Short Passes** | Count passes with length < 15 |
| **Long Passes** | Count passes with length > 30 |
| **Final Third Passes** | Count passes with start location x > 80 |
| **Crosses** | Count passes with type "Cross" |
| **Tackles** | Count Duel/Tackle events for this player |
| **Tackle Success Rate** | (Won tackles / Total tackles) * 100 |
| **Interceptions** | Count Interception events |
| **Interception Success Rate** | (Successful intercepts / Total) * 100 |

---

### Step 11: Update Club Season Statistics

```python
# Recalculate club season statistics from all matches
club_stats = aggregate_club_stats(club_id)

UPDATE club_season_statistics SET
  matches_played = club_stats['matches_played'],
  wins = club_stats['wins'],
  draws = club_stats['draws'],
  losses = club_stats['losses'],
  goals_scored = club_stats['goals_scored'],
  goals_conceded = club_stats['goals_conceded'],
  total_clean_sheets = club_stats['clean_sheets'],
  avg_goals_per_match = club_stats['goals_scored'] / club_stats['matches_played'],
  avg_possession_percentage = AVG(possession_percentage from match_statistics),
  avg_total_shots = AVG(total_shots),
  avg_shots_on_target = AVG(shots_on_target),
  avg_xg_per_match = AVG(expected_goals),
  # ... all other averages
  updated_at = NOW()
WHERE club_id = :club_id;
```

---

### Step 12: Update Player Season Statistics

```python
# For each player in the club
for player_id in get_all_players(club_id):
    player_stats = aggregate_player_stats(player_id)

    UPDATE player_season_statistics SET
      matches_played = player_stats['matches_played'],
      goals = SUM(goals from player_match_statistics),
      assists = SUM(assists),
      expected_goals = SUM(expected_goals),
      shots_per_game = AVG(shots),
      shots_on_target_per_game = AVG(shots_on_target),
      total_passes = SUM(total_passes),
      passes_completed = SUM(completed_passes),
      total_dribbles = SUM(total_dribbles),
      successful_dribbles = SUM(successful_dribbles),
      tackles = SUM(tackles),
      tackle_success_rate = (SUM(successful_tackles) / SUM(tackles)) * 100,
      interceptions = SUM(interceptions),
      interception_success_rate = calculated_value,
      # Calculate attributes from stats
      attacking_rating = calculate_attacking_rating(player_stats),
      technique_rating = calculate_technique_rating(player_stats),
      tactical_rating = calculate_tactical_rating(player_stats),
      defending_rating = calculate_defending_rating(player_stats),
      creativity_rating = calculate_creativity_rating(player_stats),
      updated_at = NOW()
    WHERE player_id = :player_id;
```

**Player Attribute Calculation (Conceptual):**
```python
def calculate_attacking_rating(stats):
    # Weighted formula based on goals, shots, xG
    return min(100, (
      stats['goals'] * 10 +
      stats['assists'] * 8 +
      stats['expected_goals'] * 5 +
      stats['shots_on_target_per_game'] * 3
    ))

def calculate_technique_rating(stats):
    # Based on dribbles, pass completion
    return min(100, (
      stats['successful_dribbles'] / max(1, stats['total_dribbles']) * 50 +
      stats['passes_completed'] / max(1, stats['total_passes']) * 50
    ))

# Similar formulas for tactical, defending, creativity
```

---

## Response Format

**Success Response (201 Created):**
```json
{
  "success": true,
  "match_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": {
    "events_processed": 3247,
    "goals_extracted": 5,
    "players_created": 3,
    "players_updated": 8,
    "opponent_players_created": 11,
    "warnings": [
      "Event data has 3 goals for your team but score says 3 (match)",
      "Event data has 2 goals for opponent but score says 2 (match)"
    ]
  },
  "new_players": [
    {
      "player_name": "Marcus Silva",
      "jersey_number": 10,
      "invite_code": "MRC-1827"
    },
    {
      "player_name": "Alex Johnson",
      "jersey_number": 4,
      "invite_code": "AJO-5643"
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | Always true for successful uploads |
| `match_id` | UUID String | Created match ID |
| `summary` | Object | Processing summary |
| `summary.events_processed` | Integer | Number of events inserted |
| `summary.goals_extracted` | Integer | Number of goals extracted and created |
| `summary.players_created` | Integer | Number of new player records created |
| `summary.players_updated` | Integer | Number of existing players updated |
| `summary.opponent_players_created` | Integer | Number of opponent players created |
| `summary.warnings` | Array of Strings | Any validation warnings |
| `new_players` | Array | List of newly created players with invite codes |

---

## Error Responses

### Validation Error (400 Bad Request)

```json
{
  "detail": "Validation failed",
  "errors": {
    "match_date": "Invalid date format. Use YYYY-MM-DD",
    "statsbomb_events": "Events array is required and must not be empty",
    "home_score": "Must be a non-negative integer"
  }
}
```

### Club Name Mismatch (400 Bad Request)

```json
{
  "detail": "Cannot match your club to teams in event data. Your club name is 'Thunder United FC' but event data has teams: 'Thunder United', 'City Strikers'"
}
```

### Missing Starting XI (400 Bad Request)

```json
{
  "detail": "Event data must contain Starting XI events for both teams"
}
```

### Unauthorized (401)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Forbidden (403)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Payload Too Large (413)

```json
{
  "detail": "Request body exceeds maximum allowed size. Limit: 50MB"
}
```

### Internal Server Error (500)

```json
{
  "detail": "An error occurred while processing the match data. Please try again."
}
```

---

## Notes

### Transaction Safety

All database operations are wrapped in a single transaction:
```python
BEGIN TRANSACTION;
try:
    # All steps 1-12
    COMMIT;
except Exception as e:
    ROLLBACK;
    raise e
```

If any step fails, the entire match upload is rolled back - no partial data is saved.

---

### Performance Considerations

- Processing ~3000 events takes approximately 5-30 seconds
- Use bulk INSERT for events table (batch 500 events per query)
- Index queries on `statsbomb_player_id`, `statsbomb_team_id`
- Consider background job processing for very large event datasets

---

### Ignored Event Types

The following events are **not processed** in the current version:
- Substitution events (substitutes are ignored)
- Injury Stoppage
- Referee Ball-Drop
- Player On/Off (substitution-related)

---

### Data Validation

1. **Event Structure**: Validate that events have required fields (type, team, period, etc.)
2. **Team Matching**: Ensure 2 teams in Starting XI events
3. **Player Matching**: Validate StatsBomb player IDs are integers
4. **Goal Counts**: Compare extracted goals with final score (warn if mismatch)
5. **Jersey Numbers**: Ensure jersey numbers are positive integers (1-99 typical)

---

### Security Considerations

1. **Max Body Size**: Limit request body to 50 MB to prevent DoS
2. **Input Sanitization**: Sanitize all text fields (player names, team names)
3. **SQL Injection**: Use parameterized queries for all database operations
4. **Authorization**: Verify coach owns the club before allowing upload

---

## Summary

### Admin Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/coach/matches` | POST | Upload match data and process StatsBomb events |

**Total: 1 endpoint**

### Processing Steps

1. ✅ Authenticate coach and get club
2. ✅ Identify teams from JSON (match club name to StatsBomb team)
3. ✅ Create/get opponent club
4. ✅ Create match record
5. ✅ Insert all events (~3000 records)
6. ✅ Extract and create goals
7. ✅ Extract and create/update players (your club)
8. ✅ Extract and create opponent players
9. ✅ Calculate and store match statistics (both teams)
10. ✅ Calculate and store player match statistics
11. ✅ Update club season statistics
12. ✅ Update player season statistics

### Key Features

- **Automatic Player Creation**: Players detected in lineup automatically get incomplete records with invite codes
- **Duplicate Prevention**: Existing players are updated, not duplicated
- **Statistics Automation**: All stats calculated from raw event data
- **Goal Validation**: Warns if event goals don't match final score
- **Opponent Tracking**: Opponent players and team stats stored for display
- **Transaction Safety**: All-or-nothing processing (rollback on failure)
