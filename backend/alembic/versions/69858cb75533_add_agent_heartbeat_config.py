"""add agent heartbeat config

Revision ID: 69858cb75533
Revises: f1a2b3c4d5e6
Create Date: 2026-02-04 16:32:42.028772

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = '69858cb75533'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS heartbeat_config JSON"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE agents DROP COLUMN IF EXISTS heartbeat_config"
    )
