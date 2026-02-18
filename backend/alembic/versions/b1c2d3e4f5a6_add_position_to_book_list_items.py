"""add position to book_list_items

Revision ID: b1c2d3e4f5a6
Revises:
Create Date: 2026-02-18 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('book_list_items', sa.Column('position', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('book_list_items', 'position')
