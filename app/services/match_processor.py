"""
Match Processor Service - Final Integration

Orchestrates all 12 iterations of match upload processing into a single
transactional pipeline:
1. Team Identification
2. Opponent Club Creation
3. Match Record Creation
4. Our Players Extraction
5. Opponent Players Extraction
6. Match Lineups Creation
7. Events Storage
8. Goals Extraction
9. Match Statistics
10. Player Match Statistics
11. Club Season Statistics Update
12. Player Season Statistics Update

This service is the glue that connects all previous iterations into one cohesive workflow.
"""

from uuid import UUID
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

# Import all service functions from iterations 1-12
from app.services.team_identifier import identify_teams
from app.services.opponent_service import get_or_create_opponent_club
from app.services.match_service import create_match_record
from app.services.player_service import extract_our_players, extract_opponent_players
from app.services.lineup_service import create_match_lineups
from app.services.event_service import insert_events
from app.services.goal_service import insert_goals
from app.services.match_statistics_service import insert_match_statistics
from app.services.player_match_statistics_service import insert_player_match_statistics
from app.services.club_season_statistics_service import update_club_season_statistics
from app.services.player_season_statistics_service import update_player_season_statistics

from app.models.coach import Coach


def process_match_upload(
    db: Session,
    coach_id: UUID,
    match_data: dict
) -> dict:
    """
    Process a match upload by orchestrating all 12 iterations.

    This function chains together all 12 iterations of match processing with
    proper transaction management, error handling, and rollback capabilities.

    Args:
        db: SQLAlchemy database session
        coach_id: UUID of the coach (from JWT token)
        match_data: Dictionary with keys:
            - opponent_name: str (required)
            - opponent_logo_url: str (optional)
            - match_date: str (YYYY-MM-DD format, required)
            - our_score: int (required, >= 0)
            - opponent_score: int (required, >= 0)
            - statsbomb_events: List[dict] (required, StatsBomb events)

    Returns:
        dict: Processing results with structure {
            'success': True,
            'match_id': str (UUID as string),
            'summary': {...counts...},
            'details': {...player lists...}
        }

    Raises:
        ValueError: If validation fails or any iteration fails
    """
    try:
        # =================================================================
        # STEP 0: Input Validation
        # =================================================================
        _validate_inputs(coach_id, match_data)

        # =================================================================
        # STEP 1: Coach & Club Lookup
        # =================================================================
        coach, club, club_id, club_name, club_statsbomb_team_id = \
            _get_coach_and_club(db, coach_id)

        # =================================================================
        # STEP 2: Extract Match Data
        # =================================================================
        opponent_name, opponent_logo_url, match_date, our_score, opponent_score, events = \
            _extract_match_data(match_data)

        # =================================================================
        # ITERATION 1: Team Identification
        # =================================================================
        try:
            team_result = identify_teams(
                club_name=club_name,
                events=events,
                club_statsbomb_team_id=club_statsbomb_team_id
            )
        except ValueError as e:
            raise ValueError(f"Iteration 1 (Team Identification) failed: {e}")

        our_club_statsbomb_team_id = team_result['our_club_statsbomb_team_id']
        opponent_statsbomb_team_id = team_result['opponent_statsbomb_team_id']
        should_update_statsbomb_id = team_result['should_update_statsbomb_id']
        new_statsbomb_team_id = team_result['new_statsbomb_team_id']

        # Update club.statsbomb_team_id if first match
        if should_update_statsbomb_id and new_statsbomb_team_id:
            club.statsbomb_team_id = new_statsbomb_team_id
            db.flush()

        # =================================================================
        # ITERATION 2: Opponent Club
        # =================================================================
        try:
            opponent_club_id = get_or_create_opponent_club(
                db=db,
                opponent_statsbomb_team_id=opponent_statsbomb_team_id,
                opponent_name=opponent_name,
                logo_url=opponent_logo_url
            )
        except Exception as e:
            raise ValueError(f"Iteration 2 (Opponent Club) failed: {e}")

        # =================================================================
        # ITERATION 3: Match Record
        # =================================================================
        try:
            match_id = create_match_record(
                db=db,
                club_id=club_id,
                opponent_club_id=opponent_club_id,
                match_date=match_date,
                our_score=our_score,
                opponent_score=opponent_score,
                opponent_name=opponent_name,
                events=events
            )
        except ValueError as e:
            raise ValueError(f"Iteration 3 (Match Record) failed: {e}")

        # =================================================================
        # ITERATION 4: Our Players
        # =================================================================
        try:
            our_players_result = extract_our_players(
                db=db,
                club_id=club_id,
                events=events
            )
        except ValueError as e:
            raise ValueError(f"Iteration 4 (Our Players) failed: {e}")

        # CRITICAL: Extract player_ids for Iteration 12
        player_ids = [p['player_id'] for p in our_players_result['players']]

        # =================================================================
        # ITERATION 5: Opponent Players
        # =================================================================
        try:
            opponent_players_result = extract_opponent_players(
                db=db,
                opponent_club_id=opponent_club_id,
                events=events
            )
        except ValueError as e:
            raise ValueError(f"Iteration 5 (Opponent Players) failed: {e}")

        # =================================================================
        # ITERATION 6: Match Lineups
        # =================================================================
        try:
            lineups_result = create_match_lineups(
                db=db,
                match_id=match_id,
                events=events
            )
        except ValueError as e:
            raise ValueError(f"Iteration 6 (Match Lineups) failed: {e}")

        # =================================================================
        # ITERATION 7: Events
        # =================================================================
        try:
            events_count = insert_events(
                db=db,
                match_id=match_id,
                events=events
            )
        except ValueError as e:
            raise ValueError(f"Iteration 7 (Events) failed: {e}")

        # =================================================================
        # ITERATION 8: Goals
        # =================================================================
        try:
            goals_count = insert_goals(
                db=db,
                match_id=match_id,
                events=events,
                our_club_statsbomb_id=our_club_statsbomb_team_id,
                opponent_statsbomb_id=opponent_statsbomb_team_id
            )
        except ValueError as e:
            raise ValueError(f"Iteration 8 (Goals) failed: {e}")

        # =================================================================
        # ITERATION 9: Match Statistics
        # =================================================================
        try:
            match_stats_count = insert_match_statistics(
                db=db,
                match_id=match_id,
                events=events,
                our_club_statsbomb_id=our_club_statsbomb_team_id,
                opponent_statsbomb_id=opponent_statsbomb_team_id
            )
        except ValueError as e:
            raise ValueError(f"Iteration 9 (Match Statistics) failed: {e}")

        # =================================================================
        # ITERATION 10: Player Match Statistics
        # =================================================================
        try:
            player_stats_count = insert_player_match_statistics(
                db=db,
                match_id=match_id,
                events=events,
                our_club_statsbomb_id=our_club_statsbomb_team_id,
                opponent_statsbomb_id=opponent_statsbomb_team_id
            )
        except ValueError as e:
            raise ValueError(f"Iteration 10 (Player Match Statistics) failed: {e}")

        # =================================================================
        # ITERATION 11: Club Season Statistics
        # =================================================================
        try:
            club_stats_updated = update_club_season_statistics(
                db=db,
                club_id=club_id
            )
        except Exception as e:
            raise ValueError(f"Iteration 11 (Club Season Statistics) failed: {e}")

        # =================================================================
        # ITERATION 12: Player Season Statistics
        # =================================================================
        try:
            player_season_count = update_player_season_statistics(
                db=db,
                player_ids=player_ids  # From Iteration 4
            )
        except Exception as e:
            raise ValueError(f"Iteration 12 (Player Season Statistics) failed: {e}")

        # =================================================================
        # COMMIT ALL CHANGES AT ONCE
        # =================================================================
        db.commit()

        # =================================================================
        # Build and return success response
        # =================================================================
        return _build_success_response(
            match_id, opponent_club_id, team_result,
            our_players_result, opponent_players_result, lineups_result,
            events_count, goals_count, match_stats_count, player_stats_count,
            club_stats_updated, player_season_count
        )

    except ValueError as e:
        # Rollback on validation or iteration failures
        db.rollback()
        raise  # Re-raise with original message

    except Exception as e:
        # Rollback on unexpected errors
        db.rollback()
        raise ValueError(f"Unexpected error during match processing: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _validate_inputs(coach_id: UUID, match_data: dict) -> None:
    """
    Validate inputs before processing.

    Args:
        coach_id: UUID of the coach
        match_data: Match data dictionary

    Raises:
        ValueError: If any validation fails
    """
    required = ['opponent_name', 'match_date', 'our_score', 'opponent_score', 'statsbomb_events']
    for field in required:
        if field not in match_data:
            raise ValueError(f"Missing required field: {field}")

    # Validate date format
    try:
        datetime.strptime(match_data['match_date'], '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {match_data['match_date']}. Expected YYYY-MM-DD")

    # Validate scores
    if match_data['our_score'] < 0 or match_data['opponent_score'] < 0:
        raise ValueError("Scores cannot be negative")

    # Validate events
    if not isinstance(match_data['statsbomb_events'], list) or len(match_data['statsbomb_events']) == 0:
        raise ValueError("statsbomb_events must be a non-empty list")


def _get_coach_and_club(db: Session, coach_id: UUID) -> tuple:
    """
    Get coach and club, raise error if not found.

    Args:
        db: Database session
        coach_id: UUID of the coach

    Returns:
        Tuple of (coach, club, club_id, club_name, statsbomb_team_id)

    Raises:
        ValueError: If coach not found or doesn't have a club
    """
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise ValueError(f"Coach with ID {coach_id} not found")

    club = coach.club
    if not club:
        raise ValueError(f"Coach {coach_id} does not have a club")

    return coach, club, club.club_id, club.club_name, club.statsbomb_team_id


def _extract_match_data(match_data: dict) -> tuple:
    """
    Extract match data from input dictionary.

    Args:
        match_data: Input dictionary

    Returns:
        Tuple of (opponent_name, opponent_logo_url, match_date, our_score, opponent_score, events)
    """
    opponent_name = match_data['opponent_name']
    opponent_logo_url = match_data.get('opponent_logo_url') or None
    match_date = match_data['match_date']
    our_score = match_data['our_score']
    opponent_score = match_data['opponent_score']
    events = match_data['statsbomb_events']

    return opponent_name, opponent_logo_url, match_date, our_score, opponent_score, events


def _build_success_response(
    match_id: UUID,
    opponent_club_id: UUID,
    team_result: dict,
    our_players_result: dict,
    opponent_players_result: dict,
    lineups_result: dict,
    events_count: int,
    goals_count: int,
    match_stats_count: int,
    player_stats_count: int,
    club_stats_updated: bool,
    player_season_count: int
) -> dict:
    """
    Build success response with all results.

    Args:
        All result values from the 12 iterations

    Returns:
        Formatted response dictionary
    """
    return {
        'success': True,
        'match_id': str(match_id),
        'summary': {
            'opponent_club_id': str(opponent_club_id),
            'our_players_processed': our_players_result['players_processed'],
            'our_players_created': our_players_result['players_created'],
            'our_players_updated': our_players_result['players_updated'],
            'opponent_players_processed': opponent_players_result['players_processed'],
            'opponent_players_created': opponent_players_result['players_created'],
            'opponent_players_updated': opponent_players_result['players_updated'],
            'lineups_created': lineups_result['lineups_created'],
            'events_inserted': events_count,
            'goals_inserted': goals_count,
            'match_statistics_created': match_stats_count,
            'player_statistics_created': player_stats_count,
            'club_statistics_updated': club_stats_updated,
            'player_season_statistics_updated': player_season_count
        },
        'details': {
            'team_identification': {
                'our_club_statsbomb_team_id': team_result['our_club_statsbomb_team_id'],
                'opponent_statsbomb_team_id': team_result['opponent_statsbomb_team_id'],
                'club_statsbomb_id_updated': team_result['should_update_statsbomb_id']
            },
            'our_players': [
                {
                    'player_id': str(p['player_id']),
                    'player_name': p['player_name'],
                    'jersey_number': p['jersey_number'],
                    'position': p['position'],
                    'invite_code': p['invite_code']
                }
                for p in our_players_result['players']
            ],
            'opponent_players': [
                {
                    'player_id': str(p['opponent_player_id']),  # opponent_player_id, not player_id
                    'player_name': p['player_name'],
                    'jersey_number': p['jersey_number'],
                    'position': p['position']
                }
                for p in opponent_players_result['players']
            ]
        }
    }


# =============================================================================
# CLI FOR MANUAL DATA ENTRY
# =============================================================================

if __name__ == "__main__":
    import json
    import sys
    from app.database import SessionLocal  # Real database connection
    from app.core.security import decode_access_token

    print("=" * 70)
    print("Match Processor - Manual Data Entry")
    print("=" * 70)

    # STEP 1: Authenticate with JWT
    print("\n[Authentication]")
    jwt_token = input("Enter your JWT token: ").strip()

    # Decode JWT to get user_id
    payload = decode_access_token(jwt_token)
    if not payload:
        print("✗ Invalid or expired JWT token")
        sys.exit(1)

    user_id = payload.get('user_id')
    if not user_id:
        print("✗ JWT token missing user_id")
        sys.exit(1)

    print(f"✓ Authenticated as user: {user_id}")

    # STEP 2: Get coach from database
    db = SessionLocal()
    try:
        coach = db.query(Coach).filter(Coach.user_id == UUID(user_id)).first()
        if not coach:
            print(f"✗ No coach found for user {user_id}")
            sys.exit(1)

        if not coach.club:
            print(f"✗ Coach {coach.coach_id} does not have a club")
            sys.exit(1)

        print(f"✓ Coach found: {coach.coach_id}")
        print(f"✓ Club: {coach.club.club_name}")

        # STEP 3: Load events from JSON file
        print("\n[Match Data]")
        json_file = input("Enter JSON file path (default: data/3869685.json): ").strip()
        if not json_file:
            json_file = "data/3869685.json"

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            print(f"✓ Loaded {len(events)} events from {json_file}\n")
        except Exception as e:
            print(f"✗ Error loading file: {e}")
            sys.exit(1)

        # STEP 4: Get match details
        print("Enter match details:")
        opponent_name = input("  Opponent name: ").strip()
        opponent_logo_url = input("  Opponent logo URL (optional): ").strip() or None
        match_date = input("  Match date (YYYY-MM-DD): ").strip()

        try:
            our_score = int(input("  Our score: "))
            opponent_score = int(input("  Opponent score: "))
        except ValueError:
            print("✗ Scores must be integers")
            sys.exit(1)

        # STEP 5: Build match_data
        match_data = {
            'opponent_name': opponent_name,
            'opponent_logo_url': opponent_logo_url,
            'match_date': match_date,
            'our_score': our_score,
            'opponent_score': opponent_score,
            'statsbomb_events': events
        }

        # STEP 6: Process match
        print("\n" + "=" * 70)
        print("Processing match through all 12 iterations...")
        print("=" * 70)

        result = process_match_upload(db, coach.coach_id, match_data)

        # STEP 7: Display results
        print("\n" + "=" * 70)
        print("✓ SUCCESS!")
        print("=" * 70)
        print(f"\nMatch ID: {result['match_id']}")
        print("\nSummary:")
        for key, val in result['summary'].items():
            print(f"  • {key}: {val}")

        print("\nTeam Identification:")
        for key, val in result['details']['team_identification'].items():
            print(f"  • {key}: {val}")

        print(f"\nOur Players: {len(result['details']['our_players'])} players")
        print(f"Opponent Players: {len(result['details']['opponent_players'])} players")

    except ValueError as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
