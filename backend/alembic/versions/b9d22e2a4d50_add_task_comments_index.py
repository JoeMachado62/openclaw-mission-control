"""add task comments index

Revision ID: b9d22e2a4d50
Revises: 8045fbfb157f
Create Date: 2026-02-04 17:32:06.204331

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = 'b9d22e2a4d50'
down_revision = '8045fbfb157f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_activity_events_task_comment "
        "ON activity_events (task_id, created_at) "
        "WHERE event_type = 'task.comment'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_activity_events_task_comment")
