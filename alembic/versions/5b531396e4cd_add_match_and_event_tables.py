"""Add match and event tables

Revision ID: 5b531396e4cd
Revises: 4a423284273a
Create Date: 2025-11-11 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5b531396e4cd'
down_revision: Union[str, None] = '4a423284273a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create opponent_clubs table
    op.create_table('opponent_clubs',
        sa.Column('opponent_club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('opponent_name', sa.String(length=255), nullable=False),
        sa.Column('statsbomb_team_id', sa.Integer(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('opponent_club_id'),
        sa.UniqueConstraint('statsbomb_team_id')
    )
    op.create_index(op.f('ix_opponent_clubs_statsbomb_team_id'), 'opponent_clubs', ['statsbomb_team_id'], unique=False)

    # Create matches table
    op.create_table('matches',
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('opponent_club_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('opponent_name', sa.String(length=255), nullable=False),
        sa.Column('match_date', sa.Date(), nullable=False),
        sa.Column('match_time', sa.Time(), nullable=True),
        sa.Column('is_home_match', sa.Boolean(), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.club_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opponent_club_id'], ['opponent_clubs.opponent_club_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('match_id')
    )
    op.create_index(op.f('ix_matches_club_id'), 'matches', ['club_id'], unique=False)
    op.create_index(op.f('ix_matches_match_date'), 'matches', ['match_date'], unique=False)

    # Create opponent_players table
    op.create_table('opponent_players',
        sa.Column('opponent_player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('opponent_club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_name', sa.String(length=255), nullable=False),
        sa.Column('statsbomb_player_id', sa.Integer(), nullable=True),
        sa.Column('jersey_number', sa.Integer(), nullable=True),
        sa.Column('position', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['opponent_club_id'], ['opponent_clubs.opponent_club_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('opponent_player_id')
    )
    op.create_index(op.f('ix_opponent_players_opponent_club_id'), 'opponent_players', ['opponent_club_id'], unique=False)
    op.create_index(op.f('ix_opponent_players_statsbomb_player_id'), 'opponent_players', ['statsbomb_player_id'], unique=False)

    # Create goals table
    op.create_table('goals',
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_name', sa.String(length=255), nullable=False),
        sa.Column('scorer_name', sa.String(length=255), nullable=False),
        sa.Column('assist_name', sa.String(length=255), nullable=True),
        sa.Column('minute', sa.Integer(), nullable=False),
        sa.Column('second', sa.Integer(), nullable=True),
        sa.Column('period', sa.Integer(), nullable=False),
        sa.Column('goal_type', sa.String(length=50), nullable=True),
        sa.Column('body_part', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.match_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('goal_id')
    )
    op.create_index(op.f('ix_goals_match_id'), 'goals', ['match_id'], unique=False)

    # Create events table with JSONB column
    op.create_table('events',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('statsbomb_player_id', sa.Integer(), nullable=True),
        sa.Column('statsbomb_team_id', sa.Integer(), nullable=True),
        sa.Column('player_name', sa.String(length=255), nullable=True),
        sa.Column('team_name', sa.String(length=255), nullable=True),
        sa.Column('event_type_name', sa.String(length=100), nullable=True),
        sa.Column('position_name', sa.String(length=50), nullable=True),
        sa.Column('minute', sa.Integer(), nullable=True),
        sa.Column('second', sa.Integer(), nullable=True),
        sa.Column('period', sa.Integer(), nullable=True),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.match_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index(op.f('ix_events_match_id'), 'events', ['match_id'], unique=False)
    op.create_index(op.f('ix_events_statsbomb_player_id'), 'events', ['statsbomb_player_id'], unique=False)
    op.create_index(op.f('ix_events_event_type_name'), 'events', ['event_type_name'], unique=False)

    # Create GIN index on event_data for efficient JSONB queries
    op.create_index('idx_events_event_data', 'events', ['event_data'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_index('idx_events_event_data', table_name='events', postgresql_using='gin')
    op.drop_index(op.f('ix_events_event_type_name'), table_name='events')
    op.drop_index(op.f('ix_events_statsbomb_player_id'), table_name='events')
    op.drop_index(op.f('ix_events_match_id'), table_name='events')
    op.drop_table('events')

    op.drop_index(op.f('ix_goals_match_id'), table_name='goals')
    op.drop_table('goals')

    op.drop_index(op.f('ix_opponent_players_statsbomb_player_id'), table_name='opponent_players')
    op.drop_index(op.f('ix_opponent_players_opponent_club_id'), table_name='opponent_players')
    op.drop_table('opponent_players')

    op.drop_index(op.f('ix_matches_match_date'), table_name='matches')
    op.drop_index(op.f('ix_matches_club_id'), table_name='matches')
    op.drop_table('matches')

    op.drop_index(op.f('ix_opponent_clubs_statsbomb_team_id'), table_name='opponent_clubs')
    op.drop_table('opponent_clubs')
