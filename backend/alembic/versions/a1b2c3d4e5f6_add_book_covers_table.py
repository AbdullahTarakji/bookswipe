"""add book_covers table for CDN cover images

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-02-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'book_covers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('book_id', sa.String(length=50), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=False),
        sa.Column('card_url', sa.String(length=500), nullable=False),
        sa.Column('detail_url', sa.String(length=500), nullable=False),
        sa.Column('blurhash', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id'),
    )
    op.create_index('ix_book_covers_book_id', 'book_covers', ['book_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_book_covers_book_id', table_name='book_covers')
    op.drop_table('book_covers')
