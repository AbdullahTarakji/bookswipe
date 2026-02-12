"""add_provider_id_index

Revision ID: c3a8f2e91d04
Revises: 1f619dddb3fd
Create Date: 2026-02-12 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3a8f2e91d04'
down_revision: Union[str, Sequence[str], None] = '1f619dddb3fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add index on users.provider_id for faster OAuth lookups."""
    op.create_index(op.f('ix_users_provider_id'), 'users', ['provider_id'], unique=False)


def downgrade() -> None:
    """Remove provider_id index."""
    op.drop_index(op.f('ix_users_provider_id'), table_name='users')
