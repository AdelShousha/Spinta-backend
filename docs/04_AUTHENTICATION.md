# Authentication

## Overview

The Spinta platform uses **JWT (JSON Web Tokens)** for stateless authentication. All authenticated requests must include a valid JWT token in the `Authorization` header.

## Authentication Flow

### Coach Registration Flow
```
1. Coach submits registration form
   ↓
2. Backend validates input
   ↓
3. Backend hashes password
   ↓
4. Backend creates user + coach + club records (transaction)
   ↓
5. Backend generates JWT token
   ↓
6. Return user data + token
   ↓
7. Frontend stores token
   ↓
8. Frontend redirects to coach dashboard
```

### Player Registration Flow
```
(See 03_PLAYER_SIGNUP_FLOW.md for detailed flow)

1. Player verifies invite code (unauthenticated)
   ↓
2. Player completes profile
   ↓
3. Backend creates user + updates player record
   ↓
4. Backend generates JWT token
   ↓
5. Return user data + token
   ↓
6. Frontend stores token
   ↓
7. Frontend redirects to player dashboard
```

### Login Flow
```
1. User submits email + password
   ↓
2. Backend looks up user by email
   ↓
3. Backend verifies password hash
   ↓
4. Backend generates JWT token
   ↓
5. Return user data + token
   ↓
6. Frontend stores token
   ↓
7. Frontend redirects to appropriate dashboard (coach/player)
```

---

## JWT Token Specification

### Token Structure

Standard JWT with three parts: `Header.Payload.Signature`

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload

**For Coach:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@email.com",
  "user_type": "coach",
  "exp": 1735230000
}
```

**For Player:**
```json
{
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "email": "marcus@email.com",
  "user_type": "player",
  "exp": 1735230000
}
```

### Payload Fields

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | String (UUID) | User's unique identifier |
| `email` | String | User's email address |
| `user_type` | String | "coach" or "player" |
| `exp` | Integer | Expiration timestamp (Unix epoch) |

**Optional fields** (can be added if needed):
- `club_id`: For quick access to club data
- `player_id`: For players (same as user_id)
- `coach_id`: For coaches (same as user_id)

### Signature

```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

**SECRET_KEY:** Must be stored securely in environment variables, minimum 256 bits (32 characters).

### Token Expiration

**Default:** 24 hours from issuance

**Calculation:**
```python
exp = datetime.utcnow() + timedelta(hours=24)
exp_timestamp = int(exp.timestamp())
```

**After expiration:** Token is invalid, user must log in again.

**Future Enhancement:** Implement refresh tokens for extended sessions.

---

## Making Authenticated Requests

### Request Header

All authenticated endpoints require the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwiZW1haWwiOiJqb2huQGVtYWlsLmNvbSIsInVzZXJfdHlwZSI6ImNvYWNoIiwiZXhwIjoxNzM1MjMwMDAwfQ.signature
```

### Backend Validation Process

For every authenticated endpoint:

**Step 1: Extract token from header**
```python
auth_header = request.headers.get('Authorization')
if not auth_header or not auth_header.startswith('Bearer '):
    return 401 Unauthorized

token = auth_header.split('Bearer ')[1]
```

**Step 2: Verify and decode token**
```python
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
except jwt.ExpiredSignatureError:
    return 401 Unauthorized - "Token has expired"
except jwt.InvalidTokenError:
    return 401 Unauthorized - "Invalid token"
```

**Step 3: Extract user info from payload**
```python
user_id = payload.get('user_id')
user_type = payload.get('user_type')
```

**Step 4: Optional - Verify user still exists**
```sql
SELECT user_id FROM users WHERE user_id = ? AND user_type = ?;
```

**Step 5: Pass user_id to endpoint handler**
- Use dependency injection or middleware
- Endpoint handlers receive authenticated `user_id`
- Use for authorization checks

---

## Authentication Endpoints

### 1. Coach Registration

**Endpoint:** `POST /api/auth/register/coach`

**Purpose:** Create new coach account with club

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "john@email.com",
  "password": "SecurePass123!",
  "full_name": "John Smith",
  "birth_date": "1985-06-15",
  "gender": "Male",
  "club": {
    "club_name": "Thunder United FC",
    "country": "United States",
    "age_group": "U16",
    "stadium": "City Stadium",
    "logo_url": "https://storage.example.com/clubs/thunder-logo.png"
  }
}
```

**Validation:**
- `email`: Required, valid format, unique
- `password`: Required, min 8 characters
- `full_name`: Required, 2-255 characters
- `birth_date`: Optional, valid date
- `gender`: Optional, string
- `club.club_name`: Required, 2-255 characters
- `club.country`: Optional
- `club.age_group`: Optional
- `club.stadium`: Optional
- `club.logo_url`: Optional, valid URL

**Backend Process:**

```sql
-- Start transaction
BEGIN;

-- 1. Hash password
password_hash = bcrypt.hash(password, cost=12)

-- 2. Create user
INSERT INTO users (user_id, email, password_hash, full_name, user_type, created_at, updated_at)
VALUES (gen_random_uuid(), ?, ?, ?, 'coach', NOW(), NOW())
RETURNING user_id;

-- 3. Create coach
INSERT INTO coaches (coach_id, birth_date, gender, created_at, updated_at)
VALUES (user_id, ?, ?, NOW(), NOW());

-- 4. Create club
INSERT INTO clubs (club_id, coach_id, club_name, country, age_group, stadium, logo_url, created_at, updated_at)
VALUES (gen_random_uuid(), user_id, ?, ?, ?, ?, ?, NOW(), NOW())
RETURNING club_id;

-- 5. Initialize club season statistics
INSERT INTO club_season_statistics (club_stats_id, club_id, updated_at)
VALUES (gen_random_uuid(), club_id, NOW());

COMMIT;

-- 6. Generate JWT token
token = generate_jwt({
  user_id: user_id,
  email: email,
  user_type: 'coach',
  exp: now + 24h
})
```

**Success Response (201 Created):**
```json
{
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@email.com",
    "user_type": "coach",
    "full_name": "John Smith",
    "coach_id": "550e8400-e29b-41d4-a716-446655440000",
    "club_id": "club-uuid-here"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

Email Already Exists (409 Conflict):
```json
{
  "detail": "An account with this email already exists."
}
```

Validation Error (400 Bad Request):
```json
{
  "detail": "Validation failed",
  "errors": {
    "email": "Invalid email format",
    "password": "Password must be at least 8 characters",
    "club.club_name": "Club name is required"
  }
}
```

---

### 2. Player Registration (Step 1: Verify Invite)

**Endpoint:** `POST /api/auth/verify-invite`

**Purpose:** Validate invite code and return pre-filled player data

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "invite_code": "MRC-1827"
}
```

**Validation:**
- `invite_code`: Required, matches format (e.g., XXX-NNNN)

**Backend Process:**

```sql
SELECT
  p.player_id,
  p.player_name,
  p.jersey_number,
  p.position,
  p.is_linked,
  c.club_name,
  c.logo_url
FROM players p
JOIN clubs c ON p.club_id = c.club_id
WHERE p.invite_code = ?
LIMIT 1;

-- Check is_linked = FALSE
-- Return 409 if is_linked = TRUE (code already used)
```

**Success Response (200 OK):**
```json
{
  "valid": true,
  "player_data": {
    "player_id": "660e8400-e29b-41d4-a716-446655440001",
    "player_name": "Marcus Silva",
    "jersey_number": 10,
    "position": "Forward",
    "club_name": "Thunder United FC",
    "club_logo_url": "https://storage.example.com/clubs/thunder-logo.png"
  }
}
```

**Error Responses:**

Invalid Code (404 Not Found):
```json
{
  "detail": "Invalid invite code. Please check with your coach."
}
```

Code Already Used (409 Conflict):
```json
{
  "detail": "This invite code has already been used."
}
```

**Rate Limiting:** 5 requests per minute per IP

---

### 3. Player Registration (Step 2: Complete Signup)

**Endpoint:** `POST /api/auth/register/player`

**Purpose:** Create player user account and link to existing player record

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "invite_code": "MRC-1827",
  "player_name": "Marcus Silva",
  "email": "marcus@email.com",
  "password": "SecurePass123!",
  "birth_date": "2008-03-20",
  "height": 180,
  "profile_image_url": "https://storage.example.com/players/marcus.jpg"
}
```

**Validation:**
- `invite_code`: Required, must be valid and unused
- `player_name`: Required, 2-255 characters
- `email`: Required, valid format, unique
- `password`: Required, min 8 characters
- `birth_date`: Required, valid date
- `height`: Required, integer 100-250
- `profile_image_url`: Optional, valid URL

**Backend Process:**

```sql
-- Start transaction
BEGIN;

-- 1. Re-validate invite code and get player_id
SELECT player_id, club_id, is_linked
FROM players
WHERE invite_code = ?
FOR UPDATE;  -- Lock row to prevent race condition

-- Check is_linked = FALSE, else return 409

-- 2. Check email uniqueness
SELECT user_id FROM users WHERE email = ?;
-- If exists, return 409

-- 3. Hash password
password_hash = bcrypt.hash(password, cost=12)

-- 4. Create user account (user_id = player_id!)
INSERT INTO users (user_id, email, password_hash, full_name, user_type, created_at, updated_at)
VALUES (player_id, ?, ?, ?, 'player', NOW(), NOW());

-- 5. Update player record
UPDATE players SET
  player_name = ?,
  birth_date = ?,
  height = ?,
  profile_image_url = ?,
  is_linked = TRUE,
  linked_at = NOW(),
  updated_at = NOW()
WHERE player_id = ?;

-- 6. Initialize player season statistics
INSERT INTO player_season_statistics (player_stats_id, player_id, updated_at)
VALUES (gen_random_uuid(), player_id, NOW());

COMMIT;

-- 7. Generate JWT token
token = generate_jwt({
  user_id: player_id,
  email: email,
  user_type: 'player',
  exp: now + 24h
})
```

**Success Response (201 Created):**
```json
{
  "user": {
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "marcus@email.com",
    "user_type": "player",
    "full_name": "Marcus Silva",
    "player_id": "660e8400-e29b-41d4-a716-446655440001",
    "club_id": "club-uuid-here",
    "jersey_number": 10,
    "position": "Forward"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:** (Same as verify-invite, plus email validation errors)

**Rate Limiting:** 3 requests per minute per IP

---

### 4. Login

**Endpoint:** `POST /api/auth/login`

**Purpose:** Authenticate existing user and return JWT token

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "john@email.com",
  "password": "SecurePass123!"
}
```

**Validation:**
- `email`: Required, valid format
- `password`: Required

**Backend Process:**

```sql
-- 1. Look up user by email
SELECT
  u.user_id,
  u.email,
  u.password_hash,
  u.full_name,
  u.user_type
FROM users u
WHERE u.email = ?
LIMIT 1;

-- 2. Verify password
is_valid = bcrypt.verify(password, password_hash)
if not is_valid:
    return 401 Invalid credentials

-- 3. Get additional user data based on type

-- If coach:
SELECT c.coach_id, cl.club_id
FROM coaches c
JOIN clubs cl ON c.coach_id = cl.coach_id
WHERE c.coach_id = user_id;

-- If player:
SELECT p.player_id, p.club_id, p.jersey_number, p.position
FROM players p
WHERE p.player_id = user_id;

-- 4. Generate JWT token
token = generate_jwt({
  user_id: user_id,
  email: email,
  user_type: user_type,
  exp: now + 24h
})
```

**Success Response (200 OK):**

**For Coach:**
```json
{
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@email.com",
    "user_type": "coach",
    "full_name": "John Smith",
    "coach_id": "550e8400-e29b-41d4-a716-446655440000",
    "club_id": "club-uuid-here"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**For Player:**
```json
{
  "user": {
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "marcus@email.com",
    "user_type": "player",
    "full_name": "Marcus Silva",
    "player_id": "660e8400-e29b-41d4-a716-446655440001",
    "club_id": "club-uuid-here",
    "jersey_number": 10,
    "position": "Forward"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

Invalid Credentials (401 Unauthorized):
```json
{
  "detail": "Invalid email or password."
}
```

**Security Notes:**
- Use same error message for "user not found" and "wrong password" (prevent email enumeration)
- Rate limit: 5 failed attempts per IP per 15 minutes
- Consider: Account lockout after 10 failed attempts

---

## Authorization

### Role-Based Access Control

#### Coach Endpoints
All endpoints under `/api/coach/*` require:
- Valid JWT token
- `user_type = "coach"` in token payload

**Authorization check:**
```python
if current_user.user_type != 'coach':
    return 403 Forbidden
```

#### Player Endpoints
All endpoints under `/api/player/*` require:
- Valid JWT token
- `user_type = "player"` in token payload

**Authorization check:**
```python
if current_user.user_type != 'player':
    return 403 Forbidden
```

### Resource Ownership

#### Coach Resources
Coaches can only access resources belonging to their club:

```python
# Get coach's club_id from database
coach_club_id = db.query(clubs.club_id).filter(clubs.coach_id == current_user.user_id).first()

# Verify resource belongs to coach's club
resource_club_id = db.query(resource.club_id).filter(resource.id == resource_id).first()

if coach_club_id != resource_club_id:
    return 403 Forbidden
```

**Examples:**
- Coach can only view players from their club
- Coach can only view matches from their club
- Coach can only create training plans for players in their club

#### Player Resources
Players can only access their own resources:

```python
# Verify resource belongs to current player
if resource.player_id != current_user.user_id:
    return 403 Forbidden
```

**Examples:**
- Player can only view their own matches
- Player can only view their own training plans
- Player can only update their own profile

---

## Security Best Practices

### Password Security

1. **Hashing Algorithm:** Use bcrypt with cost factor 12
   ```python
   password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
   ```

2. **Password Requirements:**
   - Minimum 8 characters
   - Recommend: Mix of uppercase, lowercase, numbers
   - Store requirements in environment config for easy updates

3. **Never:**
   - Store passwords in plain text
   - Log passwords (even hashed)
   - Return passwords in API responses

### Token Security

1. **Secret Key:**
   - Minimum 256 bits (32 characters)
   - Generated using cryptographically secure random
   - Stored in environment variables
   - Never committed to version control
   - Rotate periodically (requires re-login for all users)

2. **Token Storage (Client-Side):**
   - **Web:** HTTP-only cookies (preferred) or localStorage
   - **Mobile:** Secure storage (Keychain on iOS, Keystore on Android)
   - Never store in plain text or unencrypted storage

3. **Token Transmission:**
   - Always use HTTPS in production
   - Never send token in URL query parameters
   - Always use Authorization header

### Rate Limiting

Recommended limits:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 5 attempts | 15 minutes |
| `/api/auth/register/coach` | 3 attempts | 1 hour |
| `/api/auth/verify-invite` | 5 attempts | 1 minute |
| `/api/auth/register/player` | 3 attempts | 1 minute |

**Implementation:**
- Track by IP address
- Use Redis or in-memory cache
- Return 429 Too Many Requests when limit exceeded

### Input Validation

1. **Email Validation:**
   - Use regex or library (e.g., email-validator)
   - Normalize (lowercase, trim whitespace)
   - Check uniqueness before creating account

2. **Password Validation:**
   - Check length (min 8 characters)
   - Optional: Check complexity (uppercase, lowercase, numbers)
   - Check against common password lists (optional)

3. **Sanitization:**
   - Trim whitespace from all string inputs
   - Validate data types (UUID, integer, date formats)
   - Reject invalid characters in names

### HTTPS/TLS

- **Development:** HTTP acceptable
- **Production:** HTTPS required
- Configure TLS 1.2 or higher
- Use valid SSL certificate

---

## Error Handling

### Standard HTTP Status Codes

| Code | Usage |
|------|-------|
| `200` | Successful request |
| `201` | Resource created (registration, etc.) |
| `400` | Bad request (validation error) |
| `401` | Unauthorized (missing/invalid token, wrong password) |
| `403` | Forbidden (valid token, insufficient permissions) |
| `404` | Resource not found |
| `409` | Conflict (duplicate email, used invite code) |
| `429` | Too many requests (rate limit exceeded) |
| `500` | Internal server error |

### Error Response Format

All errors return JSON with `detail` field:

```json
{
  "detail": "Human-readable error message"
}
```

**With validation errors:**
```json
{
  "detail": "Validation failed",
  "errors": {
    "field_name": "Error message for this field",
    "another_field": "Error message"
  }
}
```

### Common Error Messages

**Authentication Errors:**
- `"Authentication credentials were not provided."` (401)
- `"Invalid or expired token."` (401)
- `"Invalid email or password."` (401)

**Authorization Errors:**
- `"You do not have permission to perform this action."` (403)
- `"This resource does not belong to your club."` (403)

**Validation Errors:**
- `"An account with this email already exists."` (409)
- `"Invalid invite code."` (404)
- `"This invite code has already been used."` (409)
- `"Validation failed"` (400) - with errors object

---

## Token Refresh (Future Enhancement)

Current implementation: Tokens expire after 24 hours, requiring re-login.

**Future improvement:** Implement refresh tokens for better UX.

### Proposed Flow:

1. **On Login:** Return both access token (1 hour) and refresh token (30 days)
2. **Access Token Expires:** Frontend detects 401 error
3. **Request New Access Token:** `POST /api/auth/refresh` with refresh token
4. **Refresh Token Expires:** User must log in again

### Additional Tables Needed:

```sql
CREATE TABLE refresh_tokens (
  token_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id),
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL,
  revoked BOOLEAN DEFAULT FALSE
);
```

---

## Testing Checklist

### Coach Registration
- [ ] Valid registration creates user, coach, club, and statistics records
- [ ] Returns JWT token and user data
- [ ] Duplicate email returns 409
- [ ] Invalid email format returns 400
- [ ] Short password returns 400
- [ ] Missing required fields returns 400

### Player Registration
- [ ] Step 1: Valid invite code returns player data
- [ ] Step 1: Invalid code returns 404
- [ ] Step 1: Used code returns 409
- [ ] Step 2: Valid signup creates user and updates player
- [ ] Step 2: Returns JWT token and user data
- [ ] Step 2: Duplicate email returns 409
- [ ] Step 2: Invalid input returns 400
- [ ] Race condition: Concurrent signups with same code handled correctly

### Login
- [ ] Valid credentials return token and user data
- [ ] Invalid email returns 401
- [ ] Invalid password returns 401
- [ ] Returns correct user_type (coach/player)
- [ ] Token contains correct payload

### Authorization
- [ ] Coach cannot access player endpoints
- [ ] Player cannot access coach endpoints
- [ ] Coach can only access their club's data
- [ ] Player can only access their own data
- [ ] Invalid token returns 401
- [ ] Expired token returns 401

### Security
- [ ] Passwords are hashed (not stored plain text)
- [ ] Tokens expire after 24 hours
- [ ] Rate limiting works correctly
- [ ] Error messages don't leak sensitive info
