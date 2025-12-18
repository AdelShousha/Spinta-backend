"""
LLM Service with Function Calling

Uses the google-genai package (lightweight) for Gemini API interactions
with function calling support for database queries.
"""

import json
from typing import List, Dict, Any, Optional, Callable
from uuid import UUID
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.config import settings
from app.services.chatbot import (
    find_player_by_name,
    get_player_season_stats,
    get_top_scorers,
    get_top_assisters,
    compare_players,
    get_last_match,
    get_match_details,
    get_match_statistics,
    get_club_season_stats,
    get_squad_list,
)


class LLMService:
    """Service for interacting with Gemini LLM with function calling."""

    def __init__(self):
        """Initialize Gemini API client."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be set in .env file")

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-2.5-flash"
        self.tools = self._build_tools()

    def _build_tools(self) -> List[types.Tool]:
        """Build function declarations for Gemini."""
        function_declarations = [
            types.FunctionDeclaration(
                name="get_player_season_stats",
                description="Get season statistics for a specific player including goals, assists, passes, tackles, and attribute ratings",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "player_name": types.Schema(
                            type=types.Type.STRING,
                            description="Player's name (first name, last name, or full name)"
                        )
                    },
                    required=["player_name"]
                )
            ),
            types.FunctionDeclaration(
                name="get_top_scorers",
                description="Get the top goal scorers in the team for the current season",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "limit": types.Schema(
                            type=types.Type.INTEGER,
                            description="Number of top scorers to return (default: 5)"
                        )
                    },
                    required=[]
                )
            ),
            types.FunctionDeclaration(
                name="get_top_assisters",
                description="Get top assist providers in the team for the current season",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "limit": types.Schema(
                            type=types.Type.INTEGER,
                            description="Number of top assisters to return (default: 5)"
                        )
                    },
                    required=[]
                )
            ),
            types.FunctionDeclaration(
                name="find_player_by_name",
                description="Search for a player by name (supports partial matching)",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "player_name": types.Schema(
                            type=types.Type.STRING,
                            description="Player's name or partial name to search"
                        )
                    },
                    required=["player_name"]
                )
            ),
            types.FunctionDeclaration(
                name="compare_players",
                description="Compare statistics between two players side-by-side",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "player1_name": types.Schema(
                            type=types.Type.STRING,
                            description="First player's name"
                        ),
                        "player2_name": types.Schema(
                            type=types.Type.STRING,
                            description="Second player's name"
                        )
                    },
                    required=["player1_name", "player2_name"]
                )
            ),
            types.FunctionDeclaration(
                name="get_last_match",
                description="Get the most recent match for the team",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={},
                    required=[]
                )
            ),
            types.FunctionDeclaration(
                name="get_match_details",
                description="Get basic information about a match (date, opponent, score, result)",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "match_description": types.Schema(
                            type=types.Type.STRING,
                            description="Match description like 'last match' or 'vs Team X'. Defaults to last match."
                        )
                    },
                    required=[]
                )
            ),
            types.FunctionDeclaration(
                name="get_match_statistics",
                description="Get detailed match statistics for both teams including possession, xG, shots, passes, tackles",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "match_description": types.Schema(
                            type=types.Type.STRING,
                            description="Match description like 'last match' or 'vs Team X'"
                        )
                    },
                    required=[]
                )
            ),
            types.FunctionDeclaration(
                name="get_club_season_stats",
                description="Get overall season statistics for the team including wins, losses, goals scored/conceded, and averages",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={},
                    required=[]
                )
            ),
            types.FunctionDeclaration(
                name="get_squad_list",
                description="Get list of all players in the squad with their positions and jersey numbers",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "position_filter": types.Schema(
                            type=types.Type.STRING,
                            description="Filter by position (e.g., 'forward', 'midfielder', 'defender', 'goalkeeper')"
                        )
                    },
                    required=[]
                )
            ),
        ]

        return [types.Tool(function_declarations=function_declarations)]

    def _get_tool_function(self, tool_name: str) -> Optional[Callable]:
        """Get the actual Python function for a tool name."""
        tool_map = {
            "get_player_season_stats": get_player_season_stats,
            "get_top_scorers": get_top_scorers,
            "get_top_assisters": get_top_assisters,
            "find_player_by_name": find_player_by_name,
            "compare_players": compare_players,
            "get_last_match": get_last_match,
            "get_match_details": get_match_details,
            "get_match_statistics": get_match_statistics,
            "get_club_season_stats": get_club_season_stats,
            "get_squad_list": get_squad_list,
        }
        return tool_map.get(tool_name)

    def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        db: Session,
        club_id: UUID
    ) -> Any:
        """Execute a tool function with database and club_id context."""
        function = self._get_tool_function(tool_name)
        if not function:
            return {"error": f"Unknown tool: {tool_name}"}

        # Add db and club_id to all calls
        function_args = dict(args)
        function_args['db'] = db
        function_args['club_id'] = club_id

        try:
            return function(**function_args)
        except Exception as e:
            return {"error": str(e)}

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        db: Session,
        club_id: UUID
    ) -> Dict[str, Any]:
        """
        Process a chat message with Gemini LLM and execute function calls.

        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            db: Database session
            club_id: Club ID for context

        Returns:
            Dictionary with response message and tool calls
        """
        # Build contents from history
        contents = []

        # Add system instruction via initial context
        system_message = (
            "You are an AI assistant for Spinta Stats, a soccer team management platform. "
            "You help coaches by analyzing match statistics, player performance, and team data. "
            "Use the available tools to query the database and provide accurate, data-driven responses. "
            "When users ask about 'last match' or specific players, use the appropriate tools. "
            "Be conversational and helpful. Keep responses concise but informative."
        )

        # Convert conversation history to Gemini format
        for msg in conversation_history:
            if msg["role"] == "system":
                continue  # Skip system messages, handled via system_instruction
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # Add current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            )
        )

        # Track tool calls
        tool_calls_executed = []
        tool_results = []

        # Generate initial response
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=self.tools,
                system_instruction=system_message,
            )
        )

        # Handle function calling loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Check if response has function calls
            if not response.candidates or not response.candidates[0].content.parts:
                break

            has_function_call = False
            function_responses = []

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_function_call = True
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = dict(function_call.args) if function_call.args else {}

                    # Execute the tool
                    result = self._execute_tool(function_name, function_args, db, club_id)

                    tool_calls_executed.append(function_name)
                    tool_results.append({
                        "tool_name": function_name,
                        "arguments": function_args,
                        "result": result
                    })

                    # Prepare function response
                    function_responses.append(
                        types.Part.from_function_response(
                            name=function_name,
                            response={"result": result}
                        )
                    )

            if not has_function_call:
                break

            # Add model response and function results to contents
            contents.append(response.candidates[0].content)
            contents.append(
                types.Content(
                    role="user",
                    parts=function_responses
                )
            )

            # Get next response
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=self.tools,
                    system_instruction=system_message,
                )
            )

        # Extract final text response
        final_response = "I apologize, but I couldn't process that request."
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text:
                    final_response = part.text
                    break

        return {
            "message": final_response,
            "tool_calls_executed": tool_calls_executed,
            "tool_results": tool_results
        }
