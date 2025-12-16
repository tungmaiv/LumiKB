# Sprint Change Proposal: KB Debug Mode & Prompt Integration

**Proposal ID:** CP-2025-12-16-001
**Type:** New Enhancement
**Priority:** High
**Requested By:** Tung Vu
**Proposed By:** Scrum Master (Bob)
**Date:** 2025-12-16

---

## Executive Summary

This change proposal adds a new story (9-15) to Epic 9 (Observability) to address two related issues:

1. **KB Prompt Configuration Not Applied:** The `ConversationService` currently ignores KB-level prompt settings (system_prompt, citation_style, response_language, uncertainty_handling) and uses hardcoded values instead.

2. **Debug Mode Feature:** Add a new `debug_mode` boolean field to KB Settings that, when enabled, includes RAG pipeline telemetry in chat responses (retrieved chunks with scores, timing metrics, KB parameters used).

## Business Justification

| Factor | Current State | After Change |
|--------|---------------|--------------|
| KB Prompt Config | Stored but **ignored** | Actually applied during generation |
| Troubleshooting | Requires admin dashboard access | Users can enable debug mode per-KB |
| Trust/Transparency | Users can't see how answers are generated | Full visibility into RAG pipeline |
| Optimization | Blind tuning of KB parameters | Data-driven parameter optimization |

## Impact Assessment

### Documents Updated

| Document | Change Type | Lines Changed |
|----------|-------------|---------------|
| `docs/epics/epic-9-observability.md` | Story added | +5 lines |
| `docs/prd.md` | FRs added (FR126-FR130) | +15 lines |
| `docs/sprint-artifacts/9-15-kb-debug-mode-and-prompt-integration.md` | **NEW FILE** | +250 lines |

### Documents to Update During Implementation

| Document | Required Update |
|----------|-----------------|
| `docs/sprint-artifacts/7-14-kb-settings-ui-general.md` | Add Debug Mode checkbox to General Panel |
| `backend/app/schemas/kb_settings.py` | Add `debug_mode: bool = False` field |
| `backend/app/services/conversation_service.py` | Use KB prompt config, emit debug events |
| `backend/app/services/kb_config_resolver.py` | Add `resolve_prompt_config()` method |

### Code Changes Required

| File | Change Description | Complexity |
|------|-------------------|------------|
| `kb_settings.py:239-266` | Add `debug_mode` field to `KBSettings` | Low |
| `conversation_service.py:37-53` | Remove hardcoded prompt, use KB config | Medium |
| `conversation_service.py:623-683` | Modify `_build_prompt()` to accept `KBPromptConfig` | Medium |
| `conversation_service.py:328-547` | Add debug event emission to streaming | Medium |
| `kb_config_resolver.py` | Add `resolve_prompt_config()` method | Low |
| Frontend: Chat UI | Add debug panel component | Medium |
| Frontend: KB Settings | Add debug_mode checkbox | Low |

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance impact from debug logging | Low | Low | Debug data only collected when debug_mode=true |
| Breaking existing chat behavior | Medium | High | Use empty string check for system_prompt fallback |
| Security: exposing sensitive data in debug | Medium | Medium | Only show debug to users with KB admin/edit permission |
| Increased response payload size | Low | Low | Debug data separate event, can be ignored by clients |

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Story 7-12: KB Settings Schema | Done | Base schema exists |
| Story 7-13: KBConfigResolver | Done | Resolution logic exists but incomplete |
| Story 9-1: Observability Schema | Done | Timing collection infrastructure exists |
| Story 7-14: KB Settings UI | Done | UI exists, needs debug_mode addition |

## Effort Estimate

| Task | Points | Notes |
|------|--------|-------|
| Schema changes | 1 | Simple field addition |
| ConversationService integration | 3 | Modify prompt building, add debug events |
| Frontend debug panel | 2 | New component, conditional rendering |
| KB Settings UI addition | 1 | Add checkbox to existing form |
| Tests (unit + integration) | 1 | Standard coverage |
| **Total** | **8** | Single sprint deliverable |

## Recommendation

**Approve and schedule for Sprint 22.**

This change:
- Fixes an existing bug (KB prompt config ignored)
- Adds high-value user-facing observability
- Builds on existing infrastructure (no new dependencies)
- Low risk with clear fallback behavior
- Estimated 8 points = fits in one sprint

## Approval

- [ ] Product Owner approval
- [ ] Architecture review (if needed)
- [ ] Sprint planning inclusion

---

## Appendix A: Detailed File Changes

### A.1 `backend/app/schemas/kb_settings.py`

```python
# Add to KBSettings class (line ~265)
class KBSettings(BaseModel):
    # ... existing fields ...
    debug_mode: bool = Field(
        default=False,
        description="When enabled, chat responses include RAG pipeline telemetry"
    )
```

### A.2 `backend/app/services/conversation_service.py`

```python
# Remove hardcoded CHAT_SYSTEM_PROMPT constant (lines 37-53)
# Replace _build_prompt signature:

async def _build_prompt(
    self,
    history: list[dict[str, Any]],
    message: str,
    chunks: list[SearchResultSchema],
    kb_prompt_config: KBPromptConfig,  # NEW parameter
) -> list[dict[str, str]]:
    # Use KB system prompt or default
    system_prompt = kb_prompt_config.system_prompt or DEFAULT_SYSTEM_PROMPT

    # Add citation style instruction
    # Add response language instruction
    # Add uncertainty handling instruction
    # ... rest of prompt building ...
```

### A.3 Debug Event Format (New SSE Event)

```json
{
  "type": "debug",
  "kb_params": {
    "system_prompt_preview": "First 100 chars...",
    "citation_style": "inline",
    "response_language": "en",
    "uncertainty_handling": "acknowledge"
  },
  "chunks_retrieved": [
    {
      "preview": "First 100 chars of chunk...",
      "similarity_score": 0.89,
      "document_name": "technical-guide.pdf",
      "page_number": 12
    }
  ],
  "timing": {
    "retrieval_ms": 145,
    "context_assembly_ms": 12
  }
}
```

---

## Appendix B: Traceability Matrix

| New FR | Story AC | Implementation |
|--------|----------|----------------|
| FR126 | AC-9.15.1, AC-9.15.2 | `debug_mode` field in schema, UI checkbox |
| FR127 | AC-9.15.11 | Debug event includes `kb_params` |
| FR128 | AC-9.15.11 | Debug event includes `chunks_retrieved` |
| FR129 | AC-9.15.11 | Debug event includes `timing` |
| FR130 | AC-9.15.18 | Permission check in frontend |
| FR103a | AC-9.15.4 | KB system_prompt used in `_build_prompt()` |
| FR103b | AC-9.15.7 | citation_style instruction in prompt |
| FR103c | AC-9.15.8 | response_language instruction in prompt |
| FR103d | AC-9.15.9 | uncertainty_handling instruction in prompt |

---

*Proposal Author: Scrum Master (Bob)*
*Generated: 2025-12-16*
