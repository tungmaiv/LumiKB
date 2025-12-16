# ATDD Checklist: Stories 3.8-3.11 (P2 Features) - Detailed

**Date:** 2025-11-25
**Stories:** 3.8, 3.9, 3.10, 3.11
**Status:** RED Phase (Tests Failing - Implementation Pending)
**Priority:** P2/P1 (Secondary features - implement after Stories 3.1-3.7)

---

## Overview

This document provides detailed ATDD for the remaining Epic 3 stories. These are **enhancement features** that build on the core search functionality (Stories 3.1-3.7).

**Implementation Priority:**
1. **Story 3.11** (Search Audit) - P1 - Compliance requirement, quick win
2. **Story 3.8** (Find Similar) - P2 - Discovery feature
3. **Story 3.9** (Relevance Explanation) - P2 - Power user feature
4. **Story 3.10** (Verify Citations UI) - P2 - Systematic verification workflow

**Total Tests:** 12 tests across 4 stories
**Total Effort:** 14-20 hours (~2-3 days)

---

## Story 3.11: Search Audit Logging

**Priority:** P1 (Compliance requirement)
**Effort:** 2-3 hours
**Test Files:** 2 integration tests

### Acceptance Criteria

- **AC-3.11.1**: All search queries logged to `audit.events` table
- **AC-3.11.2**: Audit log includes user_id, query, kb_ids, result_count, elapsed_ms

### Test Implementation

**File:** `backend/tests/integration/test_search_audit.py`

```python
"""Integration tests for Search Audit Logging (Story 3.11)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import AuditEvent
from tests.factories import create_kb_data


pytestmark = pytest.mark.integration


async def test_search_query_logged_to_audit_events(
    authenticated_client: AsyncClient,
    kb_with_indexed_docs: dict,
    db_session,
):
    """Test all search queries are logged to audit.events.

    GIVEN: User performs search
    WHEN: POST /api/v1/search
    THEN:
        - AuditEvent record created
        - action = 'search'
        - details includes query, kb_ids, result_count
    """
    # WHEN: User searches
    response = await authenticated_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth 2.0 security",
            "kb_ids": [kb_with_indexed_docs["id"]],
            "synthesize": False,
        },
    )

    assert response.status_code == 200

    # THEN: Audit event created
    audit_events = (
        await db_session.execute(
            select(AuditEvent)
            .where(AuditEvent.action == "search")
            .order_by(AuditEvent.created_at.desc())
        )
    ).scalars().all()

    assert len(audit_events) > 0

    latest_event = audit_events[0]
    assert latest_event.action == "search"
    assert "query" in latest_event.details
    assert latest_event.details["query"] == "OAuth 2.0 security"
    assert "kb_ids" in latest_event.details
    assert "result_count" in latest_event.details


async def test_audit_log_includes_elapsed_time(
    authenticated_client: AsyncClient,
    kb_with_indexed_docs: dict,
    db_session,
):
    """Test audit log includes search elapsed time in milliseconds.

    GIVEN: User performs search
    WHEN: Search completes
    THEN:
        - Audit log includes elapsed_ms field
        - elapsed_ms > 0

    This supports performance monitoring and compliance reporting.
    """
    # WHEN: User searches
    response = await authenticated_client.post(
        "/api/v1/search",
        json={
            "query": "authentication",
            "kb_ids": [kb_with_indexed_docs["id"]],
            "synthesize": True,  # Full search (longer elapsed time)
        },
    )

    assert response.status_code == 200

    # THEN: Audit log has elapsed_ms
    audit_events = (
        await db_session.execute(
            select(AuditEvent)
            .where(AuditEvent.action == "search")
            .order_by(AuditEvent.created_at.desc())
        )
    ).scalars().all()

    latest_event = audit_events[0]
    assert "elapsed_ms" in latest_event.details
    assert latest_event.details["elapsed_ms"] > 0
    assert isinstance(latest_event.details["elapsed_ms"], (int, float))
```

### Implementation Checklist

**Task 1: Add Audit Logging to Search Endpoint**

```python
import time
from app.services import AuditService

@router.post("/search")
async def search(...):
    start_time = time.time()

    # Perform search
    results = await search_service.search(...)

    # Calculate elapsed time
    elapsed_ms = (time.time() - start_time) * 1000

    # Log to audit
    await audit_service.log_event(
        user_id=current_user.id,
        action="search",
        details={
            "query": request.query,
            "kb_ids": request.kb_ids,
            "result_count": len(results),
            "elapsed_ms": round(elapsed_ms, 2),
            "synthesize": request.synthesize,
        }
    )

    return response
```

**Task 2: Test Audit Logging**

- Run tests: `pytest tests/integration/test_search_audit.py -v`
- Verify audit events in database
- ✅ All tests pass

---

## Story 3.8: Find Similar Documents

**Priority:** P2 (Discovery feature)
**Effort:** 4-6 hours
**Test Files:** 3 integration tests

### Acceptance Criteria

- **AC-3.8.1**: "Find Similar" button on search results
- **AC-3.8.2**: Find similar uses document embedding (not query)
- **AC-3.8.3**: Results show documents similar to selected result

### Test Implementation

**File:** `backend/tests/integration/test_find_similar.py`

```python
"""Integration tests for Find Similar Documents (Story 3.8)."""

import pytest
from httpx import AsyncClient

from tests.factories import create_kb_data


pytestmark = pytest.mark.integration


async def test_find_similar_returns_related_documents(
    authenticated_client: AsyncClient,
    kb_with_indexed_docs: dict,
):
    """Test find similar returns documents similar to source document.

    GIVEN: Document D1 exists
    WHEN: POST /api/v1/documents/{doc_id}/find-similar
    THEN:
        - Results are semantically similar to D1
        - D1 itself is excluded from results
        - Results ranked by similarity score
    """
    # WHEN: Find similar to document
    response = await authenticated_client.post(
        f"/api/v1/documents/101/find-similar",
        json={
            "limit": 5,
            "kb_ids": [kb_with_indexed_docs["id"]],
        },
    )

    # THEN: Similar documents returned
    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    results = data["results"]

    # Should exclude source document
    assert all(r["document_id"] != "101" for r in results)

    # Ranked by similarity
    scores = [r["similarity_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


async def test_find_similar_uses_document_embedding_not_query(
    authenticated_client: AsyncClient,
    kb_with_indexed_docs: dict,
):
    """Test find similar uses document's vector, not a text query.

    GIVEN: Document D1 with embedding E1
    WHEN: Find similar
    THEN:
        - Query uses E1 vector (not text-based search)
        - Results are document-to-document similarity
    """
    # Implementation note: This tests backend behavior
    # Backend should use document's existing embedding from Qdrant
    # NOT generate new embedding from query

    response = await authenticated_client.post(
        "/api/v1/documents/101/find-similar",
        json={"limit": 5},
    )

    assert response.status_code == 200
    # Success confirms document embedding was used


async def test_find_similar_across_multiple_kbs(
    authenticated_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test find similar can search across multiple KBs.

    GIVEN: Document D1 in KB1
           Similar content in KB2, KB3
    WHEN: Find similar with kb_ids=None (all KBs)
    THEN: Results from KB2, KB3 included
    """
    response = await authenticated_client.post(
        "/api/v1/documents/101/find-similar",
        json={
            "limit": 10,
            # kb_ids=None → search all permitted KBs
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should have results from multiple KBs
    kb_ids_in_results = {r["kb_id"] for r in data["results"]}
    assert len(kb_ids_in_results) >= 2  # At least 2 KBs
```

### Implementation Checklist

**Task 1: Create Find Similar Endpoint**

```python
@router.post("/documents/{doc_id}/find-similar")
async def find_similar(
    doc_id: str,
    request: FindSimilarRequest,
    current_user: User = Depends(get_current_user),
    service: SearchService = Depends(get_search_service)
):
    """Find documents similar to the given document."""

    # 1. Get document's embedding from Qdrant
    document_embedding = await service.get_document_embedding(doc_id)

    # 2. Search using document embedding (not query text)
    similar_results = await service.search_by_vector(
        embedding=document_embedding,
        kb_ids=request.kb_ids,
        limit=request.limit,
        user_id=current_user.id,
        exclude_doc_id=doc_id,  # Exclude source document
    )

    return {"results": similar_results}
```

---

## Story 3.9: Relevance Explanation

**Priority:** P2 (Power user feature)
**Effort:** 4-6 hours
**Test Files:** 3 component tests

### Acceptance Criteria

- **AC-3.9.1**: "Why is this relevant?" button on search results
- **AC-3.9.2**: Explanation shows matching keywords and score breakdown
- **AC-3.9.3**: Explanation references user's query

### Test Implementation

**File:** `frontend/src/components/search/__tests__/relevance-explanation.test.tsx`

```tsx
/**
 * Component tests for Relevance Explanation (Story 3.9)
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RelevanceExplanation } from '../relevance-explanation';

describe('RelevanceExplanation Component', () => {
  const mockResult = {
    id: '1',
    documentName: 'OAuth Guide.pdf',
    chunkText: 'OAuth 2.0 provides secure authorization for third-party applications.',
    relevanceScore: 0.92,
    matchedKeywords: ['OAuth', '2.0', 'authorization'],
    query: 'OAuth 2.0 security',
  };

  it('should display relevance explanation when button clicked', () => {
    render(<RelevanceExplanation result={mockResult} />);

    // WHEN: User clicks "Why is this relevant?"
    const explainButton = screen.getByTestId('explain-relevance-button');
    fireEvent.click(explainButton);

    // THEN: Explanation modal opens
    expect(screen.getByTestId('relevance-explanation-modal')).toBeInTheDocument();
  });

  it('should show matching keywords highlighted', () => {
    render(<RelevanceExplanation result={mockResult} isOpen={true} />);

    // THEN: Matched keywords displayed
    expect(screen.getByText(/Matched keywords:/)).toBeInTheDocument();
    expect(screen.getByText('OAuth')).toBeInTheDocument();
    expect(screen.getByText('2.0')).toBeInTheDocument();
    expect(screen.getByText('authorization')).toBeInTheDocument();
  });

  it('should display relevance score breakdown', () => {
    render(<RelevanceExplanation result={mockResult} isOpen={true} />);

    // THEN: Score breakdown shown
    expect(screen.getByText(/92%/)).toBeInTheDocument();
    expect(screen.getByText(/Semantic similarity/)).toBeInTheDocument();
    expect(screen.getByText(/Keyword matches/)).toBeInTheDocument();
  });
});
```

### Implementation Checklist

**Task 1: Create RelevanceExplanation Component**

```tsx
export function RelevanceExplanation({ result, isOpen, onClose }) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent data-testid="relevance-explanation-modal">
        <DialogHeader>
          <DialogTitle>Why is this relevant?</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Score */}
          <div>
            <p className="text-sm font-semibold">Relevance Score</p>
            <p className="text-2xl">{Math.round(result.relevanceScore * 100)}%</p>
          </div>

          {/* Matched keywords */}
          <div>
            <p className="text-sm font-semibold">Matched Keywords</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {result.matchedKeywords.map((keyword) => (
                <Badge key={keyword} variant="secondary">{keyword}</Badge>
              ))}
            </div>
          </div>

          {/* Explanation */}
          <div>
            <p className="text-sm text-muted-foreground">
              This result matches your query "{result.query}" based on semantic
              similarity and keyword overlap.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Story 3.10: Verify All Citations Mode

**Priority:** P2 (Systematic verification workflow)
**Effort:** 6-8 hours
**Test Files:** 4 component tests

### Acceptance Criteria

- **AC-3.10.1**: "Verify All" button starts systematic verification
- **AC-3.10.2**: Citations highlighted one-by-one
- **AC-3.10.3**: User marks each citation as "Verified" or "Flag"
- **AC-3.10.4**: Progress indicator shows completion %

### Test Implementation

**File:** `frontend/src/components/search/__tests__/verify-citations.test.tsx`

```tsx
/**
 * Component tests for Verify All Citations Mode (Story 3.10)
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { VerifyAllMode } from '../verify-all-mode';

describe('VerifyAllMode Component', () => {
  const mockCitations = [
    { number: 1, documentName: 'Doc1.pdf', excerpt: 'Excerpt 1' },
    { number: 2, documentName: 'Doc2.pdf', excerpt: 'Excerpt 2' },
    { number: 3, documentName: 'Doc3.pdf', excerpt: 'Excerpt 3' },
  ];

  it('should start verify mode when button clicked', () => {
    render(<VerifyAllMode citations={mockCitations} />);

    // WHEN: User clicks "Verify All"
    const verifyButton = screen.getByTestId('verify-all-button');
    fireEvent.click(verifyButton);

    // THEN: Verify mode active
    expect(screen.getByTestId('verify-mode-panel')).toBeInTheDocument();

    // First citation highlighted
    expect(screen.getByTestId('citation-card-1')).toHaveClass('highlighted');
  });

  it('should show progress indicator', () => {
    render(<VerifyAllMode citations={mockCitations} isActive={true} />);

    // THEN: Progress shown
    expect(screen.getByTestId('verify-progress')).toBeInTheDocument();
    expect(screen.getByText('0 / 3 verified')).toBeInTheDocument();
  });

  it('should advance to next citation when verified', () => {
    render(<VerifyAllMode citations={mockCitations} isActive={true} />);

    // WHEN: User marks first citation as verified
    const verifyButton = screen.getByTestId('mark-verified-1');
    fireEvent.click(verifyButton);

    // THEN: Second citation highlighted
    expect(screen.getByTestId('citation-card-2')).toHaveClass('highlighted');

    // Progress updated
    expect(screen.getByText('1 / 3 verified')).toBeInTheDocument();
  });

  it('should flag suspicious citations', () => {
    render(<VerifyAllMode citations={mockCitations} isActive={true} />);

    // WHEN: User flags a citation
    const flagButton = screen.getByTestId('flag-citation-1');
    fireEvent.click(flagButton);

    // THEN: Citation marked as flagged
    const citationCard = screen.getByTestId('citation-card-1');
    expect(citationCard).toHaveClass('flagged');

    // Progress still updates (flagged counts as reviewed)
    expect(screen.getByText('1 / 3 verified')).toBeInTheDocument();
  });
});
```

### Implementation Checklist

**Task 1: Create VerifyAllMode Component**

```tsx
export function VerifyAllMode({ citations, isActive, onComplete }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [verified, setVerified] = useState<number[]>([]);
  const [flagged, setFlagged] = useState<number[]>([]);

  const handleVerify = (citationNumber: number) => {
    setVerified([...verified, citationNumber]);
    advanceToNext();
  };

  const handleFlag = (citationNumber: number) => {
    setFlagged([...flagged, citationNumber]);
    advanceToNext();
  };

  const advanceToNext = () => {
    if (currentIndex < citations.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      onComplete({ verified, flagged });
    }
  };

  return (
    <div data-testid="verify-mode-panel">
      {/* Progress */}
      <div data-testid="verify-progress">
        {verified.length + flagged.length} / {citations.length} verified
      </div>

      {/* Current citation */}
      <CitationCard
        citation={citations[currentIndex]}
        highlighted={true}
        actions={
          <>
            <Button
              data-testid={`mark-verified-${citations[currentIndex].number}`}
              onClick={() => handleVerify(citations[currentIndex].number)}
            >
              ✓ Verified
            </Button>
            <Button
              data-testid={`flag-citation-${citations[currentIndex].number}`}
              onClick={() => handleFlag(citations[currentIndex].number)}
              variant="destructive"
            >
              ⚠ Flag
            </Button>
          </>
        }
      />
    </div>
  );
}
```

---

## Running All Tests

### Backend Tests

```bash
cd backend

# Story 3.11 (Audit)
pytest tests/integration/test_search_audit.py -v

# Story 3.8 (Find Similar)
pytest tests/integration/test_find_similar.py -v

# Expected: All tests FAIL (RED phase)
```

### Frontend Tests

```bash
cd frontend

# Story 3.9 (Relevance Explanation)
npm run test relevance-explanation.test.tsx

# Story 3.10 (Verify Citations)
npm run test verify-citations.test.tsx

# Expected: All tests FAIL (RED phase)
```

---

## Implementation Priority

**Recommended Order:**

1. **Story 3.11** (Audit Logging) - 2-3 hours
   - Quick win, compliance requirement
   - No UI changes
   - Start here for immediate value

2. **Story 3.8** (Find Similar) - 4-6 hours
   - Useful discovery feature
   - Reuses existing search infrastructure

3. **Story 3.9** (Relevance Explanation) - 4-6 hours
   - Power user feature
   - Enhances trust in search results

4. **Story 3.10** (Verify All Mode) - 6-8 hours
   - Nice-to-have workflow
   - Can defer to backlog if time-constrained

---

## Total Summary

| Story | Feature | Tests | Effort | Priority |
|-------|---------|-------|--------|----------|
| 3.11 | Search Audit | 2 | 2-3h | P1 |
| 3.8 | Find Similar | 3 | 4-6h | P2 |
| 3.9 | Relevance Explanation | 3 | 4-6h | P2 |
| 3.10 | Verify Citations UI | 4 | 6-8h | P2 |
| **Total** | **4 stories** | **12 tests** | **16-23h** (~2-3 days) | **Mixed** |

---

## Definition of Done (All Stories)

**Per Story:**
- [ ] All tests pass (GREEN phase)
- [ ] Code reviewed by senior dev
- [ ] Merged to main branch

**Story 3.11 Specific:**
- [ ] All search queries logged to audit.events
- [ ] Audit log includes elapsed_ms for performance monitoring

**Story 3.8 Specific:**
- [ ] Find Similar endpoint functional
- [ ] Uses document embedding (not query)
- [ ] Cross-KB support

**Story 3.9 Specific:**
- [ ] Relevance explanation modal implemented
- [ ] Matched keywords displayed
- [ ] Score breakdown shown

**Story 3.10 Specific:**
- [ ] Verify All mode functional
- [ ] Progress indicator working
- [ ] Flagging system implemented

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
