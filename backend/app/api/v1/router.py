from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    workspaces,
    projects,
    runs,
    endpoints,
    captures,
    clients,
    ai_providers,
    browser_providers,
    settings as settings_endpoints,
    notifications,
    health,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(endpoints.router, prefix="/endpoints", tags=["endpoints"])
api_router.include_router(captures.router, prefix="/captures", tags=["captures"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(ai_providers.router, prefix="/ai-providers", tags=["ai-providers"])
api_router.include_router(browser_providers.router, prefix="/browser-providers", tags=["browser-providers"])
api_router.include_router(settings_endpoints.router, prefix="/settings", tags=["settings"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])