"""add_scheduled_reports

Revision ID: 8a9b2c3d4e5f
Revises: 64717e3446d0
Create Date: 2026-01-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8a9b2c3d4e5f'
down_revision = '64717e3446d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Scheduled reports tablosu oluştur
    op.create_table(
        'scheduled_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('depot_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recipient_user_ids', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status_filter', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('job_type_filter', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('custom_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_reports_id'), 'scheduled_reports', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheduled_reports_id'), table_name='scheduled_reports')
    op.drop_table('scheduled_reports')
