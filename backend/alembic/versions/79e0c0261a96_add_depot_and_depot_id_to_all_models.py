"""add_depot_and_depot_id_to_all_models

Revision ID: 79e0c0261a96
Revises: 001_initial
Create Date: 2026-01-15 14:07:56.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79e0c0261a96'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create depots table
    op.create_table(
        'depots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_depots_id'), 'depots', ['id'], unique=False)
    op.create_index('ix_depots_name', 'depots', ['name'], unique=True)
    op.create_index('ix_depots_code', 'depots', ['code'], unique=True)

    # 2. Insert default depots (Manisa, İzmir, Salihli)
    op.execute("""
        INSERT INTO depots (name, code) VALUES 
        ('Manisa', 'MANISA'),
        ('İzmir', 'IZMIR'),
        ('Salihli', 'SALIHLI')
    """)

    # 3. Add depot_id to users table
    op.add_column('users', sa.Column('depot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_depot', 'users', 'depots', ['depot_id'], ['id'])

    # 4. Add depot_id to dealers table and remove unique constraint on code
    op.add_column('dealers', sa.Column('depot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_dealers_depot', 'dealers', 'depots', ['depot_id'], ['id'])
    # Remove unique constraint on code (will be unique per depot)
    op.drop_index('ix_dealers_code', table_name='dealers')
    op.create_index('ix_dealers_code', 'dealers', ['code'], unique=False)
    # Create composite unique index (code + depot_id)
    op.create_index('ix_dealers_code_depot', 'dealers', ['code', 'depot_id'], unique=True)

    # 5. Add depot_id to posm table and remove unique constraint on name
    op.add_column('posm', sa.Column('depot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_posm_depot', 'posm', 'depots', ['depot_id'], ['id'])
    # Remove unique constraint on name (will be unique per depot)
    op.drop_index('ix_posm_name', table_name='posm')
    op.create_index('ix_posm_name', 'posm', ['name'], unique=False)
    # Create composite unique index (name + depot_id)
    op.create_index('ix_posm_name_depot', 'posm', ['name', 'depot_id'], unique=True)

    # 6. Add depot_id to requests table
    op.add_column('requests', sa.Column('depot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_requests_depot', 'requests', 'depots', ['depot_id'], ['id'])

    # 7. Update existing records: Set depot_id based on dealer's depot (if dealer has depot)
    # For users: We'll leave them NULL for now, admin can assign later
    # For requests: Copy depot_id from dealer
    op.execute("""
        UPDATE requests r
        SET depot_id = d.depot_id
        FROM dealers d
        WHERE r.dealer_id = d.id AND d.depot_id IS NOT NULL
    """)


def downgrade() -> None:
    # Remove depot_id columns
    op.drop_constraint('fk_requests_depot', 'requests', type_='foreignkey')
    op.drop_column('requests', 'depot_id')
    
    op.drop_constraint('fk_posm_depot', 'posm', type_='foreignkey')
    op.drop_index('ix_posm_name_depot', table_name='posm')
    op.drop_index('ix_posm_name', table_name='posm')
    op.create_index('ix_posm_name', 'posm', ['name'], unique=True)
    op.drop_column('posm', 'depot_id')
    
    op.drop_constraint('fk_dealers_depot', 'dealers', type_='foreignkey')
    op.drop_index('ix_dealers_code_depot', table_name='dealers')
    op.drop_index('ix_dealers_code', table_name='dealers')
    op.create_index('ix_dealers_code', 'dealers', ['code'], unique=True)
    op.drop_column('dealers', 'depot_id')
    
    op.drop_constraint('fk_users_depot', 'users', type_='foreignkey')
    op.drop_column('users', 'depot_id')
    
    # Drop depots table
    op.drop_index('ix_depots_code', table_name='depots')
    op.drop_index('ix_depots_name', table_name='depots')
    op.drop_index(op.f('ix_depots_id'), table_name='depots')
    op.drop_table('depots')
