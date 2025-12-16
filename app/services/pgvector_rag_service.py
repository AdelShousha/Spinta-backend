"""
RAG Service using PostgreSQL pgvector

This service queries pre-computed embeddings stored in PostgreSQL.
Uses Google Gemini API for query embedding (lightweight, no local model needed).

This service is designed for serverless deployment (Vercel) where:
- Knowledge base embeddings are pre-computed locally
- Query embeddings are generated via Gemini API
- Similarity search is performed using pgvector in PostgreSQL

Usage:
    from app.services.pgvector_rag_service import PgVectorRAGService

    rag_service = PgVectorRAGService(db_session=db)
    relevant_chunks = rag_service.retrieve("passing drills for midfielders")
"""

import os
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from google import genai


class PgVectorRAGService:
    """RAG service using PostgreSQL pgvector for similarity search"""

    def __init__(
        self,
        db_session: Session,
        embedding_model: str = "text-embedding-004",
        top_k: int = 5,
        gemini_api_key: Optional[str] = None
    ):
        """
        Initialize RAG service

        Args:
            db_session: SQLAlchemy database session
            embedding_model: Google embedding model name
            top_k: Number of chunks to retrieve per query
            gemini_api_key: Gemini API key (defaults to env var)

        Raises:
            ValueError: If GEMINI_API_KEY is not provided
        """
        self.db = db_session
        self.embedding_model = embedding_model
        self.top_k = top_k

        # Configure Gemini client
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Set it in your .env file or pass it to the constructor."
            )

        self.client = genai.Client(api_key=api_key)

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query using Gemini API

        Args:
            query: Search query string

        Returns:
            768-dimensional embedding vector

        Note:
            Uses text-embedding-004 which supports output_dimensionality
            parameter to match the 768 dimensions stored in database.
        """
        try:
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=query,
                config={
                    "task_type": "RETRIEVAL_QUERY",
                    "output_dimensionality": 768  # Match stored embeddings
                }
            )
            return result.embeddings[0].values

        except Exception as e:
            print(f"Error generating embedding for query '{query}': {e}")
            raise

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """
        Retrieve most relevant chunks for a query

        Uses cosine distance (<=> operator in pgvector) for similarity search.
        Lower distance = higher similarity.

        Args:
            query: Search query string
            top_k: Number of results (defaults to self.top_k)

        Returns:
            List of relevant text chunks, ordered by similarity

        Example:
            >>> rag = PgVectorRAGService(db_session)
            >>> chunks = rag.retrieve("passing accuracy drills")
            >>> print(f"Found {len(chunks)} relevant chunks")
        """
        k = top_k or self.top_k

        # Get query embedding from Gemini API
        query_embedding = self._get_query_embedding(query)

        # Query pgvector using cosine distance
        # The <=> operator calculates cosine distance (1 - cosine similarity)
        # We order by distance ascending to get most similar chunks first
        results = self.db.execute(
            text("""
                SELECT
                    content,
                    1 - (embedding <=> :query_vec) as similarity,
                    source_file
                FROM knowledge_embeddings
                ORDER BY embedding <=> :query_vec
                LIMIT :limit
            """),
            {"query_vec": str(query_embedding), "limit": k}
        ).fetchall()

        return [row.content for row in results]

    def retrieve_with_sources(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[dict]:
        """
        Retrieve chunks with source information

        Args:
            query: Search query string
            top_k: Number of results

        Returns:
            List of dicts with 'content', 'similarity', and 'source' keys

        Example:
            >>> results = rag.retrieve_with_sources("finishing drills")
            >>> for r in results:
            ...     print(f"{r['source']}: {r['similarity']:.3f}")
        """
        k = top_k or self.top_k
        query_embedding = self._get_query_embedding(query)

        results = self.db.execute(
            text("""
                SELECT
                    content,
                    1 - (embedding <=> :query_vec) as similarity,
                    source_file
                FROM knowledge_embeddings
                ORDER BY embedding <=> :query_vec
                LIMIT :limit
            """),
            {"query_vec": str(query_embedding), "limit": k}
        ).fetchall()

        return [
            {
                "content": row.content,
                "similarity": float(row.similarity),
                "source": row.source_file
            }
            for row in results
        ]

    def retrieve_for_training_plan(
        self,
        position: str,
        weak_attributes: List[str],
        weak_stats: List[str]
    ) -> str:
        """
        Retrieve relevant knowledge for training plan generation

        Constructs multiple queries based on player position, weak attributes,
        and weak statistics, then retrieves and deduplicates relevant chunks.

        Args:
            position: Player position (e.g., "Forward", "Midfielder")
            weak_attributes: List of weak attribute names (e.g., ["tactical", "defending"])
            weak_stats: List of weak statistic areas (e.g., ["Passing Accuracy", "Finishing"])

        Returns:
            Combined relevant knowledge base text, separated by '---'

        Example:
            >>> knowledge = rag.retrieve_for_training_plan(
            ...     position="Forward",
            ...     weak_attributes=["tactical", "defending"],
            ...     weak_stats=["Finishing"]
            ... )
            >>> print(f"Retrieved {len(knowledge)} characters of knowledge")
        """
        queries = []

        # Position-based query
        queries.append(f"{position} training drills and exercises")

        # Attribute-based queries
        for attr in weak_attributes:
            queries.append(f"{attr} improvement drills football training")

        # Statistics-based queries
        for stat in weak_stats:
            queries.append(f"{stat} improvement football drills")

        # General coaching methodology
        queries.append("football coaching methodology training plan structure")

        # Retrieve and deduplicate chunks
        all_chunks = []
        seen_chunks = set()

        for query in queries:
            try:
                chunks = self.retrieve(query)
                for chunk in chunks:
                    # Deduplicate using hash
                    chunk_hash = hash(chunk)
                    if chunk_hash not in seen_chunks:
                        seen_chunks.add(chunk_hash)
                        all_chunks.append(chunk)
            except Exception as e:
                print(f"Warning: Failed to retrieve for query '{query}': {e}")
                continue

        if all_chunks:
            return "\n\n---\n\n".join(all_chunks)
        else:
            return "No relevant knowledge base content found."
