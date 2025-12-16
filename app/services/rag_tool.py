"""
RAG Tool for Pydantic AI Agent

Defines a tool function that the AI agent can call to retrieve
relevant coaching knowledge from the PostgreSQL vector database.

The agent autonomously decides when to call this tool based on its
analysis of player weaknesses and training plan requirements.

Usage:
    from app.services.rag_tool import create_rag_tool

    # Create tool with database session
    rag_tool = create_rag_tool(db_session)

    # Register with Pydantic AI agent
    agent = Agent(
        model="google-gla:gemini-2.5-flash",
        tools=[rag_tool],
        ...
    )
"""

from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class RAGQueryInput(BaseModel):
    """Input schema for RAG query tool"""

    query: str = Field(
        ...,
        description=(
            "Search query to find relevant coaching knowledge. "
            "Be specific about the skill, drill type, or concept you need. "
            "Examples: 'passing accuracy drills', 'defensive positioning for forwards', "
            "'finishing under pressure exercises'"
        )
    )

    num_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of relevant passages to retrieve (1-10, default 5)"
    )


class RAGQueryResult(BaseModel):
    """Result from RAG query"""

    passages: List[str] = Field(
        ...,
        description="List of relevant text passages from the knowledge base"
    )

    query_used: str = Field(
        ...,
        description="The query that was used for retrieval"
    )

    num_results: int = Field(
        ...,
        description="Number of passages retrieved"
    )


def create_rag_tool(db_session: Session, gemini_api_key: str = None):
    """
    Factory function to create RAG tool with database session

    This function creates a closure that captures the database session,
    allowing the tool to query the knowledge base when called by the agent.

    Args:
        db_session: SQLAlchemy database session
        gemini_api_key: Google Gemini API key (optional, defaults to env var)

    Returns:
        RAG query function for use as Pydantic AI tool

    Example:
        >>> from app.database import get_db
        >>> db = next(get_db())
        >>> rag_tool = create_rag_tool(db)
        >>> # Use with Pydantic AI agent
    """
    from app.services.pgvector_rag_service import PgVectorRAGService

    # Create RAG service instance
    rag_service = PgVectorRAGService(db_session=db_session, gemini_api_key=gemini_api_key)

    def query_knowledge_base(query: str, num_results: int = 5) -> RAGQueryResult:
        """
        Search the football coaching knowledge base for relevant information.

        This tool provides access to a comprehensive database of football coaching
        knowledge including:
        - Training drills and exercises
        - Coaching methodology and principles
        - Position-specific coaching advice
        - Skill improvement techniques
        - Warm-up and cooldown routines
        - Tactical concepts and strategies
        - Technical development approaches

        **When to use this tool:**
        - When you need specific drill descriptions
        - When looking for exercises to address player weaknesses
        - When seeking position-specific training approaches
        - When needing coaching methodology guidance

        **How to use effectively:**
        1. Make specific queries about skills or drills
        2. Include position information when relevant
        3. Specify the skill level or area of improvement
        4. Call multiple times for different aspects if needed

        **Examples of good queries:**
        - "passing accuracy drills for midfielders"
        - "defensive positioning exercises for forwards"
        - "finishing drills under pressure"
        - "tactical awareness training methodology"
        - "ball control exercises for technique improvement"

        Args:
            query: What you want to find in the knowledge base
            num_results: How many relevant passages to retrieve (default 5, max 10)

        Returns:
            RAGQueryResult with relevant passages from coaching textbooks
        """
        # Validate num_results
        num_results = max(1, min(num_results, 10))

        # Query the knowledge base
        passages = rag_service.retrieve(query, top_k=num_results)

        return RAGQueryResult(
            passages=passages,
            query_used=query,
            num_results=len(passages)
        )

    return query_knowledge_base
