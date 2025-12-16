"""
KnowledgeEmbedding Model

Stores vectorized chunks of football coaching knowledge for RAG retrieval.
Uses pgvector extension for efficient similarity search.

This model handles semantic search for AI training plan generation:
- Text chunks are extracted from PDFs and text files
- Embeddings are generated using Google Gemini API (768 dimensions)
- Stored with pgvector for fast cosine similarity queries
- Agent uses these embeddings to retrieve relevant coaching knowledge

Ingestion Process:
1. Run locally: scripts/ingest_knowledge_base.py
2. Extracts text from PDFs/markdown files
3. Chunks text into 300-character segments
4. Generates embeddings using sentence-transformers (local only)
5. Inserts into PostgreSQL with pgvector

Query Process (on Vercel):
1. Generate query embedding using Gemini API
2. Query pgvector using cosine similarity
3. Return top-k most relevant chunks

Fields:
1. embedding_id - UUID primary key
2. content - Original text content of the chunk
3. embedding - 768-dimensional vector (pgvector VECTOR type)
4. source_file - Name of source file (e.g., "Soccer_books.pdf")
5. chunk_index - Position of chunk in source file
6. meta_info - Additional metadata (JSONB, e.g., chapter, page)
7. created_at - Timestamp when record was created

Indexes:
- HNSW index on embedding for fast similarity search
- B-tree index on source_file for filtering
"""

from sqlalchemy import Column, String, Integer, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, GUID, generate_uuid


class KnowledgeEmbedding(Base, TimestampMixin):
    """
    Knowledge Embedding Model

    Stores text chunks with their vector embeddings for semantic search.
    Used by AI agent to retrieve relevant coaching knowledge during
    training plan generation.

    Usage:
        # Query for similar embeddings
        results = session.execute(
            text('''
                SELECT content, 1 - (embedding <=> :query_vec) as similarity
                FROM knowledge_embeddings
                ORDER BY embedding <=> :query_vec
                LIMIT 5
            '''),
            {"query_vec": str(query_embedding)}
        ).fetchall()

    Attributes:
        embedding_id: Unique identifier for this embedding
        content: Original text content of the chunk
        embedding: 768-dimensional vector for similarity search
        source_file: Name of source file (for filtering/tracking)
        chunk_index: Position of chunk in source file (0-indexed)
        meta_info: Additional information (chapter, page, etc.)
        created_at: Inherited from TimestampMixin
        updated_at: Inherited from TimestampMixin
    """

    __tablename__ = "knowledge_embeddings"

    embedding_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique embedding identifier"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Original text content of the chunk"
    )

    embedding = Column(
        Vector(768),  # 768 dimensions for Google text-embedding-004
        nullable=False,
        comment="Vector embedding for similarity search"
    )

    source_file = Column(
        String(255),
        nullable=False,
        comment="Source file name (e.g., Soccer_books.pdf)"
    )

    chunk_index = Column(
        Integer,
        nullable=False,
        comment="Position of chunk in source file (0-indexed)"
    )

    meta_info = Column(
        JSONB,
        default={},
        nullable=False,
        comment="Additional metadata (chapter, page, topic, etc.)"
    )

    __table_args__ = (
        # HNSW index for fast approximate nearest neighbor search
        # m=16: number of connections per node (higher = better recall, more memory)
        # ef_construction=64: size of candidate list during index build
        Index(
            'idx_knowledge_embeddings_vector',
            embedding,
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
        # B-tree index for filtering by source file
        Index('idx_knowledge_embeddings_source', source_file),
        # Unique constraint to prevent duplicate chunks
        Index('unique_source_chunk', source_file, chunk_index, unique=True),
    )

    def __repr__(self):
        """String representation for debugging"""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<KnowledgeEmbedding("
            f"id={self.embedding_id}, "
            f"source='{self.source_file}', "
            f"chunk={self.chunk_index}, "
            f"content='{content_preview}'"
            f")>"
        )
