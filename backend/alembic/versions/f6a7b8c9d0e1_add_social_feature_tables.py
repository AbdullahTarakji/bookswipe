"""add user_profiles, follows, book_lists, book_list_items, and activity_events tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create social feature tables."""
    op.create_table('user_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('reading_goal', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)

    op.create_table('follows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('following_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['following_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_id', 'following_id', name='uq_follow'),
    )
    op.create_index('ix_follows_follower_id', 'follows', ['follower_id'], unique=False)
    op.create_index('ix_follows_following_id', 'follows', ['following_id'], unique=False)

    op.create_table('book_lists',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=False, server_default=''),
        sa.Column('is_public', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_book_lists_user_id', 'book_lists', ['user_id'], unique=False)

    op.create_table('book_list_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.String(length=50), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['book_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('list_id', 'book_id', name='uq_list_book'),
    )
    op.create_index('ix_book_list_items_list_id', 'book_list_items', ['list_id'], unique=False)

    op.create_table('activity_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_activity_events_user_id', 'activity_events', ['user_id'], unique=False)
    op.create_index('ix_activity_events_created_at', 'activity_events', ['created_at'], unique=False)
    op.create_index('ix_activity_events_user_created', 'activity_events', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Drop social feature tables."""
    op.drop_index('ix_activity_events_user_created', table_name='activity_events')
    op.drop_index('ix_activity_events_created_at', table_name='activity_events')
    op.drop_index('ix_activity_events_user_id', table_name='activity_events')
    op.drop_table('activity_events')
    op.drop_index('ix_book_list_items_list_id', table_name='book_list_items')
    op.drop_table('book_list_items')
    op.drop_index('ix_book_lists_user_id', table_name='book_lists')
    op.drop_table('book_lists')
    op.drop_index('ix_follows_following_id', table_name='follows')
    op.drop_index('ix_follows_follower_id', table_name='follows')
    op.drop_table('follows')
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
