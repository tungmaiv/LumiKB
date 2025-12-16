# ATDD Checklist - Epic 9, Story 11: LangFuse Provider Implementation

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** API/Unit (Backend Python)

---

## Story Summary

Integrate LangFuse as an optional external observability provider for advanced LLM analytics. The provider implements the existing `ObservabilityProvider` interface using fire-and-forget patterns.

**As a** Admin/DevOps engineer
**I want** to integrate LangFuse as an optional external observability provider
**So that** I can leverage advanced LLM analytics and visualization capabilities when needed

---

## Acceptance Criteria

1. **AC1:** `LangFuseProvider` implements `ObservabilityProvider` interface
2. **AC2:** Provider disabled if `langfuse_public_key` not configured
3. **AC3:** `start_trace()` creates LangFuse trace with user_id, session_id
4. **AC4:** `log_llm_call()` creates LangFuse generation with usage metrics
5. **AC5:** Document events logged as LangFuse events with metadata
6. **AC6:** Provider sync status tracked in `provider_sync_status` table
7. **AC7:** All LangFuse calls are async and non-blocking
8. **AC8:** SDK errors caught and logged (fire-and-forget)
9. **AC9:** Flush called on trace end to ensure data sent
10. **AC10:** Integration test with LangFuse mock server

---

## Failing Tests Created (RED Phase)

### Unit Tests (12 tests)

**File:** `backend/tests/unit/test_langfuse_provider.py`

- [ ] **Test:** `test_langfuse_provider_implements_interface`
  - **Status:** RED - `LangFuseProvider` class does not exist
  - **Verifies:** AC1 - Provider implements `ObservabilityProvider` interface

- [ ] **Test:** `test_provider_disabled_when_no_public_key`
  - **Status:** RED - Provider class not implemented
  - **Verifies:** AC2 - Provider returns `enabled=False` without credentials

- [ ] **Test:** `test_provider_enabled_when_credentials_configured`
  - **Status:** RED - Provider class not implemented
  - **Verifies:** AC2 - Provider returns `enabled=True` with valid credentials

- [ ] **Test:** `test_start_trace_creates_langfuse_trace`
  - **Status:** RED - `start_trace()` method not implemented
  - **Verifies:** AC3 - Creates LangFuse trace with correct parameters

- [ ] **Test:** `test_start_trace_passes_user_id_and_session_id`
  - **Status:** RED - `start_trace()` method not implemented
  - **Verifies:** AC3 - user_id and session_id passed to LangFuse

- [ ] **Test:** `test_log_llm_call_creates_generation`
  - **Status:** RED - `log_llm_call()` method not implemented
  - **Verifies:** AC4 - Creates LangFuse generation object

- [ ] **Test:** `test_log_llm_call_includes_usage_metrics`
  - **Status:** RED - `log_llm_call()` method not implemented
  - **Verifies:** AC4 - Includes prompt_tokens, completion_tokens, cost_usd

- [ ] **Test:** `test_log_document_event_creates_langfuse_event`
  - **Status:** RED - `log_document_event()` method not implemented
  - **Verifies:** AC5 - Document events logged as LangFuse events

- [ ] **Test:** `test_all_methods_are_async_and_non_blocking`
  - **Status:** RED - Methods not implemented
  - **Verifies:** AC7 - All methods are async coroutines

- [ ] **Test:** `test_sdk_errors_caught_and_logged`
  - **Status:** RED - Error handling not implemented
  - **Verifies:** AC8 - Exceptions don't propagate to caller

- [ ] **Test:** `test_end_trace_calls_flush`
  - **Status:** RED - `end_trace()` method not implemented
  - **Verifies:** AC9 - Flush called on trace completion

- [ ] **Test:** `test_provider_sync_status_tracking`
  - **Status:** RED - Sync status logic not implemented
  - **Verifies:** AC6 - Creates/updates `provider_sync_status` records

### Integration Tests (4 tests)

**File:** `backend/tests/integration/test_langfuse_integration.py`

- [ ] **Test:** `test_langfuse_provider_registration`
  - **Status:** RED - Provider not registered in service
  - **Verifies:** AC1 - Provider registered with ObservabilityService

- [ ] **Test:** `test_langfuse_trace_flow_with_mock_server`
  - **Status:** RED - Provider not implemented
  - **Verifies:** AC10 - Full trace flow works with mock

- [ ] **Test:** `test_provider_disabled_no_sdk_calls`
  - **Status:** RED - Provider not implemented
  - **Verifies:** AC2 - No SDK calls when disabled

- [ ] **Test:** `test_sync_status_persisted_to_database`
  - **Status:** RED - Sync status not implemented
  - **Verifies:** AC6 - Sync status written to database

---

## Data Factories Created

### Provider Sync Status Factory (Existing)

**File:** `backend/tests/factories/observability_factory.py`

**Exports (already available):**

- `create_provider_sync_status(overrides?)` - Create provider sync status record
- `create_trace(overrides?)` - Create trace for testing
- `generate_trace_id()` - Generate W3C-compliant trace ID

**Example Usage:**

```python
from tests.factories import create_provider_sync_status, create_trace

# Provider sync status for LangFuse
sync_status = create_provider_sync_status(
    provider_name="langfuse",
    sync_status="synced",
    last_synced_trace_id=generate_trace_id(),
)

# Trace data for provider testing
trace_data = create_trace(
    user_id=test_user.id,
    operation_type="chat",
)
```

### New Factory Additions Needed

**File:** `backend/tests/factories/observability_factory.py`

**New Exports to Add:**

- `create_langfuse_config()` - Create mock LangFuse configuration

```python
def create_langfuse_config(
    *,
    enabled: bool = True,
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str = "https://cloud.langfuse.com",
) -> dict[str, Any]:
    """Create LangFuse configuration for testing."""
    return {
        "enabled": enabled,
        "public_key": public_key or f"pk-test-{fake.uuid4()}",
        "secret_key": secret_key or f"sk-test-{fake.uuid4()}",
        "host": host,
    }
```

---

## Fixtures Created

### LangFuse Mock Fixtures

**File:** `backend/tests/fixtures/langfuse_fixtures.py`

**Fixtures:**

- `mock_langfuse_client` - Mock LangFuse SDK client
  - **Setup:** Patches `langfuse.Langfuse` class
  - **Provides:** Mock client with trace/generation methods
  - **Cleanup:** Restores original SDK

- `langfuse_provider_enabled` - Provider with valid credentials
  - **Setup:** Configures settings with test credentials
  - **Provides:** `LangFuseProvider` instance
  - **Cleanup:** Resets settings

- `langfuse_provider_disabled` - Provider without credentials
  - **Setup:** Clears LangFuse settings
  - **Provides:** `LangFuseProvider` instance (disabled)
  - **Cleanup:** Restores settings

**Example Usage:**

```python
import pytest
from tests.fixtures.langfuse_fixtures import mock_langfuse_client

@pytest.fixture
def mock_langfuse_client(mocker):
    """Mock LangFuse SDK for unit tests."""
    mock_client = mocker.MagicMock()
    mock_trace = mocker.MagicMock()
    mock_client.trace.return_value = mock_trace
    mocker.patch("langfuse.Langfuse", return_value=mock_client)
    return mock_client

async def test_start_trace_creates_langfuse_trace(
    mock_langfuse_client,
    langfuse_provider_enabled,
):
    # Test implementation
    await langfuse_provider_enabled.start_trace(
        trace_id="abc123...",
        name="test_trace",
        timestamp=datetime.utcnow(),
    )
    mock_langfuse_client.trace.assert_called_once()
```

---

## Mock Requirements

### LangFuse SDK Mock

**Target:** `langfuse.Langfuse` class

**Methods to Mock:**

| Method | Return Type | Mock Behavior |
|--------|-------------|---------------|
| `trace()` | `LangfuseTrace` | Return mock trace object |
| `flush()` | `None` | Track call count |

**Mock Trace Object:**

```python
class MockLangfuseTrace:
    def generation(self, **kwargs):
        """Mock generation logging."""
        pass

    def event(self, **kwargs):
        """Mock event logging."""
        pass

    def span(self, **kwargs):
        """Mock span creation."""
        return MockLangfuseSpan()

    def update(self, **kwargs):
        """Mock trace update."""
        pass
```

**Error Simulation:**

```python
# Simulate SDK error for fire-and-forget testing
mock_client.trace.side_effect = Exception("Network error")
```

**Notes:**
- SDK should be optional dependency (graceful import)
- All SDK calls should be wrapped in try/except
- Mock should track all calls for verification

---

## Required Configuration

### Config Settings

**File:** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # LangFuse Configuration
    langfuse_enabled: bool = Field(default=False, env="LANGFUSE_ENABLED")
    langfuse_public_key: str | None = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, env="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        env="LANGFUSE_HOST"
    )
```

---

## Implementation Checklist

### Test: `test_langfuse_provider_implements_interface`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/services/langfuse_provider.py`
- [ ] Define `LangFuseProvider` class inheriting from `ObservabilityProvider`
- [ ] Implement `name` property returning "langfuse"
- [ ] Implement `enabled` property
- [ ] Add abstract method stubs for all interface methods
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_langfuse_provider_implements_interface -v`
- [ ] Test passes (green phase)

---

### Test: `test_provider_disabled_when_no_public_key`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Implement `__init__()` to check for `langfuse_public_key` in settings
- [ ] Set `_enabled = False` when no public key
- [ ] Implement `enabled` property to return `_enabled`
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_provider_disabled_when_no_public_key -v`
- [ ] Test passes (green phase)

---

### Test: `test_start_trace_creates_langfuse_trace`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Import `langfuse.Langfuse` SDK in provider
- [ ] Initialize LangFuse client in `__init__()` when enabled
- [ ] Implement `start_trace()` async method
- [ ] Call `self._client.trace()` with trace_id, name, timestamp
- [ ] Map user_id and session_id to LangFuse parameters
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_start_trace_creates_langfuse_trace -v`
- [ ] Test passes (green phase)

---

### Test: `test_log_llm_call_creates_generation`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Store active traces in `self._traces` dict
- [ ] Implement `log_llm_call()` async method
- [ ] Get trace from `self._traces[trace_id]`
- [ ] Call `trace.generation()` with model, name
- [ ] Include usage metrics in generation call
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_log_llm_call_creates_generation -v`
- [ ] Test passes (green phase)

---

### Test: `test_sdk_errors_caught_and_logged`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Wrap all SDK calls in try/except blocks
- [ ] Log exceptions using structlog
- [ ] Ensure no exceptions propagate to caller
- [ ] Add error handling decorator or wrapper function
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_sdk_errors_caught_and_logged -v`
- [ ] Test passes (green phase)

---

### Test: `test_end_trace_calls_flush`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Implement `end_trace()` async method
- [ ] Update trace with status and duration
- [ ] Call `self._client.flush()` after trace update
- [ ] Remove trace from `self._traces` dict
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_end_trace_calls_flush -v`
- [ ] Test passes (green phase)

---

### Test: `test_provider_sync_status_tracking`

**File:** `backend/tests/unit/test_langfuse_provider.py`

**Tasks to make this test pass:**

- [ ] Add database session injection for sync status
- [ ] Create/update `ProviderSyncStatus` on trace operations
- [ ] Track sync_status (pending/synced/failed)
- [ ] Store external_id from LangFuse response
- [ ] Run test: `pytest backend/tests/unit/test_langfuse_provider.py::test_provider_sync_status_tracking -v`
- [ ] Test passes (green phase)

---

### Test: `test_langfuse_provider_registration`

**File:** `backend/tests/integration/test_langfuse_integration.py`

**Tasks to make this test pass:**

- [ ] Import `LangFuseProvider` in `observability_service.py`
- [ ] Add to provider list in `ObservabilityService.__init__()` when enabled
- [ ] Ensure conditional registration based on settings
- [ ] Run test: `pytest backend/tests/integration/test_langfuse_integration.py::test_langfuse_provider_registration -v`
- [ ] Test passes (green phase)

---

## Running Tests

```bash
# Run all failing tests for this story
pytest backend/tests/unit/test_langfuse_provider.py backend/tests/integration/test_langfuse_integration.py -v

# Run specific test file
pytest backend/tests/unit/test_langfuse_provider.py -v

# Run tests with coverage
pytest backend/tests/unit/test_langfuse_provider.py --cov=app/services/langfuse_provider --cov-report=term-missing

# Run integration tests only
pytest backend/tests/integration/test_langfuse_integration.py -v

# Debug specific test
pytest backend/tests/unit/test_langfuse_provider.py::test_start_trace_creates_langfuse_trace -v -s
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

-  All tests written and failing
-  Fixtures and factories documented
-  Mock requirements documented
-  Implementation checklist created

**Verification:**

- All tests run and fail as expected
- Failure messages are clear and actionable
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** from implementation checklist (start with interface)
2. **Read the test** to understand expected behavior
3. **Implement minimal code** to make that specific test pass
4. **Run the test** to verify it now passes (green)
5. **Check off the task** in implementation checklist
6. **Move to next test** and repeat

**Key Principles:**

- One test at a time (don't try to fix all at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback)
- Use implementation checklist as roadmap

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass** (green phase complete)
2. **Review code for quality** (readability, maintainability)
3. **Extract duplications** (DRY principle)
4. **Ensure tests still pass** after each refactor

---

## Knowledge Base References Applied

- **data-factories.md** - Factory patterns using faker for test data
- **test-quality.md** - Test design principles (isolation, determinism)
- **network-first.md** - Mock patterns for external services
- **fixture-architecture.md** - Fixture setup/teardown patterns

---

## Notes

- LangFuse SDK (`langfuse>=2.0.0`) should be added to optional dependencies
- Provider should gracefully handle missing SDK (optional import)
- All SDK calls must be non-blocking (fire-and-forget pattern)
- Integration tests may require mock server or skip in CI

---

**Generated by BMad TEA Agent** - 2025-12-15
