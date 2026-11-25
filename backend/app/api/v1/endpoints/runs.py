import asyncio
import urllib.parse
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db, get_db_context
from app.core.security import get_current_active_user
from app.models import (
    User, Project, DiscoveryRun, RunStatus, ExecutionMode,
    RunEvent, RunLog, WorkspaceMember, UserRole
)
from app.api.v1.schemas import (
    RunCreate, RunUpdate, RunResponse,
    RunEventResponse, RunLogResponse,
    PaginatedResponse,
)
from app.services.cli_service import cli_service

router = APIRouter()


def validate_target_url(url: str) -> None:
    """Validate target URL and prevent SSRF attacks."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target URL must use HTTP or HTTPS protocol."
        )
    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hostname in target URL."
        )
    blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"]
    if host in blocked_hosts or host.endswith(".local") or host.endswith(".internal"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Navigation to restricted host '{host}' is prohibited."
        )
    if host.startswith("10.") or host.startswith("192.168.") or (host.startswith("172.") and 16 <= int(host.split(".")[1]) <= 31):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Navigation to private IP ranges is prohibited."
        )


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # SSRF Protection
    validate_target_url(run_data.target_url)

    # Check or auto-create project
    if run_data.project_id:
        result = await db.execute(
            select(Project)
            .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
            .where(
                Project.id == run_data.project_id,
                WorkspaceMember.user_id == current_user.id,
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or not authorized")
    else:
        # Auto-create project for target website
        ws_result = await db.execute(
            select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == current_user.id)
        )
        workspace_id = ws_result.scalars().first()
        if not workspace_id:
            from app.models import Workspace, UserRole
            workspace = Workspace(
                name=f"{current_user.full_name or current_user.email}'s Workspace",
                slug=f"ws-{current_user.id.hex[:8]}",
                owner_id=current_user.id,
            )
            db.add(workspace)
            await db.flush()
            member = WorkspaceMember(workspace_id=workspace.id, user_id=current_user.id, role=UserRole.OWNER)
            db.add(member)
            await db.flush()
            workspace_id = workspace.id

        domain = urllib.parse.urlparse(run_data.target_url).netloc or "Discovered Target"
        project = Project(
            name=f"Project ({domain})",
            target_website=run_data.target_url,
            workspace_id=workspace_id,
            owner_id=current_user.id,
            default_output_language=run_data.output_language,
            default_execution_mode=run_data.mode,
        )
        db.add(project)
        await db.flush()

    # Create run record
    run_dict = run_data.model_dump()
    run_dict["project_id"] = project.id
    run = DiscoveryRun(
        **run_dict,
        user_id=current_user.id,
        workspace_id=project.workspace_id,
        status=RunStatus.QUEUED,
        execution_config=run_data.model_dump(mode="json"),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Enqueue job
    await cli_service.enqueue_run(str(run.id))

    return RunResponse.model_validate(run)


@router.get("", response_model=PaginatedResponse[RunResponse])
async def list_runs(
    project_id: UUID | None = Query(None),
    status_filter: RunStatus | None = Query(None, alias="status"),
    mode_filter: ExecutionMode | None = Query(None, alias="mode"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Build query - only runs from projects user has access to
    subquery = select(Project.id).join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == current_user.id
    )

    query = select(DiscoveryRun).where(DiscoveryRun.project_id.in_(subquery))

    if project_id:
        query = query.where(DiscoveryRun.project_id == project_id)

    if status_filter:
        query = query.where(DiscoveryRun.status == status_filter)

    if mode_filter:
        query = query.where(DiscoveryRun.mode == mode_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(DiscoveryRun.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    runs = result.scalars().all()

    return PaginatedResponse(
        items=[RunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiscoveryRun)
        .join(Project, DiscoveryRun.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            DiscoveryRun.id == run_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunResponse.model_validate(run)


@router.put("/{run_id}", response_model=RunResponse)
async def update_run(
    run_id: UUID,
    run_data: RunUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiscoveryRun)
        .join(Project, DiscoveryRun.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            DiscoveryRun.id == run_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role.in_([UserRole.OWNER, UserRole.ADMIN, UserRole.DEVELOPER]),
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or not authorized")

    update_data = run_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(run, field, value)

    await db.commit()
    await db.refresh(run)

    return RunResponse.model_validate(run)


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    run_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiscoveryRun)
        .join(Project, DiscoveryRun.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            DiscoveryRun.id == run_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status not in [RunStatus.QUEUED, RunStatus.INITIALIZING, RunStatus.BROWSER_STARTING,
                          RunStatus.NAVIGATING, RunStatus.INTERACTING, RunStatus.CAPTURING_TRAFFIC,
                          RunStatus.ANALYZING_REQUESTS, RunStatus.GENERATING_CLIENT, RunStatus.VALIDATING_OUTPUT]:
        raise HTTPException(status_code=400, detail="Run cannot be cancelled in current state")

    # Cancel via CLI service
    await cli_service.cancel_run(str(run_id))

    run.status = RunStatus.CANCELLED
    await db.commit()
    await db.refresh(run)

    return RunResponse.model_validate(run)


@router.post("/{run_id}/retry", response_model=RunResponse)
async def retry_run(
    run_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiscoveryRun)
        .join(Project, DiscoveryRun.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            DiscoveryRun.id == run_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status not in [RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.TIMED_OUT]:
        raise HTTPException(status_code=400, detail="Run can only be retried from failed/cancelled/timed out state")

    # Create new run with same config
    new_run = DiscoveryRun(
        target_url=run.target_url,
        task=run.task,
        mode=run.mode,
        browser_provider=run.browser_provider,
        ai_provider=run.ai_provider,
        model=run.model,
        output_language=run.output_language,
        user_id=current_user.id,
        workspace_id=run.workspace_id,
        project_id=run.project_id,
        status=RunStatus.QUEUED,
        execution_config=run.execution_config,
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)

    # Enqueue new run
    await cli_service.enqueue_run(str(new_run.id))

    return RunResponse.model_validate(new_run)


@router.get("/{run_id}/events", response_model=list[RunEventResponse])
async def get_run_events(
    run_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify access
    run_result = await db.execute(
        select(DiscoveryRun)
        .join(Project, DiscoveryRun.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            DiscoveryRun.id == run_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    if not run_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Run not found")

    result = await db.execute(
        select(RunEvent)
        .where(RunEvent.run_id == run_id)
        .order_by(RunEvent.created_at.asc())
    )
    events = result.scalars().all()

    return [RunEventResponse.model_validate(e) for e in events]


@router.get("/{run_id}/logs", response_model=list[RunLogResponse])
async def get_run_logs(
    run_id: UUID,
    level: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify access
    run_result = await db.execute(
        select(DiscoveryRun)
        .join(Project, DiscoveryRun.project_id == Project.id)
        .join(WorkspaceMember, Project.workspace_id == WorkspaceMember.workspace_id)
        .where(
            DiscoveryRun.id == run_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    if not run_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Run not found")

    query = select(RunLog).where(RunLog.run_id == run_id)
    if level:
        query = query.where(RunLog.level == level)
    query = query.order_by(RunLog.created_at.desc()).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [RunLogResponse.model_validate(l) for l in logs]


@router.websocket("/{run_id}/ws")
async def run_websocket_endpoint(websocket: WebSocket, run_id: UUID):
    """Real-time live execution updates via WebSocket."""
    await websocket.accept()
    last_status = None
    try:
        while True:
            async with get_db_context() as db:
                run = await db.get(DiscoveryRun, run_id)
                if not run:
                    await websocket.send_json({"error": "Run not found"})
                    break

                events_res = await db.execute(
                    select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.created_at.desc()).limit(10)
                )
                events = events_res.scalars().all()

                logs_res = await db.execute(
                    select(RunLog).where(RunLog.run_id == run_id).order_by(RunLog.created_at.desc()).limit(15)
                )
                logs = logs_res.scalars().all()

                status_val = run.status.value if hasattr(run.status, "value") else str(run.status)
                payload = {
                    "run_id": str(run_id),
                    "status": status_val,
                    "duration_seconds": run.duration_seconds,
                    "exit_code": run.exit_code,
                    "error_summary": run.error_summary,
                    "events": [
                        {
                            "id": str(e.id),
                            "event_type": e.event_type,
                            "message": e.message,
                            "created_at": e.created_at.isoformat() if e.created_at else None,
                        }
                        for e in reversed(events)
                    ],
                    "logs": [
                        {
                            "id": str(l.id),
                            "level": l.level,
                            "message": l.message,
                            "source": l.source,
                            "created_at": l.created_at.isoformat() if l.created_at else None,
                        }
                        for l in reversed(logs)
                    ],
                }
                await websocket.send_json(payload)

                if status_val in ["completed", "failed", "cancelled", "timed_out"]:
                    # Finished, give client final state and wait or close
                    await asyncio.sleep(2)
                    break

            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
