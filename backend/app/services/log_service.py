"""WorkFlow — Work Log Service.

Handles:
- Saving the proof file to disk
- Recording the server-side submission timestamp
- Calling Groq AI verification with log text + proof
- Audit trail entry
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import structlog
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.work_log import WorkLog
from app.repositories.audit_repository import AuditRepository
from app.repositories.log_repository import LogRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.work_log import LogListResponse, LogResponse
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
        submitted_at=log.submitted_at,
        proof_file_name=log.proof_file_name,
        proof_mime_type=log.proof_mime_type,
        has_proof=bool(log.proof_file_path),
        ai_confidence=log.ai_confidence,
        ai_feedback=log.ai_feedback,
        ai_verified_at=log.ai_verified_at,
    )


async def _save_proof_file(
    file: UploadFile,
    log_id: uuid.UUID,
) -> tuple[str, str, str]:
    """
    Save the uploaded proof file to disk.
    Returns (file_path, original_filename, mime_type).
    """
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise filename and make it unique
    original_name = file.filename or "proof"
    suffix = Path(original_name).suffix or ""
    stored_name = f"{log_id}{suffix}"
    dest = upload_dir / stored_name

    content = await file.read()

    # Enforce size limit
    if len(content) > settings.max_upload_bytes:
        raise ValueError(
            f"File too large ({len(content) // 1024} KB). "
            f"Max allowed: {settings.max_upload_bytes // 1024} KB."
        )

    dest.write_bytes(content)
    logger.info("proof.saved", path=str(dest), size_bytes=len(content))
    return str(dest), original_name, file.content_type or "application/octet-stream"


class LogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = LogRepository(session)
        self.task_repo = TaskRepository(session)
        self.audit = AuditRepository(session)

    async def submit(
        self,
        task_id: uuid.UUID,
        employee_id: uuid.UUID,
        log_text: str,
        proof_file: Optional[UploadFile] = None,
    ) -> LogResponse:
        # ── Validate task ownership ───────────────────────────────────────────
        task = await self.task_repo.get_by_id_with_relations(task_id)
        if not task:
            raise NotFoundException("Task not found")
        if task.assigned_to != employee_id:
            raise ForbiddenException("You can only log work on your own tasks")

        # ── Record server-side timestamp (before any async I/O) ──────────────
        submitted_at = datetime.now(timezone.utc)

        # ── Create the log row (proof fields filled in after file save) ───────
        log = WorkLog(
            task_id=task_id,
            employee_id=employee_id,
            log_text=log_text,
            submitted_at=submitted_at,
        )
        log = await self.repo.create(log)

        # ── Save proof file ───────────────────────────────────────────────────
        proof_path: Optional[str] = None
        proof_name: Optional[str] = None
        proof_mime: Optional[str] = None

        if proof_file and proof_file.filename:
            try:
                proof_path, proof_name, proof_mime = await _save_proof_file(
                    proof_file, log.id
                )
                await self.repo.update(log, {
                    "proof_file_path": proof_path,
                    "proof_file_name": proof_name,
                    "proof_mime_type": proof_mime,
                })
                log.proof_file_path = proof_path
                log.proof_file_name = proof_name
                log.proof_mime_type = proof_mime
            except ValueError as exc:
                # File too large — log the warning but don't fail the submission
                logger.warning("proof.save_skipped", reason=str(exc))

        # ── AI Verification (Groq) ────────────────────────────────────────────
        try:
            result = await verifyLog(
                task_title=task.title,
                task_description=task.description,
                log_text=log_text,
                proof_file_path=proof_path,
                proof_file_name=proof_name,
                proof_mime_type=proof_mime,
            )
            ai_verified_at = datetime.now(timezone.utc)
            await self.repo.update(log, {
                "ai_confidence": result.confidence,
                "ai_feedback": result.feedback,
                "ai_verified_at": ai_verified_at,
            })
            log.ai_confidence = result.confidence
            log.ai_feedback = result.feedback
            log.ai_verified_at = ai_verified_at
            logger.info(
                "log.ai_verified",
                log_id=str(log.id),
                confidence=result.confidence,
                has_proof=bool(proof_path),
            )
        except Exception as exc:
            logger.warning("log.ai_verify_error", error=str(exc))

        # ── Index in RAG ──────────────────────────────────────────────────────
        await RAGService.index_log(
            log_text=log_text,
            metadata={
                "log_id": str(log.id),
                "task_id": str(task_id),
                "task_title": task.title,
                "employee_id": str(employee_id),
                "submitted_at": submitted_at.isoformat(),
                "has_proof": bool(proof_path),
            },
        )

        # ── Audit trail ───────────────────────────────────────────────────────
        await self.audit.log_action(
            actor_id=employee_id,
            action="log_submitted",
            entity_type="work_log",
            entity_id=log.id,
            payload={
                "task_id": str(task_id),
                "submitted_at": submitted_at.isoformat(),
                "has_proof": bool(proof_path),
                "proof_file_name": proof_name,
                "ai_confidence": str(log.ai_confidence),
                "log_preview": log_text[:100],
            },
        )

        # ── Reload with relations for full response ───────────────────────────
        stmt = (
            select(WorkLog)
            .where(WorkLog.id == log.id)
            .options(selectinload(WorkLog.task), selectinload(WorkLog.employee))
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
