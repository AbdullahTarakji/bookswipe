"""add_ban_fields_to_users

Revision ID: d4e5f6a7b8c9
Revises: c3a8f2e91d04
Create Date: 2026-02-12 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3a8f2e91d04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ban-related fields to users table."""
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('banned_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('ban_reason', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Remove ban-related fields from users table."""
    op.drop_column('users', 'ban_reason')
    op.drop_column('users', 'banned_at')
    op.drop_column('users', 'is_banned')
