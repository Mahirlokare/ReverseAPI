import asyncio
import structlog
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db_context
from app.models import DiscoveryRun, RunStatus, RunEvent, RunLog
from app.services.cli_service import cli_service

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def execute_discovery_run(self, run_id: str):
    """Execute a discovery run via the CLI service."""
    logger.info("Starting discovery run task", run_id=run_id, task_id=self.request.id)

    try:
        # Run the async CLI service
        asyncio.run(_execute_run_async(run_id))
        logger.info("Discovery run task completed", run_id=run_id)
    except Exception as exc:
        logger.error("Discovery run task failed", run_id=run_id, error=str(exc))
        raise self.retry(exc=exc)


async def _execute_run_async(run_id: str):
    """Async wrapper for run execution."""
    async with get_db_context() as db:
        run = await db.get(DiscoveryRun, UUID(run_id))
        if not run:
            logger.error("Run not found", run_id=run_id)
            return

        # Update status to initializing
        run.status = RunStatus.INITIALIZING
        run.started_at = asyncio.get_event_loop().time()  # Will be replaced with actual datetime
        await db.commit()

        # Add event
        event = RunEvent(
            run_id=run.id,
            event_type="execution_started",
            message="Discovery run started by worker",
        )
        db.add(event)
        await db.commit()

        try:
            # Execute via CLI service
            await cli_service._execute_run(run_id)
        except Exception as e:
            logger.error("CLI execution failed", run_id=run_id, error=str(e))
            run.status = RunStatus.FAILED
            run.error_summary = str(e)
            await db.commit()
            raise


@shared_task
def cancel_run_task(run_id: str):
    """Cancel a running discovery run."""
    logger.info("Cancelling run", run_id=run_id)
    asyncio.run(cli_service.cancel_run(run_id))


@shared_task
def cleanup_old_artifacts():
    """Periodic task to clean up old artifacts."""
    logger.info("Running artifact cleanup")
    # Implementation would go here
    pass


@shared_task
def health_check_providers():
    """Periodic health check for AI and browser providers."""
    logger.info("Running provider health checks")
    # Implementation would go here
    pass