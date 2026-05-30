"""WorkFlow — WorkLog Repository."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.work_log import WorkLog
from app.repositories.base import BaseRepository


class LogRepository(BaseRepository[WorkLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(WorkLog, session)

    async def get_by_task(self, task_id: uuid.UUID) -> list[WorkLog]:
        stmt = (
            select(WorkLog)
            .where(WorkLog.task_id == task_id)
            .options(selectinload(WorkLog.employee))
            .order_by(WorkLog.submitted_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_employee(
        self, employee_id: uuid.UUID, *, limit: int = 50
    ) -> list[WorkLog]:
        stmt = (
            select(WorkLog)
            .where(WorkLog.employee_id == employee_id)
            .options(selectinload(WorkLog.task))
            .order_by(WorkLog.submitted_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_for_task(self, task_id: uuid.UUID) -> WorkLog | None:
        stmt = (
            select(WorkLog)
            .where(WorkLog.task_id == task_id)
            .order_by(WorkLog.submitted_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
