from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import (
    APIEndpoint, APIRequest, APIResponse,
    Project, WorkspaceMember, User
)
from app.api.v1.schemas import (
    APIEndpointResponse, APIRequestResponse, APIResponseResponse,
    PaginatedResponse, Message
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[APIEndpointResponse])
async def list_endpoints(
    project_id: UUID | None = Query(None),
    run_id: UUID | None = Query(None),
    method: str | None = Query(None),
    host: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List discovered API endpoints with filters and pagination."""
    # Ensure user has access to the workspace of the project
    subquery = select(Project.id).join(
        WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id
    ).where(WorkspaceMember.user_id == current_user.id)

    query = select(APIEndpoint).where(APIEndpoint.project_id.in_(subquery))

    if project_id:
        query = query.where(APIEndpoint.project_id == project_id)
    if run_id:
        query = query.where(APIEndpoint.run_id == run_id)
    if method:
        query = query.where(APIEndpoint.method.ilike(method))
    if host:
        query = query.where(APIEndpoint.host.ilike(f"%{host}%"))
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                APIEndpoint.name.ilike(search_filter),
                APIEndpoint.path.ilike(search_filter),
                APIEndpoint.full_url.ilike(search_filter),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(APIEndpoint.discovered_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    endpoints = result.scalars().all()

    return PaginatedResponse(
        items=[APIEndpointResponse.model_validate(ep) for ep in endpoints],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{endpoint_id}", response_model=APIEndpointResponse)
async def get_endpoint_detail(
    endpoint_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single endpoint detail."""
    subquery = select(Project.id).join(
        WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id
    ).where(WorkspaceMember.user_id == current_user.id)

    query = select(APIEndpoint).where(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.project_id.in_(subquery)
    )
    result = await db.execute(query)
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")

    return APIEndpointResponse.model_validate(endpoint)


@router.get("/{endpoint_id}/requests", response_model=list[APIRequestResponse])
async def get_endpoint_requests(
    endpoint_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get captured requests for an endpoint."""
    subquery = select(Project.id).join(
        WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id
    ).where(WorkspaceMember.user_id == current_user.id)

    ep_check = await db.execute(
        select(APIEndpoint).where(
            APIEndpoint.id == endpoint_id,
            APIEndpoint.project_id.in_(subquery)
        )
    )
    if not ep_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")

    result = await db.execute(
        select(APIRequest).where(APIRequest.endpoint_id == endpoint_id).order_by(APIRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [APIRequestResponse.model_validate(r) for r in requests]


@router.get("/{endpoint_id}/responses", response_model=list[APIResponseResponse])
async def get_endpoint_responses(
    endpoint_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get captured responses for an endpoint."""
    subquery = select(Project.id).join(
        WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id
    ).where(WorkspaceMember.user_id == current_user.id)

    ep_check = await db.execute(
        select(APIEndpoint).where(
            APIEndpoint.id == endpoint_id,
            APIEndpoint.project_id.in_(subquery)
        )
    )
    if not ep_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")

    result = await db.execute(
        select(APIResponse).where(APIResponse.endpoint_id == endpoint_id).order_by(APIResponse.created_at.desc())
    )
    responses = result.scalars().all()
    return [APIResponseResponse.model_validate(r) for r in responses]


@router.delete("/{endpoint_id}", response_model=Message)
async def delete_endpoint(
    endpoint_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a discovered endpoint."""
    subquery = select(Project.id).join(
        WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id
    ).where(WorkspaceMember.user_id == current_user.id)

    result = await db.execute(
        select(APIEndpoint).where(
            APIEndpoint.id == endpoint_id,
            APIEndpoint.project_id.in_(subquery)
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")

    await db.delete(endpoint)
    await db.commit()
    return Message(message="Endpoint deleted successfully")
