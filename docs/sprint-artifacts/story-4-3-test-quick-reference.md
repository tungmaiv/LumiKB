# Story 4-3 Test Quick Reference

**Quick commands for running Story 4-3 test automation**

---

## Frontend Tests (15 tests)

### Run All Story 4-3 Frontend Tests

```bash
cd frontend

# All tests (existing + new)
npm run test:run \
  src/components/chat/__tests__/chat-management.test.tsx \
  src/components/chat/__tests__/chat-edge-cases.test.tsx \
  src/hooks/__tests__/useChatManagement.test.ts \
  src/hooks/__tests__/useChatManagement-kb-switching.test.ts
```

### Run New Tests Only (15 tests)

```bash
cd frontend

# New edge case + KB switching tests
npm run test:run \
  src/components/chat/__tests__/chat-edge-cases.test.tsx \
  src/hooks/__tests__/useChatManagement-kb-switching.test.ts
```

**Expected**: ✅ 15/15 passing (~1.2s)

---

## Backend Tests (11 tests)

### Prerequisites

- ✅ Docker running (for testcontainers: Postgres + Redis)
- ✅ Backend dependencies installed (`pip install -r requirements.txt`)

### Run All Story 4-3 Backend Tests

```bash
cd backend

# All integration tests
pytest tests/integration/test_conversation_management.py \
       tests/integration/test_chat_clear_undo_workflow.py -v
```

### Run New Tests Only (6 tests)

```bash
cd backend

# New workflow tests with Redis verification
pytest tests/integration/test_chat_clear_undo_workflow.py -v
```

### Run Specific Test

```bash
# Full clear+undo+restore workflow (P0)
pytest tests/integration/test_chat_clear_undo_workflow.py::test_clear_and_undo_workflow -v

# KB switching isolation (P1)
pytest tests/integration/test_chat_clear_undo_workflow.py::test_kb_switching_preserves_conversations -v
```

**Expected**: ✅ 6/6 passing (~15-30s, depending on container startup)

---

## Unit Tests (ConversationService)

```bash
cd backend

# All unit tests for ConversationService
pytest tests/unit/test_conversation_service.py -v
```

**Expected**: ✅ All passing

---

## Test Coverage by AC

| AC | Description | Tests | Command |
|----|-------------|-------|---------|
| AC-1 | New Chat | 3 tests | `pytest tests/integration/test_chat_clear_undo_workflow.py::test_new_chat_clears_existing_conversation -v` |
| AC-2 | Clear Chat | 5 tests | `pytest tests/integration/test_chat_clear_undo_workflow.py::test_clear_and_undo_workflow -v` |
| AC-3 | Undo Clear | 6 tests | `pytest tests/integration/test_chat_clear_undo_workflow.py::test_undo_fails_when_backup_expired -v` |
| AC-4 | Metadata | 3 tests | `pytest tests/integration/test_conversation_management.py::test_get_conversation_history -v` |
| AC-5 | KB Isolation | 4 tests | `npm run test:run src/hooks/__tests__/useChatManagement-kb-switching.test.ts` |
| AC-6 | Error Handling | 7 tests | `npm run test:run src/components/chat/__tests__/chat-edge-cases.test.tsx` |

---

## Priority-Based Execution

### P0 Tests Only (Critical)

```bash
# Backend P0 tests
pytest tests/integration/test_chat_clear_undo_workflow.py \
  -k "test_clear_and_undo_workflow or test_undo_fails" -v

# Frontend P0 tests
npm run test:run src/hooks/__tests__/useChatManagement.test.ts -- --grep "P0"
```

### P0 + P1 Tests (Core Functionality)

```bash
# Backend
pytest tests/integration/test_chat_clear_undo_workflow.py -v

# Frontend
npm run test:run \
  src/components/chat/__tests__/chat-edge-cases.test.tsx \
  src/hooks/__tests__/useChatManagement-kb-switching.test.ts
```

---

## Troubleshooting

### Backend: "Redis connection failed"

**Solution**: Ensure Docker is running and testcontainers can start Redis
```bash
docker ps  # Check if Redis container is running
```

### Backend: Tests timeout

**Solution**: Increase timeout (containers take ~10-15s to start)
```bash
pytest tests/integration/test_chat_clear_undo_workflow.py -v --timeout=180
```

### Frontend: "Module not found"

**Solution**: Ensure you're in the `frontend/` directory
```bash
cd frontend
npm install  # Ensure dependencies installed
```

---

## CI/CD Integration

### PR Pipeline

```yaml
# .github/workflows/pr.yml
test-frontend:
  - npm run test:run src/components/chat/__tests__/
  - npm run test:run src/hooks/__tests__/

test-backend:
  - pytest tests/integration/test_conversation_management.py -v
  - pytest tests/integration/test_chat_clear_undo_workflow.py -v
```

**Expected Duration**: < 2 minutes total

---

## Files Created

### Backend
- `backend/tests/integration/test_chat_clear_undo_workflow.py` (6 tests)
- `backend/tests/integration/conftest.py` (fixtures updated)

### Frontend
- `frontend/src/components/chat/__tests__/chat-edge-cases.test.tsx` (7 tests)
- `frontend/src/hooks/__tests__/useChatManagement-kb-switching.test.ts` (8 tests)

### Documentation
- `docs/sprint-artifacts/automation-summary-story-4-3-comprehensive.md`
- `docs/sprint-artifacts/test-fixtures-story-4-3.md`
- `docs/sprint-artifacts/story-4-3-test-quick-reference.md` (this file)

---

**Total Tests**: 37 (22 existing + 15 new)
**Status**: ✅ Frontend 15/15 passing | 🔄 Backend ready to run
**Last Updated**: 2025-11-28
