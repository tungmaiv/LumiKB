"""Data retention service for observability data cleanup.

Story 9-14: Data Retention and Cleanup

Provides methods for cleaning up old observability data using
TimescaleDB chunk management or standard DELETE operations.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Hypertables with their retention configuration settings
HYPERTABLES = [
    ("observability.traces", "observability_retention_days"),
    ("observability.spans", "observability_retention_days"),
    ("observability.chat_messages", "observability_retention_days"),
    ("observability.document_events", "observability_retention_days"),
    ("observability.metrics_aggregates", "observability_metrics_retention_days"),
]

# Allowed tables for retention operations (whitelist for SQL injection prevention)
ALLOWED_TABLES = frozenset(
    [table for table, _ in HYPERTABLES] + ["observability.provider_sync_status"]
)

# Allowed timestamp columns for DELETE operations
ALLOWED_TIMESTAMP_COLUMNS = frozenset(["timestamp", "created_at"])


def _validate_table_name(table_name: str) -> None:
    """Validate table name against whitelist to prevent SQL injection.

    Args:
        table_name: Fully qualified table name (schema.table)

    Raises:
        ValueError: If table name is not in the allowed list
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(
            f"Invalid table name: {table_name}. "
            f"Allowed tables: {sorted(ALLOWED_TABLES)}"
        )


def _validate_timestamp_column(column_name: str) -> None:
    """Validate timestamp column name against whitelist.

    Args:
        column_name: Column name to validate

    Raises:
        ValueError: If column name is not in the allowed list
    """
    if column_name not in ALLOWED_TIMESTAMP_COLUMNS:
        raise ValueError(
            f"Invalid timestamp column: {column_name}. "
            f"Allowed columns: {sorted(ALLOWED_TIMESTAMP_COLUMNS)}"
        )


def _validate_retention_days(retention_days: int) -> None:
    """Validate retention days is a reasonable positive integer.

    Args:
        retention_days: Number of days to retain

    Raises:
        ValueError: If retention_days is not valid
    """
    if (
        not isinstance(retention_days, int)
        or retention_days < 1
        or retention_days > 3650
    ):
        raise ValueError(
            f"Invalid retention_days: {retention_days}. Must be integer between 1 and 3650."
        )


class RetentionService:
    """Service for managing observability data retention.

    Handles cleanup of old data using TimescaleDB drop_chunks() for
    efficient hypertable management, or standard DELETE for regular tables.
    """

    def __init__(self, session: AsyncSession):
        """Initialize retention service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def check_timescaledb_available(self) -> bool:
        """Check if TimescaleDB extension is available.

        Returns:
            True if TimescaleDB is installed, False otherwise
        """
        try:
            result = await self.session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
            )
            return result.scalar() is not None
        except Exception as e:
            logger.warning(f"Error checking TimescaleDB availability: {e}")
            return False

    async def get_chunks_to_drop(
        self,
        table_name: str,
        retention_days: int,
    ) -> list[str]:
        """Get list of chunks that would be dropped (dry-run preview).

        Args:
            table_name: Fully qualified table name (schema.table)
            retention_days: Days of data to retain

        Returns:
            List of chunk names that would be dropped

        Raises:
            ValueError: If table_name is not in allowed list
        """
        # Validate inputs to prevent SQL injection
        _validate_table_name(table_name)
        _validate_retention_days(retention_days)

        try:
            result = await self.session.execute(
                text(f"""
                    SELECT chunk_name FROM show_chunks(
                        '{table_name}',
                        older_than => NOW() - INTERVAL '{retention_days} days'
                    )
                """)
            )
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Error getting chunks for {table_name}: {e}")
            return []

    async def drop_old_chunks(
        self,
        table_name: str,
        retention_days: int,
    ) -> int:
        """Drop chunks older than retention period.

        Args:
            table_name: Fully qualified table name (schema.table)
            retention_days: Days of data to retain

        Returns:
            Count of dropped chunks

        Raises:
            ValueError: If table_name is not in allowed list
        """
        # Validate inputs to prevent SQL injection
        _validate_table_name(table_name)
        _validate_retention_days(retention_days)

        try:
            result = await self.session.execute(
                text(f"""
                    SELECT drop_chunks(
                        '{table_name}',
                        older_than => NOW() - INTERVAL '{retention_days} days'
                    )
                """)
            )
            dropped = result.fetchall()
            return len(dropped)
        except Exception as e:
            logger.error(f"Error dropping chunks for {table_name}: {e}")
            raise

    async def delete_old_records(
        self,
        table_name: str,
        retention_days: int,
        timestamp_column: str = "timestamp",
        additional_filter: str | None = None,
    ) -> int:
        """Delete old records using standard DELETE (fallback or regular tables).

        Args:
            table_name: Fully qualified table name (schema.table)
            retention_days: Days of data to retain
            timestamp_column: Name of timestamp column
            additional_filter: Optional additional WHERE clause conditions
                (must be a safe, predefined filter string)

        Returns:
            Count of deleted records

        Raises:
            ValueError: If table_name or timestamp_column is not in allowed list
        """
        # Validate inputs to prevent SQL injection
        _validate_table_name(table_name)
        _validate_retention_days(retention_days)
        _validate_timestamp_column(timestamp_column)

        # Note: additional_filter is only used internally with hardcoded safe values
        # from cleanup_provider_sync_status. External callers should not provide
        # arbitrary filter strings.

        where_clause = f"{timestamp_column} < NOW() - INTERVAL '{retention_days} days'"
        if additional_filter:
            where_clause = f"{where_clause} AND {additional_filter}"

        try:
            result = await self.session.execute(
                text(f"DELETE FROM {table_name} WHERE {where_clause}")
            )
            return result.rowcount or 0
        except Exception as e:
            logger.error(f"Error deleting records from {table_name}: {e}")
            raise

    async def cleanup_provider_sync_status(
        self,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clean up old provider sync status records.

        Only deletes 'synced' and 'failed' records, preserves 'pending'.

        Args:
            dry_run: If True, only preview what would be deleted

        Returns:
            Dict with cleanup results
        """
        retention_days = settings.observability_sync_status_retention_days
        table_name = "observability.provider_sync_status"

        if dry_run:
            result = await self.session.execute(
                text(f"""
                    SELECT COUNT(*) FROM {table_name}
                    WHERE sync_status IN ('synced', 'failed')
                    AND created_at < NOW() - INTERVAL '{retention_days} days'
                """)
            )
            count = result.scalar() or 0
            return {
                "table": table_name,
                "records_to_delete": count,
                "dry_run": True,
            }

        deleted = await self.delete_old_records(
            table_name,
            retention_days,
            timestamp_column="created_at",
            additional_filter="sync_status IN ('synced', 'failed')",
        )

        logger.info(
            f"Cleaned up provider_sync_status: deleted={deleted}, "
            f"retention_days={retention_days}"
        )

        return {
            "table": table_name,
            "records_deleted": deleted,
            "dry_run": False,
        }

    async def cleanup_hypertable(
        self,
        table_name: str,
        retention_setting: str,
        use_timescaledb: bool,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clean up a hypertable using appropriate method.

        Args:
            table_name: Fully qualified table name
            retention_setting: Settings attribute name for retention days
            use_timescaledb: Whether TimescaleDB is available
            dry_run: If True, only preview what would be deleted

        Returns:
            Dict with cleanup results

        Raises:
            ValueError: If table_name is not in allowed list
        """
        # Validate table name to prevent SQL injection
        _validate_table_name(table_name)

        retention_days = getattr(settings, retention_setting)
        _validate_retention_days(retention_days)

        if dry_run:
            if use_timescaledb:
                chunks = await self.get_chunks_to_drop(table_name, retention_days)
                return {
                    "table": table_name,
                    "chunks_to_drop": len(chunks),
                    "chunk_names": chunks[:10],  # Limit preview to 10
                    "dry_run": True,
                }
            else:
                result = await self.session.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {table_name}
                        WHERE timestamp < NOW() - INTERVAL '{retention_days} days'
                    """)
                )
                count = result.scalar() or 0
                return {
                    "table": table_name,
                    "records_to_delete": count,
                    "dry_run": True,
                }

        # Actual deletion
        if use_timescaledb:
            chunks_dropped = await self.drop_old_chunks(table_name, retention_days)
            logger.info(
                f"Cleaned up {table_name}: chunks_dropped={chunks_dropped}, "
                f"retention_days={retention_days}"
            )
            return {
                "table": table_name,
                "chunks_dropped": chunks_dropped,
                "dry_run": False,
            }
        else:
            deleted = await self.delete_old_records(table_name, retention_days)
            logger.info(
                f"Cleaned up {table_name} (fallback DELETE): deleted={deleted}, "
                f"retention_days={retention_days}"
            )
            return {
                "table": table_name,
                "records_deleted": deleted,
                "dry_run": False,
            }

    async def cleanup_all(
        self,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clean up all observability data based on retention policies.

        Args:
            dry_run: If True, preview what would be deleted without actual deletion

        Returns:
            Dict with cleanup results for each table
        """
        start_time = datetime.utcnow()
        results: dict[str, Any] = {}
        errors: list[dict[str, str]] = []

        # Check TimescaleDB availability
        use_timescaledb = await self.check_timescaledb_available()

        if not use_timescaledb:
            logger.warning(
                "TimescaleDB not available, using fallback DELETE operations"
            )

        # Clean up hypertables
        for table_name, retention_setting in HYPERTABLES:
            try:
                result = await self.cleanup_hypertable(
                    table_name,
                    retention_setting,
                    use_timescaledb,
                    dry_run,
                )
                results[table_name] = result
            except Exception as e:
                logger.error(f"Error cleaning up {table_name}: {e}")
                errors.append({"table": table_name, "error": str(e)})
                results[table_name] = {"error": str(e)}

        # Clean up provider_sync_status (not a hypertable)
        try:
            sync_result = await self.cleanup_provider_sync_status(dry_run)
            results["observability.provider_sync_status"] = sync_result
        except Exception as e:
            logger.error(f"Error cleaning up provider_sync_status: {e}")
            errors.append(
                {"table": "observability.provider_sync_status", "error": str(e)}
            )
            results["observability.provider_sync_status"] = {"error": str(e)}

        # Commit if not dry run
        if not dry_run:
            await self.session.commit()

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "results": results,
            "errors": errors,
            "dry_run": dry_run,
            "timescaledb_used": use_timescaledb,
            "duration_ms": duration_ms,
        }
