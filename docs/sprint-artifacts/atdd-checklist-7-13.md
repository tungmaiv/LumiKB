# ATDD Checklist - Story 7-13: KBConfigResolver Service

**Story ID**: 7-13
**Status**: RED PHASE (Tests Fail - Awaiting Implementation)
**Primary Test Level**: Unit + Integration
**Generated**: 2025-12-09

---

## Story Summary

As a developer, I want a configuration resolver service, so that request/KB/system configs are merged with proper precedence.

**Core Principle**: Three-layer configuration resolution (Request → KB → System)

---

## Acceptance Criteria Breakdown

| AC ID | Description | Test Level | Priority |
|-------|-------------|------------|----------|
| AC-7.13.1 | resolve_param with request value wins | Unit | P0 |
| AC-7.13.2 | resolve_param with KB setting fallback | Unit | P0 |
| AC-7.13.3 | resolve_param with system default fallback | Unit | P0 |
| AC-7.13.4 | resolve_generation_config with merged precedence | Unit + Integration | P0 |
| AC-7.13.5 | resolve_retrieval_config with merged precedence | Unit + Integration | P0 |
| AC-7.13.6 | resolve_chunking_config from KB or system | Unit + Integration | P1 |
| AC-7.13.7 | get_kb_system_prompt with KB/system fallback | Unit + Integration | P1 |
| AC-7.13.8 | Redis caching with 5min TTL and invalidation | Unit + Integration | P0 |

---

## Test Files Created

### Unit Tests

**File**: `backend/tests/unit/test_kb_config_resolver.py`

| Test Class | Test Count | AC Coverage |
|------------|------------|-------------|
| TestResolveParamRequestWins | 3 | AC-7.13.1 |
| TestResolveParamKBFallback | 2 | AC-7.13.2 |
| TestResolveParamSystemDefault | 3 | AC-7.13.3 |
| TestResolveGenerationConfig | 4 | AC-7.13.4 |
| TestResolveRetrievalConfig | 3 | AC-7.13.5 |
| TestResolveChunkingConfig | 3 | AC-7.13.6 |
| TestGetKBSystemPrompt | 4 | AC-7.13.7 |
| TestKBSettingsCaching | 6 | AC-7.13.8 |
| TestKBConfigResolverEdgeCases | 4 | Edge cases |
| TestKBConfigResolverInit | 2 | Service init |

**Total Unit Tests**: 34

### Integration Tests

**File**: `backend/tests/integration/test_kb_config_resolver_api.py`

| Test Class | Test Count | AC Coverage |
|------------|------------|-------------|
| TestResolveGenerationConfigAPI | 4 | AC-7.13.4 |
| TestResolveRetrievalConfigAPI | 3 | AC-7.13.5 |
| TestResolveChunkingConfigAPI | 2 | AC-7.13.6 |
| TestGetKBSystemPromptAPI | 2 | AC-7.13.7 |
| TestKBSettingsCachingIntegration | 3 | AC-7.13.8 |
| TestConfigResolverPermissions | 2 | Security |
| TestConfigResolverEdgeCasesAPI | 3 | Edge cases |

**Total Integration Tests**: 19

---

## Data Factories Used

### Existing Factories (Reused)

- `UserFactory` - Creates test users with admin/non-admin roles
- `KnowledgeBaseFactory` - Creates test KBs with custom settings

### Factory Usage Patterns

```python
# KB with custom settings
test_kb = await KnowledgeBaseFactory.create_async(
    session=async_session,
    owner_id=admin_user.id,
    settings={
        "generation": {"temperature": 0.5},
        "retrieval": {"top_k": 20},
    },
)

# KB without settings (uses defaults)
test_kb_no_settings = await KnowledgeBaseFactory.create_async(
    session=async_session,
    owner_id=admin_user.id,
    settings=None,
)
```

---

## Fixtures Created

### Unit Test Fixtures

| Fixture | Purpose |
|---------|---------|
| `mock_redis` | AsyncMock Redis client for caching tests |
| `mock_session` | AsyncMock database session |
| `mock_kb_service` | AsyncMock KBService for settings retrieval |
| `mock_config_service` | AsyncMock ConfigService for system defaults |
| `sample_kb_id` | UUID fixture for KB identification |
| `sample_kb_settings` | Complete KBSettings object with custom values |
| `system_default_settings` | KBSettings with schema defaults |

### Integration Test Fixtures

| Fixture | Purpose |
|---------|---------|
| `admin_user` | Create admin user for authentication |
| `test_kb` | KB with custom settings for testing |
| `test_kb_no_settings` | KB without custom settings |
| `redis_client` | Real Redis client for caching tests |

---

## Mock Requirements

### External Services to Mock (Unit Tests)

1. **KBService.get_kb_settings()** - Returns KBSettings or None
2. **ConfigService.get_system_prompt()** - Returns system default prompt
3. **Redis Client** - get/setex/delete operations

### Mock Patterns

```python
# Mock KB settings retrieval
mock_kb_service.get_kb_settings.return_value = KBSettings(
    generation=GenerationConfig(temperature=0.5)
)

# Mock system prompt retrieval
mock_config_service.get_system_prompt.return_value = "You are a helpful assistant."

# Mock Redis cache hit
mock_redis.get.return_value = cached_settings.model_dump_json()

# Mock Redis cache miss
mock_redis.get.return_value = None
```

---

## Required Implementation

### New File

**File**: `backend/app/services/kb_config_resolver.py`

```python
class KBConfigResolver:
    """Resolves configuration with request → KB → system precedence."""

    CACHE_TTL = 300  # 5 minutes
    CACHE_KEY_PREFIX = "kb_settings:"

    def __init__(self, kb_service: KBService, config_service: ConfigService, redis: Redis):
        self._kb_service = kb_service
        self._config_service = config_service
        self._redis = redis

    def resolve_param(
        self,
        param_name: str,
        request_value: T | None,
        kb_settings: dict[str, Any],
        system_default: T
    ) -> T:
        """Resolve single parameter with precedence."""
        ...

    async def resolve_generation_config(
        self,
        kb_id: UUID,
        request_overrides: dict[str, Any] | None = None
    ) -> GenerationConfig:
        """Merge request → KB → system for generation settings."""
        ...

    async def resolve_retrieval_config(
        self,
        kb_id: UUID,
        request_overrides: dict[str, Any] | None = None
    ) -> RetrievalConfig:
        """Merge request → KB → system for retrieval settings."""
        ...

    async def resolve_chunking_config(
        self,
        kb_id: UUID
    ) -> ChunkingConfig:
        """Get chunking config from KB or system defaults."""
        ...

    async def get_kb_system_prompt(self, kb_id: UUID) -> str:
        """Get system prompt from KB or system default."""
        ...

    async def _get_kb_settings_cached(self, kb_id: UUID) -> KBSettings:
        """Get KB settings with Redis caching (5min TTL)."""
        ...

    async def invalidate_kb_settings_cache(self, kb_id: UUID) -> None:
        """Invalidate cached KB settings."""
        ...
```

### Service Export

**File**: `backend/app/services/__init__.py`

Add export:
```python
from app.services.kb_config_resolver import KBConfigResolver
```

### API Endpoints (If Needed)

Config resolution may be used internally by existing endpoints, but dedicated endpoints could include:

- `GET /api/v1/knowledge-bases/{kb_id}/config/generation`
- `GET /api/v1/knowledge-bases/{kb_id}/config/retrieval`
- `GET /api/v1/knowledge-bases/{kb_id}/config/chunking`
- `GET /api/v1/knowledge-bases/{kb_id}/config/prompt`

---

## Implementation Checklist

### Task 1: Create KBConfigResolver class (AC: 1,2,3)

- [ ] Create `backend/app/services/kb_config_resolver.py`
- [ ] Implement `resolve_param()` with three-layer precedence
- [ ] Add type hints for generic parameter resolution
- [ ] Handle falsy but valid values (0, False, "")
- [ ] Run unit tests: `pytest tests/unit/test_kb_config_resolver.py::TestResolveParam* -v`
- [ ] All `resolve_param` tests pass (GREEN)

### Task 2: Implement config resolution methods (AC: 4,5,6)

- [ ] Implement `resolve_generation_config()` returning `GenerationConfig`
- [ ] Implement `resolve_retrieval_config()` returning `RetrievalConfig`
- [ ] Implement `resolve_chunking_config()` returning `ChunkingConfig`
- [ ] Load KB settings from database via KBService
- [ ] Run unit tests: `pytest tests/unit/test_kb_config_resolver.py::TestResolve*Config -v`
- [ ] All config resolution tests pass (GREEN)

### Task 3: Implement prompt resolution (AC: 7)

- [ ] Implement `get_kb_system_prompt()` method
- [ ] Return KB prompt if set, otherwise system default
- [ ] Handle missing/empty prompt configs gracefully
- [ ] Run unit tests: `pytest tests/unit/test_kb_config_resolver.py::TestGetKBSystemPrompt -v`
- [ ] All prompt tests pass (GREEN)

### Task 4: Implement Redis caching (AC: 8)

- [ ] Add `_get_kb_settings_cached()` with 5min TTL
- [ ] Implement cache key pattern: `kb_settings:{kb_id}`
- [ ] Add `invalidate_kb_settings_cache()` method
- [ ] Handle invalid JSON in cache gracefully
- [ ] Run unit tests: `pytest tests/unit/test_kb_config_resolver.py::TestKBSettingsCaching -v`
- [ ] All caching tests pass (GREEN)

### Task 5: Service integration and exports

- [ ] Export `KBConfigResolver` from `backend/app/services/__init__.py`
- [ ] Add dependency injection pattern
- [ ] Wire invalidation to KB settings update flow
- [ ] Run full unit test suite: `pytest tests/unit/test_kb_config_resolver.py -v`
- [ ] All 34 unit tests pass (GREEN)

### Task 6: API endpoints (Optional)

- [ ] Add config resolution endpoints to KB router (if needed)
- [ ] Run integration tests: `pytest tests/integration/test_kb_config_resolver_api.py -v`
- [ ] All 19 integration tests pass (GREEN)

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

- [x] All tests written and failing
- [x] Unit tests: 34 tests failing (ModuleNotFoundError)
- [x] Integration tests: 19 tests created
- [x] Fixtures and factories identified

### GREEN Phase (DEV Team)

1. Pick one failing test (start with `TestResolveParamRequestWins`)
2. Implement minimal code to make it pass
3. Run test to verify green
4. Move to next test
5. Repeat until all tests pass

### REFACTOR Phase (DEV Team)

1. All tests passing (green)
2. Improve code quality
3. Extract duplications
4. Optimize performance
5. Ensure tests still pass

---

## Running Tests

```bash
# Run all unit tests (should fail in RED phase)
cd backend
.venv/bin/pytest tests/unit/test_kb_config_resolver.py -v

# Run specific test class
.venv/bin/pytest tests/unit/test_kb_config_resolver.py::TestResolveParamRequestWins -v

# Run with coverage
.venv/bin/pytest tests/unit/test_kb_config_resolver.py --cov=app/services/kb_config_resolver --cov-report=term-missing

# Run integration tests (requires running services)
.venv/bin/pytest tests/integration/test_kb_config_resolver_api.py -v

# Debug specific test
.venv/bin/pytest tests/unit/test_kb_config_resolver.py::TestResolveParamRequestWins::test_resolve_param_returns_request_value_when_provided -v --tb=long
```

---

## Dependencies

### Existing Schemas (from Story 7-12)

Import from `app.schemas.kb_settings`:
- `ChunkingConfig`
- `ChunkingStrategy`
- `GenerationConfig`
- `KBPromptConfig`
- `KBSettings`
- `RetrievalConfig`
- `RetrievalMethod`

### Existing Services

- `KBService` - For retrieving KB settings from database
- `ConfigService` - For system default values

### External

- Redis (async) - For caching KB settings

---

## Test Failure Verification

All 34 unit tests currently fail with:

```
ModuleNotFoundError: No module named 'app.services.kb_config_resolver'
```

This confirms we are in the RED phase - tests define expected behavior for code that doesn't exist yet.

---

## Knowledge Base References Applied

- **Given-When-Then structure**: All tests follow this pattern
- **One assertion per test**: Each test verifies single behavior
- **Mock patterns**: AsyncMock used for async dependencies
- **Factory patterns**: Using existing factories with overrides
- **Fixture architecture**: Composable fixtures with proper cleanup

---

## Traceability Matrix

| AC | Unit Test(s) | Integration Test(s) |
|----|--------------|---------------------|
| AC-7.13.1 | TestResolveParamRequestWins (3) | - |
| AC-7.13.2 | TestResolveParamKBFallback (2) | - |
| AC-7.13.3 | TestResolveParamSystemDefault (3) | - |
| AC-7.13.4 | TestResolveGenerationConfig (4) | TestResolveGenerationConfigAPI (4) |
| AC-7.13.5 | TestResolveRetrievalConfig (3) | TestResolveRetrievalConfigAPI (3) |
| AC-7.13.6 | TestResolveChunkingConfig (3) | TestResolveChunkingConfigAPI (2) |
| AC-7.13.7 | TestGetKBSystemPrompt (4) | TestGetKBSystemPromptAPI (2) |
| AC-7.13.8 | TestKBSettingsCaching (6) | TestKBSettingsCachingIntegration (3) |

---

## Next Steps for DEV Team

1. **Run failing tests**: `pytest tests/unit/test_kb_config_resolver.py -v`
2. **Review implementation checklist** above
3. **Implement one test at a time** (RED → GREEN)
4. **Refactor with confidence** (tests provide safety net)
5. **Share progress** in daily standup

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-09 | ATDD checklist generated - RED phase complete | TEA Agent |
