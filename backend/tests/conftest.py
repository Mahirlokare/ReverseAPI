import asyncio
import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_PATH = Path(__file__).parent / "test_reverse_api.db"
if TEST_DB_PATH.exists():
    try:
        TEST_DB_PATH.unlink()
    except Exception:
        pass

TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.main import app
from app.core.database import get_db
from app.models import Base, User, UserRole, Workspace, WorkspaceMember
from app.core.security import get_password_hash, create_access_token
import app.core.database as app_db

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    json_serializer=lambda obj: json.dumps(obj, default=str),
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

app_db.engine = test_engine
app_db.async_session_maker = TestingSessionLocal


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cancel any background tasks from cli_service before dropping DB
    from app.services.cli_service import cli_service
    for task in list(cli_service.running_tasks.values()):
        if not task.done():
            task.cancel()
    if cli_service.running_tasks:
        await asyncio.gather(*cli_service.running_tasks.values(), return_exceptions=True)
        cli_service.running_tasks.clear()

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def auth_user(db_session):
    user = User(
        email="developer@example.com",
        hashed_password=get_password_hash("SecretPassword123!"),
        full_name="Lead Developer",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    workspace = Workspace(
        name="Developer Workspace",
        slug="dev-ws",
        owner_id=user.id,
    )
    db_session.add(workspace)
    await db_session.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=UserRole.OWNER,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"user": user, "workspace": workspace, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
