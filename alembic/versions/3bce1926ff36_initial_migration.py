"""Initial migration

Revision ID: 3bce1926ff36
Revises: 
Create Date: 2026-05-12 12:04:02.565676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bce1926ff36'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_username', 'users', ['username'], unique=True)
    op.create_index('idx_email', 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create databases table
    op.create_table('databases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='5432'),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('database_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='disconnected'),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_owner_id', 'databases', ['owner_id'], unique=False)
    op.create_index(op.f('ix_databases_id'), 'databases', ['id'], unique=False)
    op.create_unique_constraint('unique_owner_database_name', 'databases', ['owner_id', 'name'])

    # Create tables table
    op.create_table('tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('database_id', sa.Integer(), nullable=False),
        sa.Column('row_count', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['database_id'], ['databases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tables_database_id', 'tables', ['database_id'], unique=False)
    op.create_index(op.f('ix_tables_id'), 'tables', ['id'], unique=False)
    op.create_unique_constraint('unique_database_table_name', 'tables', ['database_id', 'name'])

    # Create columns table
    op.create_table('columns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_primary_key', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_unique', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_columns_table_id', 'columns', ['table_id'], unique=False)
    op.create_index(op.f('ix_columns_id'), 'columns', ['id'], unique=False)

    # Create indexes table
    op.create_table('indexes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('columns', sa.Text(), nullable=False),
        sa.Column('is_unique', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_indexes_table_id', 'indexes', ['table_id'], unique=False)
    op.create_index(op.f('ix_indexes_id'), 'indexes', ['id'], unique=False)

    # Create query_logs table
    op.create_table('query_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('database_id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['database_id'], ['databases.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_query_logs_user_id', 'query_logs', ['user_id'], unique=False)
    op.create_index('ix_query_logs_database_id', 'query_logs', ['database_id'], unique=False)
    op.create_index('ix_query_logs_created_at', 'query_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_query_logs_id'), 'query_logs', ['id'], unique=False)

    # Create backup_logs table
    op.create_table('backup_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('database_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('backup_name', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['database_id'], ['databases.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backup_logs_database_id', 'backup_logs', ['database_id'], unique=False)
    op.create_index('ix_backup_logs_user_id', 'backup_logs', ['user_id'], unique=False)
    op.create_index('ix_backup_logs_status', 'backup_logs', ['status'], unique=False)
    op.create_index(op.f('ix_backup_logs_id'), 'backup_logs', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('backup_logs')
    op.drop_table('query_logs')
    op.drop_table('indexes')
    op.drop_table('columns')
    op.drop_table('tables')
    op.drop_table('databases')
    op.drop_table('users')
