"""merge heads before recommendation tables

Revision ID: 07d48e752bae
Revises: d4b5e6f7a8c9, d4e5f6a7b8c9
Create Date: 2026-02-13 00:12:15.576279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07d48e752bae'
down_revision: Union[str, Sequence[str], None] = ('d4b5e6f7a8c9', 'd4e5f6a7b8c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
