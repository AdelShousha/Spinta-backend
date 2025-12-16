"""merge heads

Revision ID: 6beff839c37d
Revises: a1b2c3d4e5f6, acf44237c45f
Create Date: 2025-12-15 19:40:15.457018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6beff839c37d'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'acf44237c45f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
