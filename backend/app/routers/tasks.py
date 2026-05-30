"""WorkFlow — Tasks Router."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user, require_manager
from app.models.task import Status
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskStatusUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Manager: create and assign a task."""
    return await TaskService(session).create(data, manager_id=current.id)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Status | None = Query(default=None),
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """Manager: list all tasks with optional status filter."""
    return await TaskService(session).get_all(status=status)


@router.get("/mine", response_model=TaskListResponse)
async def my_tasks(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """Employee: get tasks assigned to me."""
    return await TaskService(session).get_my_tasks(employee_id=current.id)


@router.get("/overdue", response_model=list[TaskResponse])
async def overdue_tasks(
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """Manager: get all overdue tasks."""
    return await TaskService(session).get_overdue()


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: uuid.UUID,
    data: TaskStatusUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Update task status (both roles allowed)."""
    return await TaskService(session).update_status(
        task_id=task_id, data=data, actor_id=current.id
    )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Manager: soft-delete a task."""
    await TaskService(session).soft_delete(task_id=task_id, manager_id=current.id)
