"""Change exercise columns from VARCHAR to INTEGER

Revision ID: b2c3d4e5f678
Revises: 6beff839c37d
Create Date: 2025-12-15 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f678'
down_revision: Union[str, None] = '6beff839c37d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade: Change sets, reps, duration_minutes columns from VARCHAR to INTEGER.

    This allows for proper numeric handling and validation.
    Existing string values will be converted to integers (NULL if not numeric).
    """
    # Alter sets column from VARCHAR(20) to INTEGER
    op.execute('''
        ALTER TABLE training_exercises
        ALTER COLUMN sets TYPE INTEGER
        USING NULLIF(sets, '')::INTEGER
    ''')

    # Alter reps column from VARCHAR(20) to INTEGER
    op.execute('''
        ALTER TABLE training_exercises
        ALTER COLUMN reps TYPE INTEGER
        USING NULLIF(reps, '')::INTEGER
    ''')

    # Alter duration_minutes column from VARCHAR(20) to INTEGER
    op.execute('''
        ALTER TABLE training_exercises
        ALTER COLUMN duration_minutes TYPE INTEGER
        USING NULLIF(duration_minutes, '')::INTEGER
    ''')


def downgrade() -> None:
    """
    Downgrade: Revert columns back to VARCHAR(20).
    """
    # Revert sets to VARCHAR(20)
    op.execute('''
        ALTER TABLE training_exercises
        ALTER COLUMN sets TYPE VARCHAR(20)
        USING sets::VARCHAR(20)
    ''')

    # Revert reps to VARCHAR(20)
    op.execute('''
        ALTER TABLE training_exercises
        ALTER COLUMN reps TYPE VARCHAR(20)
        USING reps::VARCHAR(20)
    ''')

    # Revert duration_minutes to VARCHAR(20)
    op.execute('''
        ALTER TABLE training_exercises
        ALTER COLUMN duration_minutes TYPE VARCHAR(20)
        USING duration_minutes::VARCHAR(20)
    ''')
