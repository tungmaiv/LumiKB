# Story 7.10: KB Model Configuration

Status: Done

## Story

As a **knowledge base owner**,
I want **to select which embedding and generation models my KB uses from the Model Registry**,
so that **I can optimize my KB for specific use cases and leverage different AI capabilities**.

## Acceptance Criteria

1. **AC-7.10.1**: Model selection dropdown during KB creation shows active models from registry
2. **AC-7.10.2**: Only active models appear in selection dropdown
3. **AC-7.10.3**: Model info (dimensions, context window) displayed on selection
4. **AC-7.10.4**: Qdrant collection auto-created with correct dimensions and distance metric from selected embedding model
5. **AC-7.10.5**: KB-level parameter overrides (similarity_threshold, top_k, rerank) supported
6. **AC-7.10.6**: Embedding model lock warning displayed after first document is processed
7. **AC-7.10.7**: Generation model changeable without document reprocessing
8. **AC-7.10.8**: Document processing uses KB-configured embedding model
9. **AC-7.10.9**: Search operations use KB-configured embedding model
10. **AC-7.10.10**: Chat/generation operations use KB-configured generation model

## Tasks / Subtasks

- [x] **Task 1: Database Schema Updates** (AC: 1, 4, 5)
  - [x] 1.1 Add embedding_model_id FK to knowledge_bases table
  - [x] 1.2 Add generation_model_id FK to knowledge_bases table
  - [x] 1.3 Add KB-level RAG parameter columns (similarity_threshold, search_top_k, etc.)
  - [x] 1.4 Add qdrant_collection_name and qdrant_vector_size columns
  - [x] 1.5 Create Alembic migration with proper constraints
  - [x] 1.6 Write tests for schema validation

- [x] **Task 2: KB Creation API Updates** (AC: 1, 2, 3, 4)
  - [x] 2.1 Update KnowledgeBaseCreate schema with model_id fields
  - [x] 2.2 Validate model_ids reference active models
  - [x] 2.3 Update POST /api/v1/knowledge-bases to accept model selection
  - [x] 2.4 Implement Qdrant collection creation on KB save
  - [x] 2.5 Store collection name and vector size in KB record
  - [x] 2.6 Write integration tests for KB creation with models

- [x] **Task 3: KB Settings API Updates** (AC: 5, 6, 7)
  - [x] 3.1 Update GET /api/v1/knowledge-bases/{id} to include model details
  - [x] 3.2 Update PUT /api/v1/knowledge-bases/{id} with model change handling
  - [x] 3.3 Implement embedding model lock check (documents > 0)
  - [x] 3.4 Allow generation model changes without restrictions
  - [x] 3.5 Implement KB-level RAG parameter updates
  - [x] 3.6 Write integration tests for KB settings updates

- [x] **Task 4: Document Processing Integration** (AC: 8, 9)
  - [x] 4.1 Update embedding worker to fetch KB's embedding model
  - [x] 4.2 Configure LiteLLM client with KB's model settings
  - [x] 4.3 Use correct Qdrant collection for KB
  - [x] 4.4 Update search service to use KB's embedding model
  - [x] 4.5 Apply KB-level RAG parameter overrides in search
  - [x] 4.6 Write integration tests for document processing with models

- [x] **Task 5: Generation Integration** (AC: 10)
  - [x] 5.1 Update generation service to fetch KB's generation model
  - [x] 5.2 Configure LiteLLM client with KB's generation settings
  - [x] 5.3 Apply KB-level generation parameter overrides
  - [x] 5.4 Write integration tests for generation with models
  - [x] 5.5 Update ConversationService to use KB-specific generation model for chat
  - [x] 5.6 Update chat API endpoints to pass db session for KB model lookup

- [x] **Task 6: KB Creation UI Updates** (AC: 1, 2, 3, 6)
  - [x] 6.1 Add embedding model dropdown to KB create modal
  - [x] 6.2 Add generation model dropdown to KB create modal
  - [x] 6.3 Fetch active models from /api/v1/models/embedding
  - [x] 6.4 Display model info (dimensions, context) on selection
  - [x] 6.5 Pre-select default models if configured
  - [x] 6.6 Write component tests for model selection

- [x] **Task 7: KB Settings UI Updates** (AC: 5, 6, 7)
  - [x] 7.1 Add Models section to KB settings page
  - [x] 7.2 Display current embedding and generation models
  - [x] 7.3 Show embedding model lock warning if documents exist
  - [x] 7.4 Allow generation model changes with confirmation
  - [x] 7.5 Add RAG parameter override fields
  - [x] 7.6 Write component tests for KB settings

## Dev Notes

### Architecture Patterns

- **Model Binding at Creation**: Embedding model locked after first document
- **Flexible Generation**: Generation model can be changed anytime
- **Collection per KB**: Each KB has its own Qdrant collection
- **Parameter Inheritance**: KB overrides > Model defaults > System defaults

### Source Tree Components

```
backend/
├── alembic/versions/
│   └── xxxx_add_model_refs_to_kb.py      # New migration
├── app/models/
│   └── knowledge_base.py                  # Update with model refs
├── app/schemas/
│   └── knowledge_base.py                  # Update with model fields
├── app/api/v1/
│   ├── chat.py                            # DI passes session for KB model lookup
│   └── chat_stream.py                     # DI passes session for KB model lookup
├── app/services/
│   ├── kb_service.py                      # Update for model handling
│   ├── search_service.py                  # Update for KB model
│   ├── generation_service.py              # Update for KB model
│   └── conversation_service.py            # KB generation model for chat
├── app/workers/
│   └── embedding.py                       # Update for KB model
└── tests/
    └── integration/
        └── test_kb_model_configuration.py

frontend/
├── src/components/kb/
│   ├── kb-create-modal.tsx                # Update with model selection
│   └── kb-settings-modal.tsx              # New component
└── src/hooks/
    └── useKBModels.ts                     # New hook
```

### Qdrant Collection Strategy

```python
# Collection naming convention
collection_name = f"kb_{kb_id}"

# Collection parameters from embedding model
vectors_config = VectorParams(
    size=embedding_model.dimensions,  # e.g., 1536
    distance=Distance[embedding_model.distance_metric.upper()]  # e.g., COSINE
)
```

### Parameter Override Hierarchy

| Parameter | KB Override | Model Default | System Default |
|-----------|-------------|---------------|----------------|
| similarity_threshold | KB.similarity_threshold | Model.similarity_threshold | 0.7 |
| top_k | KB.search_top_k | Model.search_top_k | 10 |
| temperature | KB.temperature | Model.default_temperature | 0.7 |

### Testing Standards

- **Unit Tests**: Model validation, parameter inheritance
- **Integration Tests**: KB creation with models, collection creation, search/generation with models
- **E2E Tests**: Full KB creation and document search flow with configured models

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Story 7-10: KB Model Configuration]
- [Depends On: Story 7-9 (LLM Model Registry)]
- [Source: backend/app/services/kb_service.py]
- [Source: backend/app/integrations/qdrant_client.py]

## Dev Agent Record

### Context Reference

- [7-10-kb-model-configuration.context.xml](./7-10-kb-model-configuration.context.xml)

### Agent Model Used

Claude claude-opus-4-5-20251101 (Scrum Master Agent)

### Debug Log References

### Completion Notes List

- All 7 tasks verified as complete on 2025-12-09
- Database migration `e6cb38d97509_add_model_refs_to_knowledge_bases.py` adds FK columns, RAG params, Qdrant metadata
- KB creation API validates model IDs against active models in registry
- Embedding model lock implemented (checks doc_count > 0 before allowing change)
- Generation model can be changed freely without restrictions
- Frontend KB create modal includes model selection dropdowns with `useAvailableModels` hook
- Frontend KB settings modal with embedding model change warning
- Unit tests pass: 65 tests in test_kb_schemas.py, test_kb_permissions.py
- Component tests pass: 64 tests in KB component tests (kb-create-modal, kb-settings-modal)
- Integration tests exist but require Docker (test_kb_model_configuration.py - 21 tests)

**Bug Fix (2025-12-10): Model persistence after refresh**
- Issue: KB Settings modal showed "Use system default" instead of the selected model after page refresh
- Root cause: `KBSummary` schema (used for KB list endpoint) did not include `embedding_model_id`, `generation_model_id`, or `embedding_model_locked` fields
- Fix: Updated `KBSummary` schema in `backend/app/schemas/knowledge_base.py` to include model ID fields
- Fix: Updated `kb_service.py` list query to select and return model IDs from database
- Impact: KB Settings modal now correctly displays configured models after refresh

**Enhancement (2025-12-10): Provider-based routing for embedding models**
- Issue: KB-configured Ollama embedding models (e.g., `mxbai-embed-large:latest`) failed because the LiteLLM client used OpenAI-compatible routing via proxy, which doesn't work for local providers
- Root cause: Initial implementation used hardcoded port check (`"11434" in self.api_base`) which is fragile and doesn't scale
- Solution: Implemented provider-based routing using the `provider` field from Model Registry
- Changes:
  - Added `provider` field to `EmbeddingConfig` NamedTuple in `embedding.py`
  - Updated `_get_kb_embedding_config()` in `document_tasks.py` to pass provider from model registry
  - Added `DIRECT_CALL_PROVIDERS = {"ollama", "lmstudio"}` set to `LiteLLMEmbeddingClient`
  - Refactored `_call_embedding_api()` to route based on provider, not port number
  - For direct providers (Ollama, LM Studio): Uses provider prefix (e.g., `ollama/model`) with direct API call
  - For proxy providers (OpenAI, Gemini, etc.): Uses `custom_llm_provider="openai"` through LiteLLM proxy
- Benefits: Extensible to new local providers (LM Studio, etc.) without code changes

**Enhancement (2025-12-16): Chat conversation uses KB-specific generation model**
- Issue: Chat conversations (both sync and streaming) used system default LLM model instead of KB-configured generation model
- Root cause: ConversationService did not have access to database session for KB model lookup
- Solution: Updated ConversationService and chat API endpoints to support KB model lookup
- Changes:
  - Added `_get_kb_generation_model()` method to ConversationService that queries KB's generation_model relationship
  - Updated `send_message()` and `send_message_stream()` to fetch and use KB-specific model
  - Updated `chat.py` and `chat_stream.py` dependency injection to pass AsyncSession to ConversationService
  - `chat_completion()` in LiteLLMEmbeddingClient already supports optional `model` parameter (uses `litellm_proxy/` prefix for routing)
- Flow: Chat request → ConversationService → _get_kb_generation_model(kb_id) → LLMModel.model_id → chat_completion(model=kb_model)
- Benefits: Each KB can use different generation models (e.g., gpt-4o-mini for TOGAF, gemma3:4b for IT Operations)

### File List

**Backend:**
- `backend/alembic/versions/e6cb38d97509_add_model_refs_to_knowledge_bases.py` - Migration
- `backend/app/models/knowledge_base.py` - Model with FK columns and RAG params
- `backend/app/schemas/knowledge_base.py` - Schemas with model fields
- `backend/app/api/v1/chat.py` - Chat API with session DI for KB model lookup
- `backend/app/api/v1/chat_stream.py` - Streaming chat API with session DI
- `backend/app/services/kb_service.py` - Model validation, embedding lock
- `backend/app/services/generation_service.py` - KB generation model usage
- `backend/app/services/conversation_service.py` - _get_kb_generation_model() for chat
- `backend/app/integrations/qdrant_client.py` - create_collection_for_kb()
- `backend/app/integrations/litellm_client.py` - chat_completion() with model param
- `backend/app/workers/embedding.py` - EmbeddingConfig class
- `backend/app/workers/document_tasks.py` - _get_kb_embedding_config()
- `backend/tests/unit/test_kb_schemas.py` - Schema validation tests
- `backend/tests/integration/test_kb_model_configuration.py` - Integration tests

**Frontend:**
- `frontend/src/components/kb/kb-create-modal.tsx` - Model selection dropdowns
- `frontend/src/components/kb/kb-settings-modal.tsx` - Model settings with lock warning
- `frontend/src/hooks/useAvailableModels.ts` - Hook for fetching active models
- `frontend/src/components/kb/__tests__/kb-create-modal.test.tsx` - Component tests
- `frontend/src/components/kb/__tests__/kb-settings-modal.test.tsx` - Component tests
