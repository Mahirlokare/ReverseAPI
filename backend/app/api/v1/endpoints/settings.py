from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import User, UserPreference
from app.api.v1.schemas import GeneralSettings, ExecutionSettings, StorageSettings

router = APIRouter()


@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        # Create default preferences
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return {
        "theme": prefs.theme,
        "language": prefs.language,
        "timezone": prefs.timezone,
        "notifications_enabled": prefs.notifications_enabled,
        "email_notifications": prefs.email_notifications,
        "compact_mode": prefs.compact_mode,
        "sidebar_collapsed": prefs.sidebar_collapsed,
    }


@router.put("/preferences")
async def update_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)

    allowed_fields = [
        "theme", "language", "timezone",
        "notifications_enabled", "email_notifications",
        "compact_mode", "sidebar_collapsed",
    ]

    for field, value in preferences.items():
        if field in allowed_fields:
            setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)

    return {
        "theme": prefs.theme,
        "language": prefs.language,
        "timezone": prefs.timezone,
        "notifications_enabled": prefs.notifications_enabled,
        "email_notifications": prefs.email_notifications,
        "compact_mode": prefs.compact_mode,
        "sidebar_collapsed": prefs.sidebar_collapsed,
    }


@router.get("/general", response_model=GeneralSettings)
async def get_general_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # In a real app, these would come from a settings table
    return GeneralSettings(
        app_name="Reverse API Engineer",
        workspace_name="My Workspace",
        default_discovery_mode="agent",
        default_output_language="typescript",
        default_execution_timeout=3600,
    )


@router.put("/general", response_model=GeneralSettings)
async def update_general_settings(
    settings: GeneralSettings,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # In a real app, save to settings table
    return settings


@router.get("/execution", response_model=ExecutionSettings)
async def get_execution_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return ExecutionSettings()


@router.put("/execution", response_model=ExecutionSettings)
async def update_execution_settings(
    settings: ExecutionSettings,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return settings


@router.get("/storage", response_model=StorageSettings)
async def get_storage_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return StorageSettings()


@router.put("/storage", response_model=StorageSettings)
async def update_storage_settings(
    settings: StorageSettings,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return settings


@router.get("/health")
async def system_health(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check database
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "checks": {
            "database": db_status,
            "redis": "healthy",  # Would check Redis
            "cli": "healthy",    # Would check CLI
            "storage": "healthy",
        },
        "version": "0.1.0",
    }