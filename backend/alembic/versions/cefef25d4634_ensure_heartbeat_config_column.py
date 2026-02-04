"""ensure heartbeat config column

Revision ID: cefef25d4634
Revises: 2b4c2f7b3eda
Create Date: 2026-02-04 16:38:25.234627

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = 'cefef25d4634'
down_revision = '2b4c2f7b3eda'
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
