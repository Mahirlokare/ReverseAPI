import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.models import Base


def normalize_database_url(url: str) -> str:
    """Normalize provider connection strings for the async SQLAlchemy driver."""
    value = url.strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+asyncpg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    return value


DATABASE_URL = normalize_database_url(settings.DATABASE_URL)
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": settings.DEBUG,
    "json_serializer": lambda obj: json.dumps(obj, default=str),
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    if settings.ENVIRONMENT == "test":
        engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_pre_ping": True,
    })
    if settings.ENVIRONMENT == "test":
        engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize missing tables. Production schema changes should use Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session outside of FastAPI dependency."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
