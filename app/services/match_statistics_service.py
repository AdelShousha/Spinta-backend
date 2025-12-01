"""
Match statistics service for calculating and storing team statistics from StatsBomb data.

Provides functions to calculate match statistics (possession, shots, passes, dribbles, tackles)
and store them in the match_statistics table.
"""

from typing import List, Dict
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.match_statistics import MatchStatistics


def calculate_match_statistics_from_events(
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_statsbomb_id: int
) -> Dict[str, Dict]:
    """
    Calculate match statistics from StatsBomb events (pure processing, no database).

    This helper function processes event data to extract statistics for both teams
    including possession, shots, passes, dribbles, tackles, and defensive actions.

    Args:
        events: StatsBomb events array
        our_club_statsbomb_id: StatsBomb team ID for our club
        opponent_statsbomb_id: StatsBomb team ID for opponent

    Returns:
        {
            'our_team': {
                'possession_percentage': Decimal | None,
                'expected_goals': Decimal,
                'total_shots': int,
                'shots_on_target': int,
                'shots_off_target': int,
                'goalkeeper_saves': int,
                'total_passes': int,
                'passes_completed': int,
                'pass_completion_rate': Decimal | None,
                'passes_in_final_third': int,
                'long_passes': int,
                'crosses': int,
                'total_dribbles': int,
                'successful_dribbles': int,
                'total_tackles': int,
                'tackle_success_percentage': Decimal | None,
                'interceptions': int,
                'ball_recoveries': int
            },
            'opponent_team': { ... same structure ... }
        }

    Notes:
        - Excludes penalty shootout events (period 5)
        - Possession calculated by summing event durations
        - Goalkeeper saves count opponent's shots with outcome 100 or 116
        - Tackles only include ground tackles (duel.type contains "Tackle")
        - Ball recoveries exclude failed recoveries
        - Percentages return None if denominator is 0
    """
    # Step 1: Initialize statistics dictionaries for both teams
    our_stats = _initialize_stats_dict()
    opp_stats = _initialize_stats_dict()

    # Step 2: Filter out penalty shootout events (period 5)
    regular_events = [e for e in events if e.get('period') != 5]

    # Step 3: Calculate possession by summing event durations
    our_duration = 0.0
    opp_duration = 0.0

    for event in regular_events:
        duration = event.get('duration', 0)
        poss_team_id = event.get('possession_team', {}).get('id')

        if poss_team_id == our_club_statsbomb_id:
            our_duration += duration
        elif poss_team_id == opponent_statsbomb_id:
            opp_duration += duration

    total_duration = our_duration + opp_duration
    if total_duration > 0:
        if our_duration > 0:
            our_stats['possession_percentage'] = _to_decimal(
                (our_duration / total_duration) * 100, precision=2
            )
        if opp_duration > 0:
            opp_stats['possession_percentage'] = _to_decimal(
                (opp_duration / total_duration) * 100, precision=2
            )

    # Step 4: Process all events by type
    for event in regular_events:
        team_id = event.get('team', {}).get('id')
        event_type_id = event.get('type', {}).get('id')

        # Determine which stats dict to update
        stats = our_stats if team_id == our_club_statsbomb_id else opp_stats
        opponent_stats = opp_stats if team_id == our_club_statsbomb_id else our_stats

        # SHOT EVENTS (type.id = 16)
        if event_type_id == 16:
            shot_data = event.get('shot', {})
            outcome_id = shot_data.get('outcome', {}).get('id')
            xg = shot_data.get('statsbomb_xg', 0)

            stats['total_shots'] += 1
            stats['expected_goals'] += Decimal(str(xg))

            # On target: outcomes 97 (Goal), 100 (Saved), 116 (Saved to Post)
            if outcome_id in [97, 100, 116]:
                stats['shots_on_target'] += 1
            else:
                stats['shots_off_target'] += 1

            # Goalkeeper saves: opponent's shots with outcome 100 or 116
            if outcome_id in [100, 116]:
                opponent_stats['goalkeeper_saves'] += 1

        # PASS EVENTS (type.id = 30)
        elif event_type_id == 30:
            pass_data = event.get('pass', {})
            # CHANGE 1: Get the pass type name
            pass_type_name = pass_data.get('type', {}).get('name')
            
            # CHANGE 2: Exclude Throw-ins, Goal Kicks, and Corners
            if pass_type_name not in ["Throw-in", "Goal Kick", "Corner"]:
                stats['total_passes'] += 1
                
                # CHANGE 3: More robust completion check
                # (Matches previous analysis: count unless explicitly failed)
                outcome_name = pass_data.get('outcome', {}).get('name')
                if outcome_name is None or outcome_name not in ["Incomplete", "Out", "Pass Offside", "Unknown"]:
                    stats['passes_completed'] += 1

                # CHANGE 4: Final third uses >= 80 (inclusive of the line)
                location = event.get('location', [])
                if len(location) >= 1 and location[0] >= 80:
                    stats['passes_in_final_third'] += 1

                # Long passes: pass.length > 30
                if pass_data.get('length', 0) > 30:
                    stats['long_passes'] += 1

                # Crosses: pass.cross == True
                if pass_data.get('cross') is True:
                    stats['crosses'] += 1

        # DRIBBLE EVENTS (type.id = 14)
        elif event_type_id == 14:
            dribble_data = event.get('dribble', {})
            outcome_name = dribble_data.get('outcome', {}).get('name', '')

            stats['total_dribbles'] += 1
            if outcome_name == "Complete":
                stats['successful_dribbles'] += 1

        # DUEL EVENTS (type.id = 4) - for tackles
        elif event_type_id == 4:
            duel_data = event.get('duel', {})
            duel_type_name = duel_data.get('type', {}).get('name', '')

            # Only count ground tackles (duel.type contains 'Tackle')
            if 'Tackle' in duel_type_name:
                stats['total_tackles'] += 1

                # Check outcome ID for success (4=Won, 15=Success, 16=Success In Play, 17=Success Out)
                outcome_id = duel_data.get('outcome', {}).get('id')
                if outcome_id in [4, 15, 16, 17]:
                    stats['tackle_successes'] += 1  # Track for percentage calc

        # INTERCEPTION EVENTS (type.id = 10)
        elif event_type_id == 10:
            stats['interceptions'] += 1

        # BALL RECOVERY EVENTS (type.id = 2)
        elif event_type_id == 2:
            # Exclude failed recoveries
            recovery_failure = event.get('ball_recovery', {}).get('recovery_failure', False)
            if not recovery_failure:
                stats['ball_recoveries'] += 1

    # Step 5: Calculate percentages (handle division by zero)
    # Pass completion rate
    if our_stats['total_passes'] > 0:
        our_stats['pass_completion_rate'] = _to_decimal(
            (our_stats['passes_completed'] / our_stats['total_passes']) * 100,
            precision=2
        )

    if opp_stats['total_passes'] > 0:
        opp_stats['pass_completion_rate'] = _to_decimal(
            (opp_stats['passes_completed'] / opp_stats['total_passes']) * 100,
            precision=2
        )

    # Tackle success percentage
    if our_stats['total_tackles'] > 0:
        our_stats['tackle_success_percentage'] = _to_decimal(
            (our_stats['tackle_successes'] / our_stats['total_tackles']) * 100,
            precision=2
        )

    if opp_stats['total_tackles'] > 0:
        opp_stats['tackle_success_percentage'] = _to_decimal(
            (opp_stats['tackle_successes'] / opp_stats['total_tackles']) * 100,
            precision=2
        )

    # Remove temporary tackle_successes field
    del our_stats['tackle_successes']
    del opp_stats['tackle_successes']

    # Step 6: Return both team statistics
    return {
        'our_team': our_stats,
        'opponent_team': opp_stats
    }


def _initialize_stats_dict() -> dict:
    """Initialize statistics dictionary with default values."""
    return {
        'possession_percentage': None,
        'expected_goals': Decimal('0'),
        'total_shots': 0,
        'shots_on_target': 0,
        'shots_off_target': 0,
        'goalkeeper_saves': 0,
        'total_passes': 0,
        'passes_completed': 0,
        'pass_completion_rate': None,
        'passes_in_final_third': 0,
        'long_passes': 0,
        'crosses': 0,
        'total_dribbles': 0,
        'successful_dribbles': 0,
        'total_tackles': 0,
        'tackle_successes': 0,  # Temporary field for calculation
        'tackle_success_percentage': None,
        'interceptions': 0,
        'ball_recoveries': 0
    }


def _to_decimal(value: float, precision: int) -> Decimal:
    """Convert float to Decimal with specified precision."""
    if precision == 2:
        quantize_value = Decimal('0.01')
    elif precision == 6:
        quantize_value = Decimal('0.000001')
    else:
        quantize_value = Decimal('0.01')

    return Decimal(str(value)).quantize(quantize_value, rounding=ROUND_HALF_UP)


def insert_match_statistics(
    db: Session,
    match_id: UUID,
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_statsbomb_id: int
) -> int:
    """
    Insert match statistics into database.

    Calculates and stores aggregated statistics for both teams from StatsBomb event data.
    Creates two MatchStatistics records (one for our_team, one for opponent_team).

    Args:
        db: Database session
        match_id: Match ID (UUID)
        events: StatsBomb events array
        our_club_statsbomb_id: StatsBomb team ID for our club
        opponent_statsbomb_id: StatsBomb team ID for opponent

    Returns:
        int: Number of MatchStatistics records inserted (always 2)

    Raises:
        ValueError: If match not found
        ValueError: If statistics already exist for this match
    """
    # Step 1: Validate match exists
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise ValueError(f"Match with ID {match_id} not found")

    # Step 2: Check for duplicate statistics
    existing_stats = db.query(MatchStatistics).filter(
        MatchStatistics.match_id == match_id
    ).first()
    if existing_stats:
        raise ValueError(
            f"Statistics already exist for match {match_id}. "
            f"Delete existing records before re-inserting."
        )

    # Step 3: Calculate statistics using helper function
    stats_data = calculate_match_statistics_from_events(
        events=events,
        our_club_statsbomb_id=our_club_statsbomb_id,
        opponent_statsbomb_id=opponent_statsbomb_id
    )

    # Step 4: Create MatchStatistics records for both teams
    our_team_stats = MatchStatistics(
        match_id=match_id,
        team_type='our_team',
        possession_percentage=stats_data['our_team']['possession_percentage'],
        expected_goals=stats_data['our_team']['expected_goals'],
        total_shots=stats_data['our_team']['total_shots'],
        shots_on_target=stats_data['our_team']['shots_on_target'],
        shots_off_target=stats_data['our_team']['shots_off_target'],
        goalkeeper_saves=stats_data['our_team']['goalkeeper_saves'],
        total_passes=stats_data['our_team']['total_passes'],
        passes_completed=stats_data['our_team']['passes_completed'],
        pass_completion_rate=stats_data['our_team']['pass_completion_rate'],
        passes_in_final_third=stats_data['our_team']['passes_in_final_third'],
        long_passes=stats_data['our_team']['long_passes'],
        crosses=stats_data['our_team']['crosses'],
        total_dribbles=stats_data['our_team']['total_dribbles'],
        successful_dribbles=stats_data['our_team']['successful_dribbles'],
        total_tackles=stats_data['our_team']['total_tackles'],
        tackle_success_percentage=stats_data['our_team']['tackle_success_percentage'],
        interceptions=stats_data['our_team']['interceptions'],
        ball_recoveries=stats_data['our_team']['ball_recoveries']
    )

    opponent_team_stats = MatchStatistics(
        match_id=match_id,
        team_type='opponent_team',
        possession_percentage=stats_data['opponent_team']['possession_percentage'],
        expected_goals=stats_data['opponent_team']['expected_goals'],
        total_shots=stats_data['opponent_team']['total_shots'],
        shots_on_target=stats_data['opponent_team']['shots_on_target'],
        shots_off_target=stats_data['opponent_team']['shots_off_target'],
        goalkeeper_saves=stats_data['opponent_team']['goalkeeper_saves'],
        total_passes=stats_data['opponent_team']['total_passes'],
        passes_completed=stats_data['opponent_team']['passes_completed'],
        pass_completion_rate=stats_data['opponent_team']['pass_completion_rate'],
        passes_in_final_third=stats_data['opponent_team']['passes_in_final_third'],
        long_passes=stats_data['opponent_team']['long_passes'],
        crosses=stats_data['opponent_team']['crosses'],
        total_dribbles=stats_data['opponent_team']['total_dribbles'],
        successful_dribbles=stats_data['opponent_team']['successful_dribbles'],
        total_tackles=stats_data['opponent_team']['total_tackles'],
        tackle_success_percentage=stats_data['opponent_team']['tackle_success_percentage'],
        interceptions=stats_data['opponent_team']['interceptions'],
        ball_recoveries=stats_data['opponent_team']['ball_recoveries']
    )

    # Step 5: Add records to session
    db.add(our_team_stats)
    db.add(opponent_team_stats)

    # Step 6: Flush changes (caller manages commit)
    db.flush()

    return 2


# =============================================================================
# MANUAL TESTING CLI
# =============================================================================

if __name__ == "__main__":
    import json
    from pathlib import Path

    def _print_team_stats(stats: dict):
        """Pretty print team statistics."""
        print(f"Possession: {stats['possession_percentage'] or 'N/A'}%")
        print(f"Expected Goals (xG): {stats['expected_goals']}")
        print(f"Total Shots: {stats['total_shots']} (On Target: {stats['shots_on_target']}, Off: {stats['shots_off_target']})")
        print(f"Goalkeeper Saves: {stats['goalkeeper_saves']}")
        print(f"Passes: {stats['passes_completed']}/{stats['total_passes']} ({stats['pass_completion_rate'] or 'N/A'}%)")
        print(f"  - Final Third: {stats['passes_in_final_third']}")
        print(f"  - Long Passes: {stats['long_passes']}")
        print(f"  - Crosses: {stats['crosses']}")
        print(f"Dribbles: {stats['successful_dribbles']}/{stats['total_dribbles']} successful")
        print(f"Tackles: {stats['total_tackles']} ({stats['tackle_success_percentage'] or 'N/A'}% success)")
        print(f"Interceptions: {stats['interceptions']}")
        print(f"Ball Recoveries: {stats['ball_recoveries']}")


    print("=== Match Statistics Calculator - Manual Testing ===\n")

    # Get JSON file path
    default_path = "data/france771.json"
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

    # Get team IDs
    print("Enter StatsBomb team IDs:")
    try:
        our_club_id = int(input("  Our club StatsBomb ID (default: 779 for Argentina): ").strip() or "779")
        opponent_id = int(input("  Opponent StatsBomb ID (default: 771 for France): ").strip() or "771")
    except ValueError:
        print("✗ Error: Team IDs must be integers")
        exit(1)

    # Calculate statistics
    print("\n" + "="*70)
    try:
        stats = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=our_club_id,
            opponent_statsbomb_id=opponent_id
        )

        # Display results
        print(f"\n📊 MATCH STATISTICS")
        print("="*70)

        print("\n🔵 OUR TEAM")
        print("-" * 70)
        _print_team_stats(stats['our_team'])

        print("\n🔴 OPPONENT TEAM")
        print("-" * 70)
        _print_team_stats(stats['opponent_team'])

        print("\n" + "="*70)
        print("✓ Success!")

    except ValueError as e:
        print(f"\n✗ Error: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


