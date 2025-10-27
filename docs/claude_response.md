# ⚠️ PROPOSED CHANGES - AWAITING YOUR APPROVAL

I will NOT make any changes until you approve. Let me explain **WHAT** will change and **HOW** it affects each part of the app.

---

## 🔴 CRITICAL ISSUE TO RESOLVE FIRST

### The Name Storage Problem

You said: _"each player in our club that is registered has a new incomplete entry in players table having the name (I know that the name is in the user's table but I don't know how to manage this change)"_

**The Problem:**

- `players` table has `player_id` which is a **FOREIGN KEY to users.user_id**
- We CANNOT create a player record without first creating a user record
- But we want incomplete player entries BEFORE the player signs up

**Three Solutions - Pick One:**

### Option A: Add `player_name` to players table (RECOMMENDED)

```sql
ALTER TABLE players ADD COLUMN player_name VARCHAR(255);
```

**How it works:**

1. Admin adds match → Create player record with `player_id = gen_random_uuid()`, `player_name = "Marcus Silva"`, `is_linked = FALSE`
2. Player signs up → Create user record with `user_id = existing player_id`, copy `player_name` to `users.full_name`
3. After signup, both `players.player_name` and `users.full_name` have the name (slight redundancy but works)

**Impact:**

- ✅ Simple to implement
- ✅ Works with existing FK constraint
- ⚠️ Small redundancy (name in two places after signup)

---

### Option B: Remove FK constraint (NOT RECOMMENDED)

```sql
ALTER TABLE players DROP CONSTRAINT players_player_id_fkey;
```

**How it works:**

1. Player records can exist without user records
2. `player_id` is just a UUID, not linked to users
3. On signup, somehow link player to user

**Impact:**

- ❌ Loses referential integrity
- ❌ Complex to manage relationships
- ❌ Not recommended

---

### Option C: Keep data in player_invite_codes only (ALTERNATIVE)

```sql
-- Don't create player records until signup
-- Store everything in player_invite_codes
ALTER TABLE player_invite_codes ADD COLUMN player_name VARCHAR(255);
ALTER TABLE player_invite_codes ADD COLUMN jersey_number INTEGER;
ALTER TABLE player_invite_codes ADD COLUMN position VARCHAR(50);
```

**How it works:**

1. Admin adds match → Only create invite code record (no player record)
2. Player signs up → Create user + player records from invite code data
3. No incomplete player records

**Impact:**

- ✅ Clean separation
- ✅ No redundancy
- ⚠️ Different from what you described

---

**DECISION NEEDED:** Which option do you prefer? I recommend **Option A**.

---

## 📋 DATABASE CHANGES (Assuming Option A)

### 1. `players` table

```sql
-- ADD new column for name before user signup
ALTER TABLE players ADD COLUMN player_name VARCHAR(255);

-- After this change:
-- - Admin creates player with player_name, no user yet
-- - is_linked = FALSE initially
-- - player_id is generated UUID
-- - When player signs up, create user with user_id = player_id
```

**Impact:**

- ✅ Players can exist before user accounts
- ⚠️ Name stored in two places after signup (minor redundancy)

---

### 2. `player_invite_codes` table

```sql
-- REMOVE redundant columns
ALTER TABLE player_invite_codes DROP COLUMN jersey_number;
ALTER TABLE player_invite_codes DROP COLUMN position;

-- Keep only:
-- invite_code_id, club_id, player_id (FK to players), 
-- invite_code, is_used, created_at, linked_at
```

**Impact:**

- ✅ No data redundancy
- ✅ Single source of truth (players table)
- ⚠️ Must JOIN with players to get jersey/position

---

### 3. `training_plans` table

```sql
-- ADD new columns
ALTER TABLE training_plans ADD COLUMN status VARCHAR(20);
ALTER TABLE training_plans ADD COLUMN coach_notes TEXT;

-- Status values: 'pending', 'in_progress', 'completed'
```

**Impact:**

- ✅ Status tracking moved to plans
- ✅ Coach notes moved to plans

---

### 4. `player_training_assignments` table

```sql
-- DELETE entire table
DROP TABLE IF EXISTS player_training_assignments CASCADE;
DROP TABLE IF EXISTS training_exercise_completion CASCADE;
```

**Impact:**

- ❌ LOSES assignment history tracking
- ❌ LOSES progress tracking per assignment
- ⚠️ **CRITICAL:** No way to track when plan was assigned vs created
- ⚠️ **CRITICAL:** No way to track multiple assignments of same plan

**QUESTION:** Are you sure you want to delete this? It means:

- Can't track when coach assigned a plan to player
- Can't have progress tracking per assignment
- Can't assign the same plan multiple times to same player

**ALTERNATIVE:** Keep the table but simplify it?

---

## 🔄 PLAYER SIGNUP FLOW CHANGES

### New Flow:

**Screen 1: Enter Invite Code**

```
User action: Enters "MRC-1827"
↓
API: POST /api/auth/verify-invite
Request: { "invite_code": "MRC-1827" }
Response: {
  "valid": true,
  "player_data": {
    "player_name": "Marcus Silva",  // Can be changed by player
    "jersey_number": 10,            // Read-only
    "position": "Forward",          // Read-only
    "club_name": "Thunder United"   // Read-only
  }
}
```

**Screen 2: Complete Profile**

```
User action: Fills in additional info (email, password, can change name)
↓
API: POST /api/auth/register/player
Request: {
  "invite_code": "MRC-1827",
  "player_name": "Marcus Silva",    // Player can change
  "email": "marcus@email.com",
  "password": "secure123",
  "birth_date": "2008-03-20",
  "height": 180,
  "profile_image_url": "..."
}
Response: {
  "user_id": "uuid",
  "player_id": "uuid",
  "jwt_token": "eyJ..."
}
↓
Backend actions:
1. Find player by invite code: SELECT player_id FROM player_invite_codes WHERE invite_code = ?
2. Create user: INSERT INTO users (user_id = player_id, full_name, email, password_hash, user_type='player')
3. Update player: UPDATE players SET is_linked = TRUE, height = ?, birth_date = ?, profile_image_url = ?, player_name = ? WHERE player_id = ?
4. Mark code used: UPDATE player_invite_codes SET is_used = TRUE, linked_at = NOW() WHERE invite_code = ?
5. Generate JWT token
```

**Impact on Frontend:**

- ✅ Swap screen order
- ✅ First screen simpler (just code input)
- ✅ Second screen pre-fills data from first screen
- ⚠️ Player can change name (not just read-only)

**Impact on Backend:**

- ✅ verify-invite becomes simple validation
- ✅ register-player does all the work
- ⚠️ Must handle player_name update (might differ from lineup name)

---

## 🔐 AUTHENTICATION CHANGES

### JWT Implementation

**What will change:**

```javascript
// Current: Returns user data
POST /api/auth/register/coach → { user_id, coach_id, club_id, email }

// New: Returns JWT token
POST /api/auth/register/coach → { 
  user: { user_id, coach_id, club_id, email },
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// New endpoint
POST /api/auth/login → { 
  user: { user_id, user_type, ... },
  token: "eyJ..."
}
```

**Impact:**

- ✅ Stateless authentication
- ✅ Token stored in client (localStorage/secure storage)
- ⚠️ All subsequent requests need `Authorization: Bearer <token>` header
- ⚠️ Frontend must handle token storage and refresh

---

## 📱 SCREEN-BASED ENDPOINTS (MAJOR REORGANIZATION)

I need to view the Spinta UI PDF to create the exact endpoints. Let me read it first:Let me analyze the UI screens to propose the new endpoint structure: