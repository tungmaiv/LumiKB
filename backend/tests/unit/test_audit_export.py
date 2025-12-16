"""Unit tests for audit export functionality (Story 5.3)."""

import csv
import io
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.audit import AuditEvent
from app.services.audit_service import AuditService


@pytest.fixture
def mock_audit_service():
    """Mock AuditService for unit tests."""
    service = Mock(spec=AuditService)
    service.redact_pii = Mock(side_effect=lambda event: event)
    return service


@pytest.fixture
def sample_audit_events():
    """Sample audit events for testing."""
    user_id = uuid4()
    return [
        AuditEvent(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            user_id=user_id,
            action="search",
            resource_type="search",
            resource_id=None,
            ip_address="192.168.1.1",
            details={"query": "test query", "result_count": 5},
        ),
        AuditEvent(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            user_id=user_id,
            action="generation.request",
            resource_type="draft",
            resource_id=uuid4(),
            ip_address="192.168.1.2",
            details={
                "document_type": "report",
                "kb_id": str(uuid4()),
                "request_id": "req-123",
            },
        ),
    ]


class TestExportCSVStream:
    """Tests for CSV export streaming."""

    @pytest.mark.asyncio
    async def test_csv_header_and_rows(self, mock_audit_service, sample_audit_events):
        """Test CSV export yields correct header and data rows."""
        from app.api.v1.admin import export_csv_stream

        # Mock get_events_stream to yield sample events
        async def mock_stream(*args, **kwargs):
            yield sample_audit_events

        mock_audit_service.get_events_stream = mock_stream

        # Mock database session
        db = AsyncMock()
        db.execute = AsyncMock(return_value=Mock(all=Mock(return_value=[])))

        # Collect CSV output
        csv_output = []
        async for chunk in export_csv_stream(
            mock_audit_service, db, {}, include_pii=False
        ):
            csv_output.append(chunk)

        csv_content = "".join(csv_output)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Verify header exists
        assert reader.fieldnames == [
            "id",
            "timestamp",
            "user_id",
            "user_email",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "details",
        ]

        # Verify row count matches
        assert len(rows) == len(sample_audit_events)

        # Verify first row content
        assert rows[0]["action"] == "search"
        assert rows[0]["resource_type"] == "search"

    @pytest.mark.asyncio
    async def test_csv_escaping_commas_quotes_newlines(self, mock_audit_service):
        """Test CSV export handles edge cases (commas, quotes, newlines in JSON)."""
        from app.api.v1.admin import export_csv_stream

        # Create event with special characters in details
        event_with_special_chars = AuditEvent(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            user_id=uuid4(),
            action="test.action",
            resource_type="test",
            resource_id=None,
            ip_address="192.168.1.1",
            details={
                "text_with_comma": "Hello, World",
                "text_with_quote": 'She said "hello"',
                "text_with_newline": "Line 1\nLine 2",
            },
        )

        async def mock_stream(*args, **kwargs):
            yield [event_with_special_chars]

        mock_audit_service.get_events_stream = mock_stream

        # Mock database session
        db = AsyncMock()
        db.execute = AsyncMock(return_value=Mock(all=Mock(return_value=[])))

        # Collect CSV output
        csv_output = []
        async for chunk in export_csv_stream(
            mock_audit_service, db, {}, include_pii=False
        ):
            csv_output.append(chunk)

        csv_content = "".join(csv_output)

        # Parse CSV with csv.DictReader (should handle escaping correctly)
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 1

        # Verify details JSON contains special characters
        details = json.loads(rows[0]["details"])
        assert details["text_with_comma"] == "Hello, World"
        assert details["text_with_quote"] == 'She said "hello"'
        assert details["text_with_newline"] == "Line 1\nLine 2"

    @pytest.mark.asyncio
    async def test_pii_redaction_in_export(self, sample_audit_events):
        """Test PII redaction is applied when include_pii=False."""
        from app.api.v1.admin import export_csv_stream

        # Create real AuditService instance (not mock)
        audit_service = AuditService()

        async def mock_stream(*args, **kwargs):
            yield sample_audit_events

        audit_service.get_events_stream = mock_stream

        # Mock database session
        db = AsyncMock()
        db.execute = AsyncMock(return_value=Mock(all=Mock(return_value=[])))

        # Collect CSV output with PII redaction
        csv_output = []
        async for chunk in export_csv_stream(audit_service, db, {}, include_pii=False):
            csv_output.append(chunk)

        csv_content = "".join(csv_output)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Verify IP addresses are redacted
        assert rows[0]["ip_address"] == "XXX.XXX.XXX.XXX"
        assert rows[1]["ip_address"] == "XXX.XXX.XXX.XXX"


class TestExportJSONStream:
    """Tests for JSON export streaming."""

    @pytest.mark.asyncio
    async def test_json_stream_valid_array(
        self, mock_audit_service, sample_audit_events
    ):
        """Test JSON export yields valid JSON array structure with commas."""
        from app.api.v1.admin import export_json_stream

        async def mock_stream(*args, **kwargs):
            yield sample_audit_events

        mock_audit_service.get_events_stream = mock_stream

        # Mock database session
        db = AsyncMock()
        db.execute = AsyncMock(return_value=Mock(all=Mock(return_value=[])))

        # Collect JSON output
        json_output = []
        async for chunk in export_json_stream(
            mock_audit_service, db, {}, include_pii=False
        ):
            json_output.append(chunk)

        json_content = "".join(json_output)

        # Verify valid JSON
        data = json.loads(json_content)
        assert isinstance(data, list)
        assert len(data) == len(sample_audit_events)

        # Verify first object
        assert data[0]["action"] == "search"
        assert data[0]["resource_type"] == "search"

    @pytest.mark.asyncio
    async def test_json_stream_multiple_batches(self, mock_audit_service):
        """Test JSON export handles multiple batches with correct comma placement."""
        from app.api.v1.admin import export_json_stream

        # Create multiple batches
        batch1 = [
            AuditEvent(
                id=uuid4(),
                timestamp=datetime.now(UTC),
                user_id=uuid4(),
                action="action1",
                resource_type="type1",
                resource_id=None,
                ip_address="192.168.1.1",
                details={},
            )
        ]
        batch2 = [
            AuditEvent(
                id=uuid4(),
                timestamp=datetime.now(UTC),
                user_id=uuid4(),
                action="action2",
                resource_type="type2",
                resource_id=None,
                ip_address="192.168.1.2",
                details={},
            )
        ]

        async def mock_stream(*args, **kwargs):
            yield batch1
            yield batch2

        mock_audit_service.get_events_stream = mock_stream

        # Mock database session
        db = AsyncMock()
        db.execute = AsyncMock(return_value=Mock(all=Mock(return_value=[])))

        # Collect JSON output
        json_output = []
        async for chunk in export_json_stream(
            mock_audit_service, db, {}, include_pii=False
        ):
            json_output.append(chunk)

        json_content = "".join(json_output)

        # Verify valid JSON (comma placement matters)
        data = json.loads(json_content)
        assert len(data) == 2
        assert data[0]["action"] == "action1"
        assert data[1]["action"] == "action2"


class TestCountEvents:
    """Tests for count_events method."""

    @pytest.mark.asyncio
    async def test_count_events_matches_query(self):
        """Test count_events returns same count as filtered query."""
        # This test requires database interaction - will be tested in integration tests
        # Unit test verifies the method signature and basic logic
        audit_service = AuditService()
        db = AsyncMock()

        # Mock query execution
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=42)
        db.execute = AsyncMock(return_value=mock_result)

        count = await audit_service.count_events(
            db=db,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            event_type="search",
        )

        assert count == 42
        assert db.execute.called
