from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class BoardOnboardingStart(SQLModel):
    pass


class BoardOnboardingAnswer(SQLModel):
    answer: str
    other_text: str | None = None


class BoardOnboardingConfirm(SQLModel):
    board_type: str
    objective: str | None = None
    success_metrics: dict[str, object] | None = None
    target_date: datetime | None = None


class BoardOnboardingRead(SQLModel):
    id: UUID
    board_id: UUID
    session_key: str
    status: str
    messages: list[dict[str, object]] | None = None
    draft_goal: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime
