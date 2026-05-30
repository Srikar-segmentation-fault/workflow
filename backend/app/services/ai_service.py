"""
WorkFlow — AI Service (Ollama / qwen2.5)
=========================================
1. verifyLog()              — Ollama: evaluate work log + proof file
2. generateManagerSummary() — Ollama: plain-English team briefing
3. suggestTaskPriority()    — Ollama: smart priority/deadline suggestion
4. RAGService               — lightweight in-memory semantic search fallback
"""
from __future__ import annotations

import base64
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.llm_factory import LLMFactory
from app.models.work_log import AIConfidence
from app.schemas.work_log import LogVerificationResult

logger = structlog.get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

VERIFY_SYSTEM = """You are a workplace accountability assistant. Your job is to \
evaluate whether an employee's daily work log genuinely reflects real progress \
on their assigned task. You may also receive a proof file (image, PDF text, or \
document excerpt) that the employee uploaded as evidence.

Be fair but critical of vague, evasive, or off-topic entries. If a proof file \
is provided, check whether it actually supports the claimed work."""

VERIFY_USER_NO_PROOF = """\
Task title: {title}
Task description: {description}

Employee's work log:
{log_text}

No proof file was attached.

Evaluate this log. Respond ONLY with valid JSON:
{{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}}

High = detailed, clearly relevant, specific progress described.
Medium = partially relevant or somewhat vague.
Low = vague, off-topic, or looks like bluffing."""

VERIFY_USER_WITH_PROOF = """\
Task title: {title}
Task description: {description}

Employee's work log:
{log_text}

Proof file attached: {file_name} ({mime_type})
Proof content / description:
{proof_content}

Evaluate the log AND the proof together. Does the proof support the claimed work?
Respond ONLY with valid JSON:
{{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}}

High = log is detailed AND proof clearly supports the work done.
Medium = log or proof is partially convincing.
Low = vague log, proof doesn't match the task, or proof looks irrelevant."""

SUMMARY_SYSTEM = """You are a productivity assistant helping a manager understand \
their team's current work status. Be concise, direct, and highlight risks and standouts."""

SUMMARY_USER = """\
Here is the current task list for my team:
{task_table}

Write a short plain-English briefing (max 5 sentences) covering:
1) who is behind or overdue
2) what is at risk of missing deadline
3) who is performing well
Do not list every task — synthesise."""

TRIAGE_SYSTEM = """You are WorkFlow's AI assistant. Given a task description, \
suggest an appropriate priority (low/medium/high/critical) and realistic deadline \
in days from today. Return ONLY JSON: \
{{"priority": "...", "deadline_days": <int>, "reasoning": "..."}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Proof file reader
# ─────────────────────────────────────────────────────────────────────────────

def _read_proof_content(file_path: str, mime_type: str) -> str:
    """
    Extract readable content from the uploaded proof file.
    - Images: base64-encode and describe (Groq vision not used here — we
      describe the file and let the LLM reason about its presence).
    - Text/CSV/plain: read raw text (truncated to 2000 chars).
    - PDF/DOCX: attempt text extraction, fall back to filename description.
    """
    path = Path(file_path)
    if not path.exists():
        return "[Proof file not found on server]"

    try:
        if mime_type.startswith("image/"):
            # For images, encode to base64 and note dimensions if possible
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode()[:200]  # just a snippet for context
            size_kb = len(raw) // 1024
            return (
                f"[Image file, {size_kb} KB. "
                f"Base64 preview: {b64}... "
                f"The employee uploaded a screenshot/photo as proof of work.]"
            )

        if mime_type == "application/pdf":
            try:
                import pypdf  # optional dep
                reader = pypdf.PdfReader(str(path))
                text = "\n".join(
                    page.extract_text() or "" for page in reader.pages[:3]
                )
                return text[:2000] or "[PDF has no extractable text]"
            except ImportError:
                size_kb = path.stat().st_size // 1024
                return f"[PDF file, {size_kb} KB — text extraction unavailable]"

        if mime_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            try:
                import docx  # python-docx, optional
                doc = docx.Document(str(path))
                text = "\n".join(p.text for p in doc.paragraphs)
                return text[:2000] or "[DOCX has no text content]"
            except ImportError:
                return f"[DOCX file — text extraction unavailable]"

        # Plain text / CSV
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:2000]

    except Exception as exc:
        logger.warning("proof.read_failed", path=file_path, error=str(exc))
        return f"[Could not read proof file: {exc}]"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Work-Log Verification
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def verifyLog(
    task_title: str,
    task_description: str | None,
    log_text: str,
    proof_file_path: str | None = None,
    proof_file_name: str | None = None,
    proof_mime_type: str | None = None,
) -> LogVerificationResult:
    """
    Uses Groq LLM to evaluate an employee work log + optional proof file.
    Returns LogVerificationResult(confidence, feedback).
    Retries up to 3× on failure with exponential back-off.
    """
    desc = task_description or "No description provided."

    if proof_file_path and proof_mime_type:
        proof_content = _read_proof_content(proof_file_path, proof_mime_type)
        user_prompt = VERIFY_USER_WITH_PROOF.format(
            title=task_title,
            description=desc,
            log_text=log_text,
            file_name=proof_file_name or "unknown",
            mime_type=proof_mime_type,
            proof_content=proof_content,
        )
    else:
        user_prompt = VERIFY_USER_NO_PROOF.format(
            title=task_title,
            description=desc,
            log_text=log_text,
        )

    try:
        raw = await LLMFactory.call_ollama(
            system=VERIFY_SYSTEM,
            user=user_prompt,
            temperature=0.0,
            max_tokens=256,
            json_mode=True,
        )
        data = _extract_json(raw)
        confidence_str = data.get("confidence", "Medium")
        feedback = data.get("feedback", "Unable to parse AI feedback.")

        confidence_map = {
            "high": AIConfidence.HIGH,
            "medium": AIConfidence.MEDIUM,
            "low": AIConfidence.LOW,
        }
        confidence = confidence_map.get(confidence_str.lower(), AIConfidence.MEDIUM)

        logger.info("ai.verify_log", task=task_title, confidence=confidence,
                    has_proof=bool(proof_file_path))
        return LogVerificationResult(confidence=confidence, feedback=feedback)

    except Exception as exc:
        logger.warning("ai.verify_log.failed", error=str(exc))
        return LogVerificationResult(
            confidence=AIConfidence.MEDIUM,
            feedback="Unable to verify — manual review recommended.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Manager Summary ("Where's my team?")
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
async def generateManagerSummary(tasks: list[dict[str, Any]]) -> str:
    """
    Generates a plain-English manager briefing from the task list.
    tasks: list of {title, assignedTo, priority, deadline, status}
    """
    if not tasks:
        return "No tasks are currently assigned. The team has a clean slate."

    now = datetime.now(timezone.utc)
    rows = []
    for t in tasks:
        deadline = t.get("deadline", "")
        try:
            dl = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            days_left = (dl - now).days
            deadline_label = f"{deadline[:10]} ({days_left:+d}d)"
        except Exception:
            deadline_label = deadline

        rows.append(
            f"• {t['title']} | {t.get('assignedTo', 'Unassigned')} "
            f"| {t.get('priority', 'medium').upper()} "
            f"| deadline {deadline_label} | {t.get('status', 'pending')}"
        )

    task_table = "\n".join(rows)

    try:
        summary = await LLMFactory.call_ollama(
            system=SUMMARY_SYSTEM,
            user=SUMMARY_USER.format(task_table=task_table),
            temperature=0.3,
            max_tokens=400,
        )
        logger.info("ai.manager_summary.generated", task_count=len(tasks))
        return summary.strip()
    except Exception as exc:
        logger.warning("ai.manager_summary.failed", error=str(exc))
        return "AI summary unavailable. Make sure Ollama is running and qwen2.5 is pulled."


# ─────────────────────────────────────────────────────────────────────────────
# 3. Smart Task Triage
# ─────────────────────────────────────────────────────────────────────────────

async def suggestTaskPriority(title: str, description: str) -> dict[str, Any]:
    """Suggest priority and deadline for a new task."""
    try:
        raw = await LLMFactory.call_ollama(
            system=TRIAGE_SYSTEM,
            user=f"Task: {title}\nDescription: {description}",
            temperature=0.1,
            max_tokens=200,
            json_mode=True,
        )
        return _extract_json(raw)
    except Exception as exc:
        logger.warning("ai.triage.failed", error=str(exc))
        return {"priority": "medium", "deadline_days": 7, "reasoning": "Default suggestion"}


# ─────────────────────────────────────────────────────────────────────────────
# 4. RAG Service — lightweight fallback (no pgvector dependency)
# ─────────────────────────────────────────────────────────────────────────────

class RAGService:
    """
    In-memory log store for semantic-ish search.
    Replace with pgvector/Supabase when ready.
    """
    _logs: list[dict[str, Any]] = []

    @classmethod
    async def initialize(cls, database_url: str) -> None:
        logger.info("rag.initialized", store="in_memory")

    @classmethod
    async def search_similar_logs(
        cls,
        query: str,
        task_id: uuid.UUID | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Simple keyword match fallback."""
        q = query.lower()
        results = [
            lg for lg in cls._logs
            if q in lg.get("text", "").lower()
            and (task_id is None or str(task_id) == lg.get("metadata", {}).get("task_id"))
        ]
        return results[:top_k]

    @classmethod
    async def index_log(cls, log_text: str, metadata: dict[str, Any]) -> None:
        cls._logs.append({"text": log_text, "metadata": metadata})


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict[str, Any]:
    """Robustly extract JSON from LLM output."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Cannot extract JSON from LLM output: {raw[:200]}")
