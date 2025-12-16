"""
AI Training Plan Generation Service

Uses Pydantic AI with tool-based RAG to generate personalized training plans.

The agent autonomously decides when to query the coaching knowledge base
using the RAG tool based on player weaknesses and training requirements.

Architecture:
- Pydantic AI Agent with Google Gemini 2.5 Flash
- PostgreSQL pgvector for knowledge retrieval
- Tool-based RAG (agent calls tool as needed)
- Structured output validation via Pydantic schemas

Usage:
    from app.services.ai_training_plan_service import TrainingPlanService

    service = TrainingPlanService(settings=settings, db_session=db)
    plan = await service.generate_training_plan(player_data)
"""

import os
from typing import List, Tuple
from pydantic_ai import Agent
from sqlalchemy.orm import Session

from app.config import Settings
from app.schemas.coach import (
    AITrainingPlanRequest,
    AITrainingPlanResponse,
)
from app.services.weakness_analysis_service import (
    identify_weak_attributes,
    identify_weak_statistics,
)
from app.services.rag_tool import create_rag_tool


class TrainingPlanService:
    """Service for generating AI-powered training plans"""

    def __init__(self, settings: Settings, db_session: Session):
        """
        Initialize training plan service

        Args:
            settings: Application settings (contains GEMINI_API_KEY)
            db_session: SQLAlchemy database session
        """
        self.settings = settings
        self.db = db_session
        self.model = "google-gla:gemini-2.5-flash-lite"

    def _create_system_prompt(
        self,
        player_name: str,
        position: str,
        weak_attributes: List[Tuple[str, int]],
        weak_stats: List[str]
    ) -> str:
        """
        Create system prompt for the AI agent

        Args:
            player_name: Player's name
            position: Player's position
            weak_attributes: List of (attribute_name, rating) tuples
            weak_stats: List of weak statistic area names

        Returns:
            System prompt string
        """
        prompt = f"""You are an expert football coach creating a personalized training plan for {player_name}, a {position}.

**YOUR TASK:**
Generate a comprehensive training plan with 3-10 specific exercises that address the player's weaknesses.

**PLAYER WEAKNESSES:**

Weak Attributes:
"""

        if weak_attributes:
            for attr_name, rating in weak_attributes:
                prompt += f"- {attr_name}: {rating}/100\n"
        else:
            prompt += "- No significant attribute weaknesses\n"

        prompt += "\nWeak Statistics:\n"
        if weak_stats:
            for stat in weak_stats:
                prompt += f"- {stat}\n"
        else:
            prompt += "- No significant statistical weaknesses\n"

        prompt += """
**KNOWLEDGE BASE ACCESS:**
You have access to a comprehensive football coaching knowledge base through the `query_knowledge_base` tool.

The knowledge base contains:
- Training drills and exercises
- Position-specific coaching methods
- Technical and tactical development approaches
- Warm-up and cooldown routines
- Skill improvement techniques

**HOW TO USE THE TOOL:**
1. Call `query_knowledge_base` with specific queries about drills or exercises
2. Make multiple calls for different weakness areas if needed
3. Use position-specific queries when relevant
4. Examples of good queries:
   - "passing accuracy drills for midfielders"
   - "finishing exercises under pressure"
   - "defensive positioning drills for forwards"
   - "tactical awareness training"

**IMPORTANT INSTRUCTIONS:**
1. **Query the knowledge base** for relevant drills addressing the player's weaknesses
2. **Create 3-10 exercises** - each should target specific weaknesses
3. **Be specific and practical** - provide actionable drill descriptions
4. **Include variety** - mix technical, tactical, physical, and position-specific work
5. **Use proper structure**:
   - `exercise_name`: Clear, descriptive name
   - `description`: Detailed instructions (2-4 sentences)
   - `sets`: Number of sets (e.g., 3, 4, 5)
   - `reps`: Repetitions or attempts (e.g., 10, 8, 12)
   - `duration_minutes`: Time in minutes (e.g., 15, 10, 20)
6. **Jersey number**: Choose a realistic number between 1-99
7. **Plan name**: Create an engaging, specific name (e.g., "Advanced Finishing & Positioning Plan")
8. **Duration**: Specify plan duration in weeks (e.g., "4 weeks", "6 weeks")

**OUTPUT FORMAT:**
Return a structured training plan matching the AITrainingPlanResponse schema.
"""

        return prompt

    async def generate_training_plan(
        self,
        request: AITrainingPlanRequest
    ) -> AITrainingPlanResponse:
        """
        Generate AI-powered training plan for a player

        Args:
            request: Training plan request with player data

        Returns:
            Structured training plan with exercises

        Raises:
            ValueError: If GEMINI_API_KEY is not configured
            Exception: If agent execution fails
        """
        # Validate API key
        api_key = (
            self.settings.gemini_api_key or
            os.getenv('GEMINI_API_KEY') or
            os.getenv('GOOGLE_API_KEY')
        )
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required. Set it in .env or app settings."
            )

        # Set API key in environment for Pydantic AI
        # (Pydantic AI reads from environment when creating model provider)
        os.environ['GEMINI_API_KEY'] = api_key

        # Analyze player weaknesses
        weak_attributes = identify_weak_attributes(request.attributes)
        weak_stats = identify_weak_statistics(request.season_statistics)

        # Create system prompt
        system_prompt = self._create_system_prompt(
            player_name=request.player_name,
            position=request.position,
            weak_attributes=weak_attributes,
            weak_stats=weak_stats
        )

        # Create RAG tool (pass API key from settings)
        rag_tool = create_rag_tool(db_session=self.db, gemini_api_key=api_key)

        # Create Pydantic AI Agent with tool
        agent = Agent(
            model=self.model,
            result_type=AITrainingPlanResponse,
            system_prompt=system_prompt,
            tools=[rag_tool],  # Register RAG tool
        )

        # Prepare user message with player context
        user_message = f"""Generate a training plan for:

**Player**: {request.player_name}
**Position**: {request.position}

**Current Attributes**:
- Attacking: {request.attributes.attacking_rating}/100
- Technique: {request.attributes.technique_rating}/100
- Creativity: {request.attributes.creativity_rating}/100
- Tactical: {request.attributes.tactical_rating}/100
- Defending: {request.attributes.defending_rating}/100

**Season Performance**:
- Matches Played: {request.season_statistics.general.matches_played}
- Goals: {request.season_statistics.attacking.goals}
- Assists: {request.season_statistics.attacking.assists}
- Pass Completion: {request.season_statistics.passing.passes_completed}/{request.season_statistics.passing.total_passes}

Use the knowledge base tool to find relevant drills and create a comprehensive training plan.
"""

        # Run agent
        result = await agent.run(user_message)

        return result.data


async def generate_ai_training_plan(
    request: AITrainingPlanRequest,
    settings: Settings,
    db_session: Session
) -> AITrainingPlanResponse:
    """
    Convenience function for generating training plans

    Args:
        request: Training plan request
        settings: Application settings
        db_session: Database session

    Returns:
        Generated training plan
    """
    service = TrainingPlanService(settings=settings, db_session=db_session)
    return await service.generate_training_plan(request)
