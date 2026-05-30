"""
WorkFlow — User Model
Roles: manager | employee
"""
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Role(StrEnum):
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(SQLModel, table=True):
    __tablename__ = "profiles"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=255)
    hashed_password: str = Field(max_length=255)
    role: Role = Field(default=Role.EMPLOYEE)
    department: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    assigned_tasks: list["Task"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="assignee",
        sa_relationship_kwargs={"foreign_keys": "[Task.assigned_to]"},
    )
    created_tasks: list["Task"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Task.created_by]"},
    )
    work_logs: list["WorkLog"] = Relationship(back_populates="employee")  # type: ignore[name-defined]  # noqa: F821
    audit_logs: list["AuditLog"] = Relationship(back_populates="actor")  # type: ignore[name-defined]  # noqa: F821
