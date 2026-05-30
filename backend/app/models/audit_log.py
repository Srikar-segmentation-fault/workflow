"""
WorkFlow — AuditLog Model
Append-only, tamper-resistant audit trail. Never deleted.
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    actor_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="profiles.id", index=True
    )
    action: str = Field(
        max_length=100,
        index=True,
        # Examples: task_created, task_status_changed, log_submitted,
        #           log_ai_verified, task_deleted
    )
    entity_type: str = Field(max_length=50)  # 'task' | 'work_log' | 'user'
    entity_id: uuid.UUID = Field(index=True)
    payload: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
    )
    ip_address: Optional[str] = Field(default=None, max_length=45)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    actor: Optional["User"] = Relationship(back_populates="audit_logs")  # type: ignore[name-defined]  # noqa: F821
