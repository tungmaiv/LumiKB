"""Integration tests for Data Retention and Cleanup.

Story 9-14: Data Retention and Cleanup

RED PHASE: All tests are designed to FAIL until implementation is complete.
These tests verify the admin API endpoints and full cleanup flow.

Run with: pytest backend/tests/integration/test_retention_cleanup.py -v
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.factories import (
    create_completed_trace,
)


class TestRetentionPreviewEndpoint:
    """Tests for AC2: Admin API exposes preview of records to be deleted."""

    @pytest.mark.asyncio
    async def test_preview_requires_admin_role(
        self, async_client: AsyncClient, regular_user_token: str
    ) -> None:
        """Non-admin users should not access retention preview."""
        response = await async_client.get(
            "/api/v1/admin/observability/retention/preview",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_preview_returns_table_breakdown(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Preview should return breakdown by table."""
        response = await async_client.get(
            "/api/v1/admin/observability/retention/preview",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have results for each table
        assert "tables" in data
        assert isinstance(data["tables"], list)

        # Each table entry should have expected fields
        for table in data["tables"]:
            assert "table_name" in table
            assert "records_to_delete" in table or "chunks_to_drop" in table
            assert "retention_days" in table

    @pytest.mark.asyncio
    async def test_preview_shows_chunks_with_timescaledb(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Preview should show chunks when TimescaleDB is available."""
        response = await async_client.get(
            "/api/v1/admin/observability/retention/preview",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check if timescaledb is used
        if data.get("timescaledb_available"):
            # Should show chunks_to_drop for hypertables
            traces_table = next(
                (t for t in data["tables"] if "traces" in t["table_name"]), None
            )
            assert traces_table is not None
            assert "chunks_to_drop" in traces_table


class TestRetentionCleanupEndpoint:
    """Tests for AC3: Admin can trigger cleanup via API."""

    @pytest.mark.asyncio
    async def test_cleanup_requires_admin_role(
        self, async_client: AsyncClient, regular_user_token: str
    ) -> None:
        """Non-admin users should not trigger cleanup."""
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cleanup_returns_summary(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Cleanup should return summary of deleted records."""
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "errors" in data
        assert "duration_ms" in data

    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_traces(
        self, async_client: AsyncClient, admin_token: str, db_session
    ) -> None:
        """Cleanup should delete traces older than retention period."""
        # Create old trace (older than retention period)
        old_trace = create_completed_trace(
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        db_session.add(old_trace)
        await db_session.commit()

        old_trace_id = old_trace.trace_id

        # Run cleanup
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        # Verify old trace was deleted
        from sqlalchemy import select

        from app.models.observability import Trace

        result = await db_session.execute(
            select(Trace).where(Trace.trace_id == old_trace_id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cleanup_preserves_recent_traces(
        self, async_client: AsyncClient, admin_token: str, db_session
    ) -> None:
        """Cleanup should preserve traces within retention period."""
        # Create recent trace
        recent_trace = create_completed_trace(
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(recent_trace)
        await db_session.commit()

        recent_trace_id = recent_trace.trace_id

        # Run cleanup
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        # Verify recent trace still exists
        from sqlalchemy import select

        from app.models.observability import Trace

        result = await db_session.execute(
            select(Trace).where(Trace.trace_id == recent_trace_id)
        )
        assert result.scalar_one_or_none() is not None


class TestRetentionConfiguration:
    """Tests for AC1: Configurable retention periods."""

    @pytest.mark.asyncio
    async def test_get_retention_config(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Admin should be able to get retention configuration."""
        response = await async_client.get(
            "/api/v1/admin/observability/retention/config",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "observability_retention_days" in data
        assert "observability_metrics_retention_days" in data
        assert isinstance(data["observability_retention_days"], int)

    @pytest.mark.asyncio
    async def test_update_retention_config(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Admin should be able to update retention configuration."""
        response = await async_client.put(
            "/api/v1/admin/observability/retention/config",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"observability_retention_days": 60},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["observability_retention_days"] == 60


class TestTimescaleDBIntegration:
    """Tests for AC5: TimescaleDB drop_chunks integration."""

    @pytest.mark.asyncio
    async def test_uses_drop_chunks_when_available(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Cleanup should use drop_chunks when TimescaleDB is available."""
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check if TimescaleDB was used
        assert "timescaledb_used" in data


class TestBackfillEndpoint:
    """Tests for AC7: Backfill capability."""

    @pytest.mark.asyncio
    async def test_backfill_metrics_requires_admin(
        self, async_client: AsyncClient, regular_user_token: str
    ) -> None:
        """Backfill should require admin role."""
        response = await async_client.post(
            "/api/v1/admin/observability/metrics/backfill",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "start_date": "2025-12-01",
                "end_date": "2025-12-15",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_backfill_returns_summary(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Backfill should return processing summary."""
        response = await async_client.post(
            "/api/v1/admin/observability/metrics/backfill",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "start_date": "2025-12-01",
                "end_date": "2025-12-02",
                "granularity": "hour",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "buckets_processed" in data
        assert "metrics_created" in data
        assert "duration_ms" in data


class TestProviderSyncStatusCleanup:
    """Tests for AC6: Provider sync status cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_includes_sync_status(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Cleanup should include provider sync status table."""
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check that sync status table was processed
        sync_result = next(
            (
                r
                for r in data["results"]
                if "provider_sync_status" in r.get("table", "")
            ),
            None,
        )
        assert sync_result is not None

    @pytest.mark.asyncio
    async def test_sync_status_uses_shorter_retention(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Provider sync status should use shorter retention (7 days)."""
        response = await async_client.get(
            "/api/v1/admin/observability/retention/preview",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        sync_table = next(
            (
                t
                for t in data["tables"]
                if "provider_sync_status" in t.get("table_name", "")
            ),
            None,
        )

        if sync_table:
            assert sync_table["retention_days"] == 7


class TestErrorHandling:
    """Tests for AC8: Error handling and reporting."""

    @pytest.mark.asyncio
    async def test_partial_failure_reports_errors(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Cleanup should report errors for individual table failures."""
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have errors array (even if empty)
        assert "errors" in data
        assert isinstance(data["errors"], list)

    @pytest.mark.asyncio
    async def test_cleanup_audit_logged(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Cleanup operations should be audit logged."""
        response = await async_client.post(
            "/api/v1/admin/observability/retention/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        # Check audit log for cleanup event
        audit_response = await async_client.get(
            "/api/v1/admin/audit?action=retention_cleanup",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should have at least one cleanup audit entry
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert len(audit_data["items"]) > 0
