"""add_stripe_subscription_fields

Revision ID: d4b5e6f7a8c9
Revises: c3a8f2e91d04
Create Date: 2026-02-12 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4b5e6f7a8c9'
down_revision: Union[str, Sequence[str], None] = 'c3a8f2e91d04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Stripe subscription fields to users and create daily_swipe_counts table."""
    # Add Stripe fields to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(20), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('subscription_plan', sa.String(20), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('subscription_end_date', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=False)

    # Create daily_swipe_counts table
    op.create_table(
        'daily_swipe_counts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('swipe_date', sa.Date(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'swipe_date', name='uq_user_swipe_date'),
    )
    op.create_index(op.f('ix_daily_swipe_counts_user_id'), 'daily_swipe_counts', ['user_id'], unique=False)


def downgrade() -> None:
    """Remove Stripe subscription fields and daily_swipe_counts table."""
    op.drop_index(op.f('ix_daily_swipe_counts_user_id'), table_name='daily_swipe_counts')
    op.drop_table('daily_swipe_counts')
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'subscription_end_date')
    op.drop_column('users', 'subscription_plan')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_customer_id')
