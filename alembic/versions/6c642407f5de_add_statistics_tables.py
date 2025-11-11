"""Add statistics tables

Revision ID: 6c642407f5de
Revises: 5b531396e4cd
Create Date: 2025-11-11 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6c642407f5de'
down_revision: Union[str, None] = '5b531396e4cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create match_statistics table
    op.create_table('match_statistics',
        sa.Column('statistics_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_type', sa.String(length=20), nullable=False),
        sa.Column('possession_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('expected_goals', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('total_shots', sa.Integer(), nullable=True),
        sa.Column('shots_on_target', sa.Integer(), nullable=True),
        sa.Column('shots_off_target', sa.Integer(), nullable=True),
        sa.Column('goalkeeper_saves', sa.Integer(), nullable=True),
        sa.Column('total_passes', sa.Integer(), nullable=True),
        sa.Column('passes_completed', sa.Integer(), nullable=True),
        sa.Column('pass_completion_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('passes_in_final_third', sa.Integer(), nullable=True),
        sa.Column('long_passes', sa.Integer(), nullable=True),
        sa.Column('crosses', sa.Integer(), nullable=True),
        sa.Column('total_dribbles', sa.Integer(), nullable=True),
        sa.Column('successful_dribbles', sa.Integer(), nullable=True),
        sa.Column('total_tackles', sa.Integer(), nullable=True),
        sa.Column('tackle_success_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('interceptions', sa.Integer(), nullable=True),
        sa.Column('ball_recoveries', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.match_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('statistics_id'),
        sa.UniqueConstraint('match_id', 'team_type', name='uq_match_statistics_match_team')
    )
    op.create_index(op.f('ix_match_statistics_match_id'), 'match_statistics', ['match_id'], unique=False)

    # Create player_match_statistics table
    op.create_table('player_match_statistics',
        sa.Column('player_match_stats_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assists', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expected_goals', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('shots', sa.Integer(), nullable=True),
        sa.Column('shots_on_target', sa.Integer(), nullable=True),
        sa.Column('total_dribbles', sa.Integer(), nullable=True),
        sa.Column('successful_dribbles', sa.Integer(), nullable=True),
        sa.Column('total_passes', sa.Integer(), nullable=True),
        sa.Column('completed_passes', sa.Integer(), nullable=True),
        sa.Column('short_passes', sa.Integer(), nullable=True),
        sa.Column('long_passes', sa.Integer(), nullable=True),
        sa.Column('final_third_passes', sa.Integer(), nullable=True),
        sa.Column('crosses', sa.Integer(), nullable=True),
        sa.Column('tackles', sa.Integer(), nullable=True),
        sa.Column('tackle_success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('interceptions', sa.Integer(), nullable=True),
        sa.Column('interception_success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['match_id'], ['matches.match_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('player_match_stats_id'),
        sa.UniqueConstraint('player_id', 'match_id', name='uq_player_match_statistics_player_match')
    )
    op.create_index(op.f('ix_player_match_statistics_player_id'), 'player_match_statistics', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_match_statistics_match_id'), 'player_match_statistics', ['match_id'], unique=False)

    # Create club_season_statistics table
    op.create_table('club_season_statistics',
        sa.Column('club_stats_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('matches_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('wins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('draws', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('goals_scored', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('goals_conceded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_clean_sheets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_goals_per_match', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_goals_conceded_per_match', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_possession_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_xg_per_match', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_total_shots', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_shots_on_target', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_total_passes', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('pass_completion_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_final_third_passes', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_crosses', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_dribbles', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_successful_dribbles', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_tackles', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tackle_success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_interceptions', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('interception_success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_ball_recoveries', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_saves_per_match', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.club_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('club_stats_id'),
        sa.UniqueConstraint('club_id')
    )
    op.create_index(op.f('ix_club_season_statistics_club_id'), 'club_season_statistics', ['club_id'], unique=True)

    # Create player_season_statistics table
    op.create_table('player_season_statistics',
        sa.Column('player_stats_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('matches_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('goals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assists', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expected_goals', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('shots_per_game', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('shots_on_target_per_game', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('total_passes', sa.Integer(), nullable=True),
        sa.Column('passes_completed', sa.Integer(), nullable=True),
        sa.Column('total_dribbles', sa.Integer(), nullable=True),
        sa.Column('successful_dribbles', sa.Integer(), nullable=True),
        sa.Column('tackles', sa.Integer(), nullable=True),
        sa.Column('tackle_success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('interceptions', sa.Integer(), nullable=True),
        sa.Column('interception_success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('attacking_rating', sa.Integer(), nullable=True),
        sa.Column('technique_rating', sa.Integer(), nullable=True),
        sa.Column('tactical_rating', sa.Integer(), nullable=True),
        sa.Column('defending_rating', sa.Integer(), nullable=True),
        sa.Column('creativity_rating', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('player_stats_id'),
        sa.UniqueConstraint('player_id')
    )
    op.create_index(op.f('ix_player_season_statistics_player_id'), 'player_season_statistics', ['player_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_player_season_statistics_player_id'), table_name='player_season_statistics')
    op.drop_table('player_season_statistics')

    op.drop_index(op.f('ix_club_season_statistics_club_id'), table_name='club_season_statistics')
    op.drop_table('club_season_statistics')

    op.drop_index(op.f('ix_player_match_statistics_match_id'), table_name='player_match_statistics')
    op.drop_index(op.f('ix_player_match_statistics_player_id'), table_name='player_match_statistics')
    op.drop_table('player_match_statistics')

    op.drop_index(op.f('ix_match_statistics_match_id'), table_name='match_statistics')
    op.drop_table('match_statistics')
