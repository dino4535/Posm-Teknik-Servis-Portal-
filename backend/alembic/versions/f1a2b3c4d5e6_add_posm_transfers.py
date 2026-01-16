"""add_posm_transfers

Revision ID: f1a2b3c4d5e6
Revises: 8a9b2c3d4e5f
Create Date: 2026-01-16 08:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '8a9b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # POSM transfers tablosu oluştur
    op.create_table(
        'posm_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('posm_id', sa.Integer(), nullable=False),
        sa.Column('from_depot_id', sa.Integer(), nullable=False),
        sa.Column('to_depot_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('transfer_type', sa.String(length=20), nullable=False),  # "ready" veya "repair_pending"
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('transferred_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['posm_id'], ['posm.id'], ),
        sa.ForeignKeyConstraint(['from_depot_id'], ['depots.id'], ),
        sa.ForeignKeyConstraint(['to_depot_id'], ['depots.id'], ),
        sa.ForeignKeyConstraint(['transferred_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posm_transfers_id'), 'posm_transfers', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_posm_transfers_id'), table_name='posm_transfers')
    op.drop_table('posm_transfers')
