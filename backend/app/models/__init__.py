import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, ForeignKey, Enum, Boolean,
    JSON, Index, UniqueConstraint
)
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PGDialectUUID
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    Accepts both uuid.UUID and str seamlessly, converting back to uuid.UUID.
    """
    impl = CHAR(36)
    cache_ok = True

    def __init__(self, as_uuid=True, *args, **kwargs):
        self.as_uuid = as_uuid
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGDialectUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


PG_UUID = GUID


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RunStatus(str, enum.Enum):
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


class ExecutionMode(str, enum.Enum):
    AGENT = "agent"
    MANUAL = "manual"
    ENGINEER = "engineer"


class BrowserProvider(str, enum.Enum):
    PLAYWRIGHT = "playwright"
    CHROME_MCP = "chrome_mcp"
    VERCEL_AGENT_BROWSER = "vercel_agent_browser"


class OutputLanguage(str, enum.Enum):
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


class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspaces = relationship("WorkspaceMember", back_populates="user")
    projects = relationship("Project", back_populates="owner")
    runs = relationship("DiscoveryRun", back_populates="user")
    ai_provider_configs = relationship("AIProviderConfig", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)

    __table_args__ = (
        Index("ix_users_email", "email"),
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(PG_UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspaces")

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("ix_workspace_members_workspace_id", "workspace_id"),
        Index("ix_workspace_members_user_id", "user_id"),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_website = Column(String(500), nullable=False)
    website_category = Column(String(100))
    default_task = Column(Text)
    default_output_language = Column(Enum(OutputLanguage), default=OutputLanguage.TYPESCRIPT)
    default_execution_mode = Column(Enum(ExecutionMode), default=ExecutionMode.AGENT)
    default_ai_provider = Column(String(100))
    default_model = Column(String(100))
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    workspace_id = Column(PG_UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime(timezone=True))

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    owner = relationship("User", back_populates="projects")
    runs = relationship("DiscoveryRun", back_populates="project", cascade="all, delete-orphan")
    captures = relationship("Capture", back_populates="project", cascade="all, delete-orphan")
    clients = relationship("GeneratedClient", back_populates="project", cascade="all, delete-orphan")
    endpoints = relationship("APIEndpoint", back_populates="project", cascade="all, delete-orphan")
    settings = relationship("ProjectSettings", back_populates="project", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_workspace_id", "workspace_id"),
        Index("ix_projects_owner_id", "owner_id"),
        Index("ix_projects_status", "status"),
    )


class ProjectSettings(Base):
    __tablename__ = "project_settings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    browser_provider = Column(Enum(BrowserProvider), default=BrowserProvider.PLAYWRIGHT)
    headless_mode = Column(Boolean, default=True)
    execution_timeout = Column(Integer, default=3600)
    max_retries = Column(Integer, default=2)
    artifact_retention_days = Column(Integer, default=30)
    auto_cleanup_temp = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="settings")


class DiscoveryRun(Base):
    __tablename__ = "discovery_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engine_run_id = Column(String(255))  # Original CLI run ID
    target_url = Column(String(500), nullable=False)
    task = Column(Text, nullable=False)
    mode = Column(Enum(ExecutionMode), nullable=False)
    browser_provider = Column(Enum(BrowserProvider))
    ai_provider = Column(String(100))
    model = Column(String(100))
    output_language = Column(Enum(OutputLanguage))
    status = Column(Enum(RunStatus), default=RunStatus.QUEUED, nullable=False)
    exit_code = Column(Integer)
    error_summary = Column(Text)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    execution_config = Column(JSON)  # Full config snapshot
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(PG_UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="runs")
    user = relationship("User", back_populates="runs")
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan", order_by="RunEvent.created_at")
    logs = relationship("RunLog", back_populates="run", cascade="all, delete-orphan")
    capture = relationship("Capture", back_populates="run", uselist=False)
    clients = relationship("GeneratedClient", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_discovery_runs_project_id", "project_id"),
        Index("ix_discovery_runs_user_id", "user_id"),
        Index("ix_discovery_runs_status", "status"),
        Index("ix_discovery_runs_created_at", "created_at"),
    )


class RunEvent(Base):
    __tablename__ = "run_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    message = Column(Text)
    event_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    @property
    def metadata(self):
        return self.event_metadata

    @metadata.setter
    def metadata(self, value):
        self.event_metadata = value

    # Relationships
    run = relationship("DiscoveryRun", back_populates="events")

    __table_args__ = (
        Index("ix_run_events_run_id", "run_id"),
    )


class RunLog(Base):
    __tablename__ = "run_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(20), nullable=False)  # debug, info, warning, error
    message = Column(Text, nullable=False)
    source = Column(String(100))  # cli, worker, browser, ai
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    run = relationship("DiscoveryRun", back_populates="logs")

    __table_args__ = (
        Index("ix_run_logs_run_id", "run_id"),
        Index("ix_run_logs_level", "level"),
    )


class Capture(Base):
    __tablename__ = "captures"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    request_count = Column(Integer, default=0)
    host_distribution = Column(JSON)
    methods_distribution = Column(JSON)
    target_domain = Column(String(255))
    is_sanitized = Column(Boolean, default=False)
    compatibility_status = Column(String(50))
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="captures")
    run = relationship("DiscoveryRun", back_populates="capture")
    clients = relationship("GeneratedClient", back_populates="source_capture")

    __table_args__ = (
        Index("ix_captures_project_id", "project_id"),
        Index("ix_captures_run_id", "run_id"),
    )


class APIEndpoint(Base):
    __tablename__ = "api_endpoints"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    full_url = Column(String(500))
    host = Column(String(255))
    status_code = Column(Integer)
    source_website = Column(String(500))
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    purpose = Column(Text)
    input_fields = Column(JSON)
    pagination_behavior = Column(Text)
    filter_behavior = Column(Text)
    dependencies = Column(JSON)
    related_endpoints = Column(JSON)
    confidence_level = Column(String(50))
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="SET NULL"))
    capture_id = Column(PG_UUID(as_uuid=True), ForeignKey("captures.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="endpoints")
    requests = relationship("APIRequest", back_populates="endpoint", cascade="all, delete-orphan")
    responses = relationship("APIResponse", back_populates="endpoint", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_api_endpoints_project_id", "project_id"),
        Index("ix_api_endpoints_run_id", "run_id"),
        Index("ix_api_endpoints_method", "method"),
        Index("ix_api_endpoints_host", "host"),
    )


class APIRequest(Base):
    __tablename__ = "api_requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id = Column(PG_UUID(as_uuid=True), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False)
    headers = Column(JSON)
    query_params = Column(JSON)
    path_params = Column(JSON)
    body = Column(JSON)
    content_type = Column(String(100))
    auth_metadata = Column(JSON)
    timestamp = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    endpoint = relationship("APIEndpoint", back_populates="requests")

    __table_args__ = (
        Index("ix_api_requests_endpoint_id", "endpoint_id"),
    )


class APIResponse(Base):
    __tablename__ = "api_responses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id = Column(PG_UUID(as_uuid=True), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False)
    status_code = Column(Integer)
    headers = Column(JSON)
    body = Column(JSON)
    content_type = Column(String(100))
    timing_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    endpoint = relationship("APIEndpoint", back_populates="responses")

    __table_args__ = (
        Index("ix_api_responses_endpoint_id", "endpoint_id"),
    )


class GeneratedClient(Base):
    __tablename__ = "generated_clients"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    language = Column(Enum(OutputLanguage), nullable=False)
    version = Column(String(50), default="1.0.0")
    file_count = Column(Integer, default=0)
    validation_status = Column(String(50))  # pending, passed, failed
    validation_output = Column(Text)
    source_capture_id = Column(PG_UUID(as_uuid=True), ForeignKey("captures.id", ondelete="SET NULL"))
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="SET NULL"))
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    ai_provider = Column(String(100))
    model = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="clients")
    run = relationship("DiscoveryRun", back_populates="clients")
    source_capture = relationship("Capture", back_populates="clients")
    files = relationship("GeneratedClientFile", back_populates="client", cascade="all, delete-orphan")
    versions = relationship("ClientVersion", back_populates="client", cascade="all, delete-orphan")
    executions = relationship("ClientExecution", back_populates="client", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_generated_clients_project_id", "project_id"),
        Index("ix_generated_clients_run_id", "run_id"),
        Index("ix_generated_clients_language", "language"),
    )


class GeneratedClientFile(Base):
    __tablename__ = "generated_client_files"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("generated_clients.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    content = Column(Text)
    size = Column(Integer)
    mime_type = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("GeneratedClient", back_populates="files")

    __table_args__ = (
        Index("ix_generated_client_files_client_id", "client_id"),
    )


class ClientVersion(Base):
    __tablename__ = "client_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("generated_clients.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    changelog = Column(Text)
    ai_provider = Column(String(100))
    model = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("GeneratedClient", back_populates="versions")

    __table_args__ = (
        Index("ix_client_versions_client_id", "client_id"),
    )


class ClientExecution(Base):
    __tablename__ = "client_executions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("generated_clients.id", ondelete="CASCADE"), nullable=False)
    entry_point = Column(String(255))
    parameters = Column(JSON)
    status = Column(String(50))  # running, completed, failed, cancelled
    exit_code = Column(Integer)
    output = Column(Text)
    error_summary = Column(Text)
    duration_ms = Column(Integer)
    network_activity = Column(JSON)
    result_files = Column(JSON)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("GeneratedClient", back_populates="executions")

    __table_args__ = (
        Index("ix_client_executions_client_id", "client_id"),
        Index("ix_client_executions_status", "status"),
    )


class AIProviderConfig(Base):
    __tablename__ = "ai_provider_configs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(100), nullable=False)
    model_id = Column(String(100), nullable=False)
    display_name = Column(String(255))
    auth_status = Column(String(50))  # configured, validated, failed
    provider_settings = Column(JSON)
    is_default = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    last_health_check = Column(DateTime(timezone=True))
    health_check_status = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_provider_configs")

    __table_args__ = (
        Index("ix_ai_provider_configs_user_id", "user_id"),
        UniqueConstraint("user_id", "provider", "model_id", name="uq_user_provider_model"),
    )


class BrowserProviderConfig(Base):
    __tablename__ = "browser_provider_configs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(Enum(BrowserProvider), nullable=False)
    is_available = Column(Boolean, default=False)
    health_status = Column(String(50))
    config = Column(JSON)
    last_health_check = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_browser_provider_configs_user_id", "user_id"),
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(String(20), default="system")  # light, dark, system
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    compact_mode = Column(Boolean, default=False)
    sidebar_collapsed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    data = Column(JSON)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
    )


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    workspace_id = Column(PG_UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"))
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(PG_UUID(as_uuid=True))
    activity_metadata = Column("metadata", JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    @property
    def metadata(self):
        return self.activity_metadata

    @metadata.setter
    def metadata(self, value):
        self.activity_metadata = value

    __table_args__ = (
        Index("ix_activity_logs_user_id", "user_id"),
        Index("ix_activity_logs_workspace_id", "workspace_id"),
        Index("ix_activity_logs_project_id", "project_id"),
        Index("ix_activity_logs_created_at", "created_at"),
    )


class StorageRecord(Base):
    __tablename__ = "storage_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    category = Column(String(50))  # captures, clients, exports, temp, uploads
    storage_path = Column(String(500))  # Internal storage path
    is_public = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_storage_records_project_id", "project_id"),
        Index("ix_storage_records_category", "category"),
    )