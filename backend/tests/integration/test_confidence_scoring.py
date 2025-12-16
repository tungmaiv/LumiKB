"""
ATDD Integration Tests: Epic 4 - Confidence Scoring (Story 4.5)
Status: RED phase - Tests written before implementation
Generated: 2025-11-26

Test Coverage:
- P0: Low confidence sections highlighted (R-005)
- P0: Confidence threshold enforcement (R-005)
- P0: Verification prompt for low confidence (R-005)

Risk Mitigation:
- R-005 (BUS): Low-confidence drafts not flagged to users

Knowledge Base References:
- test-quality.md: Testing calculated values and thresholds
"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestConfidenceScoring:
    """Test confidence scoring and flagging in generation"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_low_confidence_sections_highlighted(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P0 Test - Story 4.5
        Risk: R-005 (Low-confidence drafts not flagged)

        GIVEN: User generates draft with sparse/weak sources
        WHEN: Some sections have <70% confidence
        THEN: Those sections are flagged with confidence_level: "low"
        AND: UI will display amber/red highlighting
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Generate draft with query that has sparse coverage
        # (Intentionally ambiguous to trigger low confidence)
        gen_response = await client.post(
            "/api/v1/generate",
            headers=authenticated_headers,
            json={
                "document_type": "Gap Analysis",
                "context": "Quantum blockchain authentication protocols",  # Unlikely to have strong sources
                "kb_id": kb_id,
            },
        )

        assert gen_response.status_code == status.HTTP_200_OK
        data = gen_response.json()

        # Response should include confidence metadata per section
        assert "sections" in data
        sections = data["sections"]

        # Each section should have confidence score
        for section in sections:
            assert "confidence_score" in section, (
                f"Section '{section.get('title')}' missing confidence_score"
            )
            assert "confidence_level" in section  # high, medium, low
            assert 0.0 <= section["confidence_score"] <= 1.0

            # Low confidence sections should be flagged
            if section["confidence_score"] < 0.7:
                assert section["confidence_level"] in ["low", "medium"], (
                    f"Section with score {section['confidence_score']} should be flagged"
                )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_confidence_threshold_classification(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P0 Test - Story 4.5
        Risk: R-005 (Low-confidence drafts not flagged)
        FR35c: System highlights sections with <70% confidence

        GIVEN: Draft with varying confidence scores
        WHEN: Confidence is calculated
        THEN: Sections classified correctly:
              - High (80-100%): Green, no warning
              - Medium (50-79%): Amber, "Review suggested"
              - Low (<50%): Red, "Verify carefully"
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        gen_response = await client.post(
            "/api/v1/generate",
            headers=authenticated_headers,
            json={
                "document_type": "RFP Response",
                "context": "OAuth implementation with some obscure edge cases",
                "kb_id": kb_id,
            },
        )

        sections = gen_response.json()["sections"]

        # Verify threshold classification logic
        for section in sections:
            score = section["confidence_score"]
            level = section["confidence_level"]

            if score >= 0.8:
                assert level == "high", f"Score {score} should be 'high'"
            elif score >= 0.5:
                assert level in ["medium", "low"], (
                    f"Score {score} should be 'medium' or 'low'"
                )
            else:
                assert level == "low", f"Score {score} should be 'low'"

            # Verify warning message exists for low/medium confidence
            if level in ["medium", "low"]:
                assert "warning" in section or "review_required" in section, (
                    "Low/medium confidence section missing warning flag"
                )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_confidence_calculation_based_on_sources(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P0 Test - Story 4.5
        Risk: R-005 (Low-confidence drafts not flagged)

        GIVEN: Draft generation
        WHEN: Confidence is calculated
        THEN: Score reflects:
              - Retrieval relevance scores
              - Number of supporting sources
              - Semantic coherence
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        gen_response = await client.post(
            "/api/v1/generate",
            headers=authenticated_headers,
            json={
                "document_type": "RFP Response",
                "context": "OAuth 2.0 implementation best practices",
                "kb_id": kb_id,
            },
        )

        sections = gen_response.json()["sections"]

        for section in sections:
            # Confidence metadata should include calculation basis
            assert "confidence_metadata" in section

            metadata = section["confidence_metadata"]

            # Should track source quality factors
            assert "avg_retrieval_score" in metadata
            assert "source_count" in metadata
            assert "coverage_score" in metadata

            # More sources + higher relevance = higher confidence
            if metadata["source_count"] >= 3 and metadata["avg_retrieval_score"] >= 0.8:
                assert section["confidence_score"] >= 0.7, (
                    "High source count + relevance should yield high confidence"
                )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verification_prompt_for_low_confidence_export(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P0 Test - Story 4.5 + 4.7
        Risk: R-005 (Low-confidence drafts not flagged)
        FR35c: Force "Have you verified?" prompt before export

        GIVEN: Draft with low-confidence sections
        WHEN: User attempts export
        THEN: Additional verification required
        AND: Stronger warning than normal export verification
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Generate draft with low confidence
        gen_response = await client.post(
            "/api/v1/generate",
            headers=authenticated_headers,
            json={
                "document_type": "Gap Analysis",
                "context": "Obscure authentication methods",  # Sparse sources
                "kb_id": kb_id,
            },
        )
        draft_id = gen_response.json()["draft_id"]

        # Check if draft has low confidence sections
        has_low_confidence = any(
            s["confidence_level"] == "low" for s in gen_response.json()["sections"]
        )

        # Attempt export
        export_response = await client.post(
            f"/api/v1/generate/{draft_id}/export",
            headers=authenticated_headers,
            json={"format": "docx", "sources_verified": True},
            # Missing low_confidence_acknowledged if has_low_confidence
        )

        if has_low_confidence:
            # Should require additional acknowledgment
            assert export_response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_428_PRECONDITION_REQUIRED,
            ]
            error = export_response.json()
            assert (
                "low confidence" in error["detail"].lower()
                or "verify carefully" in error["detail"].lower()
            )

            # Export WITH acknowledgment should succeed
            verified_export = await client.post(
                f"/api/v1/generate/{draft_id}/export",
                headers=authenticated_headers,
                json={
                    "format": "docx",
                    "sources_verified": True,
                    "low_confidence_acknowledged": True,
                },
            )
            assert verified_export.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_source_summary_displays_confidence_factors(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P1 Test - Story 4.5
        FR35d: "Based on 5 sources from 3 documents" summary

        GIVEN: Draft is generated
        WHEN: Generation completes
        THEN: Summary displays:
              - Total sources used
              - Number of unique documents
              - Overall confidence indicator
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        gen_response = await client.post(
            "/api/v1/generate",
            headers=authenticated_headers,
            json={
                "document_type": "Checklist",
                "context": "OAuth implementation checklist",
                "kb_id": kb_id,
            },
        )

        data = gen_response.json()

        # Should include source summary
        assert "source_summary" in data

        summary = data["source_summary"]

        # Required fields
        assert "total_sources" in summary
        assert "unique_documents" in summary
        assert "overall_confidence" in summary

        # Validate values
        assert summary["total_sources"] > 0
        assert summary["unique_documents"] > 0
        assert 0.0 <= summary["overall_confidence"] <= 1.0

        # Summary text should be user-friendly
        assert "summary_text" in summary
        expected_text = f"Based on {summary['total_sources']} sources from {summary['unique_documents']} documents"
        assert expected_text in summary["summary_text"]
