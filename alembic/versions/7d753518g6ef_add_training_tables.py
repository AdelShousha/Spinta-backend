"""Add training tables

Revision ID: 7d753518g6ef
Revises: 6c642407f5de
Create Date: 2025-11-11 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7d753518g6ef'
down_revision: Union[str, None] = '6c642407f5de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create training_plans table
    op.create_table('training_plans',
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('plan_title', sa.String(length=255), nullable=False),
        sa.Column('plan_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['coaches.coach_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('plan_id')
    )
    op.create_index(op.f('ix_training_plans_player_id'), 'training_plans', ['player_id'], unique=False)
    op.create_index(op.f('ix_training_plans_created_by'), 'training_plans', ['created_by'], unique=False)
    op.create_index(op.f('ix_training_plans_status'), 'training_plans', ['status'], unique=False)

    # Create training_exercises table
    op.create_table('training_exercises',
        sa.Column('exercise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exercise_title', sa.String(length=255), nullable=False),
        sa.Column('exercise_description', sa.Text(), nullable=True),
        sa.Column('exercise_order', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('repetitions', sa.Integer(), nullable=True),
        sa.Column('sets', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['training_plans.plan_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('exercise_id')
    )
    op.create_index(op.f('ix_training_exercises_plan_id'), 'training_exercises', ['plan_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_training_exercises_plan_id'), table_name='training_exercises')
    op.drop_table('training_exercises')

    op.drop_index(op.f('ix_training_plans_status'), table_name='training_plans')
    op.drop_index(op.f('ix_training_plans_created_by'), table_name='training_plans')
    op.drop_index(op.f('ix_training_plans_player_id'), table_name='training_plans')
    op.drop_table('training_plans')
