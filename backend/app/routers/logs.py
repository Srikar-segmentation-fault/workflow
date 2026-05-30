"""WorkFlow — Work Logs Router.

POST /{task_id}  — multipart/form-data: log_text (str) + proof_file (optional file)
GET  /task/{task_id} — all logs for a task
GET  /mine           — employee's own logs
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.schemas.work_log import LogListResponse, LogResponse
from app.services.log_service import LogService

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/{task_id}", response_model=LogResponse, status_code=201)
async def submit_log(
    task_id: uuid.UUID,
    log_text: str = Form(..., min_length=10, max_length=5000,
                         description="Free-text description of work done today"),
    proof_file: Optional[UploadFile] = File(
        default=None,
        description="Optional proof-of-work file (image, PDF, text, DOCX, XLSX)",
    ),
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LogResponse:
    """
    Employee: submit a daily work log for a task.

    - **log_text**: what you worked on (required)
    - **proof_file**: screenshot, PDF, document, etc. (optional but improves AI score)

    The server records the submission timestamp automatically.
    The AI then compares the log + proof against the assigned task.
    """
    # Validate file type if provided
    if proof_file and proof_file.content_type:
        if proof_file.content_type not in settings.allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"File type '{proof_file.content_type}' is not allowed. "
                    f"Accepted: {', '.join(settings.allowed_mime_types)}"
                ),
            )

    return await LogService(session).submit(
        task_id=task_id,
        employee_id=current.id,
        log_text=log_text,
        proof_file=proof_file,
    )


@router.get("/task/{task_id}", response_model=LogListResponse)
async def get_task_logs(
    task_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LogListResponse:
    """Get all logs for a task (manager or assigned employee)."""
    return await LogService(session).get_task_logs(task_id=task_id)


@router.get("/mine", response_model=LogListResponse)
async def my_logs(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LogListResponse:
    """Employee: get my own submitted logs."""
    return await LogService(session).get_my_logs(employee_id=current.id)
