"""WorkFlow — Task Service (business logic)."""
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.task import Status, Task
from app.repositories.audit_repository import AuditRepository
from app.repositories.log_repository import LogRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskStatusUpdate, TaskUpdate

logger = structlog.get_logger()


def _task_to_response(task: Task, log_count: int = 0, latest_confidence: str | None = None) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        assigned_to=task.assigned_to,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_by=task.created_by,
        creator_name=task.creator.full_name if task.creator else None,
        priority=task.priority,
        status=task.status,
        deadline=task.deadline,
        created_at=task.created_at,
        updated_at=task.updated_at,
        log_count=log_count,
        latest_ai_confidence=latest_confidence,
    )


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TaskRepository(session)
        self.audit = AuditRepository(session)
        self.log_repo = LogRepository(session)

    async def create(self, data: TaskCreate, manager_id: uuid.UUID) -> TaskResponse:
        task = Task(
            title=data.title,
            description=data.description,
            assigned_to=data.assigned_to,
            created_by=manager_id,
            priority=data.priority,
            deadline=data.deadline,
        )
        task = await self.repo.create(task)
        await self.audit.log_action(
            actor_id=manager_id,
            action="task_created",
            entity_type="task",
            entity_id=task.id,
            payload={"title": task.title, "assigned_to": str(task.assigned_to)},
        )
        # Reload with relations
        task = await self.repo.get_by_id_with_relations(task.id)  # type: ignore[assignment]
        logger.info("task.created", task_id=str(task.id))
        return _task_to_response(task)

    async def get_all(self, *, status: Status | None = None) -> TaskListResponse:
        tasks = await self.repo.get_all_active(status=status)
        overdue = await self.repo.get_overdue()
        responses = []
        for t in tasks:
            logs = await self.log_repo.get_by_task(t.id)
            latest = logs[0].ai_confidence if logs else None
            responses.append(_task_to_response(t, len(logs), latest))
        return TaskListResponse(
            tasks=responses,
            total=len(responses),
            overdue_count=len(overdue),
        )

    async def get_my_tasks(self, employee_id: uuid.UUID) -> TaskListResponse:
        tasks = await self.repo.get_by_employee(employee_id)
        responses = []
        for t in tasks:
            logs = await self.log_repo.get_by_task(t.id)
            latest = logs[0].ai_confidence if logs else None
            responses.append(_task_to_response(t, len(logs), latest))
        return TaskListResponse(
            tasks=responses,
            total=len(responses),
            overdue_count=sum(1 for r in responses if r.status == Status.OVERDUE),
        )

    async def get_overdue(self) -> list[TaskResponse]:
        tasks = await self.repo.get_overdue()
        return [_task_to_response(t) for t in tasks]

    async def update_status(
        self,
        task_id: uuid.UUID,
        data: TaskStatusUpdate,
        actor_id: uuid.UUID,
    ) -> TaskResponse:
        task = await self.repo.get_by_id_with_relations(task_id)
        if not task:
            raise NotFoundException("Task not found")

        old_status = task.status
        task.status = data.status
        task.updated_at = datetime.utcnow()
        await self.repo.update(task, {"status": data.status, "updated_at": task.updated_at})
        await self.audit.log_action(
            actor_id=actor_id,
            action="task_status_changed",
            entity_type="task",
            entity_id=task_id,
            payload={"from": old_status, "to": data.status},
        )
        task = await self.repo.get_by_id_with_relations(task_id)  # type: ignore[assignment]
        return _task_to_response(task)

    async def soft_delete(self, task_id: uuid.UUID, manager_id: uuid.UUID) -> None:
        task = await self.repo.get_by_id_with_relations(task_id)
        if not task:
            raise NotFoundException("Task not found")
        await self.repo.soft_delete(task)
        await self.audit.log_action(
            actor_id=manager_id,
            action="task_deleted",
            entity_type="task",
            entity_id=task_id,
            payload={"title": task.title},
        )

    async def mark_overdue_tasks(self) -> int:
        """Background job: auto-mark past-deadline tasks as OVERDUE."""
        overdue = await self.repo.get_overdue()
        count = 0
        for task in overdue:
            if task.status not in (Status.COMPLETED, Status.OVERDUE):
                task.status = Status.OVERDUE
                task.updated_at = datetime.utcnow()
                await self.repo.update(task, {"status": Status.OVERDUE, "updated_at": task.updated_at})
                count += 1
        return count
