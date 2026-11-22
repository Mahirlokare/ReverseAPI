from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import User, AIProviderConfig
from app.api.v1.schemas import (
    AIProviderConfigCreate, AIProviderConfigUpdate, AIProviderConfigResponse,
    PaginatedResponse,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AIProviderConfigResponse])
async def list_ai_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AIProviderConfig).where(AIProviderConfig.user_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(AIProviderConfig.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    providers = result.scalars().all()

    return PaginatedResponse(
        items=[AIProviderConfigResponse.model_validate(p) for p in providers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=AIProviderConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_provider(
    provider_data: AIProviderConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if user already has this provider/model
    existing = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.user_id == current_user.id,
            AIProviderConfig.provider == provider_data.provider,
            AIProviderConfig.model_id == provider_data.model_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Provider configuration already exists")

    # If this is the first provider, make it default
    count_result = await db.execute(
        select(func.count(AIProviderConfig.id)).where(AIProviderConfig.user_id == current_user.id)
    )
    is_first = count_result.scalar_one() == 0

    provider = AIProviderConfig(
        **provider_data.model_dump(),
        user_id=current_user.id,
        is_default=is_first,
        auth_status="configured",
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    return AIProviderConfigResponse.model_validate(provider)


@router.get("/{provider_id}", response_model=AIProviderConfigResponse)
async def get_ai_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.id == provider_id,
            AIProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return AIProviderConfigResponse.model_validate(provider)


@router.put("/{provider_id}", response_model=AIProviderConfigResponse)
async def update_ai_provider(
    provider_id: UUID,
    provider_data: AIProviderConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.id == provider_id,
            AIProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = provider_data.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        await db.execute(
            AIProviderConfig.__table__.update()
            .where(AIProviderConfig.user_id == current_user.id)
            .values(is_default=False)
        )

    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.commit()
    await db.refresh(provider)

    return AIProviderConfigResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.id == provider_id,
            AIProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    was_default = provider.is_default
    await db.delete(provider)
    await db.commit()

    # If deleted was default, set another as default
    if was_default:
        other = await db.execute(
            select(AIProviderConfig).where(AIProviderConfig.user_id == current_user.id).limit(1)
        )
        other_provider = other.scalar_one_or_none()
        if other_provider:
            other_provider.is_default = True
            await db.commit()


@router.post("/{provider_id}/test", response_model=AIProviderConfigResponse)
async def test_ai_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.id == provider_id,
            AIProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # TODO: Implement actual health check
    from datetime import datetime
    provider.last_health_check = datetime.utcnow()
    provider.health_check_status = "healthy"
    provider.auth_status = "validated"

    await db.commit()
    await db.refresh(provider)

    return AIProviderConfigResponse.model_validate(provider)