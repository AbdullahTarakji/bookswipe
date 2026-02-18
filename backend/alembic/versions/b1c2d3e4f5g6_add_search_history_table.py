"""add search_history table

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-18 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5g6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(200), nullable=False),
        sa.Column("search_type", sa.String(20), nullable=False, server_default="all"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_history_user_id", "search_history", ["user_id"])
    op.create_index("ix_search_history_user_created", "search_history", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_search_history_user_created", table_name="search_history")
    op.drop_index("ix_search_history_user_id", table_name="search_history")
    op.drop_table("search_history")
