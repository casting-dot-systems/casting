from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20241006_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="inactive"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agents_org_id", "agents", ["org_id"])


def downgrade() -> None:
    op.drop_index("ix_agents_org_id", table_name="agents")
    op.drop_table("agents")
