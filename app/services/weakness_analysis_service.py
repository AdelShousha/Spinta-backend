"""Service for analyzing player attributes and statistics"""

from typing import List, Tuple

from app.schemas.coach import AIAttributes, AISeasonStatistics


def identify_weak_attributes(attributes: AIAttributes) -> List[Tuple[str, int]]:
    """
    Identify weak attributes (rating < 60)
    
    Args:
        attributes: Player attributes
        
    Returns:
        List of tuples (attribute_name, rating) for weak attributes
    """
    weak = []
    if attributes.attacking_rating < 60:
        weak.append(("Attacking", attributes.attacking_rating))
    if attributes.technique_rating < 60:
        weak.append(("Technique", attributes.technique_rating))
    if attributes.creativity_rating < 60:
        weak.append(("Creativity", attributes.creativity_rating))
    if attributes.tactical_rating < 60:
        weak.append(("Tactical", attributes.tactical_rating))
    if attributes.defending_rating < 60:
        weak.append(("Defending", attributes.defending_rating))
    return weak


def identify_weak_statistics(season_stats: AISeasonStatistics) -> List[str]:
    """
    Identify weak statistical areas
    
    Args:
        season_stats: Season statistics
        
    Returns:
        List of weak statistic area names
    """
    weak = []
    
    # Passing accuracy
    if season_stats.passing.total_passes > 0:
        pass_completion = (season_stats.passing.passes_completed / season_stats.passing.total_passes) * 100
        if pass_completion < 80:
            weak.append("Passing Accuracy")
    
    # Dribbling success
    if season_stats.dribbling.total_dribbles > 0:
        dribble_success = (season_stats.dribbling.successful_dribbles / season_stats.dribbling.total_dribbles) * 100
        if dribble_success < 60:
            weak.append("Dribbling Success")
    
    # Shooting accuracy
    if season_stats.attacking.shots_per_game > 0:
        shot_accuracy = (season_stats.attacking.shots_on_target_per_game / season_stats.attacking.shots_per_game) * 100
        if shot_accuracy < 50:
            weak.append("Shooting Accuracy")
    
    # Finishing (xG vs goals)
    if season_stats.attacking.expected_goals > 0:
        finishing_rate = (season_stats.attacking.goals / season_stats.attacking.expected_goals) * 100
        if finishing_rate < 80:
            weak.append("Finishing")
    
    # Tackling
    if season_stats.defending.tackle_success_rate < 70:
        weak.append("Tackling")
    
    # Interceptions
    if season_stats.defending.interception_success_rate < 70:
        weak.append("Interceptions")
    
    return weak

