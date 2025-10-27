# Player Signup Flow

## Overview

The player signup process is a **2-step flow** that allows players to join their team using a unique invite code. The key innovation is that player records are **pre-created** by the admin during match processing, so the player's basic information (name, jersey number, position, club) is already in the system before they sign up.

## Process Overview

```
Admin Side:
1. Admin uploads match video
2. CV extracts lineup (names, jersey numbers, positions, StatsBomb IDs)
3. System creates incomplete player records
4. System generates unique invite codes
5. Coach shares invite codes with players

Player Side:
6. Player receives invite code from coach
7. Player enters code in app (Step 1)
8. System validates code and returns pre-filled data
9. Player sees profile form with pre-filled info (Step 2)
10. Player fills remaining fields and submits
11. System creates user account and links to player record
12. Player is logged in
```

## Detailed Flow

### Phase 1: Admin Creates Incomplete Players

This happens when a coach uploads a match and the CV service processes the lineup.

#### Input Data (from CV Service)
```json
{
  "home_team_lineup": [
    {
      "player_name": "Marcus Silva",
      "jersey_number": 10,
      "position": "Forward",
      "statsbomb_player_id": 5470
    },
    {
      "player_name": "Jake Thompson",
      "jersey_number": 7,
      "position": "Midfielder",
      "statsbomb_player_id": 5471
    }
    // ... 9 more players
  ]
}
```

#### Backend Process

For each player in the lineup:

**Step 1: Check if player already exists**

```sql
SELECT * FROM players
WHERE club_id = ?
  AND (
    statsbomb_player_id = ?
    OR jersey_number = ?
  )
LIMIT 1;
```

**Step 2: If player doesn't exist, create new player record**

```sql
-- Generate unique invite code
-- Example algorithm: First 3 letters of name + hyphen + 4 random digits
-- "Marcus Silva" → "MAR-1827" or "MRC-1827"

INSERT INTO players (
  player_id,              -- gen_random_uuid()
  club_id,
  player_name,
  statsbomb_player_id,
  jersey_number,
  position,
  invite_code,            -- Generated unique code
  is_linked,              -- FALSE
  created_at,
  updated_at
) VALUES (
  gen_random_uuid(),
  'club-uuid-here',
  'Marcus Silva',
  5470,
  10,
  'Forward',
  'MRC-1827',
  FALSE,
  NOW(),
  NOW()
);
```

**Step 3: Store invite code for coach to share**

The invite code is now available in `players.invite_code`. The coach can:
- View all unlinked players with their invite codes
- Print/export list of codes to share with team
- Send codes individually via messaging

#### Invite Code Generation Requirements

- **Format**: 3-4 letters + hyphen + 4 digits (e.g., "MRC-1827", "JAKE-5543")
- **Uniqueness**: Must be unique across ALL players in database
- **Security**: Use cryptographically secure random for digits
- **Readability**: Use uppercase letters, avoid confusing characters (0/O, 1/I/l)
- **Collision handling**: If code exists, regenerate

**Example Generation Algorithm:**
```python
import secrets
import string

def generate_invite_code(player_name):
    # Extract initials or first 3 letters
    parts = player_name.split()
    if len(parts) >= 2:
        # Use first letter of first name + first 2 of last name
        prefix = (parts[0][0] + parts[-1][:2]).upper()
    else:
        # Use first 3 letters of name
        prefix = player_name[:3].upper()

    # Generate 4 random digits
    digits = ''.join(secrets.choice(string.digits) for _ in range(4))

    code = f"{prefix}-{digits}"

    # Check uniqueness in database, regenerate if exists
    # while code_exists_in_db(code):
    #     digits = ''.join(secrets.choice(string.digits) for _ in range(4))
    #     code = f"{prefix}-{digits}"

    return code
```

---

### Phase 2: Player Signup - Step 1 (Verify Invite Code)

The player opens the app for the first time and sees the invite code entry screen.

#### UI Screen 1: Enter Invite Code

```
┌─────────────────────────────────────┐
│                                     │
│         [⚽ Spinta Logo]             │
│                                     │
│      Join Your Team                 │
│                                     │
│  Enter the invite code your         │
│  coach gave you                     │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ MRC-1827                      │  │
│  └───────────────────────────────┘  │
│                                     │
│  [    Continue →    ]               │
│                                     │
│  Don't have a code?                 │
│  Contact your coach                 │
│                                     │
└─────────────────────────────────────┘
```

#### API Request

**Endpoint:** `POST /api/auth/verify-invite`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "invite_code": "MRC-1827"
}
```

#### Backend Processing

**Step 1: Validate invite code format**
- Check if code matches expected format (XXX-NNNN)
- Return 400 if invalid format

**Step 2: Look up invite code**
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
```

**Step 3: Validate player can sign up**
- Check if code exists (404 if not found)
- Check if `is_linked = FALSE` (409 if already used)

**Step 4: Return pre-filled data**

#### API Response

**Success Response (200 OK):**
```json
{
  "valid": true,
  "player_data": {
    "player_id": "550e8400-e29b-41d4-a716-446655440000",
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

Invalid Format (400 Bad Request):
```json
{
  "detail": "Invalid invite code format."
}
```

#### Frontend Behavior

**On Success:**
- Store `player_data` in state/local storage
- Navigate to Step 2 (Complete Profile screen)

**On Error:**
- Show error message below input field
- Keep user on same screen to retry

---

### Phase 3: Player Signup - Step 2 (Complete Profile)

After successful code verification, the player sees the profile completion form with pre-filled data.

#### UI Screen 2: Complete Your Profile

```
┌─────────────────────────────────────┐
│  ← Back                             │
│                                     │
│  Complete Your Profile              │
│                                     │
│  ┌───┐                              │
│  │🏆 │  Thunder United FC           │
│  └───┘                              │
│                                     │
│  Your Name                          │
│  ┌───────────────────────────────┐  │
│  │ Marcus Silva                  │  │ ← Editable
│  └───────────────────────────────┘  │
│                                     │
│  Jersey Number                      │
│  ┌───────────────────────────────┐  │
│  │ #10                           │  │ ← Read-only
│  └───────────────────────────────┘  │
│                                     │
│  Position                           │
│  ┌───────────────────────────────┐  │
│  │ Forward                       │  │ ← Read-only
│  └───────────────────────────────┘  │
│                                     │
│  Email                              │
│  ┌───────────────────────────────┐  │
│  │ marcus@email.com              │  │ ← User fills
│  └───────────────────────────────┘  │
│                                     │
│  Password                           │
│  ┌───────────────────────────────┐  │
│  │ ••••••••••                    │  │ ← User fills
│  └───────────────────────────────┘  │
│                                     │
│  Birth Date                         │
│  ┌───────────────────────────────┐  │
│  │ 2008-03-20         📅         │  │ ← User fills
│  └───────────────────────────────┘  │
│                                     │
│  Height (cm)                        │
│  ┌───────────────────────────────┐  │
│  │ 180                           │  │ ← User fills
│  └───────────────────────────────┘  │
│                                     │
│  Profile Photo                      │
│  ┌───────────────────────────────┐  │
│  │  [📷 Upload Photo]            │  │ ← Optional
│  └───────────────────────────────┘  │
│                                     │
│  [  Complete Signup  ]              │
│                                     │
└─────────────────────────────────────┘
```

#### Field Requirements

| Field | Status | Validation | Notes |
|-------|--------|------------|-------|
| Name | Editable | Required, 2-255 chars | Player can change pre-filled name |
| Jersey Number | Read-only | - | From pre-filled data |
| Position | Read-only | - | From pre-filled data |
| Email | Required | Valid email format, unique | Must not exist in users table |
| Password | Required | Min 8 characters | Should hash on backend |
| Birth Date | Required | Valid date, player must be 5-25 years old | Use date picker |
| Height | Required | Integer, 100-250 cm | Player height in cm |
| Profile Photo | Optional | Image file, max 5MB | Upload to cloud storage first |

#### API Request

**Endpoint:** `POST /api/auth/register/player`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "invite_code": "MRC-1827",
  "player_name": "Marcus Silva",
  "email": "marcus@email.com",
  "password": "SecurePass123!",
  "birth_date": "2008-03-20",
  "height": 180,
  "profile_image_url": "https://storage.example.com/players/marcus-profile.jpg"
}
```

**Field Notes:**
- `invite_code`: Required for validation
- `player_name`: Can differ from pre-filled (player edited it)
- `profile_image_url`: Optional, NULL if no photo uploaded

#### Backend Processing

**Step 1: Re-validate invite code**

```sql
SELECT player_id, club_id, is_linked
FROM players
WHERE invite_code = ?;
```

**Validations:**
- Code exists (404 if not)
- `is_linked = FALSE` (409 if already used)
- Prevents race conditions (code used while player on step 2)

**Step 2: Validate email uniqueness**

```sql
SELECT user_id FROM users WHERE email = ?;
```

- Return 409 if email already exists

**Step 3: Validate input data**
- Email format valid
- Password meets requirements (min 8 chars)
- Birth date valid and reasonable
- Height is valid integer (100-250 cm)

**Step 4: Hash password**
```python
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
```

**Step 5: Create user account**

```sql
INSERT INTO users (
  user_id,           -- Use the player_id from step 1!
  email,
  password_hash,
  full_name,
  user_type,
  created_at,
  updated_at
) VALUES (
  ?,                 -- player_id from players table
  ?,                 -- email from request
  ?,                 -- hashed password
  ?,                 -- player_name from request
  'player',
  NOW(),
  NOW()
);
```

**CRITICAL:** The `user_id` in the users table must be the SAME as the `player_id` that already exists in the players table. This creates the foreign key link.

**Step 6: Update player record**

```sql
UPDATE players SET
  player_name = ?,           -- Update if player changed it
  birth_date = ?,
  height = ?,
  profile_image_url = ?,
  is_linked = TRUE,
  linked_at = NOW(),
  updated_at = NOW()
WHERE player_id = ?;
```

**Step 7: Generate JWT token**

```python
payload = {
  "user_id": str(player_id),
  "email": email,
  "user_type": "player",
  "exp": datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Step 8: Return user data and token**

#### API Response

**Success Response (201 Created):**
```json
{
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "marcus@email.com",
    "user_type": "player",
    "full_name": "Marcus Silva",
    "player_id": "550e8400-e29b-41d4-a716-446655440000",
    "club_id": "club-uuid-here",
    "jersey_number": 10,
    "position": "Forward"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwiZW1haWwiOiJtYXJjdXNAZW1haWwuY29tIiwidXNlcl90eXBlIjoicGxheWVyIiwiZXhwIjoxNzM1MjMwMDAwfQ.signature"
}
```

**Error Responses:**

Email Already Exists (409 Conflict):
```json
{
  "detail": "An account with this email already exists."
}
```

Invite Code Already Used (409 Conflict):
```json
{
  "detail": "This invite code has already been used."
}
```

Invite Code Invalid (404 Not Found):
```json
{
  "detail": "Invalid invite code."
}
```

Validation Error (400 Bad Request):
```json
{
  "detail": "Validation failed",
  "errors": {
    "email": "Invalid email format",
    "password": "Password must be at least 8 characters",
    "height": "Height must be between 100 and 250 cm"
  }
}
```

#### Frontend Behavior

**On Success:**
- Store JWT token (localStorage, secure storage, etc.)
- Store user data in app state
- Navigate to player dashboard
- Show welcome message

**On Error:**
- Display error message
- Keep user on form to correct errors
- Highlight invalid fields

---

## Database State Changes

### Before Match Processing

```
players table: (empty for this player)

users table: (empty for this player)
```

### After Match Processing (Admin Creates Player)

```
players table:
player_id: 550e8400-e29b-41d4-a716-446655440000
club_id: club-uuid-here
player_name: "Marcus Silva"
statsbomb_player_id: 5470
jersey_number: 10
position: "Forward"
invite_code: "MRC-1827"
is_linked: FALSE
linked_at: NULL
birth_date: NULL
height: NULL
profile_image_url: NULL
created_at: 2025-10-14 10:00:00
updated_at: 2025-10-14 10:00:00

users table: (still empty for this player)
```

### After Player Signup

```
players table:
player_id: 550e8400-e29b-41d4-a716-446655440000
club_id: club-uuid-here
player_name: "Marcus Silva"              ← May have been updated
statsbomb_player_id: 5470
jersey_number: 10
position: "Forward"
invite_code: "MRC-1827"
is_linked: TRUE                          ← Changed to TRUE
linked_at: 2025-10-15 14:30:00          ← Set to NOW()
birth_date: 2008-03-20                  ← Filled
height: 180                              ← Filled
profile_image_url: "https://..."         ← Filled
created_at: 2025-10-14 10:00:00
updated_at: 2025-10-15 14:30:00         ← Updated

users table:
user_id: 550e8400-e29b-41d4-a716-446655440000  ← Same as player_id!
email: "marcus@email.com"
password_hash: "$2b$12$..."
full_name: "Marcus Silva"
user_type: "player"
created_at: 2025-10-15 14:30:00
updated_at: 2025-10-15 14:30:00
```

---

## Security Considerations

### 1. Invite Code Security

**Entropy:** With format XXX-NNNN:
- 26^3 = 17,576 possible letter combinations
- 10^4 = 10,000 possible digit combinations
- Total: 175,760,000 possible codes

**Brute Force Protection:**
- Rate limit verification endpoint (e.g., 5 attempts per IP per minute)
- Lock out after 10 failed attempts for same code
- Consider adding CAPTCHA after failed attempts

**Code Exposure:**
- Codes are not sensitive secrets (coach shares via messaging)
- But should not be publicly listed
- Only coach can view all unlinked player codes

### 2. Password Requirements

Recommended minimum requirements:
- At least 8 characters
- Contains uppercase and lowercase letters
- Contains at least one number
- Contains at least one special character (optional)

### 3. Email Verification

Current design does NOT include email verification. Considerations:

**Without email verification:**
- Faster onboarding
- Player can use immediately
- Risk: Typos in email mean player loses access

**With email verification:**
- Send verification email after signup
- Account active but show "Verify your email" banner
- Resend verification option

**Recommendation:** Start without email verification, add if needed.

### 4. Token Security

- JWT tokens should be stored securely on client
- Use HTTP-only cookies if web app
- Use secure storage on mobile (Keychain on iOS, Keystore on Android)
- Token expires after 24 hours
- Implement refresh token mechanism for production

---

## Testing Checklist

### Happy Path
- [ ] Admin creates match, player records created
- [ ] Player enters valid invite code, sees pre-filled data
- [ ] Player completes profile, account created successfully
- [ ] Player receives JWT token
- [ ] Player can log in with email/password
- [ ] Player sees dashboard with stats

### Error Cases
- [ ] Invalid invite code format returns 400
- [ ] Non-existent invite code returns 404
- [ ] Already used invite code returns 409
- [ ] Duplicate email returns 409
- [ ] Invalid email format returns 400
- [ ] Password too short returns 400
- [ ] Invalid birth date returns 400
- [ ] Invalid height returns 400

### Edge Cases
- [ ] Player edits name during signup
- [ ] Player uploads profile photo
- [ ] Player skips profile photo
- [ ] Multiple players sign up simultaneously (no race conditions)
- [ ] Player loses code (coach can retrieve from portal)
- [ ] Player closes app after Step 1 (can restart)

### Security
- [ ] Passwords are hashed (not stored plain text)
- [ ] JWT tokens expire after 24 hours
- [ ] Rate limiting on verify endpoint
- [ ] Email uniqueness enforced
- [ ] Invite code uniqueness enforced

---

## API Endpoints Summary

### Step 1: Verify Invite Code

**Endpoint:** `POST /api/auth/verify-invite`

**Purpose:** Validate invite code and retrieve pre-filled player data

**Authentication:** None (public endpoint)

**Rate Limiting:** 5 requests per minute per IP

---

### Step 2: Complete Signup

**Endpoint:** `POST /api/auth/register/player`

**Purpose:** Create user account and link to player record

**Authentication:** None (public endpoint)

**Rate Limiting:** 3 requests per minute per IP

---

## Flow Diagram

```
┌─────────────────┐
│  Admin Panel    │
│  Upload Match   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  CV Processes Lineup        │
│  Extracts: Name, Jersey,    │
│  Position, StatsBomb ID     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  FOR EACH PLAYER:           │
│  1. Check if exists         │
│  2. If not: Create player   │
│     - Generate invite code  │
│     - Set is_linked=FALSE   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Coach views unlinked       │
│  players & invite codes     │
│  Shares codes with team     │
└────────┬────────────────────┘
         │
         │
         ▼
┌─────────────────────────────┐
│  PLAYER SIDE                │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Screen 1:                  │
│  Enter Invite Code          │
│  [MRC-1827        ]         │
│  [ Continue →     ]         │
└────────┬────────────────────┘
         │
         ▼ POST /api/auth/verify-invite
         │
┌─────────────────────────────┐
│  Backend validates code     │
│  Returns pre-filled data    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Screen 2:                  │
│  Complete Profile           │
│  Name: [Marcus Silva   ]    │ ← Editable
│  Jersey: #10 (read-only)    │
│  Position: Forward          │
│  Email: [         ]         │ ← Fill
│  Password: [      ]         │ ← Fill
│  Birth: [         ]         │ ← Fill
│  Height: [        ]         │ ← Fill
│  Photo: [Upload]            │ ← Optional
│  [ Complete Signup ]        │
└────────┬────────────────────┘
         │
         ▼ POST /api/auth/register/player
         │
┌─────────────────────────────┐
│  Backend:                   │
│  1. Re-validate code        │
│  2. Check email unique      │
│  3. Hash password           │
│  4. Create user (user_id =  │
│     player_id)              │
│  5. Update player record:   │
│     - is_linked = TRUE      │
│     - Fill personal info    │
│  6. Generate JWT token      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Return user data + token   │
│  Player logged in!          │
│  Navigate to dashboard      │
└─────────────────────────────┘
```
