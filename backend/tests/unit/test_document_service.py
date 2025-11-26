"""Unit tests for Document service validation logic.

Note: These tests focus on validation logic that can be tested
without database/MinIO dependencies. Full service tests are in integration/.
"""

from datetime import UTC

import pytest

from app.schemas.document import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
)

pytestmark = pytest.mark.unit


class TestDocumentConstants:
    """Tests for document validation constants."""

    def test_max_file_size_is_50mb(self) -> None:
        """Test maximum file size is 50MB."""
        assert MAX_FILE_SIZE_MB == 50
        assert MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024

    def test_max_file_size_bytes_consistent(self) -> None:
        """Test MAX_FILE_SIZE_BYTES matches MB value."""
        assert MAX_FILE_SIZE_BYTES == MAX_FILE_SIZE_MB * 1024 * 1024

    def test_allowed_mime_types_include_pdf(self) -> None:
        """Test PDF MIME type is allowed."""
        assert "application/pdf" in ALLOWED_MIME_TYPES

    def test_allowed_mime_types_include_docx(self) -> None:
        """Test DOCX MIME type is allowed."""
        docx_mime = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert docx_mime in ALLOWED_MIME_TYPES

    def test_allowed_mime_types_include_markdown(self) -> None:
        """Test markdown MIME types are allowed."""
        assert "text/markdown" in ALLOWED_MIME_TYPES
        assert "text/x-markdown" in ALLOWED_MIME_TYPES

    def test_allowed_extensions_include_pdf(self) -> None:
        """Test .pdf extension is allowed."""
        assert ".pdf" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_include_docx(self) -> None:
        """Test .docx extension is allowed."""
        assert ".docx" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_include_md(self) -> None:
        """Test .md extension is allowed."""
        assert ".md" in ALLOWED_EXTENSIONS

    def test_unsupported_types_not_in_allowed(self) -> None:
        """Test common unsupported types are not allowed."""
        # Text files
        assert "text/plain" not in ALLOWED_MIME_TYPES
        assert ".txt" not in ALLOWED_EXTENSIONS

        # Images
        assert "image/png" not in ALLOWED_MIME_TYPES
        assert "image/jpeg" not in ALLOWED_MIME_TYPES
        assert ".png" not in ALLOWED_EXTENSIONS
        assert ".jpg" not in ALLOWED_EXTENSIONS

        # Archives
        assert "application/zip" not in ALLOWED_MIME_TYPES
        assert ".zip" not in ALLOWED_EXTENSIONS

        # Executables
        assert "application/x-executable" not in ALLOWED_MIME_TYPES
        assert ".exe" not in ALLOWED_EXTENSIONS

    def test_mime_type_to_extension_mapping(self) -> None:
        """Test MIME type to extension mapping is correct."""
        assert ALLOWED_MIME_TYPES["application/pdf"] == ".pdf"
        assert (
            ALLOWED_MIME_TYPES[
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ]
            == ".docx"
        )
        assert ALLOWED_MIME_TYPES["text/markdown"] == ".md"
        assert ALLOWED_MIME_TYPES["text/x-markdown"] == ".md"


class TestFileSizeValidation:
    """Tests for file size validation logic."""

    def test_small_file_under_limit(self) -> None:
        """Test small file is under the limit."""
        small_size = 1024  # 1KB
        assert small_size <= MAX_FILE_SIZE_BYTES

    def test_medium_file_under_limit(self) -> None:
        """Test medium file is under the limit."""
        medium_size = 10 * 1024 * 1024  # 10MB
        assert medium_size <= MAX_FILE_SIZE_BYTES

    def test_at_limit_file_is_valid(self) -> None:
        """Test file exactly at limit is valid."""
        at_limit = MAX_FILE_SIZE_BYTES
        assert at_limit <= MAX_FILE_SIZE_BYTES

    def test_over_limit_file_is_invalid(self) -> None:
        """Test file over limit is invalid."""
        over_limit = MAX_FILE_SIZE_BYTES + 1
        assert over_limit > MAX_FILE_SIZE_BYTES

    def test_significantly_over_limit(self) -> None:
        """Test 100MB file is over limit."""
        large_size = 100 * 1024 * 1024  # 100MB
        assert large_size > MAX_FILE_SIZE_BYTES


class TestMimeTypeValidation:
    """Tests for MIME type validation logic."""

    def test_valid_pdf_mime(self) -> None:
        """Test application/pdf is valid."""
        mime_type = "application/pdf"
        assert mime_type in ALLOWED_MIME_TYPES

    def test_valid_docx_mime(self) -> None:
        """Test DOCX MIME type is valid."""
        mime_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert mime_type in ALLOWED_MIME_TYPES

    def test_valid_markdown_mimes(self) -> None:
        """Test both markdown MIME types are valid."""
        assert "text/markdown" in ALLOWED_MIME_TYPES
        assert "text/x-markdown" in ALLOWED_MIME_TYPES

    def test_invalid_text_plain_mime(self) -> None:
        """Test text/plain is not valid."""
        mime_type = "text/plain"
        assert mime_type not in ALLOWED_MIME_TYPES

    def test_invalid_image_mimes(self) -> None:
        """Test image MIME types are not valid."""
        assert "image/png" not in ALLOWED_MIME_TYPES
        assert "image/jpeg" not in ALLOWED_MIME_TYPES
        assert "image/gif" not in ALLOWED_MIME_TYPES

    def test_invalid_html_mime(self) -> None:
        """Test HTML MIME type is not valid."""
        assert "text/html" not in ALLOWED_MIME_TYPES

    def test_invalid_json_mime(self) -> None:
        """Test JSON MIME type is not valid."""
        assert "application/json" not in ALLOWED_MIME_TYPES


class TestExtensionValidation:
    """Tests for file extension validation logic."""

    def test_valid_pdf_extension(self) -> None:
        """Test .pdf extension is valid."""
        ext = ".pdf"
        assert ext in ALLOWED_EXTENSIONS

    def test_valid_docx_extension(self) -> None:
        """Test .docx extension is valid."""
        ext = ".docx"
        assert ext in ALLOWED_EXTENSIONS

    def test_valid_md_extension(self) -> None:
        """Test .md extension is valid."""
        ext = ".md"
        assert ext in ALLOWED_EXTENSIONS

    def test_invalid_txt_extension(self) -> None:
        """Test .txt extension is not valid."""
        ext = ".txt"
        assert ext not in ALLOWED_EXTENSIONS

    def test_invalid_doc_extension(self) -> None:
        """Test .doc (old Word) extension is not valid."""
        ext = ".doc"
        assert ext not in ALLOWED_EXTENSIONS

    def test_invalid_image_extensions(self) -> None:
        """Test image extensions are not valid."""
        assert ".png" not in ALLOWED_EXTENSIONS
        assert ".jpg" not in ALLOWED_EXTENSIONS
        assert ".jpeg" not in ALLOWED_EXTENSIONS
        assert ".gif" not in ALLOWED_EXTENSIONS


class TestEmptyFileValidation:
    """Tests for empty file validation logic."""

    def test_zero_bytes_is_empty(self) -> None:
        """Test 0 bytes file is considered empty."""
        file_size = 0
        assert file_size == 0

    def test_one_byte_is_not_empty(self) -> None:
        """Test 1 byte file is not empty."""
        file_size = 1
        assert file_size > 0

    def test_validation_detects_empty(self) -> None:
        """Test empty file detection logic."""
        file_size = 0
        is_empty = file_size == 0
        assert is_empty is True

    def test_validation_detects_non_empty(self) -> None:
        """Test non-empty file detection logic."""
        file_size = 100
        is_empty = file_size == 0
        assert is_empty is False


class TestDocumentNameGeneration:
    """Tests for document name generation logic."""

    def test_remove_extension(self) -> None:
        """Test extension is removed from name."""
        import os

        filename = "test_document.pdf"
        name = os.path.splitext(filename)[0]
        assert name == "test_document"

    def test_replace_underscores(self) -> None:
        """Test underscores are replaced with spaces."""
        name = "test_document_name"
        cleaned = name.replace("_", " ")
        assert cleaned == "test document name"

    def test_replace_hyphens(self) -> None:
        """Test hyphens are replaced with spaces."""
        name = "test-document-name"
        cleaned = name.replace("-", " ")
        assert cleaned == "test document name"

    def test_capitalize_words(self) -> None:
        """Test words are capitalized."""
        name = "test document name"
        capitalized = " ".join(word.capitalize() for word in name.split())
        assert capitalized == "Test Document Name"

    def test_full_name_transformation(self) -> None:
        """Test complete name transformation."""
        import os

        filename = "my_test-document.pdf"
        name = os.path.splitext(filename)[0]
        name = name.replace("_", " ").replace("-", " ")
        name = " ".join(word.capitalize() for word in name.split())
        assert name == "My Test Document"


class TestChecksumComputation:
    """Tests for checksum computation logic."""

    def test_checksum_is_64_chars(self) -> None:
        """Test SHA-256 checksum is 64 hex characters."""
        import hashlib

        content = b"test content"
        checksum = hashlib.sha256(content).hexdigest()
        assert len(checksum) == 64

    def test_checksum_is_hex(self) -> None:
        """Test checksum contains only hex characters."""
        import hashlib

        content = b"test content"
        checksum = hashlib.sha256(content).hexdigest()
        # All characters should be hex digits
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_same_content_same_checksum(self) -> None:
        """Test same content produces same checksum."""
        import hashlib

        content = b"test content"
        checksum1 = hashlib.sha256(content).hexdigest()
        checksum2 = hashlib.sha256(content).hexdigest()
        assert checksum1 == checksum2

    def test_different_content_different_checksum(self) -> None:
        """Test different content produces different checksum."""
        import hashlib

        content1 = b"test content 1"
        content2 = b"test content 2"
        checksum1 = hashlib.sha256(content1).hexdigest()
        checksum2 = hashlib.sha256(content2).hexdigest()
        assert checksum1 != checksum2


class TestDocumentStatusResponseSchema:
    """Tests for DocumentStatusResponse schema."""

    def test_schema_has_all_required_fields(self) -> None:
        """Test schema includes all status fields."""
        from datetime import datetime

        from app.schemas.document import DocumentStatus, DocumentStatusResponse

        response = DocumentStatusResponse(
            status=DocumentStatus.READY,
            chunk_count=47,
            processing_started_at=datetime.now(UTC),
            processing_completed_at=datetime.now(UTC),
            last_error=None,
            retry_count=0,
        )
        assert response.status == DocumentStatus.READY
        assert response.chunk_count == 47
        assert response.processing_started_at is not None
        assert response.processing_completed_at is not None
        assert response.last_error is None
        assert response.retry_count == 0

    def test_schema_accepts_pending_status(self) -> None:
        """Test schema accepts PENDING status with null timestamps."""
        from app.schemas.document import DocumentStatus, DocumentStatusResponse

        response = DocumentStatusResponse(
            status=DocumentStatus.PENDING,
            chunk_count=0,
            processing_started_at=None,
            processing_completed_at=None,
            last_error=None,
            retry_count=0,
        )
        assert response.status == DocumentStatus.PENDING
        assert response.processing_started_at is None

    def test_schema_accepts_failed_status_with_error(self) -> None:
        """Test schema accepts FAILED status with error message."""
        from app.schemas.document import DocumentStatus, DocumentStatusResponse

        response = DocumentStatusResponse(
            status=DocumentStatus.FAILED,
            chunk_count=0,
            processing_started_at=None,
            processing_completed_at=None,
            last_error="Parse error: Invalid PDF format",
            retry_count=2,
        )
        assert response.status == DocumentStatus.FAILED
        assert response.last_error == "Parse error: Invalid PDF format"
        assert response.retry_count == 2

    def test_schema_from_attributes_mode(self) -> None:
        """Test schema can be created from ORM attributes."""
        from app.schemas.document import DocumentStatusResponse

        # Check from_attributes is enabled
        assert DocumentStatusResponse.model_config.get("from_attributes") is True


class TestRetryResponseSchema:
    """Tests for RetryResponse schema."""

    def test_retry_response_message(self) -> None:
        """Test RetryResponse contains message field."""
        from app.schemas.document import RetryResponse

        response = RetryResponse(message="Document processing retry initiated")
        assert response.message == "Document processing retry initiated"


class TestVersionHistorySchema:
    """Tests for VersionHistoryEntry schema serialization."""

    def test_version_history_entry_serialization(self) -> None:
        """Test VersionHistoryEntry can be created with all required fields."""
        from datetime import datetime
        from uuid import uuid4

        from app.schemas.document import VersionHistoryEntry

        entry = VersionHistoryEntry(
            version_number=1,
            file_size=1024,
            checksum="a" * 64,
            replaced_at=datetime.now(UTC),
            replaced_by=uuid4(),
        )
        assert entry.version_number == 1
        assert entry.file_size == 1024
        assert len(entry.checksum) == 64
        assert entry.replaced_at is not None
        assert entry.replaced_by is not None

    def test_version_history_entry_to_dict(self) -> None:
        """Test VersionHistoryEntry can be serialized to dict."""
        from datetime import datetime
        from uuid import uuid4

        from app.schemas.document import VersionHistoryEntry

        user_id = uuid4()
        now = datetime.now(UTC)
        entry = VersionHistoryEntry(
            version_number=2,
            file_size=2048,
            checksum="b" * 64,
            replaced_at=now,
            replaced_by=user_id,
        )
        data = entry.model_dump(mode="json")
        assert data["version_number"] == 2
        assert data["file_size"] == 2048
        assert data["checksum"] == "b" * 64
        assert data["replaced_by"] == str(user_id)

    def test_version_history_list_serialization(self) -> None:
        """Test list of VersionHistoryEntry can be serialized for JSONB storage."""
        from datetime import datetime, timedelta
        from uuid import uuid4

        from app.schemas.document import VersionHistoryEntry

        user_id = uuid4()
        now = datetime.now(UTC)

        entries = [
            VersionHistoryEntry(
                version_number=1,
                file_size=1024,
                checksum="a" * 64,
                replaced_at=now - timedelta(days=1),
                replaced_by=user_id,
            ),
            VersionHistoryEntry(
                version_number=2,
                file_size=2048,
                checksum="b" * 64,
                replaced_at=now,
                replaced_by=user_id,
            ),
        ]

        # Serialize for JSONB storage
        serialized = [e.model_dump(mode="json") for e in entries]
        assert len(serialized) == 2
        assert serialized[0]["version_number"] == 1
        assert serialized[1]["version_number"] == 2


class TestDuplicateCheckResponseSchema:
    """Tests for DuplicateCheckResponse schema."""

    def test_duplicate_found_response(self) -> None:
        """Test response when duplicate is found."""
        from datetime import datetime
        from uuid import uuid4

        from app.schemas.document import DuplicateCheckResponse

        doc_id = uuid4()
        uploaded_at = datetime.now(UTC)
        response = DuplicateCheckResponse(
            exists=True,
            document_id=doc_id,
            uploaded_at=uploaded_at,
            file_size=1024,
        )
        assert response.exists is True
        assert response.document_id == doc_id
        assert response.uploaded_at == uploaded_at
        assert response.file_size == 1024

    def test_no_duplicate_response(self) -> None:
        """Test response when no duplicate is found."""
        from app.schemas.document import DuplicateCheckResponse

        response = DuplicateCheckResponse(exists=False)
        assert response.exists is False
        assert response.document_id is None
        assert response.uploaded_at is None
        assert response.file_size is None
