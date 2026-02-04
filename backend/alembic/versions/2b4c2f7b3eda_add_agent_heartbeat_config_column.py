"""add agent heartbeat config column

Revision ID: 2b4c2f7b3eda
Revises: 69858cb75533
Create Date: 2026-02-04 16:36:55.587762

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = '2b4c2f7b3eda'
down_revision = '69858cb75533'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS heartbeat_config JSON"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS heartbeat_config")
