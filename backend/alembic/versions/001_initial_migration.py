"""Initial migration: create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (if not exists)
    conn = op.get_bind()
    
    # Check and create userrole enum
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'userrole'"))
    if result.fetchone() is None:
        op.execute("CREATE TYPE userrole AS ENUM ('user', 'admin', 'tech')")
    
    # Check and create jobtype enum
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'jobtype'"))
    if result.fetchone() is None:
        op.execute("CREATE TYPE jobtype AS ENUM ('Montaj', 'Demontaj', 'Bakım')")
    
    # Check and create requeststatus enum
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'requeststatus'"))
    if result.fetchone() is None:
        op.execute("CREATE TYPE requeststatus AS ENUM ('Beklemede', 'TakvimeEklendi', 'Tamamlandı', 'İptal')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', postgresql.ENUM('user', 'admin', 'tech', name='userrole', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create territories table
    op.create_table(
        'territories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_territories_id'), 'territories', ['id'], unique=False)
    op.create_index('ix_territories_name', 'territories', ['name'], unique=True)

    # Create dealers table
    op.create_table(
        'dealers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('territory_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.ForeignKeyConstraint(['territory_id'], ['territories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dealers_id'), 'dealers', ['id'], unique=False)
    op.create_index('ix_dealers_code', 'dealers', ['code'], unique=True)

    # Create posm table
    op.create_table(
        'posm',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('ready_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('repair_pending_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posm_id'), 'posm', ['id'], unique=False)
    op.create_index('ix_posm_name', 'posm', ['name'], unique=True)

    # Create requests table
    op.create_table(
        'requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('dealer_id', sa.Integer(), nullable=False),
        sa.Column('territory_id', sa.Integer(), nullable=True),
        sa.Column('current_posm', sa.String(), nullable=True),
        sa.Column('job_type', postgresql.ENUM('Montaj', 'Demontaj', 'Bakım', name='jobtype', create_type=False), nullable=False),
        sa.Column('job_detail', sa.Text(), nullable=True),
        sa.Column('request_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('requested_date', sa.Date(), nullable=False),
        sa.Column('planned_date', sa.Date(), nullable=True),
        sa.Column('posm_id', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('Beklemede', 'TakvimeEklendi', 'Tamamlandı', 'İptal', name='requeststatus', create_type=False), nullable=False, server_default='Beklemede'),
        sa.Column('job_done_desc', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['dealer_id'], ['dealers.id'], ),
        sa.ForeignKeyConstraint(['territory_id'], ['territories.id'], ),
        sa.ForeignKeyConstraint(['posm_id'], ['posm.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requests_id'), 'requests', ['id'], unique=False)

    # Create photos table
    op.create_table(
        'photos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('path_or_url', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_photos_id'), 'photos', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_photos_id'), table_name='photos')
    op.drop_table('photos')
    op.drop_index(op.f('ix_requests_id'), table_name='requests')
    op.drop_table('requests')
    op.drop_index('ix_posm_name', table_name='posm')
    op.drop_index(op.f('ix_posm_id'), table_name='posm')
    op.drop_table('posm')
    op.drop_index('ix_dealers_code', table_name='dealers')
    op.drop_index(op.f('ix_dealers_id'), table_name='dealers')
    op.drop_table('dealers')
    op.drop_index('ix_territories_name', table_name='territories')
    op.drop_index(op.f('ix_territories_id'), table_name='territories')
    op.drop_table('territories')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    sa.Enum(name='requeststatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
