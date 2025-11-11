"""
Quick script to create a test incomplete player for manual testing.

This script creates:
1. A test coach and club (if they don't exist)
2. An incomplete player with invite code for testing registration flow

Run with: python -m scripts.seed_test_player
"""
from app.database import SessionLocal
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player
from app.core.security import get_password_hash


def seed_test_player():
    """Create test data for player registration flow."""
    db = SessionLocal()

    try:
        print("🌱 Seeding test player data...\n")

        # 1. Create test coach and club (if they don't exist)
        coach_user = db.query(User).filter(User.email == "testcoach@example.com").first()

        if not coach_user:
            print("📋 Creating test coach and club...")
            coach_user = User(
                email="testcoach@example.com",
                password_hash=get_password_hash("password123"),
                full_name="Test Coach",
                user_type="coach"
            )
            db.add(coach_user)
            db.flush()

            coach = Coach(user_id=coach_user.user_id)
            db.add(coach)
            db.flush()

            club = Club(
                coach_id=coach.coach_id,
                club_name="Test FC",
                country="England",
                age_group="U16"
            )
            db.add(club)
            db.flush()
            print("   ✅ Test coach and club created")
        else:
            coach = coach_user.coach
            club = coach.club
            print(f"   ℹ️  Using existing test coach: {coach_user.email}")

        print(f"   Club: {club.club_name} ({club.age_group})\n")

        # 2. Create incomplete player with invite code
        invite_code = "TEST-1234"

        # Check if player already exists
        existing_player = db.query(Player).filter(Player.invite_code == invite_code).first()
        if existing_player:
            print(f"⚠️  Player already exists with invite code: {invite_code}")
            print(f"   Player Name: {existing_player.player_name}")
            print(f"   Jersey: #{existing_player.jersey_number}")
            print(f"   Position: {existing_player.position}")
            print(f"   Is Linked: {existing_player.is_linked}")
            print(f"   Club: {existing_player.club.club_name}\n")

            if existing_player.is_linked:
                print("   ⚠️  This player is already linked to a user account!")
                print("   Create a new player with a different invite code if needed.\n")
        else:
            player = Player(
                club_id=club.club_id,
                player_name="Test Player",
                jersey_number=10,
                position="Forward",
                invite_code=invite_code,
                is_linked=False
            )
            db.add(player)
            db.commit()

            print(f"✅ Created incomplete player:")
            print(f"   Invite Code: {invite_code}")
            print(f"   Player Name: {player.player_name}")
            print(f"   Jersey: #{player.jersey_number}")
            print(f"   Position: {player.position}")
            print(f"   Club: {club.club_name}\n")

        # 3. Print testing instructions
        print("=" * 60)
        print("📝 TESTING INSTRUCTIONS")
        print("=" * 60)
        print("\n1️⃣  Verify Invite Code:")
        print(f"   POST http://localhost:8000/api/auth/verify-invite")
        print(f"   Body: {{'invite_code': '{invite_code}'}}")
        print("\n2️⃣  Complete Player Registration:")
        print(f"   POST http://localhost:8000/api/auth/register/player")
        print(f"   Body:")
        print(f"   {{")
        print(f"       \"invite_code\": \"{invite_code}\",")
        print(f"       \"player_name\": \"Test Player\",")
        print(f"       \"email\": \"testplayer@example.com\",")
        print(f"       \"password\": \"password123\",")
        print(f"       \"birth_date\": \"2008-03-20\",")
        print(f"       \"height\": 175")
        print(f"   }}")
        print("\n" + "=" * 60)

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_player()
