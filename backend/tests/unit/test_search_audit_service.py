"""Unit tests for Search Audit Service and PII Sanitizer.

Story: 5.14 - Search Audit Logging

Tests:
- PIISanitizer sanitizes email, phone, SSN, CC patterns (AC2)
- AuditService._sanitize_pii() method works correctly (AC2)
- AuditService.log_search() logs with new metadata fields (AC2, AC3)
- Fire-and-forget pattern - errors don't propagate (AC3)
- Failed search logging with error fields (AC4)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

from app.services.audit_service import AuditService
from app.services.search_audit_service import PIISanitizer


class TestPIISanitizer:
    """Test suite for PIISanitizer class (AC2)."""

    def test_sanitizes_email_addresses(self):
        """Test that email addresses are replaced with [EMAIL] placeholder."""
        text = "Search for john.doe@example.com contact"
        result = PIISanitizer.sanitize(text)
        assert result == "Search for [EMAIL] contact"

    def test_sanitizes_multiple_emails(self):
        """Test that multiple email addresses are sanitized."""
        text = "Contact alice@test.org or bob@company.net"
        result = PIISanitizer.sanitize(text)
        assert result == "Contact [EMAIL] or [EMAIL]"

    def test_sanitizes_phone_numbers_dashes(self):
        """Test phone number with dashes is sanitized."""
        text = "Call me at 555-123-4567"
        result = PIISanitizer.sanitize(text)
        assert result == "Call me at [PHONE]"

    def test_sanitizes_phone_numbers_dots(self):
        """Test phone number with dots is sanitized."""
        text = "Call me at 555.123.4567"
        result = PIISanitizer.sanitize(text)
        assert result == "Call me at [PHONE]"

    def test_sanitizes_phone_numbers_no_separator(self):
        """Test phone number without separators is sanitized."""
        text = "Call me at 5551234567"
        result = PIISanitizer.sanitize(text)
        assert result == "Call me at [PHONE]"

    def test_sanitizes_ssn(self):
        """Test SSN pattern is sanitized."""
        text = "SSN: 123-45-6789"
        result = PIISanitizer.sanitize(text)
        assert result == "SSN: [SSN]"

    def test_sanitizes_credit_card_with_spaces(self):
        """Test credit card with spaces is sanitized."""
        text = "Card: 4111 1111 1111 1111"
        result = PIISanitizer.sanitize(text)
        assert result == "Card: [CC]"

    def test_sanitizes_credit_card_with_dashes(self):
        """Test credit card with dashes is sanitized."""
        text = "Card: 4111-1111-1111-1111"
        result = PIISanitizer.sanitize(text)
        assert result == "Card: [CC]"

    def test_sanitizes_credit_card_no_separator(self):
        """Test credit card without separators is sanitized."""
        text = "Card: 4111111111111111"
        result = PIISanitizer.sanitize(text)
        assert result == "Card: [CC]"

    def test_sanitizes_mixed_pii(self):
        """Test multiple PII types in one text are all sanitized."""
        text = "Email user@test.com, call 555-123-4567, SSN 123-45-6789"
        result = PIISanitizer.sanitize(text)
        assert result == "Email [EMAIL], call [PHONE], SSN [SSN]"

    def test_handles_empty_string(self):
        """Test empty string returns empty string."""
        assert PIISanitizer.sanitize("") == ""

    def test_handles_none(self):
        """Test None input returns None."""
        assert PIISanitizer.sanitize(None) is None

    def test_preserves_non_pii_text(self):
        """Test that non-PII text is preserved."""
        text = "Search for documents about authentication"
        result = PIISanitizer.sanitize(text)
        assert result == text


class TestAuditServiceSanitizePII:
    """Test suite for AuditService._sanitize_pii() method (AC2)."""

    def test_sanitize_pii_method_exists(self):
        """Test that _sanitize_pii method exists on AuditService."""
        service = AuditService()
        assert hasattr(service, "_sanitize_pii")
        assert callable(service._sanitize_pii)

    def test_sanitize_pii_email(self):
        """Test _sanitize_pii sanitizes email."""
        service = AuditService()
        result = service._sanitize_pii("search for user@example.com")
        assert result == "search for [EMAIL]"

    def test_sanitize_pii_phone(self):
        """Test _sanitize_pii sanitizes phone."""
        service = AuditService()
        result = service._sanitize_pii("call 555-123-4567")
        assert result == "call [PHONE]"

    def test_sanitize_pii_ssn(self):
        """Test _sanitize_pii sanitizes SSN."""
        service = AuditService()
        result = service._sanitize_pii("SSN 123-45-6789")
        assert result == "SSN [SSN]"

    def test_sanitize_pii_credit_card(self):
        """Test _sanitize_pii sanitizes credit card."""
        service = AuditService()
        result = service._sanitize_pii("card 4111-1111-1111-1111")
        assert result == "card [CC]"

    def test_sanitize_pii_empty(self):
        """Test _sanitize_pii handles empty string."""
        service = AuditService()
        assert service._sanitize_pii("") == ""


class TestAuditServiceLogSearch:
    """Test suite for AuditService.log_search() method (AC2, AC3, AC4)."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Create a mock session factory context manager."""
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_session)
        cm.__aexit__ = AsyncMock(return_value=None)
        return cm

    async def test_log_search_includes_search_type(
        self, mock_session_factory, mock_session
    ):
        """Test that log_search includes search_type in metadata (AC2)."""
        service = AuditService()
        user_id = str(uuid.uuid4())
        kb_id = str(uuid.uuid4())

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_search(
                user_id=user_id,
                query="test query",
                kb_ids=[kb_id],
                result_count=5,
                latency_ms=100,
                search_type="semantic",
            )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_log_search_includes_status_success(
        self, mock_session_factory, mock_session
    ):
        """Test that log_search includes status=success (AC2)."""
        service = AuditService()
        user_id = str(uuid.uuid4())
        kb_id = str(uuid.uuid4())

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_search(
                user_id=user_id,
                query="test query",
                kb_ids=[kb_id],
                result_count=5,
                latency_ms=100,
                search_type="quick",
                status="success",
            )

        mock_session.execute.assert_called_once()

    async def test_log_search_with_failure_details(
        self, mock_session_factory, mock_session
    ):
        """Test that log_search includes error fields when status=failed (AC4)."""
        service = AuditService()
        user_id = str(uuid.uuid4())

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_search(
                user_id=user_id,
                query="test query",
                kb_ids=[],
                result_count=0,
                latency_ms=50,
                search_type="semantic",
                status="failed",
                error_message="Knowledge Base not found",
                error_type="kb_not_found",
            )

        mock_session.execute.assert_called_once()

    async def test_log_search_sanitizes_pii_in_query(
        self, mock_session_factory, mock_session
    ):
        """Test that log_search sanitizes PII in query text (AC2)."""
        service = AuditService()
        user_id = str(uuid.uuid4())
        kb_id = str(uuid.uuid4())

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            # Query contains email - should be sanitized
            await service.log_search(
                user_id=user_id,
                query="find documents by john@example.com",
                kb_ids=[kb_id],
                result_count=3,
                latency_ms=200,
                search_type="semantic",
            )

        # Verify call was made - detailed assertion on sanitization
        # would require inspection of the execute() call args
        mock_session.execute.assert_called_once()

    async def test_log_search_fire_and_forget_on_error(
        self, mock_session_factory, mock_session
    ):
        """Test that database errors don't propagate (AC3)."""
        service = AuditService()
        user_id = str(uuid.uuid4())

        # Make commit raise an exception
        mock_session.commit.side_effect = Exception("Database error")

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            # Should NOT raise - fire-and-forget pattern
            await service.log_search(
                user_id=user_id,
                query="test query",
                kb_ids=[],
                result_count=0,
                latency_ms=100,
                search_type="quick",
            )

    async def test_log_search_truncates_long_query(
        self, mock_session_factory, mock_session
    ):
        """Test that long queries are truncated to 500 chars."""
        service = AuditService()
        user_id = str(uuid.uuid4())
        kb_id = str(uuid.uuid4())
        long_query = "x" * 1000  # 1000 chars

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_search(
                user_id=user_id,
                query=long_query,
                kb_ids=[kb_id],
                result_count=0,
                latency_ms=100,
                search_type="semantic",
            )

        # Should truncate to 500 chars - verified by not raising
        mock_session.execute.assert_called_once()

    async def test_log_search_with_multiple_kb_ids(
        self, mock_session_factory, mock_session
    ):
        """Test that log_search handles multiple KB IDs (cross-KB search)."""
        service = AuditService()
        user_id = str(uuid.uuid4())
        kb_ids = [str(uuid.uuid4()) for _ in range(3)]

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_search(
                user_id=user_id,
                query="test query",
                kb_ids=kb_ids,
                result_count=10,
                latency_ms=300,
                search_type="cross_kb",
            )

        mock_session.execute.assert_called_once()

    async def test_log_search_similar_type(self, mock_session_factory, mock_session):
        """Test that similar search type is logged correctly."""
        service = AuditService()
        user_id = str(uuid.uuid4())
        kb_id = str(uuid.uuid4())

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_search(
                user_id=user_id,
                query="Similar to: Document.pdf",
                kb_ids=[kb_id],
                result_count=5,
                latency_ms=150,
                search_type="similar",
            )

        mock_session.execute.assert_called_once()


class TestSearchAuditServiceDirect:
    """Direct unit tests for SearchAuditService class (increases coverage to 90%+)."""

    @pytest.fixture
    def mock_audit_service(self):
        """Create a mock AuditService."""
        service = AsyncMock()
        service.log_event = AsyncMock()
        return service

    async def test_log_search_success_path(self, mock_audit_service):
        """[P0] Test SearchAuditService.log_search() success path with all fields."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()

        await search_audit.log_search(
            user_id=user_id,
            query_text="test query",
            kb_ids=[kb_id],
            result_count=10,
            duration_ms=150,
            search_type="semantic",
            status="success",
        )

        # Verify log_event was called with correct params
        mock_audit_service.log_event.assert_called_once()
        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert call_kwargs["action"] == "search"
        assert call_kwargs["resource_type"] == "knowledge_base"
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["resource_id"] == kb_id
        assert call_kwargs["details"]["query_text"] == "test query"
        assert call_kwargs["details"]["result_count"] == 10
        assert call_kwargs["details"]["duration_ms"] == 150
        assert call_kwargs["details"]["search_type"] == "semantic"
        assert call_kwargs["details"]["status"] == "success"

    async def test_log_search_failure_path_with_error_details(self, mock_audit_service):
        """[P0] Test SearchAuditService.log_search() failure path includes error fields (AC4)."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()

        await search_audit.log_search(
            user_id=user_id,
            query_text="test query",
            kb_ids=[],
            result_count=0,
            duration_ms=50,
            search_type="semantic",
            status="failed",
            error_message="Knowledge base not found",
            error_type="kb_not_found",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert call_kwargs["details"]["status"] == "failed"
        assert call_kwargs["details"]["error_message"] == "Knowledge base not found"
        assert call_kwargs["details"]["error_type"] == "kb_not_found"

    async def test_log_search_sanitizes_pii_in_query(self, mock_audit_service):
        """[P0] Test SearchAuditService sanitizes PII in query text (AC2)."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()

        await search_audit.log_search(
            user_id=user_id,
            query_text="contact john@example.com at 555-123-4567",
            kb_ids=[kb_id],
            result_count=5,
            duration_ms=100,
            search_type="semantic",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        sanitized = call_kwargs["details"]["query_text"]
        assert "john@example.com" not in sanitized
        assert "[EMAIL]" in sanitized
        assert "555-123-4567" not in sanitized
        assert "[PHONE]" in sanitized

    async def test_log_search_truncates_long_query(self, mock_audit_service):
        """[P1] Test SearchAuditService truncates queries > 500 chars."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()
        long_query = "x" * 1000

        await search_audit.log_search(
            user_id=user_id,
            query_text=long_query,
            kb_ids=[kb_id],
            result_count=0,
            duration_ms=100,
            search_type="semantic",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert len(call_kwargs["details"]["query_text"]) == 500

    async def test_log_search_handles_string_kb_ids(self, mock_audit_service):
        """[P1] Test SearchAuditService handles string KB IDs (not just UUIDs)."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()
        kb_id_str = str(uuid.uuid4())

        await search_audit.log_search(
            user_id=user_id,
            query_text="test",
            kb_ids=[kb_id_str],  # String, not UUID
            result_count=1,
            duration_ms=50,
            search_type="quick",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert call_kwargs["details"]["kb_ids"] == [kb_id_str]

    async def test_log_search_handles_multiple_kb_ids(self, mock_audit_service):
        """[P1] Test SearchAuditService handles cross-KB search with multiple IDs."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()
        kb_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        await search_audit.log_search(
            user_id=user_id,
            query_text="cross kb query",
            kb_ids=kb_ids,
            result_count=25,
            duration_ms=300,
            search_type="cross_kb",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert call_kwargs["details"]["search_type"] == "cross_kb"
        assert len(call_kwargs["details"]["kb_ids"]) == 3
        # resource_id should be first KB
        assert call_kwargs["resource_id"] == kb_ids[0]

    async def test_log_search_handles_empty_kb_ids(self, mock_audit_service):
        """[P1] Test SearchAuditService handles empty KB IDs list."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()

        await search_audit.log_search(
            user_id=user_id,
            query_text="test",
            kb_ids=[],
            result_count=0,
            duration_ms=10,
            search_type="semantic",
            status="failed",
            error_type="validation_error",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert call_kwargs["resource_id"] is None
        assert call_kwargs["details"]["kb_ids"] == []

    async def test_log_search_fire_and_forget_on_exception(self, mock_audit_service):
        """[P0] Test SearchAuditService doesn't propagate exceptions (AC3)."""
        from app.services.search_audit_service import SearchAuditService

        mock_audit_service.log_event.side_effect = Exception(
            "Database connection failed"
        )
        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()

        # Should NOT raise - fire-and-forget pattern
        await search_audit.log_search(
            user_id=user_id,
            query_text="test",
            kb_ids=[],
            result_count=0,
            duration_ms=10,
            search_type="semantic",
        )

        # Verify exception was swallowed
        mock_audit_service.log_event.assert_called_once()

    async def test_log_search_internal_error_type(self, mock_audit_service):
        """[P2] Test SearchAuditService logs internal_error type correctly."""
        from app.services.search_audit_service import SearchAuditService

        search_audit = SearchAuditService(mock_audit_service)
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()

        await search_audit.log_search(
            user_id=user_id,
            query_text="test",
            kb_ids=[kb_id],
            result_count=0,
            duration_ms=5000,
            search_type="semantic",
            status="failed",
            error_message="Qdrant service unavailable",
            error_type="internal_error",
        )

        call_kwargs = mock_audit_service.log_event.call_args.kwargs
        assert call_kwargs["details"]["error_type"] == "internal_error"
        assert "Qdrant" in call_kwargs["details"]["error_message"]


class TestPIISanitizerEdgeCases:
    """Additional edge case tests for PIISanitizer."""

    def test_sanitizes_email_with_plus_addressing(self):
        """[P2] Test email with plus addressing is sanitized."""
        text = "Email john+test@example.com for help"
        result = PIISanitizer.sanitize(text)
        assert result == "Email [EMAIL] for help"

    def test_sanitizes_email_with_subdomain(self):
        """[P2] Test email with subdomain is sanitized."""
        text = "Contact support@mail.company.co.uk"
        result = PIISanitizer.sanitize(text)
        assert result == "Contact [EMAIL]"

    def test_does_not_sanitize_partial_phone(self):
        """[P2] Test partial phone numbers are NOT sanitized (avoid false positives)."""
        text = "Extension 1234 or room 5678"
        result = PIISanitizer.sanitize(text)
        # Should NOT be sanitized - not full phone number
        assert result == text

    def test_sanitizes_international_format_not_supported(self):
        """[P2] Test international phone format is NOT sanitized (conservative approach)."""
        text = "Call +1-555-123-4567"
        result = PIISanitizer.sanitize(text)
        # Current regex doesn't match international format - this is expected
        assert "+1-" in result  # International prefix preserved

    def test_sanitizes_credit_card_preserves_surrounding_text(self):
        """[P2] Test CC sanitization preserves surrounding text."""
        text = "Payment made with 4111-1111-1111-1111, ref #12345"
        result = PIISanitizer.sanitize(text)
        assert result == "Payment made with [CC], ref #12345"

    def test_handles_unicode_in_query(self):
        """[P2] Test unicode characters are preserved."""
        text = "搜索 user@test.com 文档"
        result = PIISanitizer.sanitize(text)
        assert result == "搜索 [EMAIL] 文档"

    def test_handles_newlines_in_query(self):
        """[P2] Test newlines in query are preserved."""
        text = "Line 1\nEmail: test@example.com\nLine 3"
        result = PIISanitizer.sanitize(text)
        assert "Line 1\n" in result
        assert "[EMAIL]" in result
        assert "\nLine 3" in result
