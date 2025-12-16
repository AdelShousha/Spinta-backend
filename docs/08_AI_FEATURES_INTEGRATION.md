# AI Features Integration Guide

**Last Updated**: December 12, 2025
**Status**: Not Started

---

## Overview

This document tracks the integration of two AI-powered features into the main Spinta backend:

1. **AI Training Plan Generation** - Generates personalized training plans using LLM + RAG
2. **AI Chatbot** - Natural language interface for querying club/player data

**Source Projects**:
- Training Plans: `ai-training-plans/`
- Chatbot: `ai-chatbot/`

**Goal**: Integrate both standalone FastAPI projects into this unified backend.

---

## Feature 1: AI Training Plan Generation

### Status: [ ] Not Started

### Source Project
`ai-training-plans/`

---

## Detailed Project Overview: AI Training Plans

### How It Works

The AI Training Plan Generator uses a **hybrid approach** combining:

1. **Deterministic Rule Engine** - Analyzes player attributes and statistics to identify weaknesses using numerical thresholds
2. **RAG (Retrieval-Augmented Generation)** - Retrieves relevant coaching knowledge from football textbooks and training manuals
3. **LLM Generation** - Uses Google Gemini via Pydantic AI to generate structured training plans validated by Pydantic models

**Complete Data Flow:**

```
User Request (Player Data)
    ↓
Deterministic Analysis (identify_weak_attributes, identify_weak_statistics)
    ↓
RAG Retrieval (ChromaDB query with embeddings)
    ↓
Agent Creation (Pydantic AI with system prompt + RAG context)
    ↓
LLM Generation (Google Gemini generates JSON)
    ↓
Pydantic Validation (TrainingPlanResponse)
    ↓
JSON Response
```

### Project File Structure

```
ai-training-plans/
├── main.py                           # FastAPI app entry point
├── rag_system.py                     # Standalone RAG (duplicate of app/services/rag_service.py)
├── requirements.txt                  # Dependencies
├── env.example                       # Environment variables template
├── test_endpoint.py                  # Automated testing script
├── check.py                          # Utility to list available Gemini models
├── knowledge_base.txt                # Text knowledge base (~6KB)
├── soccer_book/
│   └── Soccer_books.pdf              # Football coaching book (~13MB)
└── app/
    ├── config/
    │   └── settings.py               # Configuration and env loading
    ├── models/
    │   └── schemas.py                # Pydantic request/response models
    ├── api/
    │   └── routes.py                 # FastAPI routes with dependency injection
    └── services/
        ├── rag_service.py            # RAG implementation (ChromaDB + Sentence Transformers)
        ├── training_plan_service.py  # Core AI agent and training plan generation
        └── analysis_service.py       # Deterministic weakness identification functions
```

### File-by-File Breakdown

#### 1. **main.py**
- **Purpose**: FastAPI application entry point
- **What it does**:
  - Loads settings from environment
  - Initializes RAG system on startup (reads knowledge base, creates ChromaDB collection)
  - Sets up CORS middleware
  - Includes router from `app/api/routes.py`
  - Runs uvicorn server

#### 2. **app/config/settings.py**
- **Purpose**: Configuration management
- **What it does**:
  - Loads environment variables from `.env` using `python-dotenv`
  - Validates `GEMINI_API_KEY` (required)
  - Sets `GOOGLE_API_KEY` environment variable (required by Pydantic AI)
  - Defines model string format: `google-gla:models/gemini-2.5-flash-lite`
  - Configures RAG parameters (chunk_size=300, chunk_overlap=50, top_k=5)
  - Determines knowledge base path (priority: `soccer_book/` folder → `knowledge_base.txt` file)

#### 3. **app/models/schemas.py**
- **Purpose**: Pydantic data models for API request/response validation
- **Request Models**:
  - `TrainingPlanRequest`: Contains player_id, player_name, position, attributes (5 ratings 0-100), season_statistics
  - `Attributes`: attacking_rating, technique_rating, creativity_rating, tactical_rating, defending_rating
  - `SeasonStatistics`: Nested model with general, attacking, passing, dribbling, defending stats
- **Response Models**:
  - `TrainingPlanResponse`: player_name, jersey_number, plan_name, duration, exercises (3-10)
  - `Exercise`: exercise_name, description, sets, reps, duration_minutes (all strings)

#### 4. **app/services/analysis_service.py**
- **Purpose**: Deterministic weakness analysis
- **Functions**:
  - `identify_weak_attributes()`: Returns list of attributes with rating < 60
  - `identify_weak_statistics()`: Returns list of weak statistical areas based on thresholds:
    - Pass completion < 80%
    - Dribble success < 60%
    - Shot accuracy < 50%
    - Finishing rate (goals/xG) < 80%
    - Tackle success rate < 70%
    - Interception success rate < 70%

#### 5. **app/services/rag_service.py** (or `rag_system.py`)
- **Purpose**: RAG system using ChromaDB for vector storage and retrieval
- **What it does**:
  - **Initialization**:
    - Loads Sentence Transformers model (`all-MiniLM-L6-v2`) for embeddings
    - Creates ChromaDB persistent client at `chroma_db_<hash>/` folder
    - Checks if collection exists; if not, builds index from scratch
  - **Index Building** (`_build_index()`):
    - Loads all PDF/TXT/MD files from knowledge base path
    - Extracts text from PDFs using `pypdf`
    - Chunks text into 300-character segments with 50-character overlap
    - Generates embeddings for all chunks
    - Stores chunks, embeddings, and metadata in ChromaDB (batch size 100)
  - **Text Chunking** (`_chunk_text()`):
    - Splits by paragraphs (double newlines)
    - Further splits long paragraphs by sentences
    - Creates overlapping chunks to preserve context
  - **Retrieval** (`retrieve_for_training_plan()`):
    - Constructs multiple queries:
      - Position-based: "{position} training drills and exercises"
      - Attribute-based: "{attribute} improvement drills football training"
      - Statistics-based: "{stat} improvement football drills"
      - General: "football coaching methodology training plan structure"
    - Retrieves top-5 chunks per query
    - Deduplicates and combines all relevant chunks
    - Returns formatted text separated by `---`

#### 6. **app/services/training_plan_service.py**
- **Purpose**: Core AI training plan generation using Pydantic AI
- **What it does**:
  - **Agent Creation** (`_create_agent()`):
    - Builds comprehensive system prompt with:
      - RAG usage rules (use for drill descriptions, theory, NOT for numbers)
      - Deterministic rule engine instructions
      - Position-specific logic (Forward → finishing, Midfielder → passing, etc.)
      - Strict JSON output schema requirements
      - Retrieved knowledge base context
    - Creates Pydantic AI Agent with:
      - Model: `google-gla:models/gemini-2.5-flash-lite`
      - System prompt with embedded RAG context
      - Output type: `TrainingPlanResponse` (enforces schema validation)
  - **Training Plan Generation** (`generate_training_plan()`):
    1. Calls `identify_weak_attributes()` and `identify_weak_statistics()`
    2. Retrieves relevant knowledge using RAG system
    3. Creates agent with RAG context in system prompt
    4. Formats player data as YAML-style text
    5. Runs agent asynchronously with `await agent.run(player_data)`
    6. Returns validated `TrainingPlanResponse`

#### 7. **app/api/routes.py**
- **Purpose**: FastAPI route definitions with dependency injection
- **Endpoints**:
  - `POST /api/coach/training-plans/generate-ai`: Main endpoint for training plan generation
  - `GET /health`: Health check with RAG system status
  - `GET /`: Root endpoint with API metadata
- **Dependency Injection**:
  - `get_settings()`: Provides Settings instance (cached with @lru_cache)
  - `get_rag_system()`: Lazily initializes and returns singleton RAG system
  - `get_training_plan_service()`: Creates TrainingPlanService with settings and RAG system

#### 8. **test_endpoint.py**
- **Purpose**: Automated testing script
- **What it does**:
  - Sends POST request to `http://localhost:8000/api/coach/training-plans/generate-ai`
  - Uses sample payload (Marcus Silva - Forward with low tactical/defending ratings)
  - Validates response structure (required fields, exercise count 3-10)
  - Prints formatted JSON response
  - Handles connection errors, timeouts, and JSON decode errors

#### 9. **check.py**
- **Purpose**: Utility to list available Gemini models for your API key
- **What it does**:
  - Loads `GEMINI_API_KEY` or `GOOGLE_API_KEY` from environment
  - Calls `google.generativeai.list_models()`
  - Filters models supporting `generateContent` method
  - Prints available model names

#### 10. **knowledge_base.txt** and **soccer_book/**
- **Purpose**: Source material for RAG retrieval
- **Contents**:
  - `knowledge_base.txt`: Text file with football coaching knowledge (~6KB)
  - `soccer_book/Soccer_books.pdf`: Football coaching textbook (~13MB)
- **How it's used**:
  - On first run, extracted text is chunked and embedded
  - Stored in ChromaDB collection as vector embeddings
  - Retrieved based on semantic similarity to player weaknesses

### Complete Workflow Example

**Input Request:**
```json
{
  "player_id": "uuid-1234",
  "player_name": "Marcus Silva",
  "position": "Forward",
  "attributes": {
    "attacking_rating": 82,
    "technique_rating": 64,
    "creativity_rating": 85,
    "tactical_rating": 52,  // WEAK (< 60)
    "defending_rating": 28   // WEAK (< 60)
  },
  "season_statistics": {
    "general": { "matches_played": 22 },
    "attacking": {
      "goals": 12,
      "assists": 7,
      "expected_goals": 10.8,
      "shots_per_game": 4.2,
      "shots_on_target_per_game": 2.8
    },
    "passing": {
      "total_passes": 1144,
      "passes_completed": 995  // 87% pass completion (GOOD)
    },
    "dribbling": {
      "total_dribbles": 158,
      "successful_dribbles": 118  // 75% success rate (GOOD)
    },
    "defending": {
      "tackles": 45,
      "tackle_success_rate": 78.0,  // GOOD
      "interceptions": 32,
      "interception_success_rate": 81.0  // GOOD
    }
  }
}
```

**Processing Steps:**

1. **Weakness Identification (analysis_service.py)**:
   - Weak attributes: `[("Tactical", 52), ("Defending", 28)]`
   - Weak stats: `["Finishing"]` (12 goals vs 10.8 xG = 111%, but threshold is 80%)

2. **RAG Retrieval (rag_service.py)**:
   - Queries generated:
     - "Forward training drills and exercises"
     - "tactical improvement drills football training"
     - "defending improvement drills football training"
     - "Finishing improvement football drills"
     - "football coaching methodology training plan structure"
   - Retrieves top-5 chunks per query from ChromaDB
   - Combines unique chunks into context text

3. **Agent Generation (training_plan_service.py)**:
   - Creates Pydantic AI agent with system prompt containing:
     - RAG context (drill descriptions from knowledge base)
     - Deterministic rules (Forward needs finishing, Marcus has weak tactical/defending)
     - JSON schema requirements (3-5 exercises, specific field types)

4. **LLM Call (Google Gemini)**:
   - Receives player data + system prompt with RAG context
   - Generates structured JSON matching `TrainingPlanResponse` schema
   - Pydantic AI validates output against schema

5. **Response**:
```json
{
  "player_name": "Marcus Silva",
  "jersey_number": 10,
  "plan_name": "Tactical Awareness & Defensive Fundamentals for Forwards",
  "duration": "4 weeks",
  "exercises": [
    {
      "exercise_name": "Positional Awareness Drill",
      "description": "Small-sided game focusing on off-ball movement...",
      "sets": "3",
      "reps": "15",
      "duration_minutes": "20"
    },
    {
      "exercise_name": "Defensive Transition Practice",
      "description": "Counter-pressing drills after losing possession...",
      "sets": "4",
      "reps": "10",
      "duration_minutes": "15"
    },
    // ... more exercises
  ]
}
```

### How to Test the Standalone Project

#### Step 1: Setup Environment

```bash
# Navigate to project
cd ai-training-plans/

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configure Environment Variables

```bash
# Copy example env file
cp env.example .env

# Edit .env file and add your Gemini API key
# .env:
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=models/gemini-2.5-flash-lite
PORT=8000
```

#### Step 3: Check Available Models (Optional)

```bash
# Verify your API key and see available models
python check.py
```

Expected output:
```
models/gemini-2.0-flash-exp
models/gemini-2.5-flash-lite
models/gemini-1.5-pro
...
```

#### Step 4: Start the Server

```bash
python main.py
```

Expected output:
```
Loading embedding model: all-MiniLM-L6-v2...
Initializing RAG system with: /path/to/soccer_book
Loading existing ChromaDB collection with 437 documents
RAG system initialized successfully
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Note**: First run will take longer as it extracts PDF text, chunks it, and creates embeddings.

#### Step 5: Test the Endpoint

**Option A: Using the test script**
```bash
# In a new terminal (with server still running)
python test_endpoint.py
```

Expected output:
```
======================================================================
AI Training Plan Endpoint Test (Pydantic AI Version)
======================================================================

Endpoint URL: http://localhost:8000/api/coach/training-plans/generate-ai

Sending POST request with Marcus Silva payload...
----------------------------------------------------------------------

HTTP Status Code: 200
----------------------------------------------------------------------

Response JSON (formatted):
{
  "player_name": "Marcus Silva",
  "jersey_number": 10,
  "plan_name": "Tactical & Defensive Development Plan",
  "duration": "4 weeks",
  "exercises": [...]
}

----------------------------------------------------------------------
Response Validation:
----------------------------------------------------------------------
✅ All required fields present
✅ Number of exercises: 5
✅ Exercise count is within valid range (3-10)
✅ Exercise 1 structure is valid
   - Name: Warm-up: Dynamic Stretching
   - Duration: 10 minutes
...
```

**Option B: Using curl**
```bash
curl -X POST http://localhost:8000/api/coach/training-plans/generate-ai \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "uuid-string-1234",
    "player_name": "Marcus Silva",
    "position": "Forward",
    "attributes": {
      "attacking_rating": 82,
      "technique_rating": 64,
      "creativity_rating": 85,
      "tactical_rating": 52,
      "defending_rating": 28
    },
    "season_statistics": {
      "general": { "matches_played": 22 },
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
        "tackle_success_rate": 78.0,
        "interceptions": 32,
        "interception_success_rate": 81.0
      }
    }
  }'
```

**Option C: Using Swagger UI**
1. Open browser to `http://localhost:8000/docs`
2. Click on `POST /api/coach/training-plans/generate-ai`
3. Click "Try it out"
4. Paste the JSON payload
5. Click "Execute"
6. View response in the UI

#### Step 6: Verify Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Coach Dashboard API (Pydantic AI + RAG)",
  "version": "2.1.0",
  "model": "google-gla:models/gemini-2.5-flash-lite",
  "rag_system_initialized": true,
  "knowledge_base_loaded": true
}
```

### Common Issues and Troubleshooting

1. **ChromaDB Already Exists Warning**:
   - If you change the knowledge base, delete the `chroma_db_*` folder to force a rebuild
   - `rm -rf chroma_db_*`

2. **Gemini API Rate Limits**:
   - Switch to a different model: `GEMINI_MODEL=models/gemini-1.5-flash`
   - Check your quota at https://aistudio.google.com/

3. **pypdf ImportError**:
   - Install: `pip install pypdf==3.17.4`
   - PDFs will be skipped if pypdf is not installed

4. **Slow First Run**:
   - Normal - extracting 13MB PDF and creating embeddings takes time
   - Subsequent runs use cached ChromaDB collection

5. **Empty Knowledge Base**:
   - Ensure either `soccer_book/` folder or `knowledge_base.txt` exists
   - Check file permissions

---

### Endpoint
`POST /api/coach/training-plans/generate-ai`

### Architecture

| Component | Technology |
|-----------|------------|
| LLM Framework | Pydantic AI |
| LLM Provider | Google Gemini |
| RAG Vector Store | ChromaDB |
| Embeddings | Sentence Transformers |
| Weakness Analysis | Deterministic (rule-based) |

### Request/Response

**Request Body**:
```json
{
  "club_id": "uuid",
  "player_id": "uuid",
  "duration_weeks": 4,
  "sessions_per_week": 3,
  "focus_areas": ["shooting", "passing"]
}
```

**Response**: Generated training plan with weekly sessions targeting identified weaknesses.

### Key Files to Integrate

| Source File | Target Location |
|-------------|-----------------|
| `rag_system.py` | `app/services/rag_system.py` |
| `app/services/training_plan_service.py` | `app/services/ai_training_plan_service.py` |
| `app/services/analysis_service.py` | `app/services/weakness_analysis_service.py` |
| `app/models/schemas.py` | Merge into `app/schemas/coach.py` |
| `knowledge_base.txt` | `data/knowledge_base/knowledge_base.txt` |
| `soccer_book/` | `data/knowledge_base/soccer_book/` |

### New Dependencies

```
pydantic-ai==0.0.15
google-generativeai==0.8.3
chromadb==0.4.22
sentence-transformers==2.2.2
pypdf==3.17.4
```

### Environment Variables

```
GEMINI_API_KEY=your_gemini_api_key
```

### Integration Checklist

- [ ] Test standalone project (`ai-training-plans/`)
- [ ] Add dependencies to `requirements.txt`
- [ ] Add `GEMINI_API_KEY` to `app/config.py`
- [ ] Copy and adapt `rag_system.py`
- [ ] Copy and adapt `training_plan_service.py`
- [ ] Copy and adapt `analysis_service.py`
- [ ] Merge schemas into `app/schemas/coach.py`
- [ ] Copy knowledge base files to `data/knowledge_base/`
- [ ] Update route handler in `app/api/routes/coach.py`
- [ ] Test integrated endpoint

---

## Feature 2: AI Chatbot

### Status: [ ] Not Started

### Source Project
`ai-chatbot/`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/sessions` | Create new chat session |
| POST | `/api/chat/sessions/{session_id}/messages` | Send message to session |
| POST | `/api/chat/messages` | Send message (auto-create session) |
| GET | `/api/chat/sessions/{session_id}/messages` | Get conversation history |
| DELETE | `/api/chat/sessions/{session_id}` | Clear/delete session |

### Architecture

| Component | Technology |
|-----------|------------|
| LLM Provider | Google Gemini |
| Tool Calling | Gemini Function Calling |
| Database Tools | 19 specialized query tools |
| History Storage | PostgreSQL (conversation_messages table) |

### Database Tools (19 total)

The chatbot has access to these database query tools:

1. `get_club_info` - Club details
2. `get_club_players` - List club players
3. `get_player_info` - Player details
4. `get_player_season_stats` - Player season statistics
5. `get_club_matches` - List club matches
6. `get_match_details` - Match information
7. `get_player_match_stats` - Player stats for a match
8. `get_training_sessions` - List training sessions
9. `get_training_session_details` - Training session info
10. `get_training_plans` - List training plans
11. `get_training_plan_details` - Training plan info
12. `get_top_scorers` - Top scoring players
13. `get_top_assisters` - Top assist players
14. `get_player_comparison` - Compare two players
15. `get_team_performance_trend` - Performance over time
16. `get_upcoming_matches` - Future matches
17. `get_recent_results` - Recent match results
18. `get_player_form` - Player recent form
19. `search_players` - Search players by criteria

### Key Files to Integrate

| Source File | Target Location |
|-------------|-----------------|
| `app/services/llm_service.py` | `app/services/chatbot_llm_service.py` |
| `app/services/conversation_service.py` | `app/services/conversation_service.py` |
| `app/tools/*.py` (19 files) | `app/services/chatbot_tools/` |
| `app/api/chatbot.py` | `app/api/routes/chatbot.py` |
| `app/schemas/chat.py` | `app/schemas/chat.py` |

### New Database Table

```sql
CREATE TABLE conversation_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    club_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tool_calls JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (club_id) REFERENCES clubs(club_id)
);

CREATE INDEX idx_conversation_messages_session ON conversation_messages(session_id);
CREATE INDEX idx_conversation_messages_user ON conversation_messages(user_id);
```

### New Dependencies

```
aiofiles==23.2.1
httpx>=0.27.2
```

Note: `google-generativeai` is shared with training plans feature.

### Environment Variables

```
GEMINI_API_KEY=your_gemini_api_key  # Shared with training plans
```

### Integration Checklist

- [ ] Test standalone project (`ai-chatbot/`)
- [ ] Add dependencies to `requirements.txt`
- [ ] Create SQLAlchemy model in `app/models/conversation_message.py`
- [ ] Create Alembic migration for `conversation_messages` table
- [ ] Copy and adapt `llm_service.py`
- [ ] Copy and adapt `conversation_service.py`
- [ ] Copy and adapt all 19 tool files to `app/services/chatbot_tools/`
- [ ] Adapt tools to use existing SQLAlchemy models
- [ ] Create `app/schemas/chat.py`
- [ ] Create `app/api/routes/chatbot.py`
- [ ] Register chatbot router in `app/main.py`
- [ ] Test all 5 integrated endpoints

---

## Integration Workflow

### Phase 1: AI Training Plans

1. **Explore & Test Standalone**
   ```bash
   cd ai-training-plans/
   # Review implementation
   # Start and test endpoint
   ```

2. **Setup Dependencies**
   - Identify packages not in main `requirements.txt`
   - Add new packages
   - Install and verify

3. **Integrate Code**
   - Copy service files with adaptations
   - Update schemas
   - Copy knowledge base files
   - Update route handler

4. **Test Integration**
   - Start main project
   - Test `POST /api/coach/training-plans/generate-ai`
   - Verify response format

### Phase 2: AI Chatbot

1. **Explore & Test Standalone**
   ```bash
   cd ai-chatbot/
   # Review implementation
   # Start and test all 5 endpoints
   ```

2. **Setup Dependencies & Database**
   - Add remaining dependencies
   - Create Alembic migration
   - Run migration

3. **Integrate Code**
   - Copy and adapt service files
   - Copy and adapt tool files
   - Create schemas and routes
   - Register router

4. **Test Integration**
   - Start main project
   - Test all chatbot endpoints
   - Verify conversation persistence

---

## Combined Dependencies Summary

### New Packages to Add

```
# AI/LLM Dependencies
pydantic-ai==0.0.15
google-generativeai==0.8.3

# RAG System Dependencies
chromadb==0.4.22
sentence-transformers==2.2.2
pypdf==3.17.4

# Async Utilities
aiofiles==23.2.1
httpx>=0.27.2
```

### Environment Variables

Add to `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
```

Add to `app/config.py`:
```python
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
```

---

## Files Summary

### Files to Create

| File Path | Purpose |
|-----------|---------|
| `app/services/rag_system.py` | RAG system for training plans |
| `app/services/ai_training_plan_service.py` | Training plan generation service |
| `app/services/weakness_analysis_service.py` | Player weakness analysis |
| `app/services/chatbot_llm_service.py` | Chatbot LLM integration |
| `app/services/conversation_service.py` | Conversation history management |
| `app/services/chatbot_tools/` | Directory with 19 tool files |
| `app/api/routes/chatbot.py` | Chatbot API routes |
| `app/schemas/chat.py` | Chat request/response schemas |
| `app/models/conversation_message.py` | ConversationMessage model |
| `data/knowledge_base/` | Knowledge base files for RAG |
| `alembic/versions/xxx_add_conversation_messages.py` | Database migration |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `requirements.txt` | Add new dependencies |
| `app/config.py` | Add `GEMINI_API_KEY` |
| `app/api/routes/coach.py` | Update generate-ai endpoint |
| `app/main.py` | Register chatbot router |

---

## Progress Tracking

### Overall Status

| Feature | Status | Progress |
|---------|--------|----------|
| AI Training Plans | Not Started | 0/10 tasks |
| AI Chatbot | Not Started | 0/12 tasks |

### Completion Criteria

- [ ] AI Training Plan endpoint working in main project
- [ ] All 5 Chatbot endpoints working in main project
- [ ] All existing tests still passing
- [ ] New features tested and verified
