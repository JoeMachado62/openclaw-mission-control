"""add task assigned agent

Revision ID: 8045fbfb157f
Revises: 6df47d330227
Create Date: 2026-02-04 17:28:57.465934

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = '8045fbfb157f'
down_revision = '6df47d330227'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assigned_agent_id UUID"
    )
    op.execute(
        "ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS tasks_assigned_agent_id_fkey "
        "FOREIGN KEY (assigned_agent_id) REFERENCES agents(id)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_assigned_agent_id_fkey"
    )
    op.execute(
        "ALTER TABLE tasks DROP COLUMN IF EXISTS assigned_agent_id"
    )
