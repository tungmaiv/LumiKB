# CI/CD Pipeline Setup

This document describes the CI/CD pipeline configuration for LumiKB.

## Overview

LumiKB uses GitHub Actions for continuous integration and deployment:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `pr-validation.yml` | Pull requests to main/develop | Lint, test, build verification |
| `docker-build.yml` | Push to main | Build and push Docker images |
| `e2e.yml` | Manual dispatch | End-to-end testing |

## PR Validation Workflow

Runs on every pull request to `main` or `develop` branches.

### Jobs (Parallel Execution)

**Backend Jobs:**
- `lint-backend`: ruff check, ruff format --check
- `test-backend-unit`: pytest unit tests with 70% coverage threshold
- `test-backend-integration`: pytest integration tests

**Frontend Jobs:**
- `lint-frontend`: ESLint, TypeScript type checking
- `test-frontend`: Vitest tests with 60% coverage threshold
- `build-frontend`: Next.js build verification

**Coverage Report:**
- Posts coverage comment on PR
- Uploads to Codecov for tracking

### Performance Target

Total pipeline time: **< 10 minutes**

Achieved through:
- Parallel job execution (backend/frontend run simultaneously)
- Dependency caching (pip, npm)
- Concurrency control (cancels in-progress runs for same PR)

## Docker Build Workflow

Runs on merge to `main` branch.

### Images Built

| Image | Registry | Tags |
|-------|----------|------|
| `lumikb-api` | ghcr.io | `{sha}`, `latest` |
| `lumikb-worker` | ghcr.io | `{sha}`, `latest` |
| `lumikb-frontend` | ghcr.io | `{sha}`, `latest` |

### Authentication

Uses `GITHUB_TOKEN` for GHCR authentication (no additional secrets required).

## Reusable Actions

Located in `.github/actions/`:

### setup-backend

```yaml
- uses: ./.github/actions/setup-backend
  with:
    python-version: '3.11'  # optional, default: 3.11
    install-extras: 'dev'   # optional, default: dev
```

### setup-frontend

```yaml
- uses: ./.github/actions/setup-frontend
  with:
    node-version: '20'           # optional, default: 20
    install-playwright: 'false'  # optional, default: false
```

## Branch Protection Rules

Recommended branch protection settings for `main`:

### Required Status Checks

Enable "Require status checks to pass before merging" with:

- `lint-backend`
- `lint-frontend`
- `test-backend-unit`
- `test-backend-integration`
- `test-frontend`
- `build-frontend`

### Additional Settings

- [x] Require branches to be up to date before merging
- [x] Require a pull request before merging
- [ ] Require approvals (set based on team size)
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require conversation resolution before merging

### Setting Up Branch Protection

1. Go to Repository Settings > Branches
2. Click "Add branch protection rule"
3. Branch name pattern: `main`
4. Enable the settings listed above
5. Click "Create" / "Save changes"

## Coverage Thresholds

| Component | Minimum Coverage |
|-----------|------------------|
| Backend | 70% |
| Frontend | 60% |

Coverage is enforced:
- Backend: `pytest --cov-fail-under=70`
- Frontend: Vitest `thresholds` in `vitest.config.ts`

## Troubleshooting

### Pipeline Timeout

If jobs timeout, check:
- Integration tests may need testcontainers - ensure Docker is available
- Large npm/pip installs may exceed timeout - verify caching is working

### Coverage Drop

If coverage drops below threshold:
- Add tests for new code
- Check if coverage excludes are too aggressive
- Review coverage report in PR comment for uncovered lines

### Docker Build Failures

Common issues:
- GHCR authentication: Ensure `packages: write` permission is set
- Build cache: Clear GitHub Actions cache if builds are inconsistent
- Multi-arch builds: Currently building for linux/amd64 only
