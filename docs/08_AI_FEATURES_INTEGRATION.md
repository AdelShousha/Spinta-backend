# AI Features Integration Guide

**Last Updated**: December 18, 2025
**Status**: AI Chatbot Complete (12 tools), AI Training Plans (PgVector RAG) Complete

---

## Overview

This document tracks the integration of two AI-powered features into the main Spinta backend:

1. **AI Training Plan Generation** - Generates personalized training plans using LLM + RAG (pgvector)
2. **AI Chatbot** - Natural language interface for querying club/player data with function calling

**Source Projects**:
- Training Plans: `ai-training-plans/`
- Chatbot: `ai-chatbot/`

**Goal**: Integrate both standalone FastAPI projects into this unified backend.

---

## Feature 1: AI Training Plan Generation

### Status: [x] Complete (PgVector RAG)

### Implementation Summary

The AI Training Plan Generation was integrated using PostgreSQL pgvector for RAG instead of ChromaDB. This approach:
- Eliminates heavyweight dependencies (ChromaDB, sentence-transformers)
- Uses pre-computed embeddings stored in PostgreSQL
- Generates query embeddings via Gemini API at runtime
- Keeps deployment size under Vercel's 250MB limit

### Architecture

| Component | Technology |
|-----------|------------|
| LLM Provider | Google Gemini (gemini-2.5-flash) |
| RAG Vector Store | PostgreSQL pgvector |
| Embeddings | Google text-embedding-004 (768 dimensions) |
| Package | google-genai (~1MB) |

### Endpoint

`POST /api/coach/training-plans/generate-ai`

### Key Files

| File | Purpose |
|------|---------|
| `app/services/pgvector_rag_service.py` | RAG service using pgvector for similarity search |
| `app/schemas/coach.py` | Request/response schemas for training plans |
| `app/api/routes/coach.py` | Route handler with JWT authentication |
| `knowledge_embeddings` table | Stores pre-computed embeddings in PostgreSQL |

---

## Feature 2: AI Chatbot

### Status: [x] Complete

### Integration Date: December 17, 2025

### Implementation Summary

The AI Chatbot from `ai-chatbot/` was integrated into the main backend with:
- **JWT Authentication** via `require_coach` dependency (not user_id/club_id in request body)
- **Sync SQLAlchemy** operations (main backend uses sync, not async)
- **Lightweight google-genai package** (~1MB instead of 162MB google-generativeai)
- **12 Core Database Tools** with Gemini function calling

---

## AI Chatbot - Complete Implementation Details

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/sessions` | Create new chat session |
| POST | `/api/chat/messages` | Send message (auto-creates session if not provided) |
| GET | `/api/chat/sessions/{session_id}/messages` | Get conversation history |
| DELETE | `/api/chat/sessions/{session_id}` | Clear/delete session |

### Architecture

| Component | Technology |
|-----------|------------|
| LLM Provider | Google Gemini 2.5 Flash |
| LLM Package | google-genai (~1MB) |
| Tool Calling | Gemini Function Calling |
| Database Tools | 12 specialized sync query tools |
| History Storage | PostgreSQL (conversation_messages table) |
| Authentication | JWT via require_coach dependency |

### Database Tools (12 Core Tools)

The chatbot has access to these database query tools:

**Player Tools (6):**
1. `find_player_by_name` - Search for a player by name (fuzzy matching)
2. `get_player_season_stats` - Get season statistics for a specific player
3. `get_top_scorers` - Get top goal scorers in the team
4. `get_top_assisters` - Get top assist providers in the team
5. `compare_players` - Compare statistics between two players
6. `get_player_match_performance` - Get a player's performance in a specific match

**Match Tools (4):**
7. `get_last_match` - Get the most recent match
8. `get_match_details` - Get basic match information (date, opponent, score)
9. `get_match_statistics` - Get detailed match statistics for both teams
10. `get_match_goals_timeline` - Get timeline of goals with scorers

**Team Tools (2):**
11. `get_club_season_stats` - Get overall season statistics for the team
12. `get_squad_list` - Get list of all players with positions and jersey numbers

---

### Files Created

#### 1. `app/models/conversation_message.py`

SQLAlchemy model for storing chat messages.

```python
class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    session_id = Column(GUID, nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.user_id"), nullable=False, index=True)
    club_id = Column(GUID, ForeignKey("clubs.club_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    tool_calls = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
```

**Note**: The `conversation_messages` table already exists in the Neon database, so no migration was needed.

#### 2. `app/schemas/chat.py`

Pydantic models for API request/response validation.

```python
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[UUID] = None  # Auto-creates if not provided

class ChatMessageResponse(BaseModel):
    session_id: UUID
    message: str
    tool_calls_executed: List[str] = []
    timestamp: datetime

class ChatSessionResponse(BaseModel):
    session_id: UUID
    created_at: datetime

class ConversationHistoryItem(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime

class ConversationHistoryResponse(BaseModel):
    session_id: UUID
    messages: List[ConversationHistoryItem]
    total_messages: int

class ClearSessionResponse(BaseModel):
    message: str
    deleted_messages: int
```

**Key Design Decision**: `user_id` and `club_id` are NOT in `ChatMessageRequest` because they come from the authenticated coach via JWT token.

#### 3. `app/services/chatbot/__init__.py`

Package init that exports all 12 core tools.

```python
from app.services.chatbot.player_tools import (
    find_player_by_name,
    get_player_season_stats,
    get_top_scorers,
    get_top_assisters,
    compare_players,
    get_player_match_performance,
)
from app.services.chatbot.match_tools import (
    get_last_match,
    get_match_details,
    get_match_statistics,
    get_match_goals_timeline,
)
from app.services.chatbot.team_tools import (
    get_club_season_stats,
    get_squad_list,
)

__all__ = [
    "find_player_by_name", "get_player_season_stats", "get_top_scorers",
    "get_top_assisters", "compare_players", "get_player_match_performance",
    "get_last_match", "get_match_details", "get_match_statistics",
    "get_match_goals_timeline", "get_club_season_stats", "get_squad_list",
]
```

#### 4. `app/services/chatbot/player_tools.py`

Six synchronous player query tools.

```python
def find_player_by_name(db: Session, player_name: str, club_id: UUID) -> Optional[Dict[str, Any]]:
    """Find a player by name (supports fuzzy matching)."""

def get_player_season_stats(db: Session, player_name: str, club_id: UUID) -> Optional[Dict[str, Any]]:
    """Get season statistics for a specific player."""

def get_top_scorers(db: Session, club_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
    """Get top goal scorers for a club."""

def get_top_assisters(db: Session, club_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
    """Get top assist providers for a club."""

def compare_players(db: Session, player1_name: str, player2_name: str, club_id: UUID) -> Dict[str, Any]:
    """Compare statistics between two players."""

def get_player_match_performance(db: Session, player_name: str, club_id: UUID,
                                  match_description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get detailed statistics for a player in a specific match."""
```

#### 5. `app/services/chatbot/match_tools.py`

Four synchronous match query tools.

```python
def get_last_match(db: Session, club_id: UUID) -> Optional[Dict[str, Any]]:
    """Get the most recent match for a club."""

def get_match_details(db: Session, club_id: UUID, match_description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get basic information about a match."""

def get_match_statistics(db: Session, club_id: UUID, match_description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get statistics for a match (both teams)."""

def get_match_goals_timeline(db: Session, club_id: UUID, match_description: Optional[str] = None) -> Dict[str, Any]:
    """Get timeline of goals scored in a match with scorers."""
```

#### 6. `app/services/chatbot/team_tools.py`

Two synchronous team query tools.

```python
def get_club_season_stats(db: Session, club_id: UUID) -> Optional[Dict[str, Any]]:
    """Get season statistics for a club."""

def get_squad_list(db: Session, club_id: UUID, position_filter: Optional[str] = None) -> Dict[str, Any]:
    """Get list of all players in the squad."""
```

#### 7. `app/services/chatbot/conversation_service.py`

Service for managing conversation history in PostgreSQL.

```python
class ConversationService:
    @staticmethod
    def create_session(db: Session, user_id: UUID, club_id: UUID) -> UUID:
        """Create a new chat session."""

    @staticmethod
    def add_message(db: Session, session_id: UUID, user_id: UUID, club_id: UUID,
                    role: str, content: str, tool_calls: Optional[List] = None) -> ConversationMessage:
        """Add a message to the conversation history."""

    @staticmethod
    def get_conversation_history(db: Session, session_id: UUID, user_id: UUID,
                                  club_id: UUID, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""

    @staticmethod
    def clear_session(db: Session, session_id: UUID, user_id: UUID, club_id: UUID) -> int:
        """Clear all messages in a session."""

    @staticmethod
    def session_exists(db: Session, session_id: UUID, user_id: UUID, club_id: UUID) -> bool:
        """Check if a session exists and belongs to the user."""
```

#### 8. `app/services/chatbot/llm_service.py`

LLM service with Gemini function calling using the lightweight `google-genai` package.

```python
from google import genai
from google.genai import types

class LLMService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-2.5-flash"
        self.tools = self._build_tools()

    def _build_tools(self) -> List[types.Tool]:
        """Build function declarations for Gemini."""
        # Returns 12 function declarations with parameter schemas

    def _execute_tool(self, tool_name: str, args: Dict, db: Session, club_id: UUID) -> Any:
        """Execute a tool function with database and club_id context."""

    def chat(self, user_message: str, conversation_history: List, db: Session, club_id: UUID) -> Dict:
        """Process a chat message with Gemini LLM and execute function calls."""
        # Handles the function calling loop (max 10 iterations)
        # Returns {"message": str, "tool_calls_executed": List[str], "tool_results": List}
```

**Key Technical Details**:
- Uses `google-genai` package (NOT `google-generativeai`)
- Implements iterative function calling loop
- Injects `db` and `club_id` into all tool calls
- System prompt defines assistant behavior

#### 9. `app/api/routes/chat.py`

REST endpoints with JWT authentication via `require_coach`.

```python
from app.core.dependencies import require_coach

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(coach: User = Depends(require_coach), db: Session = Depends(get_db)):
    """Create a new chat session for the authenticated coach."""

@router.post("/messages", response_model=ChatMessageResponse)
def send_message(request: ChatMessageRequest, coach: User = Depends(require_coach), db: Session = Depends(get_db)):
    """Send a message to the AI chatbot."""

@router.get("/sessions/{session_id}/messages", response_model=ConversationHistoryResponse)
def get_conversation_history(session_id: UUID, coach: User = Depends(require_coach), db: Session = Depends(get_db)):
    """Get conversation history for a specific session."""

@router.delete("/sessions/{session_id}", response_model=ClearSessionResponse)
def clear_chat_session(session_id: UUID, coach: User = Depends(require_coach), db: Session = Depends(get_db)):
    """Clear all messages in a chat session."""
```

**Authentication Flow**:
1. Coach authenticates via JWT token in Authorization header
2. `require_coach` dependency validates token and returns User object
3. `user_id` extracted from `coach.user_id`
4. `club_id` extracted from `coach.coach.club.club_id`

---

### Files Modified

#### 1. `app/models/__init__.py`

Added ConversationMessage export:

```python
from app.models.conversation_message import ConversationMessage

__all__ = [
    # ... existing exports ...
    "ConversationMessage",
]
```

#### 2. `app/main.py`

Registered chat router:

```python
from app.api.routes import health, auth, coach, player, chat

# ... existing code ...

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
```

---

### How to Use the AI Chatbot

#### Prerequisites

1. **GEMINI_API_KEY** must be set in your `.env` file
2. Coach must be authenticated with a valid JWT token
3. Coach must have an associated club

#### Step 1: Authenticate

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "coach@example.com", "password": "yourpassword"}'

# Response:
# {"access_token": "eyJ...", "token_type": "bearer"}
```

#### Step 2: Send a Chat Message

```bash
# Send message (auto-creates session)
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Who are the top scorers in my team?"}'
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Here are the top scorers in your team:\n\n1. **Lionel Messi**: 5 goals in 4 matches (1.25 goals per match)\n2. **Julián Álvarez**: 2 goals in 3 matches (0.67 goals per match)\n...",
  "tool_calls_executed": ["get_top_scorers"],
  "timestamp": "2025-12-17T18:09:30.123456Z"
}
```

#### Step 3: Continue Conversation (Optional)

```bash
# Use session_id to continue conversation
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How did we perform in the last match?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

#### Step 4: Get Conversation History

```bash
curl -X GET http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "system",
      "content": "You are an AI assistant for Spinta Stats...",
      "tool_calls": null,
      "timestamp": "2025-12-17T18:09:00.000000Z"
    },
    {
      "role": "user",
      "content": "Who are the top scorers in my team?",
      "tool_calls": null,
      "timestamp": "2025-12-17T18:09:15.000000Z"
    },
    {
      "role": "assistant",
      "content": "Here are the top scorers...",
      "tool_calls": [{"tool_name": "get_top_scorers", "arguments": {}, "result": [...]}],
      "timestamp": "2025-12-17T18:09:30.000000Z"
    }
  ],
  "total_messages": 3
}
```

#### Step 5: Clear Session

```bash
curl -X DELETE http://localhost:8000/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### Detailed Tool Reference

Each tool can be triggered by natural language queries. Here's a complete reference:

#### Player Tools

| Tool | Trigger Questions | Parameters | Response Fields |
|------|-------------------|------------|-----------------|
| `find_player_by_name` | "Find a player named Julian", "Search for Messi" | `player_name` (required) | player_id, name, position, jersey_number |
| `get_player_season_stats` | "Tell me about Messi's stats", "How is Julian performing this season?" | `player_name` (required) | player_name, position, goals, assists, expected_goals, shots_per_game, passes, tackles, interceptions, attribute ratings |
| `get_top_scorers` | "Who are the top scorers?", "Who scored the most goals?" | `limit` (optional, default: 5) | rank, player_name, position, goals, assists, matches_played, goals_per_match |
| `get_top_assisters` | "Who has the most assists?", "Best assist providers" | `limit` (optional, default: 5) | player_name, position, assists, goals, matches_played, assists_per_match |
| `compare_players` | "Compare Messi and Di Maria", "Messi vs Neymar" | `player1_name`, `player2_name` (both required) | player1 stats, player2 stats, differences (goals, assists, tackles, interceptions) |
| `get_player_match_performance` | "How did Messi play in the last match?", "Julian's performance against France" | `player_name` (required), `match_description` (optional) | match_date, opponent, score, result, goals, assists, shots, passes, dribbles, tackles, interceptions |

#### Match Tools

| Tool | Trigger Questions | Parameters | Response Fields |
|------|-------------------|------------|-----------------|
| `get_last_match` | "When was our last match?", "Last game result" | None | match_id, date, opponent, score, result |
| `get_match_details` | "Tell me about the match vs France", "What happened against Spain?" | `match_description` (optional) | match_id, date, opponent, score, result |
| `get_match_statistics` | "Show me the match statistics", "How did we perform against France?" | `match_description` (optional) | match_date, opponent, score, result, our_team (possession, xG, shots, passes, tackles), opponent_team stats |
| `get_match_goals_timeline` | "Who scored in the last match?", "Show me the goals against France" | `match_description` (optional) | match_date, opponent, final_score, goals (minute, scorer, team), total_goals |

#### Team Tools

| Tool | Trigger Questions | Parameters | Response Fields |
|------|-------------------|------------|-----------------|
| `get_club_season_stats` | "What's our season record?", "How many wins do we have?" | None | club_name, matches_played, wins, draws, losses, goals_scored, goals_conceded, goal_difference, averages |
| `get_squad_list` | "Show me the squad", "Who plays as midfielder?", "List all defenders" | `position_filter` (optional) | total_players, players grouped by position (name, jersey_number) |

---

### Example Response Data

**Example: `get_top_scorers` Response**
```json
{
  "tool_name": "get_top_scorers",
  "arguments": {"limit": 3},
  "result": [
    {"rank": 1, "player_name": "Lionel Messi", "position": "Forward", "goals": 5, "assists": 3, "matches_played": 4, "goals_per_match": 1.25},
    {"rank": 2, "player_name": "Julián Álvarez", "position": "Forward", "goals": 2, "assists": 1, "matches_played": 3, "goals_per_match": 0.67},
    {"rank": 3, "player_name": "Ángel Di María", "position": "Midfielder", "goals": 2, "assists": 4, "matches_played": 4, "goals_per_match": 0.5}
  ]
}
```

**Example: `get_player_match_performance` Response**
```json
{
  "tool_name": "get_player_match_performance",
  "arguments": {"player_name": "Messi", "match_description": "last match"},
  "result": {
    "player_name": "Lionel Messi",
    "match_date": "2024-12-14",
    "opponent": "France",
    "match_score": "3-1",
    "result": "Win",
    "goals": 2,
    "assists": 1,
    "expected_goals": 1.45,
    "shots": 5,
    "shots_on_target": 3,
    "total_passes": 67,
    "completed_passes": 58,
    "tackles": 1,
    "interceptions": 2
  }
}
```

**Example: `get_match_goals_timeline` Response**
```json
{
  "tool_name": "get_match_goals_timeline",
  "arguments": {},
  "result": {
    "match_date": "2024-12-14",
    "opponent": "France",
    "final_score": "3-1",
    "goals": [
      {"minute": 23, "second": 45, "scorer": "Lionel Messi", "is_our_goal": true, "team": "Our Team"},
      {"minute": 37, "second": 12, "scorer": "Kylian Mbappé", "is_our_goal": false, "team": "France"},
      {"minute": 64, "second": 30, "scorer": "Lionel Messi", "is_our_goal": true, "team": "Our Team"},
      {"minute": 89, "second": 55, "scorer": "Julián Álvarez", "is_our_goal": true, "team": "Our Team"}
    ],
    "total_goals": 4
  }
}
```

---

### Complex Multi-Message Test Flows

Use these conversation flows to test the chatbot's ability to handle multi-turn conversations and multiple tool calls.

#### Flow 1: Player Deep Dive

Test the chatbot's ability to explore a player's performance across different contexts.

```
User: Who are the top scorers?
Bot: [calls get_top_scorers] "Your top scorers this season are:
     1. Lionel Messi - 5 goals (1.25 per match)
     2. Julián Álvarez - 2 goals (0.67 per match)..."

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

#### Flow 2: Match Analysis Deep Dive

Test the chatbot's ability to provide comprehensive match analysis.

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

User: Compare Messi and Álvarez from that match
Bot: [calls compare_players] "Comparing the two scorers:
     Messi: 5 goals, 3 assists this season
     Álvarez: 2 goals, 1 assist this season
     Messi leads in goals (+3) and assists (+2)..."
```

#### Flow 3: Team Overview and Squad Management

Test the chatbot's ability to provide team-level insights.

```
User: What's our season record?
Bot: [calls get_club_season_stats] "Your season performance:
     - 4 matches played
     - 3 wins, 0 draws, 1 loss
     - Goals: 12 scored, 5 conceded (+7 GD)
     - Average goals per match: 3.0"

User: Show me all the midfielders
Bot: [calls get_squad_list with position_filter="midfielder"] "Your midfielders:
     - #10 Ángel Di María
     - #7 Rodrigo De Paul
     - #5 Leandro Paredes
     - #18 Guido Rodríguez"

User: How is Di Maria performing?
Bot: [calls get_player_season_stats] "Di María's season stats:
     - 2 goals, 4 assists in 4 matches
     - Key playmaker with 85% pass accuracy
     - Strong creativity rating: 88/100..."
```

#### Flow 4: Cross-Match Player Tracking

Test the chatbot's ability to track player performance contextually.

```
User: Find a player named Julian
Bot: [calls find_player_by_name] "Found: Julián Álvarez
     - Position: Forward
     - Jersey Number: 9"

User: How many goals has he scored this season?
Bot: [calls get_player_season_stats] "Julián Álvarez this season:
     - 2 goals and 1 assist
     - Expected goals: 1.8
     - Plays as the #9 striker..."

User: Did he score in the last match?
Bot: [calls get_match_goals_timeline] "Yes! Julián Álvarez scored in the 89th minute
     in your 3-1 win against France, sealing the victory."
```

---

### Example Queries (Quick Reference)

**Player Statistics:**
- "Who are the top scorers?"
- "Tell me about Messi's season stats"
- "Compare Messi and Di Maria"
- "Who has the most assists?"
- "Find a player named Julian"
- "How did Messi play in the last match?"

**Match Information:**
- "How did we do in the last match?"
- "What were the stats against France?"
- "Show me the match statistics"
- "Who scored the goals in the last match?"

**Team Overview:**
- "What's our season record?"
- "Show me the squad list"
- "Who plays as midfielder?"
- "How many wins do we have?"

---

### Testing the Integration

#### Test Database Tools Directly

```python
from dotenv import load_dotenv
load_dotenv()
from app.database import SessionLocal
from app.services.chatbot import get_club_season_stats, get_top_scorers
from uuid import UUID

db = SessionLocal()
club_id = UUID("your-club-id-here")

# Test team stats
stats = get_club_season_stats(db, club_id)
print(f"Club: {stats['club_name']} - {stats['matches_played']} matches")

# Test top scorers
scorers = get_top_scorers(db, club_id)
print(f"Top scorers: {len(scorers)} players")

db.close()
```

#### Test LLM Chat

```python
from dotenv import load_dotenv
load_dotenv()
from app.database import SessionLocal
from app.services.chatbot.llm_service import LLMService
from uuid import UUID

db = SessionLocal()
club_id = UUID("your-club-id-here")
llm = LLMService()

response = llm.chat(
    user_message="Who are the top scorers?",
    conversation_history=[],
    db=db,
    club_id=club_id
)

print(f"Tools executed: {response['tool_calls_executed']}")
print(f"Response: {response['message']}")

db.close()
```

---

### Technical Decisions

#### 1. Sync vs Async

The `ai-chatbot` project uses async SQLAlchemy, but the main backend uses sync. All tools were converted:

```python
# ai-chatbot (async):
async def find_player_by_name(db: AsyncSession, ...):
    result = await db.execute(query)

# Main backend (sync):
def find_player_by_name(db: Session, ...):
    result = db.execute(query)
```

#### 2. google-genai vs google-generativeai

The main backend uses `google-genai` (~1MB) instead of `google-generativeai` (~162MB) to stay under Vercel's 250MB deployment limit.

```python
# google-genai API pattern:
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

#### 3. JWT Authentication

Authentication uses `require_coach` dependency instead of user_id/club_id in request body:

```python
# Extract context from authenticated coach:
def get_coach_context(coach: User) -> tuple[UUID, UUID]:
    return coach.user_id, coach.coach.club.club_id
```

---

### Dependencies

No new dependencies were added. The chatbot uses existing packages:

```
google-genai  # Already installed for training plans (lightweight ~1MB)
```

### Environment Variables

```
GEMINI_API_KEY=your_gemini_api_key  # Already configured for training plans
```

---

## Complete File Structure After Integration

```
app/
├── api/
│   └── routes/
│       ├── chat.py                    # NEW: Chat API endpoints
│       ├── coach.py                   # Existing (has AI training plan endpoint)
│       └── ...
├── models/
│   ├── conversation_message.py        # NEW: ConversationMessage model
│   ├── __init__.py                    # MODIFIED: Added ConversationMessage export
│   └── ...
├── schemas/
│   ├── chat.py                        # NEW: Chat request/response schemas
│   └── ...
├── services/
│   ├── chatbot/
│   │   ├── __init__.py                # NEW: Package exports (12 tools)
│   │   ├── player_tools.py            # NEW: 6 player query tools
│   │   ├── match_tools.py             # NEW: 4 match query tools
│   │   ├── team_tools.py              # NEW: 2 team query tools
│   │   ├── conversation_service.py    # NEW: Session/history management
│   │   └── llm_service.py             # NEW: Gemini function calling
│   ├── pgvector_rag_service.py        # Existing: RAG for training plans
│   └── ...
└── main.py                            # MODIFIED: Registered chat router

docs/
├── 08_AI_FEATURES_INTEGRATION.md      # This file: Integration guide + tool reference
└── 09_CHATBOT_ENDPOINTS.md            # NEW: Detailed endpoint documentation
```

---

## Progress Tracking

### Overall Status

| Feature | Status | Progress |
|---------|--------|----------|
| AI Training Plans (PgVector) | Complete | 10/10 tasks |
| AI Chatbot | Complete | 14/14 tasks |

### Completion Criteria

- [x] AI Training Plan endpoint working in main project
- [x] All 4 Chatbot endpoints working in main project
- [x] JWT authentication working for chat endpoints
- [x] Function calling working with 12 database tools
- [x] Conversation history persistence working
- [x] All existing tests still passing
- [x] Detailed tool documentation with trigger questions
- [x] Complex multi-message test flows documented

---

## Deployment Notes

### Vercel Deployment

Both AI features are compatible with Vercel's constraints:
- Total deployment size under 250MB
- Uses lightweight `google-genai` package
- Uses PostgreSQL pgvector for RAG (no local ChromaDB)
- All operations are synchronous (compatible with serverless)

### Environment Variables Required

```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your_jwt_secret
```
