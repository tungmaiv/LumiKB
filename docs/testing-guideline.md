# Testing Guideline

Quick reference for running tests in LumiKB.

## Test Commands

### Backend Tests (pytest)

```bash
make test-unit          # Unit tests only (fast, no Docker)
make test-integration   # Integration tests (uses testcontainers)
make test-all           # All backend tests
make test-coverage      # Tests with coverage report
```

### Frontend Tests (Vitest + Testing Library)

```bash
make test-frontend           # Run frontend unit tests
make test-frontend-watch     # Watch mode
make test-frontend-coverage  # With coverage report
```

### E2E Tests (Playwright)

```bash
make test-e2e         # Run E2E tests (headless)
make test-e2e-ui      # Interactive UI mode
make test-e2e-headed  # See browser while testing
```

## Running E2E Tests Locally

E2E tests require the full stack to be running:

```bash
# Terminal 1: Start infrastructure
make dev

# Terminal 2: Start backend
make dev-backend

# Terminal 3: Start frontend
make dev-frontend

# Terminal 4: Run E2E tests
make test-e2e         # Headless
make test-e2e-headed  # See browser
make test-e2e-ui      # Interactive UI
```

## CI/CD Behavior

| Test Type | Trigger | Notes |
|-----------|---------|-------|
| Backend Unit | Push/PR | Fast, no Docker needed |
| Backend Integration | Push/PR | Uses testcontainers |
| Frontend Unit | Push/PR | Vitest with jsdom |
| E2E | Manual only | Requires `workflow_dispatch` |

### Running E2E in CI

E2E tests are currently **manual-only** in GitHub Actions. To run:

1. Go to Actions tab in GitHub
2. Select "E2E Tests" workflow
3. Click "Run workflow"
4. Choose environment (local/staging)

This will be automated when full Docker Compose CI setup is complete.

## Test Specifications

For detailed patterns, fixtures, and best practices:

| Document | Purpose |
|----------|---------|
| [testing-backend-specification.md](testing-backend-specification.md) | pytest markers, fixtures, factories |
| [testing-frontend-specification.md](testing-frontend-specification.md) | Vitest, Testing Library patterns |
| [testing-e2e-specification.md](testing-e2e-specification.md) | Playwright, Page Objects, CI setup |

## Quick Tips

### Backend

- Use `@pytest.mark.unit` for tests without external dependencies
- Use `@pytest.mark.integration` for tests requiring database
- Integration tests use testcontainers - no manual Docker setup needed

### Frontend

- Co-locate tests in `__tests__/` directories next to components
- Use `screen.getByRole()` and `screen.getByLabelText()` for accessible queries
- Use `userEvent` instead of `fireEvent` for realistic interactions

### E2E

- Use Page Object Model pattern (see `frontend/e2e/pages/`)
- Tests use auth fixture for pre-authenticated state
- Artifacts (screenshots, videos) saved on failure
