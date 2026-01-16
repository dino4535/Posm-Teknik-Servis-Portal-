"""add_completed_date_and_completed_by_to_requests

Revision ID: d026fb8dc746
Revises: 79e0c0261a96
Create Date: 2026-01-15 14:42:48.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd026fb8dc746'
down_revision = '79e0c0261a96'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add completed_date and completed_by columns to requests table
    op.add_column('requests', sa.Column('completed_date', sa.Date(), nullable=True))
    op.add_column('requests', sa.Column('completed_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_requests_completed_by', 'requests', 'users', ['completed_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_requests_completed_by', 'requests', type_='foreignkey')
    op.drop_column('requests', 'completed_by')
    op.drop_column('requests', 'completed_date')
