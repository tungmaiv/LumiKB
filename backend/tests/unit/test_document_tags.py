"""Unit tests for document tags validation.

Story 5-22: Document Tags
Tests the tag validation and normalization logic.
"""

from app.schemas.document import (
    MAX_TAG_LENGTH,
    MAX_TAGS_PER_DOCUMENT,
    validate_tags,
)


class TestValidateTags:
    """Tests for the validate_tags function."""

    def test_empty_list_returns_empty(self):
        """Empty list input returns empty list."""
        assert validate_tags([]) == []

    def test_single_tag(self):
        """Single tag is returned as-is (lowercased)."""
        assert validate_tags(["Python"]) == ["python"]

    def test_multiple_tags(self):
        """Multiple tags are all processed."""
        result = validate_tags(["Python", "API", "Testing"])
        assert result == ["python", "api", "testing"]

    def test_converts_to_lowercase(self):
        """All tags are converted to lowercase."""
        assert validate_tags(["PYTHON"]) == ["python"]
        assert validate_tags(["PyThOn"]) == ["python"]
        assert validate_tags(["python"]) == ["python"]

    def test_strips_whitespace(self):
        """Whitespace is stripped from tags."""
        assert validate_tags(["  python  "]) == ["python"]
        assert validate_tags(["\tpython\n"]) == ["python"]
        assert validate_tags(["  python", "api  "]) == ["python", "api"]

    def test_removes_empty_tags(self):
        """Empty strings and whitespace-only strings are removed."""
        assert validate_tags([""]) == []
        assert validate_tags(["   "]) == []
        assert validate_tags(["python", "", "api"]) == ["python", "api"]
        assert validate_tags(["", "python", "  ", "api"]) == ["python", "api"]

    def test_removes_duplicates(self):
        """Duplicate tags are removed (after normalization)."""
        assert validate_tags(["python", "python"]) == ["python"]
        assert validate_tags(["Python", "python", "PYTHON"]) == ["python"]
        assert validate_tags(["api", "API", "Api"]) == ["api"]

    def test_preserves_order_first_occurrence(self):
        """First occurrence is kept when removing duplicates."""
        result = validate_tags(["first", "second", "first", "third"])
        assert result == ["first", "second", "third"]

    def test_max_10_tags(self):
        """Only first 10 tags are kept."""
        tags = [f"tag{i}" for i in range(15)]
        result = validate_tags(tags)
        assert len(result) == MAX_TAGS_PER_DOCUMENT
        assert result == [f"tag{i}" for i in range(10)]

    def test_max_50_chars_per_tag(self):
        """Tags longer than 50 chars are truncated."""
        long_tag = "a" * 100
        result = validate_tags([long_tag])
        assert len(result[0]) == MAX_TAG_LENGTH
        assert result[0] == "a" * 50

    def test_truncation_happens_before_dedup(self):
        """Truncation is applied, then dedup checks for duplicates."""
        # Two different 60-char tags that become the same after truncation
        tag1 = "a" * 50 + "xyz"
        tag2 = "a" * 50 + "abc"
        result = validate_tags([tag1, tag2])
        # Both truncate to same 50-char string, so dedup removes one
        assert len(result) == 1
        assert result[0] == "a" * 50

    def test_none_handling_inside_list(self):
        """None values in list should be handled gracefully."""
        # This shouldn't happen normally, but be defensive
        result = validate_tags(["python", None, "api"])  # type: ignore
        assert "python" in result
        assert "api" in result
        # None should be skipped or cause no error

    def test_special_characters_preserved(self):
        """Special characters in tags are preserved."""
        assert validate_tags(["c++", "c#"]) == ["c++", "c#"]
        assert validate_tags(["machine-learning"]) == ["machine-learning"]
        assert validate_tags(["node.js"]) == ["node.js"]

    def test_unicode_characters(self):
        """Unicode characters are handled correctly."""
        assert validate_tags(["日本語"]) == ["日本語"]
        assert validate_tags(["café"]) == ["café"]
        assert validate_tags(["naïve"]) == ["naïve"]

    def test_realistic_tag_set(self):
        """Test with a realistic set of tags."""
        tags = [
            "Python",
            "  Machine Learning  ",
            "API",
            "Tutorial",
            "machine learning",  # duplicate after normalization
            "data-science",
            "PYTHON",  # duplicate after normalization
        ]
        result = validate_tags(tags)
        assert result == [
            "python",
            "machine learning",
            "api",
            "tutorial",
            "data-science",
        ]


class TestTagsConstants:
    """Tests for tag constants."""

    def test_max_tags_per_document(self):
        """MAX_TAGS_PER_DOCUMENT is 10."""
        assert MAX_TAGS_PER_DOCUMENT == 10

    def test_max_tag_length(self):
        """MAX_TAG_LENGTH is 50."""
        assert MAX_TAG_LENGTH == 50
