"""WorkFlow — Pydantic schemas for Task endpoints."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import Priority, Status


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    description: str | None = None
    assigned_to: uuid.UUID
    priority: Priority = Priority.MEDIUM
    deadline: datetime


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assigned_to: uuid.UUID | None = None
    priority: Priority | None = None
    deadline: datetime | None = None


class TaskStatusUpdate(BaseModel):
    status: Status


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    assigned_to: uuid.UUID | None
    assignee_name: str | None  # flattened for convenience
    created_by: uuid.UUID
    creator_name: str | None
    priority: Priority
    status: Status
    deadline: datetime
    created_at: datetime
    updated_at: datetime
    log_count: int = 0
    latest_ai_confidence: str | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    overdue_count: int
