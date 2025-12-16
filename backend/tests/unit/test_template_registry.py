"""Unit tests for template registry.

Story 4.9: Generation Templates
Tests AC-1 (templates available), AC-2 (system prompts), AC-5 (structured output)
"""

import pytest

from app.services.template_registry import TEMPLATES, Template, get_template, list_templates


def test_get_template_returns_correct_template():
    """Test retrieving a template by ID."""
    template = get_template("rfp_response")

    assert template.id == "rfp_response"
    assert template.name == "RFP Response Section"
    assert "Executive Summary" in template.sections
    assert "cite every claim" in template.system_prompt.lower()


def test_get_template_raises_on_invalid_id():
    """Test error handling for invalid template ID."""
    with pytest.raises(ValueError, match="Unknown template"):
        get_template("invalid_template_id")


def test_list_templates_returns_all_templates():
    """Test listing all templates."""
    templates = list_templates()

    assert len(templates) == 4
    template_ids = [t.id for t in templates]
    assert "rfp_response" in template_ids
    assert "checklist" in template_ids
    assert "gap_analysis" in template_ids
    assert "custom" in template_ids


def test_all_templates_have_citation_requirement():
    """Test that all templates enforce citation requirements.

    AC-2: Each template has structured system prompt with citation requirements.
    """
    for template in TEMPLATES.values():
        # Check for citation format markers [1], [2]
        assert "[1]" in template.system_prompt or "[2]" in template.system_prompt
        # Check for citation instruction keywords
        assert "cite" in template.system_prompt.lower()


def test_rfp_response_template_structure():
    """Test RFP Response template has correct structure.

    AC-5: Templates produce structured output with specific sections.
    """
    template = get_template("rfp_response")

    assert len(template.sections) == 4
    assert "Executive Summary" in template.sections
    assert "Technical Approach" in template.sections
    assert "Relevant Experience" in template.sections
    assert "Pricing" in template.sections
    assert template.example_output is not None


def test_checklist_template_format():
    """Test Checklist template has correct format instructions.

    AC-5: Checklist template produces checklist items with Requirement, Status, Notes.
    """
    template = get_template("checklist")

    # Verify checkbox format
    assert "- [ ]" in template.system_prompt
    assert "Status" in template.system_prompt
    assert "Notes" in template.system_prompt


def test_gap_analysis_template_table_format():
    """Test Gap Analysis template includes table format.

    AC-5: Gap Analysis template produces table with specific columns.
    """
    template = get_template("gap_analysis")

    # Verify table column headers
    assert "Requirement" in template.system_prompt
    assert "Current State" in template.system_prompt
    assert "Gap" in template.system_prompt
    assert "Recommendation" in template.system_prompt
    assert "Source" in template.system_prompt


def test_custom_template_has_no_structure():
    """Test Custom template has no predefined sections.

    AC-4: Custom prompt template accepts user instructions with no specific structure.
    """
    template = get_template("custom")

    assert len(template.sections) == 0
    assert template.example_output is None
    assert "user's custom instructions" in template.system_prompt.lower()
