# Chatbot API Endpoints

## Overview

The AI Chatbot provides conversational access to team analytics through natural language queries. It uses **Gemini AI** with function calling to query the database and provide data-driven responses about players, matches, and team statistics.

**Base URL**: `/api/chat`

## Authentication

All endpoints require **JWT Bearer token** authentication. The coach must be authenticated and have an associated club.

```
Authorization: Bearer <your_jwt_token>
```

**Authentication Flow**:
1. Login via `POST /api/auth/login` to get a JWT token
2. Include the token in the `Authorization` header for all chat requests
3. The system extracts `user_id` and `club_id` from the token

---

## Endpoints Reference

### 1. Create Chat Session

Create a new chat session for the authenticated coach.

```
POST /api/chat/sessions
```

**Request Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**: None

**Response** (201 Created):
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-01-15T10:30:00.000Z"
}
```

**Errors**:
| Status | Description |
|--------|-------------|
| 400 | Coach does not have an associated club |
| 401 | Invalid or missing authentication token |

---

### 2. Send Chat Message

Send a message to the AI chatbot and receive a response.

```
POST /api/chat/messages
```

**Request Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
    "message": "Who are the top scorers?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User message (1-2000 characters) |
| `session_id` | UUID | No | Session ID to continue conversation. Creates new session if not provided. |

**Response** (200 OK):
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Your top scorers this season are:\n\n1. **Messi** - 5 goals (0.83 per match)\n2. **Ronaldo** - 4 goals (0.67 per match)\n3. **Neymar** - 3 goals (0.50 per match)",
    "tool_calls_executed": ["get_top_scorers"],
    "timestamp": "2025-01-15T10:31:00.000Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUID | Session ID for continuing the conversation |
| `message` | string | AI assistant's response |
| `tool_calls_executed` | string[] | List of database tools that were called |
| `timestamp` | datetime | When the response was generated |

**Errors**:
| Status | Description |
|--------|-------------|
| 400 | Coach does not have an associated club |
| 401 | Invalid or missing authentication token |
| 500 | Error processing message (LLM or database error) |

---

### 3. Get Conversation History

Retrieve all messages in a specific chat session.

```
GET /api/chat/sessions/{session_id}/messages
```

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | UUID | The chat session ID |

**Response** (200 OK):
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [
        {
            "role": "user",
            "content": "Who are the top scorers?",
            "tool_calls": null,
            "timestamp": "2025-01-15T10:30:30.000Z"
        },
        {
            "role": "assistant",
            "content": "Your top scorers this season are...",
            "tool_calls": [
                {
                    "tool_name": "get_top_scorers",
                    "arguments": {"limit": 5},
                    "result": {...}
                }
            ],
            "timestamp": "2025-01-15T10:31:00.000Z"
        }
    ],
    "total_messages": 2
}
```

**Errors**:
| Status | Description |
|--------|-------------|
| 404 | Session not found or no messages |
| 401 | Invalid or missing authentication token |

---

### 4. Clear Chat Session

Delete all messages in a chat session.

```
DELETE /api/chat/sessions/{session_id}
```

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | UUID | The chat session ID to clear |

**Response** (200 OK):
```json
{
    "message": "Session cleared successfully",
    "deleted_messages": 10
}
```

**Errors**:
| Status | Description |
|--------|-------------|
| 404 | Session not found |
| 401 | Invalid or missing authentication token |

---

## Example Usage with cURL

### Step 1: Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "coach@example.com", "password": "password123"}'
```

Response:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

### Step 2: Create a Session (Optional)

```bash
curl -X POST http://localhost:8000/api/chat/sessions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Step 3: Send a Message

```bash
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"message": "Who are the top scorers?"}'
```

### Step 4: Continue the Conversation

```bash
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about the first one",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

## Error Response Format

All error responses follow this format:

```json
{
    "detail": "Error description message"
}
```

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 400 | "Coach does not have an associated club" | Create a club first via coach API |
| 401 | "Not authenticated" | Include valid JWT token |
| 401 | "Token has expired" | Re-authenticate to get new token |
| 404 | "Session not found or no messages" | Check session_id or create new session |
| 500 | "Error processing message: ..." | Check server logs, may be API key or DB issue |

---

## Rate Limits

The chatbot uses the Gemini API which has its own rate limits:
- **Free tier**: 15 requests per minute
- **Paid tier**: Higher limits based on plan

If rate limited, wait a moment and retry.

---

## Best Practices

1. **Reuse sessions**: Include `session_id` to maintain conversation context
2. **Be specific**: "How did Messi perform in the last match?" gets better results than "player stats"
3. **Handle errors**: Always check for error responses and handle gracefully
4. **Clear old sessions**: Use DELETE endpoint to clean up completed conversations
