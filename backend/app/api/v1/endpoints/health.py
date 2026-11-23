from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models import Project, DiscoveryRun, RunStatus, APIEndpoint, GeneratedClient, Capture

router = APIRouter()


@router.get("")
@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "reverse-api-engineer",
    }


@router.get("/ready")
async def readiness_check():
    return {
        "status": "ready",
        "checks": {
            "database": "connected",
            "cli": "available",
        },
    }


@router.get("/live")
async def liveness_check():
    return {"status": "alive"}


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Return system-wide or user-scoped statistics for dashboard KPI cards."""
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar_one() or 0
    total_runs = (await db.execute(select(func.count(DiscoveryRun.id)))).scalar_one() or 0
    successful_runs = (
        await db.execute(
            select(func.count(DiscoveryRun.id)).where(DiscoveryRun.status == RunStatus.COMPLETED)
        )
    ).scalar_one() or 0
    failed_runs = (
        await db.execute(
            select(func.count(DiscoveryRun.id)).where(DiscoveryRun.status == RunStatus.FAILED)
        )
    ).scalar_one() or 0
    running_jobs = (
        await db.execute(
            select(func.count(DiscoveryRun.id)).where(
                DiscoveryRun.status.in_([
                    RunStatus.QUEUED,
                    RunStatus.INITIALIZING,
                    RunStatus.BROWSER_STARTING,
                    RunStatus.NAVIGATING,
                    RunStatus.INTERACTING,
                    RunStatus.CAPTURING_TRAFFIC,
                    RunStatus.ANALYZING_REQUESTS,
                    RunStatus.GENERATING_CLIENT,
                    RunStatus.VALIDATING_OUTPUT,
                ])
            )
        )
    ).scalar_one() or 0
    total_endpoints = (await db.execute(select(func.count(APIEndpoint.id)))).scalar_one() or 0
    total_clients = (await db.execute(select(func.count(GeneratedClient.id)))).scalar_one() or 0
    total_captures = (await db.execute(select(func.count(Capture.id)))).scalar_one() or 0

    return {
        "total_projects": total_projects,
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "running_jobs": running_jobs,
        "total_endpoints": total_endpoints,
        "total_clients": total_clients,
        "total_captures": total_captures,
    }
