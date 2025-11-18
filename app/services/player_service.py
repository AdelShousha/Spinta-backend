"""
Player service.

This module provides player-related operations including extracting players
from StatsBomb Starting XI events and creating incomplete player records.
"""

from typing import List, Optional
from uuid import UUID
import secrets
import string
from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.opponent_player import OpponentPlayer


def generate_invite_code() -> str:
    """
    Generate a unique invite code in format XXX-#### (3 letters + 4 digits).

    Uses cryptographically secure random generation.

    Returns:
        str: Invite code (e.g., "ARG-1234")
    """
    # Generate 3 uppercase letters
    letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))

    # Generate 4 digits
    digits = ''.join(secrets.choice(string.digits) for _ in range(4))

    return f"{letters}-{digits}"


def parse_our_lineup_from_events(
    events: List[dict],
    our_club_statsbomb_team_id: int
) -> List[dict]:
    """
    Parse our team's lineup from StatsBomb Starting XI events.

    Pure processing function - no database operations.
    Extracts player data from the Starting XI event matching our team's StatsBomb ID.

    Args:
        events: Full StatsBomb events array
        our_club_statsbomb_team_id: Our club's StatsBomb team ID

    Returns:
        List of 11 players with structure:
        [
            {
                'player_name': str,
                'statsbomb_player_id': int,
                'jersey_number': int,
                'position': str
            },
            ...
        ]

    Raises:
        ValueError: If validation fails or team not found
    """
    # Step 1: Extract Starting XI events
    starting_xi_events = [e for e in events if e.get('type', {}).get('id') == 35]

    # Validation: Must have exactly 2 events
    if len(starting_xi_events) != 2:
        raise ValueError(
            f"Expected 2 Starting XI events, found {len(starting_xi_events)}"
        )

    # Step 2: Find our team's Starting XI event by team.id
    our_starting_xi = None
    for event in starting_xi_events:
        if event.get('team', {}).get('id') == our_club_statsbomb_team_id:
            our_starting_xi = event
            break

    if not our_starting_xi:
        raise ValueError(
            f"Team with StatsBomb ID {our_club_statsbomb_team_id} not found in Starting XI events"
        )

    # Step 3: Extract lineup
    lineup = our_starting_xi.get('tactics', {}).get('lineup', [])

    # Validation: Must have exactly 11 players
    if len(lineup) != 11:
        team_name = our_starting_xi.get('team', {}).get('name', 'Unknown')
        raise ValueError(
            f"Starting XI for {team_name} has {len(lineup)} players (expected 11)"
        )

    # Step 4: Parse player data
    players = []
    for player_data in lineup:
        players.append({
            'player_name': player_data['player']['name'],
            'statsbomb_player_id': player_data['player']['id'],
            'jersey_number': player_data['jersey_number'],
            'position': player_data['position']['name']  # Use name, not id
        })

    return players


def extract_our_players(
    db: Session,
    club_id: UUID,
    events: List[dict]
) -> dict:
    """
    Extract our club's players from Starting XI and create/update player records.

    Creates or updates Player records in the database:
    - For new players: Create with is_linked=False, user_id=NULL, unique invite code
    - For existing incomplete players (is_linked=False): Update jersey/position if changed
    - For existing linked players (is_linked=True): Skip (count as processed, return existing data)

    IMPORTANT: Only updates incomplete players. Linked players are never modified.
    This preserves user account integrity and invite codes that may have been shared.

    Parameter Sources:
    - club_id: Query clubs table using our_club_statsbomb_team_id from Iteration 1
    - events: StatsBomb events array from request body

    Args:
        db: Database session
        club_id: Our club's ID (UUID)
        events: StatsBomb events array

    Returns:
        {
            'players_processed': int,  # Total (created + updated + linked)
            'players_created': int,
            'players_updated': int,
            'players': [
                {
                    'player_id': UUID,
                    'player_name': str,
                    'statsbomb_player_id': int,
                    'jersey_number': int,
                    'position': str,
                    'invite_code': str
                },
                ...
            ]
        }

    Raises:
        ValueError: If club not found or validation fails
    """
    # Step 1: Get club and its StatsBomb team ID
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise ValueError(f"Club with ID {club_id} not found")

    our_club_statsbomb_team_id = club.statsbomb_team_id

    # Step 2: Parse lineup from events
    lineup = parse_our_lineup_from_events(events, our_club_statsbomb_team_id)

    # Step 3: Create or update players
    players_created = 0
    players_updated = 0
    processed_players = []

    for player_data in lineup:
        # Check if player exists by (club_id, statsbomb_player_id)
        # Note: We check ALL players (linked and incomplete) to handle both cases
        existing_player = db.query(Player).filter(
            Player.club_id == club_id,
            Player.statsbomb_player_id == player_data['statsbomb_player_id']
        ).first()

        if existing_player:
            # Player exists - check if linked or incomplete
            if existing_player.is_linked:
                # Linked player - skip update, just include in results
                processed_players.append({
                    'player_id': existing_player.player_id,
                    'player_name': existing_player.player_name,
                    'statsbomb_player_id': existing_player.statsbomb_player_id,
                    'jersey_number': existing_player.jersey_number,
                    'position': existing_player.position,
                    'invite_code': existing_player.invite_code
                })
            else:
                # Incomplete player - update jersey/position if changed
                updated = False
                if existing_player.jersey_number != player_data['jersey_number']:
                    existing_player.jersey_number = player_data['jersey_number']
                    updated = True
                if existing_player.position != player_data['position']:
                    existing_player.position = player_data['position']
                    updated = True
                # Note: We do NOT update player_name or invite_code

                if updated:
                    players_updated += 1

                db.flush()  # Ensure changes are reflected

                processed_players.append({
                    'player_id': existing_player.player_id,
                    'player_name': existing_player.player_name,
                    'statsbomb_player_id': existing_player.statsbomb_player_id,
                    'jersey_number': existing_player.jersey_number,
                    'position': existing_player.position,
                    'invite_code': existing_player.invite_code
                })

        else:
            # New player - generate invite code and create
            invite_code = generate_invite_code()
            while db.query(Player).filter(Player.invite_code == invite_code).first():
                invite_code = generate_invite_code()

            new_player = Player(
                club_id=club_id,
                player_name=player_data['player_name'],
                statsbomb_player_id=player_data['statsbomb_player_id'],
                jersey_number=player_data['jersey_number'],
                position=player_data['position'],
                invite_code=invite_code,
                is_linked=False,
                user_id=None  # NULL - incomplete player
            )

            db.add(new_player)
            db.flush()  # Get player_id without committing
            players_created += 1

            processed_players.append({
                'player_id': new_player.player_id,
                'player_name': new_player.player_name,
                'statsbomb_player_id': new_player.statsbomb_player_id,
                'jersey_number': new_player.jersey_number,
                'position': new_player.position,
                'invite_code': new_player.invite_code
            })

    # Commit all changes at once
    db.commit()

    return {
        'players_processed': len(processed_players),
        'players_created': players_created,
        'players_updated': players_updated,
        'players': processed_players
    }


def parse_opponent_lineup_from_events(
    events: List[dict],
    opponent_statsbomb_team_id: int
) -> List[dict]:
    """
    Parse opponent team's lineup from StatsBomb Starting XI events.

    Identical logic to parse_our_lineup_from_events() but for opponent team.

    Args:
        events: Full StatsBomb events array
        opponent_statsbomb_team_id: Opponent's StatsBomb team ID

    Returns:
        List of 11 players with structure:
        [
            {
                'player_name': str,
                'statsbomb_player_id': int,
                'jersey_number': int,
                'position': str
            },
            ...
        ]

    Raises:
        ValueError: If validation fails or team not found
    """
    # Reuse the same logic as our team parsing
    return parse_our_lineup_from_events(events, opponent_statsbomb_team_id)


def extract_opponent_players(
    db: Session,
    opponent_club_id: UUID,
    events: List[dict]
) -> dict:
    """
    Extract opponent team's players from Starting XI and create/update records.

    Creates or updates OpponentPlayer records:
    - If player exists (by statsbomb_player_id): Update jersey/position if changed
    - If player doesn't exist: Create new record

    Parameter Sources:
    - opponent_club_id: Output from get_or_create_opponent_club() (Iteration 2)
    - events: StatsBomb events array from request body

    Args:
        db: Database session
        opponent_club_id: Opponent club's ID (UUID)
        events: StatsBomb events array

    Returns:
        {
            'players_processed': int,  # Total (created + updated)
            'players_created': int,
            'players_updated': int,
            'players': [
                {
                    'opponent_player_id': UUID,
                    'player_name': str,
                    'statsbomb_player_id': int,
                    'jersey_number': int,
                    'position': str
                },
                ...
            ]
        }

    Raises:
        ValueError: If opponent club not found or validation fails
    """
    # Step 1: Get opponent club and its StatsBomb team ID
    opponent_club = db.query(OpponentClub).filter(
        OpponentClub.opponent_club_id == opponent_club_id
    ).first()
    if not opponent_club:
        raise ValueError(f"Opponent club with ID {opponent_club_id} not found")

    opponent_statsbomb_team_id = opponent_club.statsbomb_team_id

    # Step 2: Parse lineup from events
    lineup = parse_opponent_lineup_from_events(events, opponent_statsbomb_team_id)

    # Step 3: Create or update opponent players
    players_created = 0
    players_updated = 0
    processed_players = []

    for player_data in lineup:
        # Check if player exists by (opponent_club_id, statsbomb_player_id)
        existing_player = db.query(OpponentPlayer).filter(
            OpponentPlayer.opponent_club_id == opponent_club_id,
            OpponentPlayer.statsbomb_player_id == player_data['statsbomb_player_id']
        ).first()

        if existing_player:
            # Update jersey/position if changed
            updated = False
            if existing_player.jersey_number != player_data['jersey_number']:
                existing_player.jersey_number = player_data['jersey_number']
                updated = True
            if existing_player.position != player_data['position']:
                existing_player.position = player_data['position']
                updated = True

            if updated:
                players_updated += 1

            db.flush()  # Ensure changes are reflected

            processed_players.append({
                'opponent_player_id': existing_player.opponent_player_id,
                'player_name': existing_player.player_name,
                'statsbomb_player_id': existing_player.statsbomb_player_id,
                'jersey_number': existing_player.jersey_number,
                'position': existing_player.position
            })

        else:
            # Create new opponent player record
            new_player = OpponentPlayer(
                opponent_club_id=opponent_club_id,
                player_name=player_data['player_name'],
                statsbomb_player_id=player_data['statsbomb_player_id'],
                jersey_number=player_data['jersey_number'],
                position=player_data['position']
            )

            db.add(new_player)
            db.flush()  # Get opponent_player_id without committing
            players_created += 1

            processed_players.append({
                'opponent_player_id': new_player.opponent_player_id,
                'player_name': new_player.player_name,
                'statsbomb_player_id': new_player.statsbomb_player_id,
                'jersey_number': new_player.jersey_number,
                'position': new_player.position
            })

    # Commit all changes at once
    db.commit()

    return {
        'players_processed': len(processed_players),
        'players_created': players_created,
        'players_updated': players_updated,
        'players': processed_players
    }


# Interactive manual testing
# run python -m app.services.player_service
if __name__ == "__main__":
    import json
    import sys

    print("=" * 60)
    print("Player Lineup Parsing - Manual Test")
    print("=" * 60)

    try:
        json_file_path = input("\nEnter path to JSON file (or press Enter for default): ").strip()
        if not json_file_path:
            json_file_path = "docs/15946.json"

        team_type = input("Parse (o)ur team or (op)ponent team? [o/op]: ").strip().lower()
        if team_type not in ['o', 'op']:
            print("Error: Please enter 'o' for our team or 'op' for opponent team")
            sys.exit(1)

        team_id_input = input("Enter StatsBomb team ID: ").strip()
        if not team_id_input:
            print("Error: StatsBomb team ID is required")
            sys.exit(1)
        team_id = int(team_id_input)

        print("\n" + "-" * 60)
        print(f"Loading events from: {json_file_path}")
        print(f"Team type: {'Our Team' if team_type == 'o' else 'Opponent Team'}")
        print(f"StatsBomb team ID: {team_id}")
        print("-" * 60)

        # Load events from file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)

        print(f"✓ Loaded {len(events)} events")

        # Run function
        print("\nParsing lineup...")
        if team_type == 'o':
            lineup = parse_our_lineup_from_events(events, team_id)
        else:
            lineup = parse_opponent_lineup_from_events(events, team_id)

        # Print result
        print("\n" + "=" * 60)
        print(f"RESULT: {len(lineup)} players found")
        print("=" * 60)
        for i, player in enumerate(lineup, 1):
            print(f"{i}. {player['player_name']}")
            print(f"   StatsBomb ID: {player['statsbomb_player_id']}")
            print(f"   Jersey: #{player['jersey_number']}")
            print(f"   Position: {player['position']}")
            print()
        print("=" * 60)
        print("✓ Success!")

    except FileNotFoundError:
        print(f"\n✗ Error: File '{json_file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON in '{json_file_path}': {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
