"""Add knowledge_embeddings table for pgvector RAG

Revision ID: a1b2c3d4e5f6
Revises: fa912f5abb62
Create Date: 2025-12-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fa912f5abb62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade: Add knowledge_embeddings table with pgvector support

    This table stores text chunks with their embeddings for AI-powered
    training plan generation using Retrieval-Augmented Generation (RAG).
    """
    # Enable pgvector extension (idempotent operation)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create knowledge_embeddings table
    op.create_table(
        'knowledge_embeddings',
        sa.Column(
            'embedding_id',
            UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text('gen_random_uuid()'),
            comment='Unique embedding identifier'
        ),
        sa.Column(
            'content',
            sa.Text(),
            nullable=False,
            comment='Original text content of the chunk'
        ),
        sa.Column(
            'embedding',
            sa.TEXT(),  # Will be replaced by VECTOR type in raw SQL
            nullable=False,
            comment='Vector embedding for similarity search'
        ),
        sa.Column(
            'source_file',
            sa.String(255),
            nullable=False,
            comment='Source file name (e.g., Soccer_books.pdf)'
        ),
        sa.Column(
            'chunk_index',
            sa.Integer(),
            nullable=False,
            comment='Position of chunk in source file (0-indexed)'
        ),
        sa.Column(
            'meta_info',
            JSONB(),
            nullable=False,
            server_default='{}',
            comment='Additional metadata (chapter, page, topic, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='Timestamp when record was created'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='Timestamp when record was last updated'
        ),
        sa.PrimaryKeyConstraint('embedding_id'),
    )

    # Alter embedding column to use VECTOR type (768 dimensions for Google text-embedding-004)
    # This is done with raw SQL because SQLAlchemy doesn't have native VECTOR support
    op.execute('ALTER TABLE knowledge_embeddings ALTER COLUMN embedding TYPE VECTOR(768) USING embedding::VECTOR(768)')

    # Create HNSW index for fast approximate nearest neighbor search
    # HNSW (Hierarchical Navigable Small World) is optimal for cosine similarity
    # m=16: connections per node (higher = better recall, more memory)
    # ef_construction=64: candidate list size during index build
    op.execute('''
        CREATE INDEX idx_knowledge_embeddings_vector
        ON knowledge_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')

    # Create B-tree index on source_file for filtering
    op.create_index(
        'idx_knowledge_embeddings_source',
        'knowledge_embeddings',
        ['source_file']
    )

    # Create unique constraint to prevent duplicate chunks from same source
    op.create_index(
        'unique_source_chunk',
        'knowledge_embeddings',
        ['source_file', 'chunk_index'],
        unique=True
    )


def downgrade() -> None:
    """
    Downgrade: Remove knowledge_embeddings table and pgvector extension

    Note: The pgvector extension is not dropped as other tables might use it.
    """
    # Drop indexes first
    op.drop_index('unique_source_chunk', table_name='knowledge_embeddings')
    op.drop_index('idx_knowledge_embeddings_source', table_name='knowledge_embeddings')
    op.drop_index('idx_knowledge_embeddings_vector', table_name='knowledge_embeddings')

    # Drop table
    op.drop_table('knowledge_embeddings')

    # Note: We don't drop the vector extension as it might be used by other tables
    # If you want to drop it: op.execute('DROP EXTENSION IF EXISTS vector')
