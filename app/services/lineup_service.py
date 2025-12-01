"""
Lineup service for match lineup creation.

Provides functions to create match lineup records from Starting XI events.
"""

from typing import List, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.player import Player
from app.models.opponent_player import OpponentPlayer
from app.models.match_lineup import MatchLineup


def parse_both_lineups_from_events(
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_club_statsbomb_id: int
) -> dict:
    """
    Parse both team lineups from Starting XI events (pure processing, no database).

    This is a helper function that extracts lineup data from StatsBomb events
    without database access, making it easy to test manually.

    Uses possession_team.id to identify which lineup belongs to which team.

    Args:
        events: StatsBomb events array
        our_club_statsbomb_id: Our team's StatsBomb team ID
        opponent_club_statsbomb_id: Opponent team's StatsBomb team ID

    Returns:
        {
            'our_lineup': [
                {
                    'player_name': str,
                    'statsbomb_player_id': int,
                    'jersey_number': int,
                    'position': str
                },
                ... (11 players)
            ],
            'opponent_lineup': [
                {
                    'player_name': str,
                    'statsbomb_player_id': int,
                    'jersey_number': int,
                    'position': str
                },
                ... (11 players)
            ]
        }

    Raises:
        ValueError: If validation fails (not 2 Starting XI events, not 11 players, etc.)
    """
    # Step 1: Extract Starting XI events
    starting_xi_events = [
        event for event in events
        if event.get('type', {}).get('id') == 35
    ]

    if len(starting_xi_events) != 2:
        raise ValueError(
            f"Expected 2 Starting XI events, found {len(starting_xi_events)}"
        )

    # Step 2: Identify which lineup is ours vs opponent using team.id
    our_starting_xi = None
    opponent_starting_xi = None

    for event in starting_xi_events:
        team_id = event.get('team', {}).get('id')

        if team_id == our_club_statsbomb_id:
            our_starting_xi = event
        elif team_id == opponent_club_statsbomb_id:
            opponent_starting_xi = event

    # Validate both teams found
    if our_starting_xi is None:
        raise ValueError(
            f"Team with StatsBomb ID {our_club_statsbomb_id} not found in Starting XI events"
        )
    if opponent_starting_xi is None:
        raise ValueError(
            f"Team with StatsBomb ID {opponent_club_statsbomb_id} not found in Starting XI events"
        )

    # Step 3: Extract our lineup
    our_lineup_data = our_starting_xi.get('tactics', {}).get('lineup', [])
    if len(our_lineup_data) != 11:
        raise ValueError(
            f"Our team Starting XI has {len(our_lineup_data)} players (expected 11)"
        )

    our_lineup = []
    for player_data in our_lineup_data:
        our_lineup.append({
            'player_name': player_data['player']['name'],
            'statsbomb_player_id': player_data['player']['id'],
            'jersey_number': player_data['jersey_number'],
            'position': player_data['position']['name']
        })

    # Step 4: Extract opponent lineup
    opponent_lineup_data = opponent_starting_xi.get('tactics', {}).get('lineup', [])
    if len(opponent_lineup_data) != 11:
        raise ValueError(
            f"Opponent Starting XI has {len(opponent_lineup_data)} players (expected 11)"
        )

    opponent_lineup = []
    for player_data in opponent_lineup_data:
        opponent_lineup.append({
            'player_name': player_data['player']['name'],
            'statsbomb_player_id': player_data['player']['id'],
            'jersey_number': player_data['jersey_number'],
            'position': player_data['position']['name']
        })

    return {
        'our_lineup': our_lineup,
        'opponent_lineup': opponent_lineup
    }


def create_match_lineups(
    db: Session,
    match_id: UUID,
    events: List[dict]
) -> dict:
    """
    Create match lineup records for both teams from Starting XI events.

    Creates 22 MatchLineup records (11 our_team + 11 opponent_team) by:
    1. Getting match and team IDs from database
    2. Parsing lineups from events using helper function
    3. Matching players to database IDs
    4. Creating denormalized lineup records

    Args:
        db: Database session
        match_id: Match ID (UUID)
        events: StatsBomb events array

    Returns:
        {
            'lineups_created': 22,
            'our_team_count': 11,
            'opponent_team_count': 11
        }

    Raises:
        ValueError: If validation fails (match not found, player not found, duplicates, etc.)
    """
    # Step 1: Validate match exists and get team IDs
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise ValueError(f"Match with ID {match_id} not found")

    club_id = match.club_id
    opponent_club_id = match.opponent_club_id

    # Step 2: Get StatsBomb team IDs
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise ValueError(f"Club with ID {club_id} not found")

    opponent_club = db.query(OpponentClub).filter(
        OpponentClub.opponent_club_id == opponent_club_id
    ).first()
    if not opponent_club:
        raise ValueError(f"Opponent club with ID {opponent_club_id} not found")

    our_statsbomb_id = club.statsbomb_team_id
    opponent_statsbomb_id = opponent_club.statsbomb_team_id

    # Step 3: Check for duplicate lineups
    existing_lineups = db.query(MatchLineup).filter(
        MatchLineup.match_id == match_id
    ).first()

    if existing_lineups:
        raise ValueError(f"Lineups already exist for match {match_id}")

    # Step 4: Parse both lineups using helper function
    lineups = parse_both_lineups_from_events(
        events=events,
        our_club_statsbomb_id=our_statsbomb_id,
        opponent_club_statsbomb_id=opponent_statsbomb_id
    )

    our_lineup = lineups['our_lineup']
    opponent_lineup = lineups['opponent_lineup']

    # Step 5: Process our team lineup (11 players)
    our_team_count = 0
    for player_data in our_lineup:
        # Find player in database
        player = db.query(Player).filter(
            Player.club_id == club_id,
            Player.statsbomb_player_id == player_data['statsbomb_player_id']
        ).first()

        if not player:
            raise ValueError(
                f"Player {player_data['player_name']} "
                f"(StatsBomb ID: {player_data['statsbomb_player_id']}) "
                f"not found in players table"
            )

        # Create lineup record
        lineup_entry = MatchLineup(
            match_id=match_id,
            team_type='our_team',
            player_id=player.player_id,
            opponent_player_id=None,
            player_name=player_data['player_name'],
            jersey_number=player_data['jersey_number'],
            position=player_data['position']
        )
        db.add(lineup_entry)
        our_team_count += 1

    # Step 6: Process opponent team lineup (11 players)
    opponent_team_count = 0
    for player_data in opponent_lineup:
        # Find opponent player in database
        opponent_player = db.query(OpponentPlayer).filter(
            OpponentPlayer.opponent_club_id == opponent_club_id,
            OpponentPlayer.statsbomb_player_id == player_data['statsbomb_player_id']
        ).first()

        if not opponent_player:
            raise ValueError(
                f"Opponent player {player_data['player_name']} "
                f"(StatsBomb ID: {player_data['statsbomb_player_id']}) "
                f"not found in opponent_players table"
            )

        # Create lineup record
        lineup_entry = MatchLineup(
            match_id=match_id,
            team_type='opponent_team',
            player_id=None,
            opponent_player_id=opponent_player.opponent_player_id,
            player_name=player_data['player_name'],
            jersey_number=player_data['jersey_number'],
            position=player_data['position']
        )
        db.add(lineup_entry)
        opponent_team_count += 1

    # Step 7: Validate total count
    total_count = our_team_count + opponent_team_count
    if total_count != 22:
        raise ValueError(
            f"Expected 22 lineup records, created {total_count}"
        )

    # Flush all lineup records (caller manages commit)
    db.flush()

    return {
        'lineups_created': total_count,
        'our_team_count': our_team_count,
        'opponent_team_count': opponent_team_count
    }


# Manual testing CLI
if __name__ == "__main__":
    import json
    from pathlib import Path

    print("=== Match Lineups Parser - Manual Testing ===\n")

    # Get JSON file path
    default_path = "data/3869685.json"
    json_path = input(f"Enter JSON file path (default: {default_path}): ").strip()
    if not json_path:
        json_path = default_path

    # Load events
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        print(f"✓ Loaded {len(events)} events from {json_path}\n")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {json_path}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON: {e}")
        exit(1)

    # Get our team StatsBomb ID
    our_id = input("Enter our team StatsBomb ID (e.g., 779 for Argentina): ").strip()
    try:
        our_statsbomb_id = int(our_id)
    except ValueError:
        print("✗ Error: StatsBomb ID must be an integer")
        exit(1)

    # Get opponent team StatsBomb ID
    opp_id = input("Enter opponent team StatsBomb ID (e.g., 771 for France): ").strip()
    try:
        opponent_statsbomb_id = int(opp_id)
    except ValueError:
        print("✗ Error: StatsBomb ID must be an integer")
        exit(1)

    # Parse lineups
    print("\n" + "="*60)
    try:
        result = parse_both_lineups_from_events(
            events=events,
            our_club_statsbomb_id=our_statsbomb_id,
            opponent_club_statsbomb_id=opponent_statsbomb_id
        )

        # Display our team lineup
        print(f"\n🔵 OUR TEAM LINEUP (StatsBomb ID: {our_statsbomb_id})")
        print("="*60)
        print(f"{'#':<3} {'Player Name':<35} {'SB ID':<8} {'Jersey':<8} {'Position':<20}")
        print("-"*60)
        for i, player in enumerate(result['our_lineup'], 1):
            print(f"{i:<3} {player['player_name']:<35} {player['statsbomb_player_id']:<8} "
                  f"{player['jersey_number']:<8} {player['position']:<20}")

        # Display opponent team lineup
        print(f"\n🔴 OPPONENT TEAM LINEUP (StatsBomb ID: {opponent_statsbomb_id})")
        print("="*60)
        print(f"{'#':<3} {'Player Name':<35} {'SB ID':<8} {'Jersey':<8} {'Position':<20}")
        print("-"*60)
        for i, player in enumerate(result['opponent_lineup'], 1):
            print(f"{i:<3} {player['player_name']:<35} {player['statsbomb_player_id']:<8} "
                  f"{player['jersey_number']:<8} {player['position']:<20}")

        # Summary
        print("\n" + "="*60)
        print(f"✓ Total players: {len(result['our_lineup']) + len(result['opponent_lineup'])}")
        print(f"✓ Our team: {len(result['our_lineup'])} players")
        print(f"✓ Opponent team: {len(result['opponent_lineup'])} players")

    except ValueError as e:
        print(f"\n✗ Error: {e}")
        exit(1)
