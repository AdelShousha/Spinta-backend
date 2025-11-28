"""
Player Match Statistics Service.

Calculates and stores individual player statistics from StatsBomb events.
Only tracks our team's starting 11 players (no opponent players, no substitutes).
"""

from typing import List, Dict
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.match_lineup import MatchLineup
from app.models.match import Match


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _initialize_player_stats_dict() -> Dict:
    """
    Initialize a player statistics dictionary with default values.

    Returns:
        Dict with all 17 statistics initialized to 0 or None.
    """
    return {
        # Required fields (default 0)
        'goals': 0,
        'assists': 0,

        # Optional statistics (initialized to 0 for counting)
        'expected_goals': Decimal('0.00'),
        'shots': 0,
        'shots_on_target': 0,
        'total_dribbles': 0,
        'successful_dribbles': 0,
        'total_passes': 0,
        'completed_passes': 0,
        'short_passes': 0,
        'long_passes': 0,
        'final_third_passes': 0,
        'crosses': 0,
        'tackles': 0,
        'tackle_successes': 0,  # Temporary for calculation
        'tackle_success_rate': None,
        'interceptions': 0,
        'interception_successes': 0,  # Temporary for calculation
        'interception_success_rate': None,
    }


def _to_decimal(value: float, precision: int = 6) -> Decimal:
    """
    Convert float to Decimal with specified precision.

    Args:
        value: Float value to convert
        precision: Number of decimal places (default 6 for xG, 2 for percentages)

    Returns:
        Decimal value rounded to precision
    """
    if precision == 2:
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    elif precision == 6:
        return Decimal(str(value)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    else:
        return Decimal(str(value))


# =============================================================================
# PURE PROCESSING FUNCTION (MANUALLY TESTABLE)
# =============================================================================

def calculate_player_match_statistics_from_events(
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_statsbomb_id: int
) -> Dict[int, Dict]:
    """
    Calculate player statistics from StatsBomb events.

    This is a pure processing function that can be tested manually without a database.

    Args:
        events: StatsBomb events array
        our_club_statsbomb_id: StatsBomb team ID for our club
        opponent_statsbomb_id: StatsBomb team ID for opponent

    Returns:
        Dict keyed by statsbomb_player_id with statistics:
        {
            5503: {  # Messi's statsbomb_player_id
                'goals': 2,
                'assists': 1,
                'expected_goals': Decimal('1.8'),
                'shots': 5,
                'shots_on_target': 3,
                'total_dribbles': 8,
                'successful_dribbles': 6,
                'total_passes': 45,
                'completed_passes': 38,
                'short_passes': 30,
                'long_passes': 15,
                'final_third_passes': 12,
                'crosses': 3,
                'tackles': 2,
                'tackle_success_rate': Decimal('50.00'),
                'interceptions': 1,
                'interception_success_rate': Decimal('100.00')
            },
            ...
        }

    Notes:
        - Only includes our team's players (filters by team_id)
        - Excludes penalty shootout events (period 5)
        - Returns empty dict if no events for our players
    """
    # Dictionary to store statistics per player: {statsbomb_player_id: stats_dict}
    player_stats: Dict[int, Dict] = {}

    for event in events:
        # Exclude penalty shootout events (period 5)
        period = event.get('period')
        if period == 5:
            continue

        # Only process events from our team
        team_id = event.get('team', {}).get('id')
        if team_id != our_club_statsbomb_id:
            continue

        # Get player ID from event
        player_id = event.get('player', {}).get('id')
        if player_id is None:
            continue  # Some events don't have player attribution

        # Initialize player stats if first time seeing this player
        if player_id not in player_stats:
            player_stats[player_id] = _initialize_player_stats_dict()

        # Get event type
        event_type_id = event.get('type', {}).get('id')

        # =============================================================================
        # Process events by type
        # =============================================================================

        # 1. SHOT EVENTS (Type 16)
        if event_type_id == 16:
            shot_data = event.get('shot', {})
            outcome_id = shot_data.get('outcome', {}).get('id')

            # Count total shots
            player_stats[player_id]['shots'] += 1

            # Sum expected goals (xG)
            xg = shot_data.get('statsbomb_xg', 0)
            player_stats[player_id]['expected_goals'] += _to_decimal(xg, precision=6)

            # Count goals (outcome 97)
            if outcome_id == 97:
                player_stats[player_id]['goals'] += 1

            # Count shots on target (outcomes: 97=Goal, 100=Saved, 116=Saved to Post)
            if outcome_id in [97, 100, 116]:
                player_stats[player_id]['shots_on_target'] += 1

        # 2. PASS EVENTS (Type 30)
        elif event_type_id == 30:
            pass_data = event.get('pass', {})

            # Check if this is a set piece (exclude from pass counts)
            pass_type_name = pass_data.get('type', {}).get('name')
            is_set_piece = pass_type_name in ["Throw-in", "Goal Kick", "Corner"]

            # Count assists (pass.goal_assist = True)
            if pass_data.get('goal_assist') is True:
                player_stats[player_id]['assists'] += 1

            # Process non-set-piece passes
            if not is_set_piece:
                # Count total passes
                player_stats[player_id]['total_passes'] += 1

                # Check pass completion
                # Completed: outcome is None or not in failure list
                outcome_name = pass_data.get('outcome', {}).get('name')
                if outcome_name is None or outcome_name not in ["Incomplete", "Out", "Pass Offside", "Unknown"]:
                    player_stats[player_id]['completed_passes'] += 1

                # Categorize by length
                pass_length = pass_data.get('length', 0)
                if pass_length <= 30:
                    player_stats[player_id]['short_passes'] += 1
                else:
                    player_stats[player_id]['long_passes'] += 1

                # Check if final third pass (location[0] >= 80)
                location = event.get('location', [0, 0])
                if len(location) >= 1 and location[0] >= 80:
                    player_stats[player_id]['final_third_passes'] += 1

                # Count crosses
                if pass_data.get('cross') is True:
                    player_stats[player_id]['crosses'] += 1

        # 3. DRIBBLE EVENTS (Type 14)
        elif event_type_id == 14:
            dribble_data = event.get('dribble', {})
            outcome_name = dribble_data.get('outcome', {}).get('name')

            player_stats[player_id]['total_dribbles'] += 1

            if outcome_name == "Complete":
                player_stats[player_id]['successful_dribbles'] += 1

        # 4. DUEL EVENTS (Type 4) - for Tackles
        elif event_type_id == 4:
            duel_data = event.get('duel', {})
            duel_type_name = duel_data.get('type', {}).get('name', '')
            outcome_id = duel_data.get('outcome', {}).get('id')

            # Only count tackles (duel type contains "Tackle")
            if 'Tackle' in duel_type_name:
                player_stats[player_id]['tackles'] += 1

                # Check tackle success (outcome IDs: 4=Won, 15=Success, 16=Success In Play, 17=Success Out)
                if outcome_id in [4, 15, 16, 17]:
                    player_stats[player_id]['tackle_successes'] += 1

        # 5. INTERCEPTION EVENTS (Type 10)
        elif event_type_id == 10:
            player_stats[player_id]['interceptions'] += 1

            # Check interception success (same IDs as tackles: 4, 15, 16, 17)
            interception_data = event.get('interception', {})
            outcome_id = interception_data.get('outcome', {}).get('id')

            if outcome_id in [4, 15, 16, 17]:
                player_stats[player_id]['interception_successes'] += 1

    # =============================================================================
    # Calculate percentage rates for all players
    # =============================================================================

    for player_id, stats in player_stats.items():
        # Calculate tackle success rate
        if stats['tackles'] > 0:
            success_rate = (stats['tackle_successes'] / stats['tackles']) * 100
            stats['tackle_success_rate'] = _to_decimal(success_rate, precision=2)

        # Calculate interception success rate
        if stats['interceptions'] > 0:
            success_rate = (stats['interception_successes'] / stats['interceptions']) * 100
            stats['interception_success_rate'] = _to_decimal(success_rate, precision=2)

        # Remove temporary fields
        del stats['tackle_successes']
        del stats['interception_successes']

    return player_stats


# =============================================================================
# DATABASE FUNCTION
# =============================================================================

def insert_player_match_statistics(
    db: Session,
    match_id: UUID,
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_statsbomb_id: int
) -> int:
    """
    Insert player match statistics for our team's starting 11.

    Queries match_lineups to get our team's players, calculates stats,
    and inserts records into player_match_statistics table.

    Args:
        db: Database session
        match_id: Match ID (UUID)
        events: StatsBomb events array
        our_club_statsbomb_id: StatsBomb team ID for our club
        opponent_statsbomb_id: StatsBomb team ID for opponent

    Returns:
        Number of player records inserted (typically 11 for starting lineup)

    Raises:
        ValueError: If match not found
        ValueError: If statistics already exist for this match

    Processing:
        1. Validate match exists
        2. Check for duplicate statistics
        3. Query MatchLineup for our_team players (team_type='our_team')
        4. Build mapping: player_id → statsbomb_player_id
        5. Calculate statistics using helper function
        6. Map statsbomb_player_id back to player_id
        7. Insert PlayerMatchStatistics records (only for starting 11)
        8. Commit transaction
    """
    # 1. Validate match exists
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise ValueError(f"Match with ID {match_id} not found")

    # 2. Check for duplicate statistics
    existing_stats = db.query(PlayerMatchStatistics).filter(
        PlayerMatchStatistics.match_id == match_id
    ).first()
    if existing_stats:
        raise ValueError(f"Player statistics already exist for match {match_id}")

    # 3. Query MatchLineup for our team's starting 11 (with Player join to get statsbomb_player_id)
    from app.models.player import Player

    our_lineup = db.query(MatchLineup, Player).join(
        Player, MatchLineup.player_id == Player.player_id
    ).filter(
        MatchLineup.match_id == match_id,
        MatchLineup.team_type == 'our_team'
    ).all()

    if not our_lineup:
        # No lineup data means no stats to insert
        return 0

    # 4. Build mapping: player_id (UUID) → statsbomb_player_id (int)
    player_id_to_statsbomb_id = {
        player.player_id: player.statsbomb_player_id
        for lineup, player in our_lineup
    }

    # Also build reverse mapping: statsbomb_player_id → player_id
    statsbomb_id_to_player_id = {
        player.statsbomb_player_id: player.player_id
        for lineup, player in our_lineup
        if player.statsbomb_player_id is not None  # Some players might not have statsbomb_player_id
    }

    # 5. Calculate statistics using helper function
    player_stats = calculate_player_match_statistics_from_events(
        events=events,
        our_club_statsbomb_id=our_club_statsbomb_id,
        opponent_statsbomb_id=opponent_statsbomb_id
    )

    # 6. Map statsbomb_player_id back to player_id and insert records
    inserted_count = 0

    for statsbomb_player_id, stats in player_stats.items():
        # Only insert for players in our starting lineup
        if statsbomb_player_id not in statsbomb_id_to_player_id:
            continue

        player_id = statsbomb_id_to_player_id[statsbomb_player_id]

        # Create PlayerMatchStatistics record
        player_match_stats = PlayerMatchStatistics(
            player_id=player_id,
            match_id=match_id,
            goals=stats['goals'],
            assists=stats['assists'],
            expected_goals=stats['expected_goals'] if stats['expected_goals'] > 0 else None,
            shots=stats['shots'] if stats['shots'] > 0 else None,
            shots_on_target=stats['shots_on_target'] if stats['shots_on_target'] > 0 else None,
            total_dribbles=stats['total_dribbles'] if stats['total_dribbles'] > 0 else None,
            successful_dribbles=stats['successful_dribbles'] if stats['successful_dribbles'] > 0 else None,
            total_passes=stats['total_passes'] if stats['total_passes'] > 0 else None,
            completed_passes=stats['completed_passes'] if stats['completed_passes'] > 0 else None,
            short_passes=stats['short_passes'] if stats['short_passes'] > 0 else None,
            long_passes=stats['long_passes'] if stats['long_passes'] > 0 else None,
            final_third_passes=stats['final_third_passes'] if stats['final_third_passes'] > 0 else None,
            crosses=stats['crosses'] if stats['crosses'] > 0 else None,
            tackles=stats['tackles'] if stats['tackles'] > 0 else None,
            tackle_success_rate=stats['tackle_success_rate'],
            interceptions=stats['interceptions'] if stats['interceptions'] > 0 else None,
            interception_success_rate=stats['interception_success_rate']
        )

        db.add(player_match_stats)
        inserted_count += 1

    # 7. Commit transaction
    db.commit()

    return inserted_count


# =============================================================================
# MANUAL TESTING CLI
# =============================================================================

if __name__ == "__main__":
    """
    Manual testing CLI for calculate_player_match_statistics_from_events().

    This allows testing the calculation logic without needing a database.
    Useful for verifying statistics are calculated correctly from StatsBomb events.

    Usage:
        python -m app.services.player_match_statistics_service <events_json_file>

    Example:
        python -m app.services.player_match_statistics_service data/events/7478.json
    """
    import json
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.player_match_statistics_service <events_json_file>")
        print("Example: python -m app.services.player_match_statistics_service data/events/7478.json")
        sys.exit(1)

    events_file = sys.argv[1]

    # Load events from JSON file
    print(f"\nLoading events from: {events_file}")
    try:
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {events_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        sys.exit(1)

    print(f"Loaded {len(events)} events")

    # Get team IDs from user
    print("\n" + "="*80)
    print("TEAM IDENTIFICATION")
    print("="*80)
    our_team_id = int(input("Enter our club's StatsBomb team ID (e.g., 217 for Barcelona): "))
    opponent_id = int(input("Enter opponent's StatsBomb team ID (e.g., 206 for Alavés): "))

    # Build player name mapping from events
    print("\n" + "="*80)
    print("EXTRACTING PLAYER NAMES")
    print("="*80)
    player_names = {}
    for event in events:
        player_data = event.get('player', {})
        player_id = player_data.get('id')
        player_name = player_data.get('name')
        if player_id and player_name and player_id not in player_names:
            player_names[player_id] = player_name
    print(f"Found {len(player_names)} unique players in events")

    # Calculate player statistics
    print("\n" + "="*80)
    print("CALCULATING PLAYER STATISTICS")
    print("="*80)
    player_stats = calculate_player_match_statistics_from_events(
        events=events,
        our_club_statsbomb_id=our_team_id,
        opponent_statsbomb_id=opponent_id
    )

    # Display results
    print(f"\nFound statistics for {len(player_stats)} players from our team:")
    print("\n" + "="*80)
    print("PLAYER MATCH STATISTICS")
    print("="*80)

    if not player_stats:
        print("No player statistics calculated (no events for our team's players)")
    else:
        for statsbomb_player_id, stats in player_stats.items():
            # Get player name
            player_name = player_names.get(statsbomb_player_id, "Unknown Player")

            print(f"\n{player_name} (StatsBomb ID: {statsbomb_player_id})")
            print("-" * 80)

            # Goals and Assists (required fields - always show)
            print(f"  Goals:                        {stats['goals']}")
            print(f"  Assists:                      {stats['assists']}")

            # Shooting statistics (always show all fields)
            print(f"  Expected Goals (xG):          {stats['expected_goals'] or 0}")
            print(f"  Shots:                        {stats['shots'] or 0}")
            print(f"  Shots on Target:              {stats['shots_on_target'] or 0}")

            # Passing statistics (always show all fields)
            print(f"  Total Passes:                 {stats['total_passes'] or 0}")
            print(f"  Completed Passes:             {stats['completed_passes'] or 0}")
            print(f"  Short Passes (≤30m):          {stats['short_passes'] or 0}")
            print(f"  Long Passes (>30m):           {stats['long_passes'] or 0}")
            print(f"  Final Third Passes:           {stats['final_third_passes'] or 0}")
            print(f"  Crosses:                      {stats['crosses'] or 0}")

            # Dribbling statistics (always show all fields)
            print(f"  Total Dribbles:               {stats['total_dribbles'] or 0}")
            print(f"  Successful Dribbles:          {stats['successful_dribbles'] or 0}")

            # Defensive statistics (always show all fields)
            print(f"  Tackles:                      {stats['tackles'] or 0}")
            if stats['tackle_success_rate'] is not None:
                print(f"  Tackle Success Rate:          {stats['tackle_success_rate']}%")
            else:
                print(f"  Tackle Success Rate:          N/A")

            print(f"  Interceptions:                {stats['interceptions'] or 0}")
            if stats['interception_success_rate'] is not None:
                print(f"  Interception Success Rate:    {stats['interception_success_rate']}%")
            else:
                print(f"  Interception Success Rate:    N/A")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total events processed:         {len(events)}")
    print(f"Players with statistics:        {len(player_stats)}")
    print(f"Events excluded (period 5):     {sum(1 for e in events if e.get('period') == 5)}")
    print("="*80)
