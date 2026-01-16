"""add_audit_logs_and_priority

Revision ID: 64717e3446d0
Revises: a08d779b7ba5
Create Date: 2026-01-15 14:31:20.023846

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '64717e3446d0'
down_revision = 'a08d779b7ba5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Audit logs tablosu oluştur
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('old_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    
    # Requests tablosuna priority field ekle
    op.add_column('requests', sa.Column('priority', sa.String(length=20), server_default='Orta', nullable=False))


def downgrade() -> None:
    # Priority field'ı kaldır
    op.drop_column('requests', 'priority')
    
    # Audit logs tablosunu kaldır
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
