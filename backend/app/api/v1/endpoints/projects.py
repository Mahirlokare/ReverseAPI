from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import (
    User, Project, ProjectSettings, ProjectStatus,
    DiscoveryRun, RunStatus, ExecutionMode,
    WorkspaceMember, UserRole
)
from app.api.v1.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectSettingsBase, ProjectSettingsResponse,
    RunCreate, RunUpdate, RunResponse,
    RunEventResponse, RunLogResponse,
    PaginatedResponse,
)

router = APIRouter()


def get_workspace_member_check(workspace_id: UUID, user_id: UUID, required_roles=None):
    """Dependency to check workspace membership."""
    async def check(db: AsyncSession = Depends(get_db)):
        query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        if required_roles:
            query = query.where(WorkspaceMember.role.in_(required_roles))
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
        return member
    return check


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check workspace membership
    member_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project_data.workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    project = Project(
        **project_data.model_dump(),
        owner_id=current_user.id,
    )
    db.add(project)
    await db.flush()

    # Create default settings
    settings = ProjectSettings(project_id=project.id)
    db.add(settings)

    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    workspace_id: UUID | None = Query(None),
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Build query - only projects from workspaces user is member of
    subquery = select(WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == current_user.id
    )

    query = select(Project).where(Project.workspace_id.in_(subquery))

    if workspace_id:
        query = query.where(Project.workspace_id == workspace_id)

    if status_filter:
        query = query.where(Project.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Apply pagination
    query = query.order_by(Project.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    projects = result.scalars().all()

    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check access via workspace membership
    result = await db.execute(
        select(Project)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Project.id == project_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .options(selectinload(Project.settings))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Add counts
    project.run_count = (await db.execute(
        select(func.count(DiscoveryRun.id)).where(DiscoveryRun.project_id == project_id)
    )).scalar_one()

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Project.id == project_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role.in_([UserRole.OWNER, UserRole.ADMIN, UserRole.DEVELOPER]),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not authorized")

    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Project.id == project_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role.in_([UserRole.OWNER, UserRole.ADMIN]),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not authorized")

    # Soft delete
    project.status = ProjectStatus.DELETED
    await db.commit()


@router.get("/{project_id}/settings", response_model=ProjectSettingsResponse)
async def get_project_settings(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProjectSettings)
        .join(Project, ProjectSettings.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Project.id == project_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return ProjectSettingsResponse.model_validate(settings)


@router.put("/{project_id}/settings", response_model=ProjectSettingsResponse)
async def update_project_settings(
    project_id: UUID,
    settings_data: ProjectSettingsBase,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProjectSettings)
        .join(Project, ProjectSettings.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Project.id == project_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role.in_([UserRole.OWNER, UserRole.ADMIN, UserRole.DEVELOPER]),
        )
    )
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    for field, value in settings_data.model_dump().items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return ProjectSettingsResponse.model_validate(settings)