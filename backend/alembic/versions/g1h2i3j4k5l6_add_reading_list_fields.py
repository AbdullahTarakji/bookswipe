"""Add position, title, authors, thumbnail to book_list_items

Revision ID: g1h2i3j4k5l6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-18 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "g1h2i3j4k5l6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("book_list_items", sa.Column("title", sa.String(500), nullable=False, server_default=""))
    op.add_column("book_list_items", sa.Column("authors", sa.String(500), nullable=False, server_default=""))
    op.add_column("book_list_items", sa.Column("thumbnail", sa.String(500), nullable=False, server_default=""))
    op.add_column("book_list_items", sa.Column("position", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("book_list_items", "position")
    op.drop_column("book_list_items", "thumbnail")
    op.drop_column("book_list_items", "authors")
    op.drop_column("book_list_items", "title")
