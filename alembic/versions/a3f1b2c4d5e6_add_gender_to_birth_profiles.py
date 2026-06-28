"""add gender to birth_profiles

Revision ID: a3f1b2c4d5e6
Revises: 6fb9f6c0ff16
Create Date: 2026-06-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a3f1b2c4d5e6'
down_revision: Union[str, None] = '6fb9f6c0ff16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'birth_profiles',
        sa.Column('gender', sa.String(), nullable=False, server_default='male'),
    )
    op.alter_column('birth_profiles', 'gender', server_default=None)


def downgrade() -> None:
    op.drop_column('birth_profiles', 'gender')
