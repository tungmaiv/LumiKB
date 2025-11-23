# LumiKB

Enterprise RAG-powered knowledge management platform built on a citation-first architecture.

## Overview

LumiKB ensures every AI-generated statement traces back to source documents with passage-level precision. Built for Banking & Financial Services compliance requirements (SOC 2, GDPR, PCI-DSS awareness).

## Project Structure

```
lumikb/
├── frontend/          # Next.js 15 application
├── backend/           # FastAPI application
├── infrastructure/    # Docker and deployment configs
├── docs/              # Project documentation
├── .env.example       # Environment variable template
├── Makefile           # Common development commands
└── README.md
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Celery
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS 4, Zustand
- **Database**: PostgreSQL 16, Qdrant (vectors), Redis (cache/queue)
- **Storage**: MinIO (S3-compatible)
- **LLM**: LiteLLM Proxy

## Quick Start

### Prerequisites

- Python 3.11
- Node.js 20+
- Docker & Docker Compose

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd lumikb

# Start infrastructure services
docker compose up -d postgres qdrant minio redis

# Backend setup
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Available Commands

```bash
make help       # Show all available commands
make dev        # Start infrastructure services
make test       # Run all tests
make lint       # Run all linters
make migrate    # Run database migrations
make seed       # Seed demo Knowledge Base with sample documents
```

## Testing

LumiKB uses a comprehensive multi-level testing strategy. See the full specifications in `docs/testing-*.md`.

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
make test-e2e         # Run E2E tests
make test-e2e-ui      # Interactive UI mode
make test-e2e-headed  # See browser while testing
```

### Test Documentation

| Document | Purpose |
|----------|---------|
| [testing-backend-specification.md](docs/testing-backend-specification.md) | pytest markers, fixtures, factories |
| [testing-frontend-specification.md](docs/testing-frontend-specification.md) | Vitest, Testing Library patterns |
| [testing-e2e-specification.md](docs/testing-e2e-specification.md) | Playwright, Page Objects, CI setup |

### Demo Data Seeding

LumiKB includes a Sample Knowledge Base with demo documents to help you explore the platform immediately:

```bash
# Option 1: Using the shell script (requires backend venv)
./infrastructure/scripts/seed-data.sh

# Option 2: Using make (wrapper for the shell script)
make seed

# Option 3: Using Docker Compose
docker compose -f infrastructure/docker/docker-compose.yml run --rm seed
```

After seeding, you can log in with the demo user:
- **Email**: demo@lumikb.local
- **Password**: demo123 (or set via `DEMO_USER_PASSWORD` env var)

The demo user has READ access to the Sample Knowledge Base containing:
- Getting Started with LumiKB
- Understanding Citations and Trust
- Knowledge Base Management Guide
- Search and Q&A Features

## Authentication

LumiKB uses email/password authentication with HTTP-only cookies.

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "yourpassword123"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=yourpassword123"
```

> **Note**: The login endpoint uses OAuth2 form format - use `username` field for email, not JSON.

### Using the Demo User

After running `make seed`, you can login with the demo credentials:
- **Email**: demo@lumikb.local
- **Password**: demo123

## Documentation

- [Architecture](docs/architecture.md) - System design and decisions
- [Coding Standards](docs/coding-standards.md) - Development conventions
- [PRD](docs/prd.md) - Product requirements

## License

Proprietary - All rights reserved
