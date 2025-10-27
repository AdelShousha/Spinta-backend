# Spinta Backend - Overview

## Document Purpose

This comprehensive guide documents the database schema and API specifications for the Spinta youth soccer analytics platform. This guide reflects all approved changes and design decisions.

## Project Overview

**Spinta** is a youth soccer analytics platform that enables coaches to manage their teams and provides players with access to their performance statistics, training plans, and match history.

### Key Features

1. **Coach Management**
   - Club and team management
   - Match upload and lineup management
   - Player performance tracking
   - Training plan creation and assignment
   - Season statistics dashboard

2. **Player Management**
   - Profile management with invite code signup
   - Personal performance statistics
   - Match history and detailed stats
   - Training plan access and progress tracking
   - Performance attributes visualization

3. **Data Integration**
   - StatsBomb data integration for match events
   - Computer vision processing for match lineups
   - Automated statistics calculation
   - Player attribute generation

## User Roles

### 1. Coach
- Creates and manages club
- Uploads matches and manages lineups
- Views team and player statistics
- Creates and assigns training plans
- Manages player invitations

### 2. Player
- Signs up using unique invite code
- Views personal statistics and match history
- Accesses assigned training plans
- Tracks training progress
- Updates profile information

## Core Workflows

### Coach Workflow
1. Sign up and create club
2. Upload match video
3. CV processes video and extracts lineup
4. Coach fills in match details and confirms lineup
5. System fetches StatsBomb data
6. Statistics are calculated and displayed
7. Coach can create training plans for players
8. Coach can view player progress

### Player Workflow
1. Receive invite code from coach
2. Enter invite code in app
3. View pre-filled profile data (name, jersey, position)
4. Complete signup with email, password, and personal info
5. Access dashboard with stats and training
6. Complete assigned training exercises
7. View match history and detailed statistics

## Document Structure

This guide is organized into the following sections:

1. **01_OVERVIEW.md** (this file) - Project overview and introduction
2. **02_DATABASE_SCHEMA.md** - Complete database schema and table definitions
3. **03_PLAYER_SIGNUP_FLOW.md** - Detailed player signup process
4. **04_AUTHENTICATION.md** - JWT authentication specification
5. **05_COACH_ENDPOINTS.md** - All coach-facing API endpoints
6. **06_PLAYER_ENDPOINTS.md** - All player-facing API endpoints

## Key Design Decisions

### 1. Invite Code Storage
**Decision**: Store invite codes directly in the `players` table instead of a separate `player_invite_codes` table.

**Rationale**:
- Simpler data model (one-to-one relationship)
- Fewer JOINs required
- No data redundancy
- Easier to maintain

### 2. Player Name Storage
**Decision**: Add `player_name` column to `players` table (separate from `users.full_name`).

**Rationale**:
- Player records must exist before user account creation
- Admin creates player records during match processing
- Player can update name during signup
- Name needed for lineup displays before player signs up

### 3. StatsBomb Player ID
**Decision**: Add `statsbomb_player_id` column to `players` table.

**Rationale**:
- Links player records to StatsBomb event data
- Provided by admin during match processing
- Enables accurate event-to-player mapping
- Essential for statistics calculation

### 4. Training Assignments
**Decision**: Remove `player_training_assignments` table; track completion directly in `training_exercises` table.

**Rationale**:
- Training plans are not reused multiple times
- No need to track assignment history
- Simpler data model
- Direct completion tracking per exercise

### 5. Screen-Based API Design
**Decision**: Create one endpoint per UI screen that returns ALL data needed for that screen.

**Rationale**:
- Reduces number of API calls
- Improves performance (fewer round trips)
- Easier frontend implementation
- Clear mapping between UI and API

### 6. JWT Authentication
**Decision**: Use JWT tokens for all authenticated requests.

**Rationale**:
- Stateless authentication
- Scalable architecture
- Standard industry practice
- Easy to implement on mobile apps

## Data Flow

### Match Processing Flow
```
1. Coach uploads match video
   ↓
2. CV Service processes video
   ↓
3. Lineup extracted (names, jersey numbers, positions)
   ↓
4. For each player:
   - Check if player exists (by statsbomb_player_id or jersey_number)
   - If not exists:
     * Create player record with player_name, jersey_number, position
     * Add statsbomb_player_id from CV data
     * Generate unique invite_code
     * Set is_linked = FALSE
   ↓
5. Coach reviews and confirms lineup
   ↓
6. Fetch StatsBomb data using statsbomb_player_id
   ↓
7. Process events and calculate statistics
   ↓
8. Update match_statistics, player_match_statistics,
   club_season_statistics, player_season_statistics
```

### Player Signup Flow
```
1. Player opens app
   ↓
2. Enters invite code
   ↓
3. App validates code (POST /api/auth/verify-invite)
   ↓
4. Server returns pre-filled data (name, jersey, position, club)
   ↓
5. Player sees pre-filled form
   ↓
6. Player fills email, password, birth date, height, photo
   ↓
7. Player can edit name if needed
   ↓
8. Player submits (POST /api/auth/register/player)
   ↓
9. Server:
   - Creates user account (user_id = player_id)
   - Updates player record (is_linked = TRUE, linked_at = NOW())
   - Updates player_name if changed
   - Fills in birth_date, height, profile_image_url
   - Generates JWT token
   ↓
10. Player logged in, redirected to dashboard
```

### Training Progress Flow
```
1. Coach creates training plan for player
   ↓
2. Plan status = 'pending'
   ↓
3. Player opens app, sees new training plan
   ↓
4. Player opens plan, sees exercises
   ↓
5. Player completes exercise, checks checkbox
   ↓
6. PUT /api/player/training/exercises/{exercise_id}/toggle
   ↓
7. Server updates:
   - training_exercises.completed = TRUE
   - training_exercises.completed_at = NOW()
   - If first exercise: training_plans.status = 'in_progress'
   - If all exercises done: training_plans.status = 'completed'
   ↓
8. Player sees updated progress percentage
```

## Statistics Calculation

### Match-Level Statistics
- Calculated after match is processed
- Stored in `match_statistics` table
- Both team and opponent stats stored
- Used for match detail screens

### Player Match Statistics
- Calculated per player per match
- Stored in `player_match_statistics` table
- Derived from StatsBomb events using `statsbomb_player_id`
- Used for player performance tracking

### Season Aggregates
- **Club Season Statistics**: Aggregated from all match_statistics for the club
- **Player Season Statistics**: Aggregated from all player_match_statistics for the player
- Recalculated after each new match is processed
- Used for dashboard displays

### Player Attributes
- Calculated from season statistics using proprietary formulas
- 5 categories: Attacking, Technique, Tactical, Defending, Creativity
- Ratings from 0-100
- Stored in `player_season_statistics` table
- Displayed as radar chart in player profiles

## API Design Principles

### 1. RESTful Conventions
- **GET**: Retrieve resources
- **POST**: Create new resources
- **PUT**: Update existing resources
- **DELETE**: Remove resources

### 2. Authentication
- All endpoints (except auth endpoints) require JWT token
- Token passed in `Authorization: Bearer <token>` header
- Token contains: `user_id`, `email`, `user_type` (coach/player)

### 3. Response Format
All endpoints return JSON:

**Success Response:**
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Error Response:**
```json
{
  "detail": "Human-readable error message"
}
```

### 4. Pagination
List endpoints support pagination via query parameters:
- `limit`: Number of items (default 20)
- `offset`: Number of items to skip (default 0)

Response includes `total_count` or similar field for total items.

### 5. Filtering
List endpoints support filtering via query parameters where applicable:
- Example: `/api/player/training?status=in_progress`

## Security Considerations

### 1. Authentication
- Passwords must be hashed (bcrypt recommended)
- JWT tokens expire after 24 hours
- Tokens signed with secret key

### 2. Authorization
- Coach can only access their own club's data
- Player can only access their own data
- Server validates ownership on every request

### 3. Invite Codes
- Generated using cryptographically secure random
- Unique constraint enforced at database level
- Can only be used once (validated by `is_linked` flag)

### 4. Data Validation
- All inputs must be validated
- Email format validation
- Password strength requirements (min 8 characters recommended)
- File upload size and type restrictions

## Error Codes

Standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request (validation error) |
| `401` | Unauthorized (invalid/missing token) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found |
| `409` | Conflict (duplicate email, used invite code) |
| `422` | Unprocessable Entity |
| `500` | Internal Server Error |

## Database Summary

### Core Tables (11 tables)
1. **users** - User accounts (coaches and players)
2. **coaches** - Coach-specific data
3. **clubs** - Club/team information
4. **players** - Player profiles and invite codes
5. **opponent_clubs** - Opponent team information
6. **matches** - Match records
7. **goals** - Goal events
8. **events** - StatsBomb event data
9. **training_plans** - Training plans assigned to players
10. **training_exercises** - Individual exercises within plans

### Statistics Tables (4 tables)
11. **match_statistics** - Team statistics per match
12. **player_match_statistics** - Player statistics per match
13. **club_season_statistics** - Aggregated club season stats
14. **player_season_statistics** - Aggregated player season stats

## API Summary

### Authentication Endpoints (4)
- `POST /api/auth/login`
- `POST /api/auth/register/coach`
- `POST /api/auth/verify-invite`
- `POST /api/auth/register/player`

### Coach Endpoints (8)
- `GET /api/coach/dashboard`
- `GET /api/coach/matches`
- `GET /api/coach/matches/{match_id}`
- `GET /api/coach/players`
- `GET /api/coach/players/{player_id}`
- `POST /api/coach/training-plans`
- `PUT /api/coach/training-plans/{plan_id}`
- `DELETE /api/coach/training-plans/{plan_id}`

### Player Endpoints (9)
- `GET /api/player/dashboard`
- `GET /api/player/matches`
- `GET /api/player/matches/{match_id}`
- `GET /api/player/training`
- `GET /api/player/training/{plan_id}`
- `PUT /api/player/training/exercises/{exercise_id}/toggle`
- `GET /api/player/profile`
- `PUT /api/player/profile`

**Total: 21 endpoints**

## Changelog

### Version 1.0 (Current)
- Initial comprehensive design
- Screen-based API architecture
- Invite code stored in players table
- StatsBomb player ID added to players table
- Training completion tracked in exercises table
- JWT authentication
- Player attributes calculation
