"""WorkFlow — Audit Trail Router."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_manager
from app.repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/")
async def audit_trail(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    current=Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Manager: get full paginated audit trail."""
    repo = AuditRepository(session)
    logs = await repo.get_recent(limit=limit, offset=offset)
    total = await repo.count()
    return {
        "success": True,
        "data": [
            {
                "id": str(log.id),
                "actor": log.actor.full_name if log.actor else "System",
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id),
                "payload": log.payload,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
    }


@router.get("/{entity_id}")
async def entity_history(
    entity_id: uuid.UUID,
    current=Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Get the full history for a specific task or work log."""
    repo = AuditRepository(session)
    logs = await repo.get_for_entity(entity_id)
    return {
        "success": True,
        "data": [
            {
                "id": str(log.id),
                "actor": log.actor.full_name if log.actor else "System",
                "action": log.action,
                "payload": log.payload,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
