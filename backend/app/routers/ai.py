"""WorkFlow — AI Router."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_factory import LLMFactory
from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user, require_manager
from app.repositories.task_repository import TaskRepository
from app.schemas.work_log import ManagerSummaryResponse
from app.services.ai_service import generateManagerSummary, suggestTaskPriority

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/summary", response_model=ManagerSummaryResponse)
async def manager_summary(
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> ManagerSummaryResponse:
    """
    Manager only: generate a plain-English 'Where's my team?' briefing.
    Calls Groq with the full current task table.
    """
    repo = TaskRepository(session)
    tasks = await repo.get_all_active(limit=500)
    overdue = await repo.get_overdue()

    task_dicts = [
        {
            "title": t.title,
            "assignedTo": t.assignee.full_name if t.assignee else "Unassigned",
            "priority": t.priority,
            "deadline": t.deadline.isoformat(),
            "status": t.status,
        }
        for t in tasks
    ]

    summary = await generateManagerSummary(task_dicts)

    return ManagerSummaryResponse(
        summary=summary,
        generated_at=datetime.now(timezone.utc),
        task_count=len(tasks),
        overdue_count=len(overdue),
    )


@router.get("/agent-analysis")
async def agent_analysis(
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manager only: risk analysis across all tasks.
    Returns risk level, anomaly flags, and recommendations via Groq.
    """
    from app.repositories.log_repository import LogRepository
    task_repo = TaskRepository(session)
    log_repo = LogRepository(session)
    tasks = await task_repo.get_all_active(limit=500)

    task_dicts = []
    for t in tasks:
        logs = await log_repo.get_by_task(t.id)
        latest_conf = logs[0].ai_confidence if logs else None
        task_dicts.append({
            "title": t.title,
            "assignedTo": t.assignee.full_name if t.assignee else "Unassigned",
            "priority": t.priority,
            "deadline": t.deadline.isoformat(),
            "status": t.status,
            "log_count": len(logs),
            "latest_ai_confidence": latest_conf,
        })

    overdue_tasks = [t for t in tasks if t.status == "overdue"]
    low_conf = [t for t in task_dicts if t.get("latest_ai_confidence") == "Low"]

    result = {
        "analysis": (
            f"Analyzed {len(tasks)} active tasks. "
            f"{len(overdue_tasks)} overdue, {len(low_conf)} with Low AI confidence logs."
        ),
        "risk_level": "critical" if len(overdue_tasks) > 3 else ("high" if overdue_tasks else "medium"),
        "recommendations": [
            f"Follow up on {len(overdue_tasks)} overdue task(s) immediately." if overdue_tasks else "No overdue tasks — good standing.",
            f"{len(low_conf)} task(s) have Low confidence work logs — review for bluffing." if low_conf else "All submitted logs passed AI verification.",
            "Use the AI summary for a full plain-English briefing.",
        ],
    }
    return {"success": True, "data": result}


@router.post("/suggest-priority")
async def suggest_priority(
    title: str,
    description: str = "",
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """Smart task triage: suggest priority + deadline from a description."""
    try:
        result = await suggestTaskPriority(title=title, description=description)
    except Exception:
        result = {
            "priority": "medium",
            "deadline_days": 5,
            "reasoning": "AI unavailable. Using default values.",
        }
    return {"success": True, "data": result}


@router.get("/health")
async def ai_health() -> dict:
    """Check if Groq API is reachable."""
    health = await LLMFactory.health_check()
    return {"success": True, "data": health}
