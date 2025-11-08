"""
SQLAlchemy Base and Common Utilities

This module provides the declarative base for all SQLAlchemy models
and common utilities used across models.

Key Concepts:
- Declarative Base: All models inherit from this
- UUID primary keys: Using Python's uuid4 for unique identifiers
- Timestamps: created_at and updated_at automatically managed
"""

from sqlalchemy import Column, DateTime, String, TypeDecorator, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    String(36) for SQLite and other databases.

    This allows our models to work with both PostgreSQL (production)
    and SQLite (testing) without changes.

    Technical Details:
    - PostgreSQL: Stores as native UUID type (efficient)
    - SQLite: Stores as String(36) (compatible)
    - Python: Always works with strings

    Usage:
        from app.models.base import GUID
        id = Column(GUID, primary_key=True, default=generate_uuid)
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """
        Return appropriate type for the dialect.

        Args:
            dialect: SQLAlchemy dialect (postgresql, sqlite, etc.)

        Returns:
            UUID for PostgreSQL, String(36) for others
        """
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """
        Process value before sending to database.

        Args:
            value: The UUID value (string or None)
            dialect: The database dialect

        Returns:
            String representation of UUID or None
        """
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        """
        Process value coming from database.

        Args:
            value: The UUID value from database
            dialect: The database dialect

        Returns:
            String representation of UUID or None
        """
        if value is None:
            return value
        return str(value)


# Create the declarative base
# All models will inherit from this Base class
Base = declarative_base()


class TimestampMixin:
    """
    Mixin for adding created_at and updated_at timestamps.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            # ... other fields

    What this provides:
    - created_at: Automatically set when record is created
    - updated_at: Automatically updated when record is modified

    Why use a mixin?
    - DRY (Don't Repeat Yourself): Define once, use everywhere
    - Consistency: All tables have same timestamp behavior
    - Automatic: No need to manually set timestamps
    """

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # PostgreSQL NOW() function
        comment="Timestamp when record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # Automatically update on record modification
        comment="Timestamp when record was last updated"
    )


def generate_uuid():
    """
    Generate a new UUID for primary keys.

    Why use UUIDs instead of auto-incrementing integers?
    - Globally unique (no collisions across databases)
    - Non-sequential (better for security)
    - Can generate client-side
    - Better for distributed systems

    Returns:
        str: String representation of UUID
    """
    return str(uuid.uuid4())


# Common metadata for all tables
# This can be used to set database-wide defaults
metadata = Base.metadata


# Example of how to create a model (not a real model, just for reference):
"""
from app.models.base import Base, TimestampMixin, generate_uuid, GUID
from sqlalchemy import Column, String

class ExampleModel(Base, TimestampMixin):
    '''Example model showing how to use the base'''
    __tablename__ = "example_table"

    # Primary key with GUID (works with both PostgreSQL and SQLite)
    id = Column(
        GUID,  # Platform-independent UUID type
        primary_key=True,
        default=generate_uuid,
        comment="Unique identifier"
    )

    # Other fields
    name = Column(String(255), nullable=False)

    # created_at and updated_at are inherited from TimestampMixin
"""
