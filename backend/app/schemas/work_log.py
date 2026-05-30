"""WorkFlow — Pydantic schemas for WorkLog + AI responses."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.work_log import AIConfidence


class LogSubmit(BaseModel):
    """Used only when submitting via JSON (no file). Prefer the multipart endpoint."""
    log_text: str = Field(min_length=10, max_length=5000)


class LogResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_title: Optional[str] = None
    employee_id: uuid.UUID
    employee_name: Optional[str] = None

    log_text: str
    submitted_at: datetime          # server-recorded timestamp

    # Proof file
    proof_file_name: Optional[str] = None
    proof_mime_type: Optional[str] = None
    has_proof: bool = False         # convenience flag for the frontend

    # AI verification
    ai_confidence: AIConfidence
    ai_feedback: Optional[str] = None
    ai_verified_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    logs: list[LogResponse]
    total: int


# ── AI response schemas ────────────────────────────────────────────────────────
class LogVerificationResult(BaseModel):
    """Structured output from the AI work-log verification."""
    confidence: AIConfidence
    feedback: str = Field(
        description="One-sentence explanation of the confidence rating"
    )


class ManagerSummaryResponse(BaseModel):
    summary: str
    generated_at: datetime
    task_count: int
    overdue_count: int
