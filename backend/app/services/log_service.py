"""WorkFlow — Work Log Service."""
import uuid
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.work_log import WorkLog
from app.repositories.audit_repository import AuditRepository
from app.repositories.log_repository import LogRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.work_log import LogListResponse, LogResponse, LogSubmit
from app.services.ai_service import RAGService, verifyLog

logger = structlog.get_logger()


def _log_to_response(log: WorkLog) -> LogResponse:
    return LogResponse(
        id=log.id,
        task_id=log.task_id,
        task_title=log.task.title if log.task else None,
        employee_id=log.employee_id,
        employee_name=log.employee.full_name if log.employee else None,
        log_text=log.log_text,
        ai_confidence=log.ai_confidence,
        ai_feedback=log.ai_feedback,
        ai_verified_at=log.ai_verified_at,
        submitted_at=log.submitted_at,
    )


class LogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = LogRepository(session)
        self.task_repo = TaskRepository(session)
        self.audit = AuditRepository(session)

    async def submit(
        self,
        task_id: uuid.UUID,
        employee_id: uuid.UUID,
        data: LogSubmit,
    ) -> LogResponse:
        # Verify task exists and belongs to this employee
        task = await self.task_repo.get_by_id_with_relations(task_id)
        if not task:
            raise NotFoundException("Task not found")
        if task.assigned_to != employee_id:
            raise ForbiddenException("You can only log work on your own tasks")

        # Create the log entry
        log = WorkLog(
            task_id=task_id,
            employee_id=employee_id,
            log_text=data.log_text,
        )
        log = await self.repo.create(log)

        # ── AI Verification (inline, fast enough for 3b model) ───────────────
        try:
            result = await verifyLog(
                task_title=task.title,
                task_description=task.description,
                log_text=data.log_text,
            )
            log.ai_confidence = result.confidence
            log.ai_feedback = result.feedback
            log.ai_verified_at = datetime.utcnow()
            await self.repo.update(log, {
                "ai_confidence": result.confidence,
                "ai_feedback": result.feedback,
                "ai_verified_at": log.ai_verified_at,
            })
            logger.info("log.ai_verified", log_id=str(log.id), confidence=result.confidence)
        except Exception as exc:
            logger.warning("log.ai_verify_error", error=str(exc))

        # ── Index in RAG ──────────────────────────────────────────────────────
        await RAGService.index_log(
            log_text=data.log_text,
            metadata={
                "log_id": str(log.id),
                "task_id": str(task_id),
                "task_title": task.title,
                "employee_id": str(employee_id),
            },
        )

        # ── Audit ─────────────────────────────────────────────────────────────
        await self.audit.log_action(
            actor_id=employee_id,
            action="log_submitted",
            entity_type="work_log",
            entity_id=log.id,
            payload={
                "task_id": str(task_id),
                "ai_confidence": log.ai_confidence,
                "log_preview": data.log_text[:100],
            },
        )

        # Reload with relations for full response
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from app.models.work_log import WorkLog as WLModel
        stmt = (
            select(WLModel)
            .where(WLModel.id == log.id)
            .options(selectinload(WLModel.task), selectinload(WLModel.employee))
        )
        result2 = await self.repo.session.execute(stmt)
        log = result2.scalar_one()
        return _log_to_response(log)

    async def get_task_logs(self, task_id: uuid.UUID) -> LogListResponse:
        logs = await self.repo.get_by_task(task_id)
        return LogListResponse(
            logs=[_log_to_response(lg) for lg in logs],
            total=len(logs),
        )

    async def get_my_logs(self, employee_id: uuid.UUID) -> LogListResponse:
        logs = await self.repo.get_by_employee(employee_id)
        return LogListResponse(
            logs=[_log_to_response(lg) for lg in logs],
            total=len(logs),
        )
