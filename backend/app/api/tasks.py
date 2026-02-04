from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc
from sqlmodel import Session, col, select

from app.api.deps import (
    ActorContext,
    get_board_or_404,
    get_task_or_404,
    require_admin_auth,
    require_admin_or_agent,
)
from app.core.auth import AuthContext
from app.db.session import get_session
from app.models.agents import Agent
from app.models.activity_events import ActivityEvent
from app.models.boards import Board
from app.models.tasks import Task
from app.schemas.tasks import (
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.services.activity_log import record_activity

router = APIRouter(prefix="/boards/{board_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    board: Board = Depends(get_board_or_404),
    session: Session = Depends(get_session),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> list[Task]:
    return list(session.exec(select(Task).where(Task.board_id == board.id)))


@router.post("", response_model=TaskRead)
def create_task(
    payload: TaskCreate,
    board: Board = Depends(get_board_or_404),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(require_admin_auth),
) -> Task:
    task = Task.model_validate(payload)
    task.board_id = board.id
    if task.created_by_user_id is None and auth.user is not None:
        task.created_by_user_id = auth.user.id
    session.add(task)
    session.commit()
    session.refresh(task)

    record_activity(
        session,
        event_type="task.created",
        task_id=task.id,
        message=f"Task created: {task.title}.",
    )
    session.commit()
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    payload: TaskUpdate,
    task: Task = Depends(get_task_or_404),
    session: Session = Depends(get_session),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> Task:
    previous_status = task.status
    updates = payload.model_dump(exclude_unset=True)
    if actor.actor_type == "agent":
        if actor.agent and actor.agent.board_id and task.board_id:
            if actor.agent.board_id != task.board_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        allowed_fields = {"status"}
        if not set(updates).issubset(allowed_fields):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        if "status" in updates:
            if updates["status"] == "inbox":
                task.assigned_agent_id = None
            else:
                task.assigned_agent_id = actor.agent.id if actor.agent else None
    elif "status" in updates and updates["status"] == "inbox":
        task.assigned_agent_id = None
    if "assigned_agent_id" in updates and updates["assigned_agent_id"]:
        agent = session.get(Agent, updates["assigned_agent_id"])
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if agent.board_id and task.board_id and agent.board_id != task.board_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)
    for key, value in updates.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    if "status" in updates and task.status != previous_status:
        event_type = "task.status_changed"
        message = f"Task moved to {task.status}: {task.title}."
    else:
        event_type = "task.updated"
        message = f"Task updated: {task.title}."
    record_activity(
        session,
        event_type=event_type,
        task_id=task.id,
        message=message,
        agent_id=actor.agent.id if actor.actor_type == "agent" and actor.agent else None,
    )
    session.commit()
    return task


@router.delete("/{task_id}")
def delete_task(
    session: Session = Depends(get_session),
    task: Task = Depends(get_task_or_404),
    auth: AuthContext = Depends(require_admin_auth),
) -> dict[str, bool]:
    session.delete(task)
    session.commit()
    return {"ok": True}


@router.get("/{task_id}/comments", response_model=list[TaskCommentRead])
def list_task_comments(
    task: Task = Depends(get_task_or_404),
    session: Session = Depends(get_session),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> list[ActivityEvent]:
    if actor.actor_type == "agent" and actor.agent:
        if actor.agent.board_id and task.board_id and actor.agent.board_id != task.board_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    statement = (
        select(ActivityEvent)
        .where(col(ActivityEvent.task_id) == task.id)
        .where(col(ActivityEvent.event_type) == "task.comment")
        .order_by(asc(col(ActivityEvent.created_at)))
    )
    return list(session.exec(statement))


@router.post("/{task_id}/comments", response_model=TaskCommentRead)
def create_task_comment(
    payload: TaskCommentCreate,
    task: Task = Depends(get_task_or_404),
    session: Session = Depends(get_session),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> ActivityEvent:
    if actor.actor_type == "agent" and actor.agent:
        if actor.agent.board_id and task.board_id and actor.agent.board_id != task.board_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    event = ActivityEvent(
        event_type="task.comment",
        message=payload.message.strip(),
        task_id=task.id,
        agent_id=actor.agent.id if actor.actor_type == "agent" and actor.agent else None,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
