"""add agent delete confirmation

Revision ID: e0f28e965fa5
Revises: cefef25d4634
Create Date: 2026-02-04 16:55:33.389505

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = 'e0f28e965fa5'
down_revision = 'cefef25d4634'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS delete_requested_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS delete_confirm_token_hash VARCHAR"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE agents DROP COLUMN IF EXISTS delete_confirm_token_hash"
    )
    op.execute(
        "ALTER TABLE agents DROP COLUMN IF EXISTS delete_requested_at"
    )
