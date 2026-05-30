"""WorkFlow — Task Repository."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Status, Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def get_by_id_with_relations(self, task_id: uuid.UUID) -> Task | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.is_deleted == False)  # noqa: E712
            .options(selectinload(Task.assignee), selectinload(Task.creator))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active(
        self,
        *,
        limit: int = 200,
        offset: int = 0,
        status: Status | None = None,
        priority: str | None = None,
    ) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.is_deleted == False)  # noqa: E712
            .options(selectinload(Task.assignee), selectinload(Task.creator))
            .order_by(Task.deadline.asc())
            .offset(offset)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Task.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_employee(self, employee_id: uuid.UUID) -> list[Task]:
        stmt = (
            select(Task)
            .where(
                Task.assigned_to == employee_id,
                Task.is_deleted == False,  # noqa: E712
            )
            .options(selectinload(Task.creator))
            .order_by(Task.deadline.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue(self) -> list[Task]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Task)
            .where(
                Task.deadline < now,
                Task.status.not_in([Status.COMPLETED]),
                Task.is_deleted == False,  # noqa: E712
            )
            .options(selectinload(Task.assignee))
            .order_by(Task.deadline.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, task: Task) -> Task:
        task.is_deleted = True
        task.updated_at = datetime.utcnow()
        self.session.add(task)
        await self.session.flush()
        return task
