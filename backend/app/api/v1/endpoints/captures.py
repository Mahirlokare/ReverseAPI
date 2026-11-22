from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import Capture, Project, WorkspaceMember, UserRole, User
from app.api.v1.schemas import CaptureResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CaptureResponse])
async def list_captures(
    project_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Build query with project access check
    subquery = select(Project.id).join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == current_user.id
    )

    query = select(Capture).where(Capture.project_id.in_(subquery))

    if project_id:
        query = query.where(Capture.project_id == project_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Capture.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    captures = result.scalars().all()

    return PaginatedResponse(
        items=[CaptureResponse.model_validate(c) for c in captures],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{capture_id}", response_model=CaptureResponse)
async def get_capture(
    capture_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Capture)
        .join(Project, Capture.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Capture.id == capture_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    capture = result.scalar_one_or_none()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    return CaptureResponse.model_validate(capture)


@router.get("/{capture_id}/download")
async def download_capture(
    capture_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the raw or sanitized HAR capture file."""
    result = await db.execute(
        select(Capture)
        .join(Project, Capture.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Capture.id == capture_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    capture = result.scalar_one_or_none()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    import os
    from fastapi.responses import FileResponse, PlainTextResponse
    if capture.file_path and os.path.exists(capture.file_path):
        return FileResponse(
            capture.file_path,
            media_type="application/json",
            filename=f"capture-{capture_id}.har"
        )
    return PlainTextResponse("{}", media_type="application/json")


@router.delete("/{capture_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capture(
    capture_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Capture)
        .join(Project, Capture.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Capture.id == capture_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role.in_([UserRole.OWNER, UserRole.ADMIN, UserRole.DEVELOPER]),
        )
    )
    capture = result.scalar_one_or_none()
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found or not authorized")

    await db.delete(capture)
    await db.commit()


@router.post("", response_model=CaptureResponse, status_code=status.HTTP_201_CREATED)
async def import_capture(
    file_path: str,
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check project access
    project_result = await db.execute(
        select(Project)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            Project.id == project_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not authorized")

    # TODO: Validate HAR file, parse metadata
    import os
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

    capture = Capture(
        file_path=file_path,
        file_size=file_size,
        project_id=project_id,
        target_domain="unknown",
    )
    db.add(capture)
    await db.commit()
    await db.refresh(capture)

    return CaptureResponse.model_validate(capture)