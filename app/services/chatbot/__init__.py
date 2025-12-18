"""
Chatbot Tools Package

Contains database query tools for the AI chatbot.
All tools use synchronous SQLAlchemy operations.

Core Tools (10 total):
- Player: find_player_by_name, get_player_season_stats, get_top_scorers, get_top_assisters, compare_players
- Match: get_last_match, get_match_details, get_match_statistics
- Team: get_club_season_stats, get_squad_list
"""

from app.services.chatbot.player_tools import (
    find_player_by_name,
    get_player_season_stats,
    get_top_scorers,
    get_top_assisters,
    compare_players,
)

from app.services.chatbot.match_tools import (
    get_last_match,
    get_match_details,
    get_match_statistics,
)

from app.services.chatbot.team_tools import (
    get_club_season_stats,
    get_squad_list,
)

__all__ = [
    # Player tools (5)
    "find_player_by_name",
    "get_player_season_stats",
    "get_top_scorers",
    "get_top_assisters",
    "compare_players",
    # Match tools (3)
    "get_last_match",
    "get_match_details",
    "get_match_statistics",
    # Team tools (2)
    "get_club_season_stats",
    "get_squad_list",
]
