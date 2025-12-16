"""Unit tests for Retention Service.

Story 9-14: Data Retention and Cleanup
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.retention_service import (
    ALLOWED_TABLES,
    ALLOWED_TIMESTAMP_COLUMNS,
    HYPERTABLES,
    RetentionService,
    _validate_retention_days,
    _validate_table_name,
    _validate_timestamp_column,
)


class TestTimescaleDBAvailability:
    """Test TimescaleDB availability checking."""

    @pytest.mark.asyncio
    async def test_timescaledb_available(self):
        """Test detection when TimescaleDB is installed."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        available = await service.check_timescaledb_available()

        assert available is True
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_timescaledb_not_available(self):
        """Test detection when TimescaleDB is not installed."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        available = await service.check_timescaledb_available()

        assert available is False

    @pytest.mark.asyncio
    async def test_timescaledb_check_handles_error(self):
        """Test that errors during check return False."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("DB error"))

        service = RetentionService(mock_session)
        available = await service.check_timescaledb_available()

        assert available is False


class TestGetChunksToDrop:
    """Test chunk preview functionality."""

    @pytest.mark.asyncio
    async def test_get_chunks_returns_list(self):
        """Test getting list of chunks to drop."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("_hyper_1_chunk_1",),
            ("_hyper_1_chunk_2",),
            ("_hyper_1_chunk_3",),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        chunks = await service.get_chunks_to_drop("observability.traces", 90)

        assert len(chunks) == 3
        assert "_hyper_1_chunk_1" in chunks
        assert "_hyper_1_chunk_2" in chunks
        assert "_hyper_1_chunk_3" in chunks

    @pytest.mark.asyncio
    async def test_get_chunks_empty_result(self):
        """Test when no chunks to drop."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        chunks = await service.get_chunks_to_drop("observability.traces", 90)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_get_chunks_handles_error(self):
        """Test that errors return empty list."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Query error"))

        service = RetentionService(mock_session)
        chunks = await service.get_chunks_to_drop("observability.traces", 90)

        assert chunks == []


class TestDropOldChunks:
    """Test chunk dropping functionality."""

    @pytest.mark.asyncio
    async def test_drop_chunks_returns_count(self):
        """Test dropping chunks returns count."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("_hyper_1_chunk_1",),
            ("_hyper_1_chunk_2",),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        count = await service.drop_old_chunks("observability.traces", 90)

        assert count == 2

    @pytest.mark.asyncio
    async def test_drop_chunks_raises_on_error(self):
        """Test that drop errors are raised."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Drop failed"))

        service = RetentionService(mock_session)

        with pytest.raises(Exception, match="Drop failed"):
            await service.drop_old_chunks("observability.traces", 90)


class TestDeleteOldRecords:
    """Test fallback DELETE functionality."""

    @pytest.mark.asyncio
    async def test_delete_old_records(self):
        """Test deleting old records with standard DELETE."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 150
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        count = await service.delete_old_records("observability.traces", 90)

        assert count == 150

    @pytest.mark.asyncio
    async def test_delete_with_additional_filter(self):
        """Test delete with additional filter condition."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 50
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        count = await service.delete_old_records(
            "observability.provider_sync_status",
            7,
            timestamp_column="created_at",
            additional_filter="sync_status IN ('synced', 'failed')",
        )

        assert count == 50

        # Verify the query includes the filter
        call_args = mock_session.execute.call_args
        query = str(call_args[0][0])
        assert "sync_status IN ('synced', 'failed')" in query

    @pytest.mark.asyncio
    async def test_delete_raises_on_error(self):
        """Test that delete errors are raised."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Delete failed"))

        service = RetentionService(mock_session)

        with pytest.raises(Exception, match="Delete failed"):
            await service.delete_old_records("observability.traces", 90)


class TestCleanupProviderSyncStatus:
    """Test provider sync status cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_dry_run(self):
        """Test dry-run preview for sync status."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        result = await service.cleanup_provider_sync_status(dry_run=True)

        assert result["table"] == "observability.provider_sync_status"
        assert result["records_to_delete"] == 25
        assert result["dry_run"] is True

    @pytest.mark.asyncio
    async def test_cleanup_actual_delete(self):
        """Test actual deletion of sync status records."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 30
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)

        with patch.object(service, "delete_old_records", return_value=30):
            result = await service.cleanup_provider_sync_status(dry_run=False)

        assert result["table"] == "observability.provider_sync_status"
        assert result["records_deleted"] == 30
        assert result["dry_run"] is False


class TestCleanupHypertable:
    """Test single hypertable cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_dry_run_with_timescaledb(self):
        """Test dry-run preview using TimescaleDB."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with patch.object(
            service,
            "get_chunks_to_drop",
            return_value=["chunk1", "chunk2", "chunk3"],
        ):
            result = await service.cleanup_hypertable(
                "observability.traces",
                "observability_retention_days",
                use_timescaledb=True,
                dry_run=True,
            )

        assert result["table"] == "observability.traces"
        assert result["chunks_to_drop"] == 3
        assert result["dry_run"] is True

    @pytest.mark.asyncio
    async def test_cleanup_dry_run_without_timescaledb(self):
        """Test dry-run preview using standard DELETE count."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1000
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RetentionService(mock_session)
        result = await service.cleanup_hypertable(
            "observability.traces",
            "observability_retention_days",
            use_timescaledb=False,
            dry_run=True,
        )

        assert result["table"] == "observability.traces"
        assert result["records_to_delete"] == 1000
        assert result["dry_run"] is True

    @pytest.mark.asyncio
    async def test_cleanup_actual_with_timescaledb(self):
        """Test actual cleanup using TimescaleDB drop_chunks."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with patch.object(service, "drop_old_chunks", return_value=5):
            result = await service.cleanup_hypertable(
                "observability.traces",
                "observability_retention_days",
                use_timescaledb=True,
                dry_run=False,
            )

        assert result["table"] == "observability.traces"
        assert result["chunks_dropped"] == 5
        assert result["dry_run"] is False

    @pytest.mark.asyncio
    async def test_cleanup_actual_without_timescaledb(self):
        """Test actual cleanup using standard DELETE."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with patch.object(service, "delete_old_records", return_value=200):
            result = await service.cleanup_hypertable(
                "observability.traces",
                "observability_retention_days",
                use_timescaledb=False,
                dry_run=False,
            )

        assert result["table"] == "observability.traces"
        assert result["records_deleted"] == 200
        assert result["dry_run"] is False


class TestCleanupAll:
    """Test full cleanup operation."""

    @pytest.mark.asyncio
    async def test_cleanup_all_with_timescaledb(self):
        """Test cleanup of all tables with TimescaleDB."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        service = RetentionService(mock_session)

        with (
            patch.object(service, "check_timescaledb_available", return_value=True),
            patch.object(
                service,
                "cleanup_hypertable",
                return_value={"table": "test", "chunks_dropped": 2, "dry_run": False},
            ),
            patch.object(
                service,
                "cleanup_provider_sync_status",
                return_value={
                    "table": "observability.provider_sync_status",
                    "records_deleted": 10,
                    "dry_run": False,
                },
            ),
        ):
            result = await service.cleanup_all(dry_run=False)

        assert result["timescaledb_used"] is True
        assert result["dry_run"] is False
        assert len(result["errors"]) == 0

        # Should have results for all hypertables plus sync status
        assert len(result["results"]) == len(HYPERTABLES) + 1

        # Session should be committed
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cleanup_all_dry_run_no_commit(self):
        """Test that dry-run does not commit."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        service = RetentionService(mock_session)

        with (
            patch.object(service, "check_timescaledb_available", return_value=False),
            patch.object(
                service,
                "cleanup_hypertable",
                return_value={
                    "table": "test",
                    "records_to_delete": 100,
                    "dry_run": True,
                },
            ),
            patch.object(
                service,
                "cleanup_provider_sync_status",
                return_value={
                    "table": "observability.provider_sync_status",
                    "records_to_delete": 5,
                    "dry_run": True,
                },
            ),
        ):
            result = await service.cleanup_all(dry_run=True)

        assert result["dry_run"] is True
        # Session should NOT be committed for dry run
        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cleanup_all_handles_individual_errors(self):
        """Test that errors in one table don't stop others."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        service = RetentionService(mock_session)

        call_count = [0]

        async def cleanup_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Second table fails
                raise Exception("Table cleanup failed")
            return {"table": "test", "chunks_dropped": 1, "dry_run": False}

        with (
            patch.object(service, "check_timescaledb_available", return_value=True),
            patch.object(
                service, "cleanup_hypertable", side_effect=cleanup_side_effect
            ),
            patch.object(
                service,
                "cleanup_provider_sync_status",
                return_value={
                    "table": "observability.provider_sync_status",
                    "records_deleted": 5,
                    "dry_run": False,
                },
            ),
        ):
            result = await service.cleanup_all(dry_run=False)

        # Should have at least one error
        assert len(result["errors"]) == 1
        assert "Table cleanup failed" in result["errors"][0]["error"]

        # Should still have results for other tables
        assert len(result["results"]) >= len(HYPERTABLES)

    @pytest.mark.asyncio
    async def test_cleanup_all_without_timescaledb(self):
        """Test cleanup falls back to DELETE when no TimescaleDB."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        service = RetentionService(mock_session)

        with (
            patch.object(service, "check_timescaledb_available", return_value=False),
            patch.object(
                service,
                "cleanup_hypertable",
                return_value={"table": "test", "records_deleted": 50, "dry_run": False},
            ),
            patch.object(
                service,
                "cleanup_provider_sync_status",
                return_value={
                    "table": "observability.provider_sync_status",
                    "records_deleted": 5,
                    "dry_run": False,
                },
            ),
        ):
            result = await service.cleanup_all(dry_run=False)

        assert result["timescaledb_used"] is False


class TestHypertableConfiguration:
    """Test hypertable configuration is correct."""

    def test_all_hypertables_defined(self):
        """Test that all expected hypertables are configured."""
        expected_tables = [
            "observability.traces",
            "observability.spans",
            "observability.chat_messages",
            "observability.document_events",
            "observability.metrics_aggregates",
        ]

        table_names = [table for table, _ in HYPERTABLES]

        for expected in expected_tables:
            assert expected in table_names

    def test_retention_settings_valid(self):
        """Test that all retention settings reference valid config attributes."""
        valid_settings = [
            "observability_retention_days",
            "observability_metrics_retention_days",
        ]

        for _, retention_setting in HYPERTABLES:
            assert retention_setting in valid_settings

    def test_metrics_aggregates_has_longer_retention(self):
        """Test that metrics_aggregates uses longer retention setting."""
        for table, setting in HYPERTABLES:
            if "metrics_aggregates" in table:
                assert setting == "observability_metrics_retention_days"


class TestInputValidation:
    """Test SQL injection prevention through input validation."""

    def test_validate_table_name_accepts_allowed_tables(self):
        """Test that all allowed tables pass validation."""
        for table in ALLOWED_TABLES:
            # Should not raise
            _validate_table_name(table)

    def test_validate_table_name_rejects_invalid_tables(self):
        """Test that invalid table names are rejected."""
        invalid_tables = [
            "public.users",
            "observability.traces; DROP TABLE users;--",
            "malicious_table",
            "",
            "observability.traces'--",
        ]
        for table in invalid_tables:
            with pytest.raises(ValueError, match="Invalid table name"):
                _validate_table_name(table)

    def test_validate_timestamp_column_accepts_allowed(self):
        """Test that allowed timestamp columns pass validation."""
        for column in ALLOWED_TIMESTAMP_COLUMNS:
            # Should not raise
            _validate_timestamp_column(column)

    def test_validate_timestamp_column_rejects_invalid(self):
        """Test that invalid column names are rejected."""
        invalid_columns = [
            "id",
            "timestamp; DROP TABLE--",
            "",
            "created_at'--",
        ]
        for column in invalid_columns:
            with pytest.raises(ValueError, match="Invalid timestamp column"):
                _validate_timestamp_column(column)

    def test_validate_retention_days_accepts_valid(self):
        """Test that valid retention days pass validation."""
        valid_values = [1, 30, 90, 365, 3650]
        for days in valid_values:
            # Should not raise
            _validate_retention_days(days)

    def test_validate_retention_days_rejects_invalid(self):
        """Test that invalid retention days are rejected."""
        invalid_values = [0, -1, 3651, 10000]
        for days in invalid_values:
            with pytest.raises(ValueError, match="Invalid retention_days"):
                _validate_retention_days(days)

    def test_validate_retention_days_rejects_non_integer(self):
        """Test that non-integer values are rejected."""
        invalid_values = ["30", 30.5, None]
        for days in invalid_values:
            with pytest.raises(ValueError, match="Invalid retention_days"):
                _validate_retention_days(days)

    @pytest.mark.asyncio
    async def test_get_chunks_rejects_invalid_table(self):
        """Test that get_chunks_to_drop rejects invalid table names."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with pytest.raises(ValueError, match="Invalid table name"):
            await service.get_chunks_to_drop("malicious.table", 90)

    @pytest.mark.asyncio
    async def test_drop_chunks_rejects_invalid_table(self):
        """Test that drop_old_chunks rejects invalid table names."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with pytest.raises(ValueError, match="Invalid table name"):
            await service.drop_old_chunks("malicious.table", 90)

    @pytest.mark.asyncio
    async def test_delete_records_rejects_invalid_table(self):
        """Test that delete_old_records rejects invalid table names."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with pytest.raises(ValueError, match="Invalid table name"):
            await service.delete_old_records("malicious.table", 90)

    @pytest.mark.asyncio
    async def test_delete_records_rejects_invalid_column(self):
        """Test that delete_old_records rejects invalid timestamp columns."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with pytest.raises(ValueError, match="Invalid timestamp column"):
            await service.delete_old_records(
                "observability.traces", 90, timestamp_column="malicious_column"
            )

    @pytest.mark.asyncio
    async def test_cleanup_hypertable_rejects_invalid_table(self):
        """Test that cleanup_hypertable rejects invalid table names."""
        mock_session = AsyncMock()
        service = RetentionService(mock_session)

        with pytest.raises(ValueError, match="Invalid table name"):
            await service.cleanup_hypertable(
                "malicious.table",
                "observability_retention_days",
                use_timescaledb=True,
                dry_run=True,
            )
