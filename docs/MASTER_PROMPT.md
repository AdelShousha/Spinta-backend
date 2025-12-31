# SPINTA - Master Project Specification

**Project Name:** SPINTA
**Slogan:** Boost Your Abilities (Potenzia le tue abilità)
**Version:** 1.0
**Last Updated:** December 2025
**Document Type:** Graduation Project Master Reference

---

## Table of Contents

1. [Introduction & Project Description](#chapter-1-introduction--project-description)
2. [Building Blocks: Tools & Technologies](#chapter-2-building-blocks-tools--technologies)
3. [Video Intelligence Engine](#chapter-3-video-intelligence-engine)
4. [SPINTA AI Assistant](#chapter-4-spinta-ai-assistant)
5. [AI-Powered Training Plans](#chapter-5-ai-powered-training-plans)
6. [Backend Architecture](#chapter-6-backend-architecture)
7. [Mobile Application](#chapter-7-mobile-application)
8. [UI/UX & Visual Identity](#chapter-8-uiux--visual-identity)
9. [Business Strategy](#chapter-9-business-strategy)

---

# Chapter 1: Introduction & Project Description

## 1.1 Vision Statement

SPINTA is an AI-driven football analytics platform designed to mainstream professional-grade performance analysis for youth football academies. By combining computer vision, natural language processing, and intelligent training recommendations, SPINTA empowers coaches and players with actionable insights that were previously accessible only to elite professional clubs.

## 1.2 Problem Statement

### The Challenge

Youth football academies in Egypt and the MENA region face significant barriers in accessing modern performance analytics:

1. **Cost Barrier**: Existing solutions like Wyscout, InStat, and Hudl are prohibitively expensive for small to medium-sized academies, with annual subscriptions often exceeding tens of thousands of dollars.

2. **Complexity**: Professional analytics platforms are designed for dedicated analysts, not coaches who manage multiple responsibilities. The learning curve and technical requirements create adoption barriers.

3. **Lack of Personalization**: Generic statistics don't translate into actionable training recommendations. Coaches must manually interpret data to create improvement plans.

4. **Limited Player Engagement**: Players have no direct access to their performance data, missing opportunities for self-improvement and motivation.

5. **Manual Video Analysis**: Coaches spend countless hours manually reviewing match footage to extract insights, a time-consuming and error-prone process.

### The Gap

There is no affordable, AI-powered, mobile-first football analytics solution tailored for the Egyptian and MENA youth academy market that:
- Automates video analysis
- Provides AI-generated training recommendations
- Offers conversational data access through natural language
- Engages both coaches and players through dedicated interfaces

## 1.3 Project Objectives

### Primary Objectives

1. **Automate Match Analysis**: Process match videos using computer vision to extract comprehensive event data (passes, shots, dribbles, tackles, etc.)

2. **Enable AI-Powered Insights**: Provide an intelligent assistant that coaches can query using natural language to understand player and team performance

3. **Generate Personalized Training Plans**: Use AI to create customized training plans based on individual player statistics and areas for improvement

4. **Empower Player Development**: Give players direct access to their statistics, training assignments, and progress tracking

5. **Deliver Affordable Analytics**: Create a solution priced appropriately for the Egyptian and MENA youth academy market

### Secondary Objectives

- Establish a scalable architecture for future feature expansion
- Create an intuitive mobile-first user experience
- Build a foundation for regional market expansion
- Develop reusable AI components for football analytics

## 1.4 Target Audience

### Primary: Youth Football Academies in Egypt

| Segment | Description | Size Estimate |
|---------|-------------|---------------|
| Small Academies | 1-3 teams, < 50 players | ~500+ academies |
| Medium Academies | 4-10 teams, 50-200 players | ~100+ academies |
| Large Academies | 10+ teams, 200+ players | ~20+ academies |

### Age Groups Supported

- U6 to U21 age categories
- Senior teams (18+)

### User Personas

**Coach Ahmed** - Youth Academy Coach
- Manages 2 teams (U14 and U16)
- Limited time for video analysis
- Needs quick insights before training sessions
- Wants to track player development over time

**Player Omar** - U16 Forward
- Wants to see his statistics 
- Motivated by progress tracking
- Needs clear training assignments from coach
- Uses mobile phone as primary device

## 1.5 Key Features Overview

### For Coaches

| Feature | Description |
|---------|-------------|
| Match Upload & Analysis | Upload match videos for automated event extraction |
| Player Management | View all players, invite codes, performance tracking |
| SPINTA AI Assistant | Natural language queries about players and matches |
| AI Training Plans | Generate personalized training plans with AI |
| Match Statistics | Detailed match-by-match statistics with comparisons |

### For Players

| Feature | Description |
|---------|-------------|
| Personal Dashboard | Season statistics and attribute ratings |
| Match History | Performance in each match with detailed stats |
| Training Plans | View assigned training plans and exercises |
| Progress Tracking | Mark exercises complete, track improvement |
| Profile Management | Personal information and settings |

## 1.6 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        SPINTA Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  Admin Dashboard │    │   Mobile App    │    │   Backend   │ │
│  │     (React)      │    │ (React Native)  │    │  (FastAPI)  │ │
│  └────────┬────────┘    └────────┬────────┘    └──────┬──────┘ │
│           │                      │                     │        │
│           └──────────────────────┼─────────────────────┘        │
│                                  │                              │
│                    ┌─────────────▼─────────────┐                │
│                    │     PostgreSQL (Neon)     │                │
│                    │   + pgvector extension    │                │
│                    └───────────────────────────┘                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    AI Services                           │   │
│  │  ┌──────────────────┐    ┌─────────────────────────┐    │   │
│  │  │ Video Processing │    │ Google Gemini 2.5 Flash │    │   │
│  │  │  (CV Pipeline)   │    │  - AI Assistant         │    │   │
│  │  │                  │    │  - Training Plans (RAG) │    │   │
│  │  └──────────────────┘    └─────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# Chapter 2: Building Blocks: Tools & Technologies

## 2.1 Technology Stack Overview

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend - Admin** | React | Admin dashboard for match upload |
| **Frontend - Mobile** | React Native | Cross-platform mobile app |
| **Backend** | FastAPI (Python) | REST API server |
| **Database** | PostgreSQL + pgvector | Data storage + vector embeddings |
| **Database Hosting** | Neon | Serverless PostgreSQL |
| **Backend Hosting** | Vercel | Serverless deployment |
| **AI/LLM** | Google Gemini 2.5 Flash | AI assistant + training plans |
| **AI Package** | google-genai | Lightweight Gemini client (~1MB) |
| **UI Design** | Figma | Interface design |
| **Computer Vision** | [TBD] | Match video analysis |

## 2.2 Backend Technologies

### FastAPI Framework

FastAPI was chosen for its:
- **Performance**: One of the fastest Python frameworks
- **Type Safety**: Built-in Pydantic validation
- **Documentation**: Automatic OpenAPI/Swagger docs
- **Async Support**: Native async/await (though we use sync for simplicity)
- **Modern Python**: Leverages Python 3.8+ features

```python
# Example FastAPI endpoint structure
@router.get("/api/coach/dashboard")
def get_dashboard(
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """Returns all data needed for coach dashboard screen."""
    ...
```

### SQLAlchemy ORM

- **Version**: SQLAlchemy 2.0
- **Pattern**: Declarative models with relationships
- **Sessions**: Synchronous sessions for Vercel compatibility

### Pydantic

- **Purpose**: Request/response validation
- **Settings**: Environment variable management via `pydantic-settings`
- **Schemas**: Type-safe API contracts

## 2.3 Database Architecture

### PostgreSQL with Neon

**Why Neon?**
- Serverless PostgreSQL (scales to zero)
- pgvector extension pre-installed
- Generous free tier
- Automatic connection pooling
- Compatible with Vercel deployment

**Configuration:**
```python
engine = create_engine(
    database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Important for Neon
    pool_size=5,
    max_overflow=10
)
```

### pgvector Extension

Used for RAG (Retrieval-Augmented Generation) in training plan generation:
- **Embedding Model**: Google text-embedding-004 (768 dimensions)
- **Index Type**: IVFFlat for approximate nearest neighbor search
- **Table**: `knowledge_embeddings` stores pre-computed vectors

## 2.4 AI/ML Services

### Google Gemini Integration

**Package**: `google-genai` (NOT `google-generativeai`)
- Size: ~1MB vs 162MB
- Critical for Vercel's 250MB deployment limit

**Model**: `gemini-2.5-flash`
- Fast response times
- Function calling support
- Cost-effective for high-volume queries

**API Pattern**:
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        tools=tools,
        system_instruction=system_message,
    )
)
```

## 2.5 Frontend Technologies

### React (Admin Dashboard)

- **Purpose**: Match upload and processing interface
- **Features**:
  - Video upload with progress tracking
  - Match details form (opponent, date, scores, lineups)
  - Processing status visualization
  - StatsBomb JSON file upload

### React Native (Mobile App)

- **Platform**: iOS and Android from single codebase
- **Navigation**: Tab-based (Club, Players, Chatbot, Profile for Coach)
- **State Management**: [To be determined]
- **Status**: In development

## 2.6 Deployment Infrastructure

### Vercel

**Constraints**:
- 250MB deployment size limit
- Serverless functions (no persistent connections)
- 10-second timeout on free tier

**Optimizations**:
- Lightweight packages (google-genai vs google-generativeai)
- No local file storage (Neon database for all data)
- Efficient cold starts

### Environment Variables

```
DATABASE_URL=postgresql://...@neon.tech/...
SECRET_KEY=<jwt-secret>
GEMINI_API_KEY=<google-api-key>
CORS_ORIGINS=http://localhost:3000,https://app.spinta.com
```

## 2.7 External Data Format

### StatsBomb Open Data Format

Event data follows StatsBomb specification (v4.0.0):
- ~3000 events per match
- ~160,000 lines of JSON
- Event types: Pass, Shot, Dribble, Tackle, etc.
- Rich metadata: positions, outcomes, qualifiers

Reference: `docs/Open Data Events v4.0.0.pdf`

---

# Chapter 3: Video Intelligence Engine

> **Note**: This chapter contains placeholder content. Technical details for the Computer Vision pipeline will be added once available.

## 3.1 Overview

The Video Intelligence Engine is responsible for processing match videos and extracting structured event data that powers all analytics features.

## 3.2 Pipeline Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Match Video  │───▶│ Player       │───▶│ Event        │───▶│ StatsBomb    │
│ Input        │    │ Detection &  │    │ Recognition  │    │ JSON Output  │
│              │    │ Tracking     │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

## 3.3 Technology Stack

[To be documented]

- Player Detection Model: [TBD]
- Player Tracking: [TBD]
- Event Recognition: [TBD]
- Ball Detection: [TBD]

## 3.4 Output Format

The CV pipeline outputs data in StatsBomb event format:

```json
{
  "id": "8f8c3e0c-9a4a-4d2e-b5c3-1a2b3c4d5e6f",
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
    "id": 217,
    "name": "Barcelona"
  },
  "play_pattern": {
    "id": 1,
    "name": "Regular Play"
  },
  "team": {
    "id": 217,
    "name": "Barcelona"
  },
  "tactics": {
    "formation": 433,
    "lineup": [...]
  }
}
```

## 3.5 Event Types Extracted

| Event Type | Description |
|------------|-------------|
| Starting XI | Team lineups at match start |
| Pass | All pass attempts with success/failure |
| Shot | Shots with xG and outcome |
| Dribble | Dribble attempts |
| Tackle | Defensive tackles |
| Interception | Ball interceptions |
| Ball Recovery | Regaining possession |
| Foul | Fouls committed/won |
| Goal | Goals scored (subset of shots) |

## 3.6 Admin Dashboard Integration

The Admin Dashboard provides the interface for video processing:

1. **Match Details Input**
   - Opponent name
   - Match date
   - Our score / Opponent score
   - Home/Away team lineups

2. **Video Upload**
   - Supports common video formats
   - Progress indicator during upload
   - Processing status visualization

3. **Processing Flow** (Current Implementation)
   - Video upload triggers CV overlay (for demonstration)
   - StatsBomb JSON file uploaded separately
   - Backend processes JSON to extract all statistics

4. **Output**
   - Match record created
   - Events stored in database
   - Statistics calculated (match + player level)
   - Season aggregates updated

---

# Chapter 4: SPINTA AI Assistant

## 4.1 Overview

The SPINTA AI Assistant is a conversational interface that allows coaches to query their team and player data using natural language. Built on Google Gemini with function calling, it provides instant access to statistics without navigating through multiple screens.

**UI Label**: "AI Coach Assistant - Your tactical companion"

## 4.2 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SPINTA AI Assistant                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Message: "Who are the top scorers?"                       │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Google Gemini 2.5 Flash                     │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ System Prompt: Football analytics assistant     │    │   │
│  │  │ Tools: 12 database query functions              │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│         Function Call: get_top_scorers(limit=5)                │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Database Tools                          │   │
│  │  - Executes SQL query against PostgreSQL                │   │
│  │  - Returns structured data                               │   │
│  │  - Injected with club_id from JWT                       │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  Response: "Your top scorers this season are:                  │
│            1. Lionel Messi - 5 goals..."                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 4.3 Database Tools (12 Core Functions)

### Player Tools (6)

| Tool | Purpose | Parameters | Example Query |
|------|---------|------------|---------------|
| `find_player_by_name` | Search player by name (fuzzy) | `player_name` | "Find a player named Julian" |
| `get_player_season_stats` | Get player's season statistics | `player_name` | "Tell me about Messi's stats" |
| `get_top_scorers` | Get top goal scorers | `limit` (optional) | "Who are the top scorers?" |
| `get_top_assisters` | Get top assist providers | `limit` (optional) | "Who has the most assists?" |
| `compare_players` | Compare two players | `player1_name`, `player2_name` | "Compare Messi and Ronaldo" |
| `get_player_match_performance` | Player stats in specific match | `player_name`, `match_description` | "How did Messi play vs France?" |

### Match Tools (4)

| Tool | Purpose | Parameters | Example Query |
|------|---------|------------|---------------|
| `get_last_match` | Get most recent match | None | "When was our last match?" |
| `get_match_details` | Get match basic info | `match_description` | "Tell me about the France game" |
| `get_match_statistics` | Get detailed match stats | `match_description` | "Show match statistics" |
| `get_match_goals_timeline` | Get goals with scorers | `match_description` | "Who scored in the last match?" |

### Team Tools (2)

| Tool | Purpose | Parameters | Example Query |
|------|---------|------------|---------------|
| `get_club_season_stats` | Get team season statistics | None | "What's our season record?" |
| `get_squad_list` | List all players | `position_filter` (optional) | "Show me all midfielders" |

## 4.4 Function Calling Flow

```python
# Simplified function calling loop
while True:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conversation_history,
        config=GenerateContentConfig(tools=tools)
    )

    if response.candidates[0].content.parts[0].function_call:
        # Extract function call
        func_call = response.candidates[0].content.parts[0].function_call

        # Execute tool with database session and club_id
        result = execute_tool(func_call.name, func_call.args, db, club_id)

        # Add result to conversation
        conversation_history.append(function_response(result))
    else:
        # No more function calls, return final response
        return response.text
```

## 4.5 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/sessions` | Create new chat session |
| POST | `/api/chat/messages` | Send message (creates session if needed) |
| GET | `/api/chat/sessions/{id}/messages` | Get conversation history |
| DELETE | `/api/chat/sessions/{id}` | Clear session |

### Request Example

```bash
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Who are the top scorers?"}'
```

### Response Example

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Your top scorers this season are:\n\n1. **Lionel Messi** - 5 goals (1.25 per match)\n2. **Julian Alvarez** - 2 goals (0.67 per match)",
  "tool_calls_executed": ["get_top_scorers"],
  "timestamp": "2025-12-17T18:09:30.123456Z"
}
```

## 4.6 Conversation History

Messages are stored in `conversation_messages` table:

```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    club_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tool_calls JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);
```

## 4.7 Example Conversation Flows

### Flow 1: Player Deep Dive

```
User: Who are the top scorers?
Bot: [calls get_top_scorers] "Your top scorers this season are:
     1. Lionel Messi - 5 goals (1.25 per match)
     2. Julián Álvarez - 2 goals..."

User: Tell me more about Messi's season performance
Bot: [calls get_player_season_stats] "Messi has had an excellent season:
     - 5 goals and 3 assists in 4 matches
     - Expected goals: 4.2 (outperforming)
     - Pass completion: 89%..."

User: How did he perform in the last match?
Bot: [calls get_player_match_performance] "In the match against France (3-1 win):
     - 2 goals, 1 assist
     - 5 shots (3 on target)
     - 67 passes (87% completion)..."
```

### Flow 2: Match Analysis

```
User: How did we do in the last match?
Bot: [calls get_match_statistics] "You won 3-1 against France:
     - Possession: 58%
     - Expected goals: 2.8 vs 1.2
     - Shots on target: 8 vs 4..."

User: Who scored the goals?
Bot: [calls get_match_goals_timeline] "Goals timeline:
     - 23' - Lionel Messi (Our Team)
     - 37' - Kylian Mbappé (France)
     - 64' - Lionel Messi (Our Team)
     - 89' - Julián Álvarez (Our Team)"
```

---

# Chapter 5: AI-Powered Training Plans

## 5.1 Overview

SPINTA uses Retrieval-Augmented Generation (RAG) to create personalized training plans based on player statistics and a curated knowledge base of football training exercises.

## 5.2 RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               AI Training Plan Generation                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: Player statistics + weakness areas                      │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          Query Embedding (text-embedding-004)           │   │
│  │  "Forward player, needs shooting improvement"            │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              pgvector Similarity Search                  │   │
│  │  SELECT * FROM knowledge_embeddings                      │   │
│  │  ORDER BY embedding <=> query_embedding                  │   │
│  │  LIMIT 5                                                 │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│         Retrieved: Relevant training exercises                  │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Google Gemini 2.5 Flash                     │   │
│  │  Prompt: Player stats + Retrieved exercises              │   │
│  │  Output: Structured training plan                        │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  Output: {                                                      │
│    "plan_name": "Shooting Accuracy Program",                   │
│    "duration": "4 weeks",                                       │
│    "exercises": [...]                                           │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 5.3 Knowledge Base

### Structure

The knowledge base contains training exercises organized by:
- **Skill Category**: Shooting, Passing, Dribbling, Defending, etc.
- **Position Relevance**: Forward, Midfielder, Defender, Goalkeeper
- **Difficulty Level**: Beginner, Intermediate, Advanced
- **Equipment Required**: Cones, Balls, Goals, etc.

### Storage

```sql
CREATE TABLE knowledge_embeddings (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768)  -- text-embedding-004 dimensions
);

CREATE INDEX ON knowledge_embeddings
USING ivfflat (embedding vector_cosine_ops);
```

## 5.4 API Endpoint

### POST `/api/coach/training-plans/generate-ai`

**Request:**
```json
{
  "player_id": "uuid",
  "focus_areas": ["shooting", "finishing"],
  "duration": "4 weeks",
  "additional_context": "Player is recovering from minor injury"
}
```

**Response:**
```json
{
  "plan_name": "Shooting Accuracy Program",
  "duration": "4 weeks",
  "exercises": [
    {
      "exercise_name": "Target Practice",
      "description": "Shooting at specific zones in the goal from various distances",
      "sets": "3",
      "reps": "15",
      "duration_minutes": "20"
    },
    {
      "exercise_name": "One-Touch Finishing",
      "description": "Quick shots immediately after receiving pass",
      "sets": "4",
      "reps": "10",
      "duration_minutes": "15"
    }
  ],
  "coach_notes": "Focus on weak foot development"
}
```

## 5.5 Training Plan Data Model

### Training Plans Table

```sql
CREATE TABLE training_plans (
    plan_id UUID PRIMARY KEY,
    player_id UUID NOT NULL REFERENCES players(player_id),
    plan_name VARCHAR(255) NOT NULL,
    duration VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed
    coach_notes TEXT,
    created_by UUID REFERENCES coaches(coach_id),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Training Exercises Table

```sql
CREATE TABLE training_exercises (
    exercise_id UUID PRIMARY KEY,
    plan_id UUID NOT NULL REFERENCES training_plans(plan_id),
    exercise_name VARCHAR(255) NOT NULL,
    description TEXT,
    sets VARCHAR(20),
    reps VARCHAR(20),
    duration_minutes VARCHAR(20),
    exercise_order INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);
```

## 5.6 User Flow

### Coach Side

1. Navigate to player profile
2. Click "Create Training Plan Using AI"
3. Select focus areas (optional)
4. Review AI-generated plan
5. Edit exercises if needed
6. Assign to player

### Player Side

1. View assigned training plans
2. Open plan to see exercises
3. Mark exercises as complete
4. Track progress percentage
5. View coach notes

---

# Chapter 6: Backend Architecture

## 6.1 Project Structure

```
app/
├── api/
│   └── routes/
│       ├── auth.py          # Authentication endpoints
│       ├── coach.py         # Coach endpoints
│       ├── player.py        # Player endpoints
│       ├── chat.py          # AI Assistant endpoints
│       └── health.py        # Health check
├── core/
│   └── dependencies.py      # Auth dependencies (require_coach, require_player)
├── models/
│   ├── __init__.py          # All SQLAlchemy models
│   ├── user.py
│   ├── coach.py
│   ├── club.py
│   ├── player.py
│   ├── match.py
│   └── ...
├── schemas/
│   ├── auth.py              # Auth request/response schemas
│   ├── coach.py             # Coach schemas
│   ├── player.py            # Player schemas
│   └── chat.py              # Chat schemas
├── services/
│   ├── chatbot/
│   │   ├── __init__.py      # Tool exports
│   │   ├── player_tools.py  # 6 player query tools
│   │   ├── match_tools.py   # 4 match query tools
│   │   ├── team_tools.py    # 2 team query tools
│   │   ├── llm_service.py   # Gemini integration
│   │   └── conversation_service.py
│   └── pgvector_rag_service.py  # RAG for training plans
├── config.py                # Pydantic settings
├── database.py              # SQLAlchemy setup
└── main.py                  # FastAPI app
```

## 6.2 Database Schema Summary

### 15 Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | User accounts | user_id, email, password_hash, user_type |
| `coaches` | Coach profiles | coach_id, user_id, birth_date |
| `clubs` | Team/club info | club_id, coach_id, club_name, statsbomb_team_id |
| `players` | Player profiles | player_id, user_id, club_id, invite_code, is_linked |
| `opponent_clubs` | Opponent teams | opponent_club_id, opponent_name |
| `opponent_players` | Opponent lineups | opponent_player_id, opponent_club_id |
| `matches` | Match records | match_id, club_id, opponent_name, result |
| `match_lineups` | Starting XI | lineup_id, match_id, player_id |
| `goals` | Goal events | goal_id, match_id, scorer_name, minute |
| `events` | Raw StatsBomb data | event_id, match_id, event_data (JSONB) |
| `match_statistics` | Team match stats | statistics_id, match_id, team_type |
| `player_match_statistics` | Player match stats | player_match_stats_id, player_id, match_id |
| `club_season_statistics` | Team season stats | club_stats_id, club_id, wins, goals_scored |
| `player_season_statistics` | Player season stats | player_stats_id, player_id, goals, assists |
| `training_plans` | Training plans | plan_id, player_id, status |
| `training_exercises` | Exercises | exercise_id, plan_id, completed |
| `conversation_messages` | Chat history | id, session_id, role, content |

## 6.3 API Endpoints Summary

### Authentication (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login with email/password |
| POST | `/api/auth/register/coach` | Register new coach |
| POST | `/api/auth/verify-invite` | Validate player invite code |
| POST | `/api/auth/register/player` | Complete player registration |

### Coach Endpoints (11 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/coach/dashboard` | Club overview + season stats |
| GET | `/api/coach/matches` | List all matches |
| GET | `/api/coach/matches/{id}` | Match details + statistics |
| POST | `/api/coach/matches` | Upload match (admin) |
| GET | `/api/coach/players` | List team players |
| GET | `/api/coach/players/{id}` | Player profile + season stats |
| GET | `/api/coach/players/{id}/matches/{mid}` | Player match performance |
| GET | `/api/coach/profile` | Coach profile info |
| POST | `/api/coach/training-plans` | Create training plan |
| POST | `/api/coach/training-plans/generate-ai` | AI generate plan |
| GET | `/api/coach/training-plans/{id}` | Training plan details |

### Player Endpoints (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/player/dashboard` | Personal stats + attributes |
| GET | `/api/player/matches` | Match history |
| GET | `/api/player/matches/{id}` | Match performance |
| GET | `/api/player/training` | List training plans |
| GET | `/api/player/training/{id}` | Plan with exercises |
| PUT | `/api/player/training/exercises/{id}/toggle` | Mark complete |
| GET | `/api/player/profile` | Profile info |

### Chat Endpoints (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/sessions` | Create session |
| POST | `/api/chat/messages` | Send message |
| GET | `/api/chat/sessions/{id}/messages` | Get history |
| DELETE | `/api/chat/sessions/{id}` | Clear session |

**Total: 26+ endpoints**

## 6.4 Authentication Flow

### JWT Token Structure

```json
{
  "user_id": "uuid",
  "email": "coach@example.com",
  "user_type": "coach"
}
```

### Auth Dependencies

```python
def require_coach(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validates JWT and returns coach user with club relationship loaded."""
    payload = verify_token(token)
    user = db.query(User).filter(User.user_id == payload["user_id"]).first()
    if user.user_type != "coach":
        raise HTTPException(status_code=403, detail="Coach access required")
    return user

def require_player(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validates JWT and returns player user."""
    ...
```

## 6.5 Match Processing Pipeline

When a match is uploaded via admin panel:

```python
# Simplified match processing flow
def process_match(match_data, events_json, db):
    # 1. Create match record
    match = create_match(match_data, db)

    # 2. Insert all events (~3000)
    bulk_insert_events(events_json, match.match_id, db)

    # 3. Extract and create goals
    extract_goals(events_json, match.match_id, db)

    # 4. Process lineups (create players if needed)
    process_lineups(events_json, match, db)

    # 5. Calculate match statistics (both teams)
    calculate_match_stats(match.match_id, db)

    # 6. Calculate player match statistics
    calculate_player_match_stats(match.match_id, db)

    # 7. Update season aggregates
    update_club_season_stats(match.club_id, db)
    update_player_season_stats(match.club_id, db)

    return match
```

## 6.6 Error Handling

### Standard Error Response

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 400 | Validation error |
| 401 | Not authenticated |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 500 | Server error |

---

# Chapter 7: Mobile Application

## 7.1 Overview

The SPINTA mobile application is built with React Native, providing native iOS and Android experiences from a single codebase. The app serves two user types: Coaches and Players, each with dedicated interfaces.

**Status**: In Development

## 7.2 Navigation Structure

### Coach Navigation

```
Bottom Tab Navigator
├── Club (Home)
│   ├── Summary Tab
│   │   ├── Season Record
│   │   ├── Team Form
│   │   └── Recent Matches
│   └── Statistics Tab
│       ├── Season Summary
│       ├── Attacking Stats
│       ├── Passing Stats
│       └── Defending Stats
├── Players
│   └── Player List
│       └── Player Detail
│           ├── Summary Tab (Attributes radar, Season stats)
│           ├── Matches Tab (Match history)
│           └── Training Tab (Training plans)
├── Chatbot (AI Coach Assistant)
└── Profile
```

### Player Navigation

```
Bottom Tab Navigator
├── My Stats (Home)
│   ├── Attribute Overview (Radar chart)
│   └── Season Statistics
├── Matches
│   └── Match Detail (Personal performance)
├── Training
│   └── Training Plan Detail
│       └── Exercise List (with completion tracking)
└── Profile
```

## 7.3 Screen Descriptions

### Authentication Screens

| Screen | Description |
|--------|-------------|
| Login | Email + password form |
| Role Selection | Choose Coach or Player |
| Coach Registration (Step 1) | Personal info (name, email, password, DOB, gender) |
| Coach Registration (Step 2) | Club info (name, logo, country, age group, stadium) |
| Player Registration (Step 1) | Enter invite code |
| Player Registration (Step 2) | Complete profile (pre-filled + email, password, DOB, height, photo) |
| Welcome Screen | Confirmation with club/player info |

### Coach Screens

| Screen | Key Data |
|--------|----------|
| Club Dashboard | Season record (W/D/L), form, match list |
| Club Statistics | Detailed attacking/passing/defending stats |
| Match Detail | Goal scorers, statistics comparison, lineups |
| Players List | All players with status (Joined/Pending) |
| Player Profile | Attributes radar, season stats |
| Player Match Performance | Individual match statistics |
| Player Training | Training plans list + AI generate button |
| Create Training Plan | AI-generated exercises with edit capability |
| AI Assistant | Chat interface with suggestions |
| Profile | Coach info, club stats summary |

### Player Screens

| Screen | Key Data |
|--------|----------|
| My Stats | Attributes radar, season statistics |
| Match History | List of matches with results |
| Match Performance | Personal stats in specific match |
| Training Plans | List with status (Completed/In Progress) |
| Training Detail | Exercises with checkboxes, progress percentage |
| Profile | Personal info, season summary |

## 7.4 Key UI Components

### Attribute Radar Chart

Five attributes displayed as pentagon radar:
- **ATT** (Attacking): Goals, shots, xG
- **TEC** (Technique): Dribbles, ball control
- **TAC** (Tactical): Positioning, passing decisions
- **DEF** (Defending): Tackles, interceptions
- **CRE** (Creativity): Assists, key passes

### Team Form Indicator

Visual display of last 5 matches:
- **W** (Green) - Win
- **D** (Gray) - Draw
- **L** (Red) - Loss

### Match Statistics Bars

Side-by-side comparison bars showing:
- Ball Possession
- Expected Goals (xG)
- Total Shots
- Passes Completed
- Tackles
- etc.

## 7.5 API Integration

### Authentication Storage

```javascript
// After login/registration
await AsyncStorage.setItem('jwt_token', response.token);
await AsyncStorage.setItem('user_type', response.user.user_type);
```

### API Service Pattern

```javascript
const api = axios.create({
  baseURL: 'https://spinta-backend.vercel.app/api',
});

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## 7.6 Offline Considerations

- Cache dashboard data for offline viewing
- Queue training exercise completions for sync
- Display cached match history when offline
- Show clear offline indicators

---

# Chapter 8: UI/UX & Visual Identity

## 8.1 Brand Identity

### Brand Name
**SPINTA** - Italian word meaning "push" or "boost"

### Slogan
**"Boost Your Abilities"** (English)
**"Potenzia le tue abilità"** (Italian)

### Logo Concept

The SPINTA logo combines multiple symbolic elements:
1. **Football/Soccer Ball** - Core sport focus
2. **Boost/Speed Symbol** - Forward chevrons indicating acceleration
3. **Data/Analytics** - Pie chart reference for statistics
4. **Leaning Tower of Pisa** - The "I" in SPINTA references Italy

The logo uses a simplified, modern design suitable for mobile app icons.

## 8.2 Color Palette

| Color | Hex Code | Usage |
|-------|----------|-------|
| **Primary Red** | `#FF3000` | Primary buttons, accents, logo |
| **Black** | `#000000` | Text, icons, secondary elements |
| **White** | `#FFFFFF` | Backgrounds, text on dark |
| **Orange Gradient** | `#FFA500 → #FF3000` | Button gradients |
| **Success Green** | `#4CAF50` | Win indicators, completed items |
| **Warning Yellow** | `#FFC107` | Draw indicators, in-progress |
| **Error Red** | `#F44336` | Loss indicators, errors |

### Gradient Usage

Primary buttons use orange-to-red gradient:
```css
background: linear-gradient(90deg, #FFA500, #FF3000);
```

## 8.3 Typography

### Primary Font
**Franklin Gothic Heavy** - Used for headings, logo

### Logo Typography
**Franklin Gothic Heavy Italic** - The SPINTA wordmark

### Body Text
System fonts (San Francisco on iOS, Roboto on Android)

### Hierarchy

| Level | Usage | Style |
|-------|-------|-------|
| H1 | Screen titles | 24px Bold |
| H2 | Section headers | 20px Bold |
| H3 | Card titles | 18px SemiBold |
| Body | Content text | 16px Regular |
| Caption | Labels, hints | 14px Regular |
| Small | Timestamps | 12px Regular |

## 8.4 UI Components

### Buttons

**Primary Button**
- Orange-red gradient background
- White text
- Rounded corners (8px)
- Full width on mobile

**Secondary Button**
- White background
- Gray border
- Dark text

### Cards

- White background
- Light shadow
- 12px border radius
- 16px padding

### Navigation

**Bottom Tab Bar**
- 4 tabs for each user type
- Icons + labels
- Active state: Primary red
- Inactive state: Gray

### Statistics Display

**Stat Row**
- Label on left
- Value on right
- Optional progress bar

**Comparison Bar**
- Two-sided horizontal bar
- Our team color vs opponent color
- Values on each end

## 8.5 Screen Layout Patterns

### Dashboard Pattern
```
┌─────────────────────────┐
│ Header (Club/Player)    │
├─────────────────────────┤
│ Tab Selector            │
├─────────────────────────┤
│                         │
│ Stats Card              │
│                         │
├─────────────────────────┤
│                         │
│ List Items              │
│                         │
└─────────────────────────┘
│    Bottom Tab Bar       │
└─────────────────────────┘
```

### Detail Pattern
```
┌─────────────────────────┐
│ ← Back    Title         │
├─────────────────────────┤
│                         │
│ Hero Section            │
│ (Image/Chart)           │
│                         │
├─────────────────────────┤
│ Tab Selector            │
├─────────────────────────┤
│                         │
│ Content Sections        │
│                         │
└─────────────────────────┘
```

## 8.6 Figma Design Reference

Complete UI designs are available in: `docs/Spinta UI.pdf` (30 pages)

**Pages Include:**
1. Login Screen
2. Role Selection
3-4. Coach Registration (2 steps)
5. Coach Welcome
6-7. Club Dashboard (Summary + Statistics)
8-10. Match Detail (Summary, Statistics, Lineup)
11-18. Player Management (List, Profile tabs, Training)
19. AI Coach Assistant
20. Coach Profile
21-24. Player Registration Flow
25-30. Player App Screens

---

# Chapter 9: Business Strategy

## 9.1 Market Analysis

### Egyptian Youth Football Landscape

| Metric | Estimate |
|--------|----------|
| Registered youth players | 500,000+ |
| Youth academies | 600+ |
| Professional club academies | 50+ |
| Private academies | 500+ |
| Average players per academy | 50-200 |

### Market Pain Points

1. **Manual Analysis**: Coaches spend 5-10 hours/week on video review
2. **No Data Infrastructure**: Most academies track stats on paper/Excel
3. **Expensive Solutions**: Professional tools cost $10,000-50,000/year
4. **Limited Player Engagement**: Players don't see their own data
5. **Training Inconsistency**: No standardized training approach

## 9.2 Competitive Landscape

| Competitor | Target Market | Price Range | Key Limitation |
|------------|--------------|-------------|----------------|
| **Wyscout** | Professional clubs | $$$$ | Too expensive for youth |
| **InStat** | Pro/Semi-pro | $$$$ | Complex, requires analyst |
| **Hudl** | Pro to amateur | $$$ | Limited AI features |
| **Coach's Eye** | Individual coaches | $ | No team analytics |
| **SPINTA** | Youth academies | $$ | New entrant |

### SPINTA Competitive Advantages

1. **Price Point**: 80-90% cheaper than professional solutions
2. **AI-Powered**: Automated training recommendations
3. **Mobile-First**: Designed for coaches on the field
4. **Player App**: Unique engagement for youth players
5. **Arabic Support**: Localized for Egyptian market (future)

## 9.3 Target Customer Profile

### Ideal Customer

**Academy Profile:**
- 50-200 players
- 3-10 teams (different age groups)
- 2-5 coaches
- Plays in local/regional leagues
- Monthly budget: $200-500 for technology

**Coach Profile:**
- Age: 25-45
- Tech-savvy (uses smartphone daily)
- Limited time for administrative tasks
- Values player development
- Open to AI assistance

## 9.4 Pricing Strategy

### Recommended: Tiered SaaS Model

| Tier | Target | Monthly Price | Features |
|------|--------|--------------|----------|
| **Starter** | Small academies | $99/month | 1 team, 25 players, basic stats |
| **Pro** | Medium academies | $249/month | 5 teams, 100 players, AI features |
| **Enterprise** | Large academies | $499/month | Unlimited teams, priority support |

### Alternative Models Considered

1. **Per-Player Pricing**: $5/player/month
   - Pro: Scales with academy size
   - Con: May discourage adding all players

2. **Per-Match Pricing**: $20/match analyzed
   - Pro: Pay-as-you-go flexibility
   - Con: Unpredictable revenue

3. **One-Time License**: $2,000/year
   - Pro: Simple purchase decision
   - Con: Lower recurring revenue

### Freemium Consideration

**Free Tier** (Future):
- 1 team, 15 players
- Basic statistics only
- No AI features
- SPINTA branding on exports

## 9.5 Go-to-Market Strategy

### Phase 1: Pilot (Months 1-3)
- Partner with 5-10 academies in Cairo
- Free access in exchange for feedback
- Refine product based on usage

### Phase 2: Beta Launch (Months 4-6)
- Launch paid subscriptions
- Target 50 paying academies
- Build case studies and testimonials

### Phase 3: Scale (Months 7-12)
- Expand to Alexandria, Giza
- Partner with Egyptian FA youth programs
- Hire sales representatives

### Phase 4: Regional Expansion (Year 2+)
- Gulf countries (UAE, Saudi Arabia)
- North Africa (Morocco, Tunisia)
- Arabic language support

## 9.6 Revenue Projections

### Conservative Scenario

| Year | Academies | ARPU | Annual Revenue |
|------|-----------|------|----------------|
| Year 1 | 50 | $150 | $90,000 |
| Year 2 | 200 | $175 | $420,000 |
| Year 3 | 500 | $200 | $1,200,000 |

### Key Assumptions
- 20% month-over-month growth in Year 1
- 90% annual retention rate
- Average contract: Pro tier

## 9.7 Key Metrics to Track

| Metric | Target |
|--------|--------|
| Monthly Active Academies | Growing |
| Matches Analyzed per Academy | 2+/month |
| AI Assistant Queries | 10+/week/academy |
| Player App Engagement | 50%+ weekly active |
| Training Plan Completion | 70%+ |
| Net Promoter Score | 50+ |
| Churn Rate | <5% monthly |

## 9.8 Risk Factors

| Risk | Mitigation |
|------|------------|
| Low adoption | Start with free pilot, prove value |
| Competition from big players | Focus on price + localization |
| Technical reliability | Invest in testing, monitoring |
| CV accuracy concerns | Transparent about capabilities |
| Economic downturn | Flexible pricing options |

---

# Appendices

## Appendix A: Placeholder Sections

The following sections require additional information:

- [ ] **Academic Context**: University name, faculty, team members, graduation year
- [ ] **Computer Vision Details**: Technical stack, model architectures, accuracy metrics
- [ ] **React Native Implementation**: Specific libraries, state management, testing approach

## Appendix B: Reference Documents

| Document | Location | Content |
|----------|----------|---------|
| Backend Overview | `docs/01_OVERVIEW.md` | Project overview, design decisions |
| Database Schema | `docs/02_DATABASE_SCHEMA.md` | Complete table definitions |
| Player Signup | `docs/03_PLAYER_SIGNUP_FLOW.md` | Signup flow details |
| Authentication | `docs/04_AUTHENTICATION.md` | JWT specification |
| Coach Endpoints | `docs/05_COACH_ENDPOINTS.md` | Coach API reference |
| Player Endpoints | `docs/06_PLAYER_ENDPOINTS.md` | Player API reference |
| Admin Endpoints | `docs/07_ADMIN_ENDPOINTS.md` | Match upload API |
| AI Features | `docs/08_AI_FEATURES_INTEGRATION.md` | AI implementation details |
| Chat Endpoints | `docs/09_CHATBOT_ENDPOINTS.md` | Chat API reference |
| Admin Panel Specs | `docs/Admin Panel Specifications.md` | Admin dashboard requirements |
| UI Designs | `docs/Spinta UI.pdf` | Figma exports (30 pages) |
| StatsBomb Format | `docs/Open Data Events v4.0.0.pdf` | Event data specification |
| Visual Identity | `docs/vv-01.jpg`, `docs/vv-02.jpg` | Logo and color palette |

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **xG (Expected Goals)** | Statistical measure of shot quality |
| **StatsBomb** | Football data company; data format standard |
| **RAG** | Retrieval-Augmented Generation |
| **pgvector** | PostgreSQL extension for vector similarity |
| **JWT** | JSON Web Token for authentication |
| **Invite Code** | Unique code for player registration |
| **Function Calling** | LLM feature to execute code functions |

---

*This document serves as the master reference for the SPINTA graduation project. For detailed API specifications, refer to the individual documentation files in the `/docs` directory.*
