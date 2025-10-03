
"""initial schema

Revision ID: 0001_init
Revises: 
Create Date: 2025-10-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'members',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('primary_email', sa.String(length=320), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'meetings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('scheduled_start', sa.DateTime, nullable=True),
        sa.Column('scheduled_end', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'application_identities',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('application', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=512), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('uri', sa.String(length=1024), nullable=True),
        sa.Column('is_primary', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('entity_type', 'entity_id', 'application', name='uq_identity_entity_app')
    )
    op.create_index('ix_identities_entity', 'application_identities', ['entity_type', 'entity_id'])
    op.create_index('ix_identities_application', 'application_identities', ['application'])


def downgrade() -> None:
    op.drop_index('ix_identities_application', table_name='application_identities')
    op.drop_index('ix_identities_entity', table_name='application_identities')
    op.drop_table('application_identities')
    op.drop_table('projects')
    op.drop_table('meetings')
    op.drop_table('members')
