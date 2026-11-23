from typing import Optional, List, Generic, TypeVar
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

# Enums matching database models
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RunStatus(str, Enum):
    QUEUED = "queued"
    INITIALIZING = "initializing"
    BROWSER_STARTING = "browser_starting"
    NAVIGATING = "navigating"
    INTERACTING = "interacting"
    CAPTURING_TRAFFIC = "capturing_traffic"
    ANALYZING_REQUESTS = "analyzing_requests"
    GENERATING_CLIENT = "generating_client"
    VALIDATING_OUTPUT = "validating_output"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ExecutionMode(str, Enum):
    AGENT = "agent"
    MANUAL = "manual"
    ENGINEER = "engineer"


class BrowserProvider(str, Enum):
    PLAYWRIGHT = "playwright"
    CHROME_MCP = "chrome_mcp"
    VERCEL_AGENT_BROWSER = "vercel_agent_browser"


class OutputLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    C = "c"
    POWERSHELL = "powershell"


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class Message(BaseModel):
    message: str


# Workspace schemas
class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True


class WorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: UserRole
    joined_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


class WorkspaceMemberInvite(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.DEVELOPER


# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_website: str = Field(..., max_length=500)
    website_category: Optional[str] = None
    default_task: Optional[str] = None
    default_output_language: OutputLanguage = OutputLanguage.TYPESCRIPT
    default_execution_mode: ExecutionMode = ExecutionMode.AGENT
    default_ai_provider: Optional[str] = None
    default_model: Optional[str] = None


class ProjectCreate(ProjectBase):
    workspace_id: UUID


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_website: Optional[str] = Field(None, max_length=500)
    website_category: Optional[str] = None
    default_task: Optional[str] = None
    default_output_language: Optional[OutputLanguage] = None
    default_execution_mode: Optional[ExecutionMode] = None
    default_ai_provider: Optional[str] = None
    default_model: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    id: UUID
    status: ProjectStatus
    workspace_id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime]
    run_count: int = 0
    endpoint_count: int = 0
    client_count: int = 0

    class Config:
        from_attributes = True


class ProjectSettingsBase(BaseModel):
    browser_provider: BrowserProvider = BrowserProvider.PLAYWRIGHT
    headless_mode: bool = True
    execution_timeout: int = 3600
    max_retries: int = 2
    artifact_retention_days: int = 30
    auto_cleanup_temp: bool = True


class ProjectSettingsResponse(ProjectSettingsBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Discovery Run schemas
class RunBase(BaseModel):
    target_url: str = Field(..., max_length=500)
    task: str
    mode: ExecutionMode
    browser_provider: Optional[BrowserProvider] = None
    ai_provider: Optional[str] = None
    model: Optional[str] = None
    output_language: OutputLanguage = OutputLanguage.TYPESCRIPT


class RunCreate(RunBase):
    project_id: UUID


class RunUpdate(BaseModel):
    status: Optional[RunStatus] = None
    error_summary: Optional[str] = None


class RunResponse(RunBase):
    id: UUID
    engine_run_id: Optional[str]
    status: RunStatus
    exit_code: Optional[int]
    error_summary: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[int]
    execution_config: Optional[dict]
    project_id: UUID
    user_id: UUID
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunEventResponse(BaseModel):
    id: UUID
    run_id: UUID
    event_type: str
    message: Optional[str]
    metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class RunLogResponse(BaseModel):
    id: UUID
    run_id: UUID
    level: str
    message: str
    source: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Capture schemas
class CaptureResponse(BaseModel):
    id: UUID
    file_path: str
    file_size: Optional[int]
    request_count: int
    host_distribution: Optional[dict]
    methods_distribution: Optional[dict]
    target_domain: Optional[str]
    is_sanitized: bool
    compatibility_status: Optional[str]
    project_id: UUID
    run_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Endpoint schemas
class APIEndpointBase(BaseModel):
    name: str
    method: str
    path: str
    full_url: Optional[str]
    host: Optional[str]
    status_code: Optional[int]


class APIEndpointResponse(APIEndpointBase):
    id: UUID
    source_website: Optional[str]
    discovered_at: datetime
    purpose: Optional[str]
    input_fields: Optional[dict]
    pagination_behavior: Optional[str]
    filter_behavior: Optional[str]
    dependencies: Optional[dict]
    related_endpoints: Optional[dict]
    confidence_level: Optional[str]
    project_id: UUID
    run_id: Optional[UUID]
    capture_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIRequestResponse(BaseModel):
    id: UUID
    endpoint_id: UUID
    headers: Optional[dict]
    query_params: Optional[dict]
    path_params: Optional[dict]
    body: Optional[dict]
    content_type: Optional[str]
    auth_metadata: Optional[dict]
    timestamp: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIResponseResponse(BaseModel):
    id: UUID
    endpoint_id: UUID
    status_code: Optional[int]
    headers: Optional[dict]
    body: Optional[dict]
    content_type: Optional[str]
    timing_ms: Optional[int]
    timestamp: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Generated Client schemas
class GeneratedClientFileResponse(BaseModel):
    id: UUID
    client_id: UUID
    file_path: str
    file_name: str
    content: Optional[str]
    size: Optional[int]
    mime_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedClientBase(BaseModel):
    name: str
    language: OutputLanguage


class GeneratedClientResponse(GeneratedClientBase):
    id: UUID
    version: str
    file_count: int
    validation_status: Optional[str]
    validation_output: Optional[str]
    source_capture_id: Optional[UUID]
    run_id: Optional[UUID]
    project_id: UUID
    ai_provider: Optional[str]
    model: Optional[str]
    created_at: datetime
    updated_at: datetime
    files: List[GeneratedClientFileResponse] = []

    class Config:
        from_attributes = True


class ClientVersionResponse(BaseModel):
    id: UUID
    client_id: UUID
    version: str
    changelog: Optional[str]
    ai_provider: Optional[str]
    model: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ClientExecutionResponse(BaseModel):
    id: UUID
    client_id: UUID
    entry_point: Optional[str]
    parameters: Optional[dict]
    status: str
    exit_code: Optional[int]
    output: Optional[str]
    error_summary: Optional[str]
    duration_ms: Optional[int]
    network_activity: Optional[dict]
    result_files: Optional[dict]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# AI Provider schemas
class AIProviderConfigBase(BaseModel):
    provider: str
    model_id: str
    display_name: Optional[str] = None
    provider_settings: Optional[dict] = None


class AIProviderConfigCreate(AIProviderConfigBase):
    pass


class AIProviderConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    provider_settings: Optional[dict] = None
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None


class AIProviderConfigResponse(AIProviderConfigBase):
    id: UUID
    user_id: UUID
    auth_status: str
    is_default: bool
    is_enabled: bool
    last_health_check: Optional[datetime]
    health_check_status: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Browser Provider schemas
class BrowserProviderConfigBase(BaseModel):
    provider: BrowserProvider


class BrowserProviderConfigCreate(BrowserProviderConfigBase):
    config: Optional[dict] = None


class BrowserProviderConfigResponse(BrowserProviderConfigBase):
    id: UUID
    user_id: UUID
    is_available: bool
    health_status: Optional[str]
    config: Optional[dict]
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Settings schemas
class GeneralSettings(BaseModel):
    app_name: str = "Reverse API Engineer"
    workspace_name: str
    default_project_behavior: str = "create"
    default_discovery_mode: ExecutionMode = ExecutionMode.AGENT
    default_output_language: OutputLanguage = OutputLanguage.TYPESCRIPT
    default_execution_timeout: int = 3600


class ExecutionSettings(BaseModel):
    max_concurrent_jobs: int = 3
    max_execution_duration: int = 3600
    per_job_resource_limits: dict = {}
    artifact_retention: int = 30
    worker_availability: bool = True
    safe_retry_configuration: dict = {}


class StorageSettings(BaseModel):
    artifact_storage_location: str
    max_upload_size_mb: int = 100
    max_project_storage_gb: int = 10
    har_retention: int = 30
    generated_client_retention: int = 90
    temporary_file_cleanup: bool = True


# Notification schemas
class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: Optional[str]
    data: Optional[dict]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Pagination
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int