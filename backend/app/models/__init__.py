"""SQLAlchemy models."""

from app.models.audit import AuditEvent
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.config import SystemConfig
from app.models.document import Document, DocumentStatus
from app.models.draft import Draft, DraftStatus
from app.models.group import Group, UserGroup
from app.models.kb_access_log import AccessType, KBAccessLog
from app.models.kb_group_permission import KBGroupPermission
from app.models.knowledge_base import KnowledgeBase
from app.models.llm_model import LLMModel, ModelProvider, ModelStatus, ModelType
from app.models.observability import (
    DocumentEvent,
    MetricsAggregate,
    ObsChatMessage,
    ProviderSyncStatus,
    Span,
    Trace,
)
from app.models.outbox import Outbox
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Models
    "User",
    "KnowledgeBase",
    "KBPermission",
    "KBGroupPermission",
    "KBAccessLog",
    "Document",
    "Draft",
    "Group",
    "UserGroup",
    "LLMModel",
    "Outbox",
    "AuditEvent",
    "SystemConfig",
    # Observability Models
    "Trace",
    "Span",
    "ObsChatMessage",
    "DocumentEvent",
    "MetricsAggregate",
    "ProviderSyncStatus",
    # Enums
    "AccessType",
    "DocumentStatus",
    "DraftStatus",
    "ModelProvider",
    "ModelStatus",
    "ModelType",
    "PermissionLevel",
]
