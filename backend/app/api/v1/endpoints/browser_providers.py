from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import User, BrowserProviderConfig, BrowserProvider
from app.api.v1.schemas import (
    BrowserProviderConfigCreate, BrowserProviderConfigResponse,
)

router = APIRouter()


@router.get("", response_model=list[BrowserProviderConfigResponse])
async def list_browser_providers(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrowserProviderConfig).where(BrowserProviderConfig.user_id == current_user.id)
    )
    providers = result.scalars().all()
    return [BrowserProviderConfigResponse.model_validate(p) for p in providers]


@router.post("", response_model=BrowserProviderConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_browser_provider(
    provider_data: BrowserProviderConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    provider = BrowserProviderConfig(
        **provider_data.model_dump(),
        user_id=current_user.id,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    return BrowserProviderConfigResponse.model_validate(provider)


@router.get("/{provider_id}", response_model=BrowserProviderConfigResponse)
async def get_browser_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrowserProviderConfig).where(
            BrowserProviderConfig.id == provider_id,
            BrowserProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return BrowserProviderConfigResponse.model_validate(provider)


@router.put("/{provider_id}", response_model=BrowserProviderConfigResponse)
async def update_browser_provider(
    provider_id: UUID,
    provider_data: BrowserProviderConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrowserProviderConfig).where(
            BrowserProviderConfig.id == provider_id,
            BrowserProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = provider_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.commit()
    await db.refresh(provider)

    return BrowserProviderConfigResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_browser_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrowserProviderConfig).where(
            BrowserProviderConfig.id == provider_id,
            BrowserProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    await db.commit()


@router.get("/available/list")
async def list_available_browser_providers():
    """List all supported browser providers."""
    return {
        "providers": [
            {
                "id": "playwright",
                "name": "Playwright",
                "description": "Headless browser automation with Playwright",
                "supports_headless": True,
                "supports_manual": False,
            },
            {
                "id": "chrome_mcp",
                "name": "Chrome MCP",
                "description": "Chrome DevTools Protocol via MCP",
                "supports_headless": True,
                "supports_manual": True,
            },
            {
                "id": "vercel_agent_browser",
                "name": "Vercel Agent Browser",
                "description": "Vercel's agent browser integration",
                "supports_headless": True,
                "supports_manual": False,
            },
        ]
    }


@router.post("/{provider_id}/test")
async def test_browser_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrowserProviderConfig).where(
            BrowserProviderConfig.id == provider_id,
            BrowserProviderConfig.user_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # TODO: Implement actual health check
    from datetime import datetime
    provider.last_health_check = datetime.utcnow()
    provider.is_available = True
    provider.health_status = "healthy"

    await db.commit()
    await db.refresh(provider)

    return BrowserProviderConfigResponse.model_validate(provider)