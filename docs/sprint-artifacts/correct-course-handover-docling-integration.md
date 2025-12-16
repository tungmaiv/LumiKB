# Correct Course Handover: Docling PDF Parser Integration

**Date**: 2025-12-16
**Initiated By**: Dev Agent (Amelia)
**Target Workflow**: `/bmad:bmm:workflows:correct-course`
**Change Category**: Feature Enhancement / New Capability

---

## 1. Change Trigger Summary

### What Changed
During research for document processing improvements, the **Docling** library was identified as a superior alternative to the current Unstructured library for PDF parsing. A proof-of-concept implementation plan has been created on branch `feature/docling-parser-poc`.

### Why This Requires Correct-Course
This is a **scope addition** that:
1. Introduces a new optional dependency (`docling>=2.0.0`)
2. Adds new configuration options (system + KB level)
3. Creates a new worker module (`docling_parser.py`)
4. Modifies existing parsing pipeline with strategy pattern
5. Is NOT currently tracked in any epic/story

### Discovery Context
- User requested analysis of Docling for LumiKB document processing
- Research confirmed significant benefits over current implementation
- POC branch created but implementation paused pending proper scoping

---

## 2. Docling Library Analysis

### Key Benefits Over Unstructured

| Capability | Current (Unstructured) | Docling |
|------------|----------------------|---------|
| PDF Layout Analysis | Basic | Advanced (Heron model) |
| Table Extraction | Element-level | Cell-level (TableFormer) |
| OCR Backends | PyTesseract | RapidOCR, EasyOCR, Tesseract |
| Format Support | 3 (PDF, DOCX, MD) | 15+ (PDF, DOCX, PPTX, XLSX, HTML, images, audio) |
| Reading Order | Sequential | ML-inferred logical order |
| Framework Integration | None | LangChain, LlamaIndex native |
| GitHub Stars | N/A | 46.8k (highly active) |

### Known Concerns
- **Memory growth** in v2.60+ for large documents (>500 pages)
- **Model size**: ~300MB with AI models (Heron, TableFormer)
- **Initial latency**: Model loading on first use

### License
MIT License - fully permissible for commercial use.

---

## 3. Proposed Implementation Scope

### Files to Modify (5)

| File | Change |
|------|--------|
| `backend/app/core/config.py` | Add 4 Docling config options |
| `backend/app/workers/parsing.py` | Add strategy pattern, fallback logic |
| `backend/app/workers/document_tasks.py` | Pass kb_id to parse_document |
| `backend/app/schemas/kb_settings.py` | Add PdfParserChoice enum |
| `backend/pyproject.toml` | Add docling optional dependency |

### Files to Create (3)

| File | Purpose |
|------|---------|
| `backend/app/workers/docling_parser.py` | Docling parser implementation (~180 lines) |
| `backend/tests/unit/test_docling_parser.py` | Unit tests with mocked docling |
| `backend/tests/integration/test_parser_strategy.py` | Strategy selection tests |

### Estimated Effort
- **Implementation**: 4-6 hours
- **Testing**: 2-3 hours
- **Total**: ~8 hours (1 story point)

---

## 4. Feature Toggle Design

### Two-Level Configuration

```
System Level (config.py):
  LUMIKB_PARSER_DOCLING_ENABLED=false (default)
       │
       ├── If false → Always use Unstructured
       └── If true  → Check KB settings
                          │
KB Level (kb_settings.processing.pdf_parser):
  "unstructured" → Use Unstructured
  "docling"      → Use Docling only
  "auto"         → Try Docling, fallback to Unstructured
```

### Rollback Strategy
- Set `LUMIKB_PARSER_DOCLING_ENABLED=false` for immediate disable
- No data migration required (same ParsedContent format)
- All existing documents remain valid

---

## 5. Impact Analysis for SM

### Epic/Story Impact

**Option A: Add to Epic 7 (Infrastructure & DevOps)**
- Aligns with tech improvements focus
- Story: `7-32-docling-pdf-parser-integration`
- Dependencies: None (self-contained)

**Option B: Add to Epic 9 (if future document improvements planned)**
- Could be part of document processing enhancements
- Depends on product roadmap

**Option C: Standalone Tech Debt Story**
- Quick implementation, low risk
- Feature-flagged, can be enabled gradually

### PRD Impact
- FR related to document parsing may benefit from enhanced extraction
- No PRD changes required (enhancement to existing capability)

### Architecture Impact
- Strategy pattern adds abstraction layer
- No breaking changes to existing interfaces
- `ParsedContent` contract preserved

### Test Impact
- Existing `test_parsing.py` unchanged (160+ tests)
- New tests added for Docling-specific functionality
- Integration tests optional (skip if docling not installed)

---

## 6. Questions for SM Decision

1. **Epic Assignment**: Which epic should this story belong to?
   - Epic 7 (Infrastructure) recommended
   - Or create new Epic 10 (Document Processing Enhancements)?

2. **Priority**: Where in the backlog should this be placed?
   - After current Epic 9 work?
   - Higher priority due to quality improvements?

3. **Acceptance Criteria Scope**:
   - PDF-only first (recommended)?
   - Or include DOCX/PPTX from start?

4. **Feature Toggle Default**:
   - Start disabled (recommended for safety)?
   - Or enable "auto" mode for immediate A/B testing?

5. **Documentation Requirements**:
   - User-facing docs for KB settings?
   - Admin guide for enabling Docling?

---

## 7. Artifacts Available

### POC Branch
- **Branch**: `feature/docling-parser-poc`
- **Status**: Created, implementation paused
- **Contains**: Empty branch ready for implementation

### Implementation Plan
- **Location**: `/home/tungmv/.claude/plans/steady-cuddling-harp.md`
- **Contents**: Detailed step-by-step implementation guide

### Research Notes
- Docling GitHub: https://github.com/docling-project/docling
- Technical report: https://arxiv.org/abs/2408.09869

---

## 8. Recommended Next Steps for SM

1. **Run Correct-Course Workflow**:
   ```
   /bmad:bmm:workflows:correct-course
   ```

2. **Input for Step 1**:
   - Change trigger: "Add Docling PDF parser as alternative to Unstructured"
   - Mode: Incremental (recommended)

3. **Expected Outputs**:
   - New story added to appropriate epic
   - Acceptance criteria defined
   - Sprint status updated

4. **Post-Approval**:
   - Dev can resume implementation on existing branch
   - Feature-flagged deployment allows gradual rollout

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Memory issues with large PDFs | Medium | Medium | max_pages limit (500) |
| Docling library breaking changes | Low | Medium | Pin version, test before upgrade |
| Performance regression | Low | Low | Fallback to Unstructured |
| Dependency conflicts | Low | Medium | Separate optional extra |

---

**Handover Complete** - Ready for SM to run correct-course workflow.
