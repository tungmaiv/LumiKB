"""Test data factories for admin features (Epic 5 Stories 5.1-5.6).

Provides factory functions for:
- Admin statistics data
- Audit log filters and events
- Queue status and worker info
- System configuration
- KB statistics (admin view)

Usage:
    from tests.factories import create_admin_stats, create_audit_filter

    stats = create_admin_stats(total_users=100)
    filter_data = create_audit_filter(start_date="2025-01-01", user_email="test@example.com")
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


def create_admin_stats(**overrides: Any) -> dict[str, Any]:
    """Create admin dashboard statistics response (Story 5.1).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching AdminStats schema

    Example:
        stats = create_admin_stats(users={"total": 150, "active": 120})
    """
    defaults = {
        "users": {
            "total": 50,
            "active": 35,  # Active in last 30 days
            "inactive": 15,
        },
        "knowledgeBases": {
            "total": 20,
            "byStatus": {"active": 18, "archived": 2},
        },
        "documents": {
            "total": 500,
            "byStatus": {"processed": 480, "queued": 15, "failed": 5},
        },
        "storage": {
            "totalBytes": 10 * 1024 * 1024 * 1024,  # 10 GB
            "avgDocSizeBytes": 20 * 1024 * 1024,  # 20 MB
        },
        "activity": {
            "searches": {"last24h": 120, "last7d": 850, "last30d": 3200},
            "generations": {"last24h": 45, "last7d": 320, "last30d": 1100},
        },
        "trends": {
            "searches": [50, 55, 60, 58, 62, 65, 70, 75, 80, 85] * 3,  # 30 days
            "generations": [20, 22, 25, 28, 30, 32, 35, 38, 40, 42] * 3,
        },
    }

    # Merge nested dictionaries properly
    result = defaults.copy()
    for key, value in overrides.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = {**result[key], **value}
        else:
            result[key] = value

    return result


def create_audit_filter(**overrides: Any) -> dict[str, Any]:
    """Create audit log filter request (Story 5.2).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching AuditLogFilter schema

    Example:
        filter = create_audit_filter(action_type="search", page=2)
    """
    defaults = {
        "start_date": None,
        "end_date": None,
        "user_email": None,
        "action_type": None,  # search, generation, document_upload, etc.
        "resource_type": None,  # knowledge_base, document, user, etc.
        "page": 1,
        "page_size": 50,
    }

    return {**defaults, **overrides}


def create_audit_event(**overrides: Any) -> dict[str, Any]:
    """Create audit log event (Story 5.2).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching AuditEvent model

    Example:
        event = create_audit_event(action_type="search", user_email="test@example.com")
    """
    now = datetime.now(UTC)

    defaults = {
        "id": str(uuid4()),
        "timestamp": now.isoformat(),
        "user_id": str(uuid4()),
        "user_email": "test@example.com",
        "action_type": "search",
        "resource_type": "knowledge_base",
        "resource_id": str(uuid4()),
        "status": "success",
        "duration_ms": 150,
        "ip_address": "192.168.1.1",
        "details": {
            "query": "test query",
            "result_count": 10,
        },
    }

    return {**defaults, **overrides}


def create_queue_status(**overrides: Any) -> dict[str, Any]:
    """Create processing queue status (Story 5.4).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching QueueStatus schema

    Example:
        status = create_queue_status(queue_name="document_processing", depth=25)
    """
    defaults = {
        "queue_name": "document_processing",
        "depth": 10,  # Tasks waiting
        "active_tasks": 3,
        "scheduled_tasks": 2,
        "workers": [
            {
                "worker_id": "worker-1@lumikb-backend",
                "status": "online",
                "active_tasks": 2,
                "processed_count": 150,
            },
            {
                "worker_id": "worker-2@lumikb-backend",
                "status": "online",
                "active_tasks": 1,
                "processed_count": 135,
            },
        ],
    }

    return {**defaults, **overrides}


def create_worker_info(**overrides: Any) -> dict[str, Any]:
    """Create worker information (Story 5.4).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching WorkerInfo schema

    Example:
        worker = create_worker_info(worker_id="worker-3", status="offline")
    """
    defaults = {
        "worker_id": "worker-1@lumikb-backend",
        "status": "online",  # online, offline
        "active_tasks": 2,
        "processed_count": 150,
    }

    return {**defaults, **overrides}


def create_config_value(**overrides: Any) -> dict[str, Any]:
    """Create system configuration value (Story 5.5).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching ConfigValue schema

    Example:
        config = create_config_value(key="session_timeout", value=3600)
    """
    defaults = {
        "key": "session_timeout",
        "value": 1800,  # 30 minutes in seconds
        "description": "Session timeout in seconds",
        "data_type": "integer",
        "is_sensitive": False,
        "last_updated": datetime.now(UTC).isoformat(),
        "updated_by": "admin@example.com",
    }

    return {**defaults, **overrides}


def create_kb_stats(**overrides: Any) -> dict[str, Any]:
    """Create KB statistics (admin view) (Story 5.6).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching KBDetailedStats schema

    Example:
        stats = create_kb_stats(document_count=100, chunk_count=5000)
    """
    defaults = {
        "kb_id": str(uuid4()),
        "kb_name": "Test Knowledge Base",
        "document_count": 50,
        "total_chunks": 2500,
        "total_embeddings": 2500,
        "storage_size_bytes": 500 * 1024 * 1024,  # 500 MB
        "usage_metrics": {
            "searches_30d": 250,
            "generations_30d": 80,
            "unique_users_30d": 15,
        },
        "top_documents": [
            {
                "document_id": str(uuid4()),
                "title": "Annual Report 2024.pdf",
                "access_count": 45,
                "last_accessed": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
            },
            {
                "document_id": str(uuid4()),
                "title": "Product Roadmap Q1.docx",
                "access_count": 38,
                "last_accessed": (datetime.now(UTC) - timedelta(hours=5)).isoformat(),
            },
            {
                "document_id": str(uuid4()),
                "title": "Engineering Guidelines.md",
                "access_count": 32,
                "last_accessed": (datetime.now(UTC) - timedelta(hours=8)).isoformat(),
            },
        ],
    }

    return {**defaults, **overrides}


def create_onboarding_state(**overrides: Any) -> dict[str, Any]:
    """Create onboarding wizard state (Story 5.7).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching OnboardingState schema

    Example:
        state = create_onboarding_state(current_step=2, completed_steps=[1])
    """
    defaults = {
        "user_id": str(uuid4()),
        "current_step": 1,
        "completed_steps": [],
        "total_steps": 3,
        "is_completed": False,
        "skipped": False,
    }

    return {**defaults, **overrides}


def create_kb_recommendation(**overrides: Any) -> dict[str, Any]:
    """Create KB recommendation (Story 5.8).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching KBRecommendation schema

    Example:
        rec = create_kb_recommendation(kb_name="Engineering Docs", score=0.85)
    """
    defaults = {
        "kb_id": str(uuid4()),
        "kb_name": "Engineering Documentation",
        "description": "Internal engineering guides and best practices",
        "score": 0.75,
        "reason": "Based on recent search patterns",
        "last_accessed": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
    }

    return {**defaults, **overrides}


def create_recent_kb(**overrides: Any) -> dict[str, Any]:
    """Create recent KB entry (Story 5.9).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching recent KB schema

    Example:
        recent = create_recent_kb(kb_name="Product Docs", last_accessed="2025-01-01T10:00:00Z")
    """
    defaults = {
        "kb_id": str(uuid4()),
        "kb_name": "Product Documentation",
        "description": "Product specs and user guides",
        "last_accessed": datetime.now(UTC).isoformat(),
    }

    return {**defaults, **overrides}


def create_task_info(**overrides: Any) -> dict[str, Any]:
    """Create Celery task information (Story 5.4).

    Args:
        **overrides: Override default values

    Returns:
        Dictionary matching TaskInfo schema

    Example:
        task = create_task_info(task_name="process_document", status="running")
    """
    defaults = {
        "task_id": str(uuid4()),
        "task_name": "process_document",
        "status": "pending",  # pending, running, success, failed
        "started_at": datetime.now(UTC).isoformat(),
        "estimated_duration": 120,  # seconds
        "progress": 0.0,  # 0.0 to 1.0
    }

    return {**defaults, **overrides}
