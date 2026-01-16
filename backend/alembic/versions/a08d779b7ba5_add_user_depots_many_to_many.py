"""add_user_depots_many_to_many

Revision ID: a08d779b7ba5
Revises: d026fb8dc746
Create Date: 2026-01-15 15:35:22.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a08d779b7ba5'
down_revision = 'd026fb8dc746'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_depots junction table
    op.create_table(
        'user_depots',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('depot_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depot_id'], ['depots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'depot_id')
    )
    op.create_index('ix_user_depots_user_id', 'user_depots', ['user_id'])
    op.create_index('ix_user_depots_depot_id', 'user_depots', ['depot_id'])
    
    # Migrate existing depot_id data to user_depots
    # Copy users with depot_id to user_depots table
    op.execute("""
        INSERT INTO user_depots (user_id, depot_id)
        SELECT id, depot_id
        FROM users
        WHERE depot_id IS NOT NULL
    """)
    
    # Note: depot_id column in users table will remain for backward compatibility
    # but we'll use user_depots for many-to-many relationship


def downgrade() -> None:
    op.drop_index('ix_user_depots_depot_id', table_name='user_depots')
    op.drop_index('ix_user_depots_user_id', table_name='user_depots')
    op.drop_table('user_depots')
