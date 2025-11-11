"""
Coach/Admin Routes

These routes handle coach-specific operations including match upload
and processing of StatsBomb event data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
import difflib
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player
from app.schemas.match import (
    MatchUploadRequest,
    MatchUploadResponse,
    MatchUploadSummary,
    NewPlayerInfo
)
from app.crud import (
    opponent_club as opponent_club_crud,
    opponent_player as opponent_player_crud,
    match as match_crud,
    goal as goal_crud,
    event as event_crud,
    match_statistics as match_statistics_crud,
    player_match_statistics as player_match_statistics_crud,
    club_season_statistics as club_season_statistics_crud,
    player_season_statistics as player_season_statistics_crud,
    club as club_crud
)

router = APIRouter()


def get_current_coach(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Coach:
    """
    Dependency to get current authenticated coach.

    Verifies that the current user is a coach and retrieves the coach record.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Coach instance

    Raises:
        HTTPException 403: If user is not a coach
        HTTPException 404: If coach record not found
    """
    if current_user.user_type != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can access this endpoint"
        )

    coach = db.query(Coach).filter(Coach.user_id == current_user.user_id).first()
    if not coach:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach record not found"
        )

    return coach


def match_team_name(club_name: str, team1_name: str, team2_name: str) -> Optional[int]:
    """
    Fuzzy match club name to one of two team names from StatsBomb data.

    Uses exact matching, substring matching, and fuzzy matching with 80% threshold.

    Args:
        club_name: Our club name from database
        team1_name: First team name from StatsBomb data
        team2_name: Second team name from StatsBomb data

    Returns:
        1 if club matches team1, 2 if club matches team2, None if no match

    Example:
        >>> match_team_name("Thunder United", "Thunder United FC", "City Strikers")
        1
    """
    club_lower = club_name.lower()
    team1_lower = team1_name.lower()
    team2_lower = team2_name.lower()

    # Try exact match first
    if club_lower == team1_lower:
        return 1
    if club_lower == team2_lower:
        return 2

    # Try substring match (handles "Thunder United" vs "Thunder United FC")
    if club_lower in team1_lower or team1_lower in club_lower:
        return 1
    if club_lower in team2_lower or team2_lower in club_lower:
        return 2

    # Try fuzzy match with 80% similarity threshold
    sim1 = difflib.SequenceMatcher(None, club_lower, team1_lower).ratio()
    sim2 = difflib.SequenceMatcher(None, club_lower, team2_lower).ratio()

    if sim1 > 0.8 and sim1 > sim2:
        return 1
    if sim2 > 0.8:
        return 2

    return None


def generate_invite_code(db: Session, player_name: str) -> str:
    """
    Generate unique invite code for player signup.

    Format: XXX-NNNN (3 letters from name + 4 random digits)

    Args:
        db: Database session
        player_name: Player full name

    Returns:
        Unique invite code (e.g., "MRC-1827")

    Example:
        >>> generate_invite_code(db, "Marcus Silva")
        "MRS-1827"
    """
    # Extract prefix from name
    parts = player_name.split()
    if len(parts) >= 2:
        prefix = (parts[0][0] + parts[-1][:2]).upper()
    else:
        prefix = player_name[:3].upper()

    # Generate unique code
    max_attempts = 100
    for _ in range(max_attempts):
        digits = ''.join(secrets.choice(string.digits) for _ in range(4))
        code = f"{prefix}-{digits}"

        # Check uniqueness
        existing = db.query(Player).filter(Player.invite_code == code).first()
        if not existing:
            return code

    # Fallback if max attempts reached (very unlikely)
    raise ValueError("Could not generate unique invite code after 100 attempts")


def calculate_team_statistics(
    db: Session,
    match_id: str,
    team_name: str
) -> Dict[str, Any]:
    """
    Calculate team statistics from events for a specific match and team.

    Args:
        db: Database session
        match_id: Match UUID
        team_name: Team name to calculate stats for

    Returns:
        Dictionary with calculated team statistics

    Aggregates:
        - Possession percentage
        - Expected goals (xG)
        - Shots (total, on target, off target)
        - Goalkeeper saves
        - Passes (total, completed, completion rate, final third, long, crosses)
        - Dribbles (total, successful)
        - Tackles (total, success percentage)
        - Interceptions
        - Ball recoveries
    """
    # Get all events for this team in this match
    events = db.query(event_crud.Event).filter(
        event_crud.Event.match_id == match_id,
        event_crud.Event.team_name == team_name
    ).all()

    if not events:
        return {}

    # Initialize counters
    total_duration = 0
    team_duration = 0
    total_xg = 0.0
    total_shots = 0
    shots_on_target = 0
    shots_off_target = 0
    goalkeeper_saves = 0
    total_passes = 0
    passes_completed = 0
    passes_final_third = 0
    long_passes = 0
    crosses = 0
    total_dribbles = 0
    successful_dribbles = 0
    total_tackles = 0
    successful_tackles = 0
    interceptions = 0
    ball_recoveries = 0

    # Process each event
    for event in events:
        event_data = event.event_data or {}
        event_type = event.event_type_name

        # Track duration for possession
        duration = event_data.get('duration', 0)
        if duration and duration > 0:
            total_duration += duration
            # Check if team has possession
            possession_team = event_data.get('possession_team', {})
            if possession_team.get('name') == team_name:
                team_duration += duration

        # Shot events
        if event_type == "Shot":
            total_shots += 1
            shot_data = event_data.get('shot', {})

            # xG
            xg = shot_data.get('statsbomb_xg', 0)
            if xg:
                total_xg += float(xg)

            # On target / off target
            outcome = shot_data.get('outcome', {}).get('name', '')
            if outcome in ["Saved", "Goal", "Saved to Post", "Post"]:
                shots_on_target += 1
            elif outcome in ["Off T", "Wayward", "Blocked"]:
                shots_off_target += 1

        # Pass events
        elif event_type == "Pass":
            total_passes += 1
            pass_data = event_data.get('pass', {})

            # Completed passes (no outcome field means successful)
            if 'outcome' not in pass_data or pass_data.get('outcome') is None:
                passes_completed += 1

            # Final third passes (x > 80)
            location = event_data.get('location', [])
            if location and len(location) >= 2 and location[0] > 80:
                passes_final_third += 1

            # Long passes (length > 30)
            pass_length = pass_data.get('length', 0)
            if pass_length and pass_length > 30:
                long_passes += 1

            # Crosses
            pass_type = pass_data.get('type', {}).get('name', '')
            if 'Cross' in pass_type:
                crosses += 1

        # Dribble events
        elif event_type == "Dribble":
            total_dribbles += 1
            dribble_data = event_data.get('dribble', {})
            outcome = dribble_data.get('outcome', {}).get('name', '')
            if outcome == "Complete":
                successful_dribbles += 1

        # Tackle events (Duel with Tackle sub-type)
        elif event_type == "Duel":
            duel_data = event_data.get('duel', {})
            duel_type = duel_data.get('type', {}).get('name', '')
            if duel_type == "Tackle":
                total_tackles += 1
                outcome = duel_data.get('outcome', {}).get('name', '')
                if outcome in ["Won", "Success"]:
                    successful_tackles += 1

        # Interception events
        elif event_type == "Interception":
            interceptions += 1

        # Ball Recovery events
        elif event_type == "Ball Recovery":
            ball_recoveries += 1

    # Calculate derived statistics
    possession_pct = (team_duration / total_duration * 100) if total_duration > 0 else 0
    pass_completion_rate = (passes_completed / total_passes * 100) if total_passes > 0 else 0
    tackle_success_pct = (successful_tackles / total_tackles * 100) if total_tackles > 0 else 0

    # For goalkeeper saves, need to look at opponent shots that were saved
    # This requires querying opponent events
    opponent_shots = db.query(event_crud.Event).filter(
        event_crud.Event.match_id == match_id,
        event_crud.Event.event_type_name == "Shot"
    ).all()

    for shot_event in opponent_shots:
        if shot_event.team_name != team_name:  # Opponent shot
            shot_data = shot_event.event_data.get('shot', {}) if shot_event.event_data else {}
            outcome = shot_data.get('outcome', {}).get('name', '')
            if outcome == "Saved":
                goalkeeper_saves += 1

    return {
        "possession_percentage": Decimal(str(round(possession_pct, 2))) if possession_pct > 0 else None,
        "expected_goals": Decimal(str(round(total_xg, 6))) if total_xg > 0 else None,
        "total_shots": total_shots if total_shots > 0 else None,
        "shots_on_target": shots_on_target if shots_on_target > 0 else None,
        "shots_off_target": shots_off_target if shots_off_target > 0 else None,
        "goalkeeper_saves": goalkeeper_saves if goalkeeper_saves > 0 else None,
        "total_passes": total_passes if total_passes > 0 else None,
        "passes_completed": passes_completed if passes_completed > 0 else None,
        "pass_completion_rate": Decimal(str(round(pass_completion_rate, 2))) if pass_completion_rate > 0 else None,
        "passes_in_final_third": passes_final_third if passes_final_third > 0 else None,
        "long_passes": long_passes if long_passes > 0 else None,
        "crosses": crosses if crosses > 0 else None,
        "total_dribbles": total_dribbles if total_dribbles > 0 else None,
        "successful_dribbles": successful_dribbles if successful_dribbles > 0 else None,
        "total_tackles": total_tackles if total_tackles > 0 else None,
        "tackle_success_percentage": Decimal(str(round(tackle_success_pct, 2))) if tackle_success_pct > 0 else None,
        "interceptions": interceptions if interceptions > 0 else None,
        "ball_recoveries": ball_recoveries if ball_recoveries > 0 else None
    }


def calculate_player_statistics(
    db: Session,
    match_id: str,
    statsbomb_player_id: int
) -> Dict[str, Any]:
    """
    Calculate player statistics from events for a specific match and player.

    Args:
        db: Database session
        match_id: Match UUID
        statsbomb_player_id: StatsBomb player ID

    Returns:
        Dictionary with calculated player statistics
    """
    # Get all events for this player in this match
    events = db.query(event_crud.Event).filter(
        event_crud.Event.match_id == match_id,
        event_crud.Event.statsbomb_player_id == statsbomb_player_id
    ).all()

    if not events:
        return {"goals": 0, "assists": 0}

    # Initialize counters
    goals = 0
    assists = 0
    total_xg = 0.0
    shots = 0
    shots_on_target = 0
    total_dribbles = 0
    successful_dribbles = 0
    total_passes = 0
    completed_passes = 0
    short_passes = 0
    long_passes = 0
    final_third_passes = 0
    crosses = 0
    tackles = 0
    successful_tackles = 0
    interceptions = 0
    successful_interceptions = 0

    # Get all match events for assist checking
    all_events = db.query(event_crud.Event).filter(
        event_crud.Event.match_id == match_id
    ).all()
    events_by_id = {e.event_data.get('id'): e for e in all_events if e.event_data}

    # Process each player event
    for event in events:
        event_data = event.event_data or {}
        event_type = event.event_type_name

        # Goals
        if event_type == "Shot":
            shots += 1
            shot_data = event_data.get('shot', {})

            # xG
            xg = shot_data.get('statsbomb_xg', 0)
            if xg:
                total_xg += float(xg)

            # Goal scored
            outcome = shot_data.get('outcome', {}).get('name', '')
            if outcome == "Goal":
                goals += 1

            # Shots on target
            if outcome in ["Saved", "Goal"]:
                shots_on_target += 1

        # Assists (check if pass led to goal)
        elif event_type == "Pass":
            total_passes += 1
            pass_data = event_data.get('pass', {})

            # Completed passes
            if 'outcome' not in pass_data or pass_data.get('outcome') is None:
                completed_passes += 1

            # Goal assist
            if pass_data.get('goal_assist'):
                assists += 1

            # Pass length classification
            pass_length = pass_data.get('length', 0)
            if pass_length:
                if pass_length < 15:
                    short_passes += 1
                elif pass_length > 30:
                    long_passes += 1

            # Final third passes
            location = event_data.get('location', [])
            if location and len(location) >= 2 and location[0] > 80:
                final_third_passes += 1

            # Crosses
            pass_type = pass_data.get('type', {}).get('name', '')
            if 'Cross' in pass_type:
                crosses += 1

        # Dribbles
        elif event_type == "Dribble":
            total_dribbles += 1
            dribble_data = event_data.get('dribble', {})
            outcome = dribble_data.get('outcome', {}).get('name', '')
            if outcome == "Complete":
                successful_dribbles += 1

        # Tackles
        elif event_type == "Duel":
            duel_data = event_data.get('duel', {})
            duel_type = duel_data.get('type', {}).get('name', '')
            if duel_type == "Tackle":
                tackles += 1
                outcome = duel_data.get('outcome', {}).get('name', '')
                if outcome in ["Won", "Success"]:
                    successful_tackles += 1

        # Interceptions
        elif event_type == "Interception":
            interceptions += 1
            interception_data = event_data.get('interception', {})
            outcome = interception_data.get('outcome', {}).get('name', '')
            if outcome in ["Won", "Success"]:
                successful_interceptions += 1

    # Calculate rates
    tackle_success_rate = (successful_tackles / tackles * 100) if tackles > 0 else None
    interception_success_rate = (successful_interceptions / interceptions * 100) if interceptions > 0 else None

    return {
        "goals": goals,
        "assists": assists,
        "expected_goals": Decimal(str(round(total_xg, 6))) if total_xg > 0 else None,
        "shots": shots if shots > 0 else None,
        "shots_on_target": shots_on_target if shots_on_target > 0 else None,
        "total_dribbles": total_dribbles if total_dribbles > 0 else None,
        "successful_dribbles": successful_dribbles if successful_dribbles > 0 else None,
        "total_passes": total_passes if total_passes > 0 else None,
        "completed_passes": completed_passes if completed_passes > 0 else None,
        "short_passes": short_passes if short_passes > 0 else None,
        "long_passes": long_passes if long_passes > 0 else None,
        "final_third_passes": final_third_passes if final_third_passes > 0 else None,
        "crosses": crosses if crosses > 0 else None,
        "tackles": tackles if tackles > 0 else None,
        "tackle_success_rate": Decimal(str(round(tackle_success_rate, 2))) if tackle_success_rate else None,
        "interceptions": interceptions if interceptions > 0 else None,
        "interception_success_rate": Decimal(str(round(interception_success_rate, 2))) if interception_success_rate else None
    }


@router.post("/matches", response_model=MatchUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_match(
    request: MatchUploadRequest,
    db: Session = Depends(get_db),
    current_coach: Coach = Depends(get_current_coach)
):
    """
    Upload match data with StatsBomb events.

    This endpoint processes match video analysis results, creates match records,
    extracts lineups, calculates statistics, and generates player invite codes.

    **12-Step Processing Pipeline:**
    1. Authentication & Authorization
    2. Identify teams from JSON
    3. Create/get opponent club
    4. Create match record
    5. Insert all events (~3000 records)
    6. Extract and create goals
    7. Extract and create/update players (your club)
    8. Extract and create opponent players
    9. Calculate and store match statistics (both teams)
    10. Calculate and store player match statistics
    11. Update club season statistics
    12. Update player season statistics

    Args:
        request: Match upload request with metadata and StatsBomb events
        db: Database session
        current_coach: Current authenticated coach

    Returns:
        MatchUploadResponse with match_id, summary, and new player invite codes

    Raises:
        HTTPException 400: Validation errors, team matching errors
        HTTPException 403: Coach doesn't own a club
        HTTPException 500: Processing errors
    """
    try:
        # STEP 1: Authentication & Authorization (handled by dependency)
        club = db.query(Club).filter(Club.coach_id == current_coach.coach_id).first()
        if not club:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must create a club before uploading matches"
            )

        # STEP 2: Identify teams from JSON
        starting_xi_events = [
            e for e in request.statsbomb_events
            if e.get('type', {}).get('name') == 'Starting XI'
        ]

        # Validation: Must have exactly 2 Starting XI events
        if len(starting_xi_events) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected 2 Starting XI events, found {len(starting_xi_events)}"
            )

        # Validation: Each Starting XI must have 11 players
        for xi_event in starting_xi_events:
            lineup_count = len(xi_event.get('tactics', {}).get('lineup', []))
            if lineup_count != 11:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Starting XI for {xi_event['team']['name']} has {lineup_count} players (expected 11)"
                )

        # Extract team information
        team_1 = starting_xi_events[0]['team']
        team_2 = starting_xi_events[1]['team']

        # Determine which team is the coach's club
        matched_team = match_team_name(club.club_name, team_1['name'], team_2['name'])

        if matched_team == 1:
            our_team_id = team_1['id']
            our_team_name = team_1['name']
            opponent_team_id = team_2['id']
            opponent_team_name = team_2['name']
            our_starting_xi = starting_xi_events[0]
            opponent_starting_xi = starting_xi_events[1]
        elif matched_team == 2:
            our_team_id = team_2['id']
            our_team_name = team_2['name']
            opponent_team_id = team_1['id']
            opponent_team_name = team_1['name']
            our_starting_xi = starting_xi_events[1]
            opponent_starting_xi = starting_xi_events[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot match your club name '{club.club_name}' to teams in event data: '{team_1['name']}', '{team_2['name']}'"
            )

        # Set statsbomb_team_id if not already set
        if club.statsbomb_team_id is None:
            club.statsbomb_team_id = our_team_id
            db.flush()

        # STEP 3: Create/Get Opponent Club
        opponent_club = opponent_club_crud.get_or_create_opponent_club(
            db=db,
            opponent_name=request.opponent_name,
            statsbomb_team_id=opponent_team_id,
            logo_url=request.opponent_logo_url
        )

        # STEP 4: Create Match Record
        match = match_crud.create_match(
            db=db,
            club_id=str(club.club_id),
            opponent_name=request.opponent_name,
            match_date=request.match_date,
            is_home_match=request.is_home_match,
            opponent_club_id=str(opponent_club.opponent_club_id),
            match_time=request.match_time,
            home_score=request.home_score,
            away_score=request.away_score
        )

        # STEP 5: Insert All Events (bulk insert for performance)
        events_data = []
        for event_dict in request.statsbomb_events:
            events_data.append({
                "event_data": event_dict,
                "statsbomb_player_id": event_dict.get('player', {}).get('id') if 'player' in event_dict else None,
                "statsbomb_team_id": event_dict.get('team', {}).get('id'),
                "player_name": event_dict.get('player', {}).get('name') if 'player' in event_dict else None,
                "team_name": event_dict.get('team', {}).get('name'),
                "event_type_name": event_dict.get('type', {}).get('name'),
                "position_name": event_dict.get('position', {}).get('name') if 'position' in event_dict else None,
                "minute": event_dict.get('minute'),
                "second": event_dict.get('second'),
                "period": event_dict.get('period')
            })

        events_processed = event_crud.create_events_bulk(
            db=db,
            match_id=str(match.match_id),
            events_data=events_data
        )

        # STEP 6: Extract and Create Goals
        goal_events = [
            e for e in request.statsbomb_events
            if e.get('type', {}).get('name') == 'Shot'
            and e.get('shot', {}).get('outcome', {}).get('name') == 'Goal'
        ]

        # Map event IDs for assist lookup
        events_by_id = {e.get('id'): e for e in request.statsbomb_events}

        goals_extracted = 0
        for goal_event in goal_events:
            # Find assist
            key_pass_id = goal_event.get('shot', {}).get('key_pass_id')
            assist_name = None

            if key_pass_id and key_pass_id in events_by_id:
                assist_event = events_by_id[key_pass_id]
                if assist_event.get('pass', {}).get('goal_assist'):
                    assist_name = assist_event.get('player', {}).get('name')

            goal_crud.create_goal(
                db=db,
                match_id=str(match.match_id),
                team_name=goal_event['team']['name'],
                scorer_name=goal_event['player']['name'],
                minute=goal_event['minute'],
                period=goal_event['period'],
                assist_name=assist_name,
                second=goal_event.get('second'),
                goal_type=goal_event.get('shot', {}).get('type', {}).get('name'),
                body_part=goal_event.get('shot', {}).get('body_part', {}).get('name')
            )
            goals_extracted += 1

        # Goal validation warnings
        warnings = []
        our_goals_from_json = len([g for g in goal_events if g['team']['name'] == our_team_name])
        opponent_goals_from_json = len([g for g in goal_events if g['team']['name'] == opponent_team_name])

        our_score_input = request.home_score if request.is_home_match else request.away_score
        opponent_score_input = request.away_score if request.is_home_match else request.home_score

        if our_goals_from_json != our_score_input:
            warnings.append(
                f"Event data has {our_goals_from_json} goals for your team but score says {our_score_input}"
            )

        if opponent_goals_from_json != opponent_score_input:
            warnings.append(
                f"Event data has {opponent_goals_from_json} goals for opponent but score says {opponent_score_input}"
            )

        # STEP 7: Extract and Create/Update Players (Our Club)
        our_lineup = our_starting_xi['tactics']['lineup']
        new_players = []
        players_created = 0
        players_updated = 0

        for player_data in our_lineup:
            statsbomb_player_id = player_data['player']['id']
            player_name = player_data['player']['name']
            jersey_number = player_data['jersey_number']
            position = player_data['position']['name']

            # Check if player exists by statsbomb_player_id
            existing_player = db.query(Player).filter(
                Player.club_id == club.club_id,
                Player.statsbomb_player_id == statsbomb_player_id
            ).first()

            if existing_player:
                # Update existing player
                existing_player.jersey_number = jersey_number
                existing_player.position = position
                existing_player.updated_at = datetime.now(timezone.utc)
                players_updated += 1
            else:
                # Check by name or jersey
                existing_player_by_name = db.query(Player).filter(
                    Player.club_id == club.club_id
                ).filter(
                    (Player.player_name == player_name) | (Player.jersey_number == jersey_number)
                ).first()

                if existing_player_by_name:
                    # Update with statsbomb_player_id
                    existing_player_by_name.statsbomb_player_id = statsbomb_player_id
                    existing_player_by_name.player_name = player_name
                    existing_player_by_name.jersey_number = jersey_number
                    existing_player_by_name.position = position
                    existing_player_by_name.updated_at = datetime.now(timezone.utc)
                    players_updated += 1
                else:
                    # Create new player
                    invite_code = generate_invite_code(db, player_name)

                    new_player = Player(
                        club_id=club.club_id,
                        player_name=player_name,
                        statsbomb_player_id=statsbomb_player_id,
                        jersey_number=jersey_number,
                        position=position,
                        invite_code=invite_code,
                        is_linked=False,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(new_player)
                    db.flush()

                    # Initialize season statistics
                    player_season_statistics_crud.get_or_create_player_season_statistics(
                        db=db,
                        player_id=str(new_player.player_id)
                    )

                    new_players.append({
                        "player_name": player_name,
                        "jersey_number": jersey_number,
                        "invite_code": invite_code
                    })
                    players_created += 1

        # STEP 8: Extract and Create Opponent Players
        opponent_lineup = opponent_starting_xi['tactics']['lineup']
        opponent_players_created = 0

        for player_data in opponent_lineup:
            statsbomb_player_id = player_data['player']['id']
            player_name = player_data['player']['name']
            jersey_number = player_data['jersey_number']
            position = player_data['position']['name']

            opponent_player_crud.get_or_create_opponent_player(
                db=db,
                opponent_club_id=str(opponent_club.opponent_club_id),
                player_name=player_name,
                statsbomb_player_id=statsbomb_player_id,
                jersey_number=jersey_number,
                position=position
            )
            opponent_players_created += 1

        # Flush to ensure all players are created before calculating stats
        db.flush()

        # STEP 9: Calculate and Store Match Statistics (Both Teams)
        our_team_stats = calculate_team_statistics(db, str(match.match_id), our_team_name)
        match_statistics_crud.create_match_statistics(
            db=db,
            match_id=str(match.match_id),
            team_type="our_team",
            **our_team_stats
        )

        opponent_team_stats = calculate_team_statistics(db, str(match.match_id), opponent_team_name)
        match_statistics_crud.create_match_statistics(
            db=db,
            match_id=str(match.match_id),
            team_type="opponent_team",
            **opponent_team_stats
        )

        # STEP 10: Calculate and Store Player Match Statistics
        for player_data in our_lineup:
            statsbomb_player_id = player_data['player']['id']

            # Get player_id
            player = db.query(Player).filter(
                Player.club_id == club.club_id,
                Player.statsbomb_player_id == statsbomb_player_id
            ).first()

            if player:
                player_stats = calculate_player_statistics(db, str(match.match_id), statsbomb_player_id)
                player_match_statistics_crud.create_player_match_statistics(
                    db=db,
                    player_id=str(player.player_id),
                    match_id=str(match.match_id),
                    **player_stats
                )

        # STEP 11: Update Club Season Statistics
        club_season_statistics_crud.recalculate_club_season_statistics(
            db=db,
            club_id=str(club.club_id)
        )

        # STEP 12: Update Player Season Statistics
        all_players = db.query(Player).filter(Player.club_id == club.club_id).all()
        for player in all_players:
            player_season_statistics_crud.recalculate_player_season_statistics(
                db=db,
                player_id=str(player.player_id)
            )

        # Commit transaction
        db.commit()

        # Build response
        return MatchUploadResponse(
            success=True,
            match_id=str(match.match_id),
            summary=MatchUploadSummary(
                events_processed=events_processed,
                goals_extracted=goals_extracted,
                players_created=players_created,
                players_updated=players_updated,
                opponent_players_created=opponent_players_created,
                warnings=warnings
            ),
            new_players=[NewPlayerInfo(**p) for p in new_players]
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the match data: {str(e)}"
        )
