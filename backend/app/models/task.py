"""
WorkFlow — Task Model
Priority: low | medium | high | critical
Status: pending | in_progress | completed | overdue
"""
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    title: str = Field(max_length=500, index=True)
    description: Optional[str] = Field(default=None)
    assigned_to: Optional[uuid.UUID] = Field(
        default=None, foreign_key="profiles.id", index=True
    )
    created_by: uuid.UUID = Field(foreign_key="profiles.id")
    priority: Priority = Field(default=Priority.MEDIUM)
    status: Status = Field(default=Status.PENDING)
    deadline: datetime
    is_deleted: bool = Field(default=False)  # soft delete
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    assignee: Optional["User"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="assigned_tasks",
        sa_relationship_kwargs={"foreign_keys": "[Task.assigned_to]"},
    )
    creator: "User" = Relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="created_tasks",
        sa_relationship_kwargs={"foreign_keys": "[Task.created_by]"},
    )
    work_logs: list["WorkLog"] = Relationship(back_populates="task")  # type: ignore[name-defined]  # noqa: F821
