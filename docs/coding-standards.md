# LumiKB Coding Standards

This document defines coding conventions for the LumiKB project. All contributors (human and AI) should follow these standards to ensure consistency across the codebase.

**Reference:** For architectural decisions, patterns, and technology choices, see [architecture.md](architecture.md).

---

## Table of Contents

1. [General Principles](#general-principles)
2. [Python Standards (Backend)](#python-standards-backend)
3. [TypeScript Standards (Frontend)](#typescript-standards-frontend)
4. [API Design Standards](#api-design-standards)
5. [Database Standards](#database-standards)
6. [Testing Standards](#testing-standards)
7. [Git & Version Control](#git--version-control)
8. [Documentation Standards](#documentation-standards)
9. [Security Standards](#security-standards)

---

## General Principles

### Core Philosophy

| Principle | Meaning | Application |
|-----------|---------|-------------|
| **KISS** | Keep It Simple, Stupid | Prefer simple solutions over clever ones |
| **DRY** | Don't Repeat Yourself | Extract common code AFTER 3+ repetitions |
| **YAGNI** | You Aren't Gonna Need It | Don't build for hypothetical requirements |

### When NOT to Abstract

- Don't create helpers for one-time operations
- Don't add error handling for scenarios that can't happen
- Don't use feature flags when you can just change the code
- Three similar lines of code is better than a premature abstraction

### Code Quality Rules

1. **No dead code** - Delete unused code completely, don't comment it out
2. **No backwards-compatibility hacks** - Don't rename unused `_vars` or add `// removed` comments
3. **Trust internal code** - Only validate at system boundaries (user input, external APIs)
4. **Fail fast** - Raise exceptions early, handle them centrally

---

## Python Standards (Backend)

### Version & Environment

- **Python 3.11** (required for redis-py compatibility)
- Use `pyproject.toml` for project configuration
- Use `venv` for local development

### Code Style

```python
# Use Black formatter with default settings
# Line length: 88 characters (Black default)
# Use double quotes for strings

# Imports: grouped and sorted
from collections.abc import Sequence  # stdlib
from typing import Any

from fastapi import Depends, HTTPException  # third-party
from pydantic import BaseModel

from app.core.config import settings  # local
from app.models.user import User
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `auth_service.py` |
| Classes | PascalCase | `KnowledgeBase` |
| Functions | snake_case | `get_user_by_id()` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |
| Private | Leading underscore | `_internal_helper()` |

### Type Hints

Always use type hints. This enables better IDE support and catches errors early.

```python
# Good
async def get_document(doc_id: str) -> Document | None:
    ...

# Good - use modern union syntax (3.10+)
def process(data: str | bytes) -> dict[str, Any]:
    ...

# Avoid - don't use Optional, use | None instead
def get_user(user_id: str) -> Optional[User]:  # Avoid
    ...
```

### Async/Await

All I/O operations must be async. Never block the event loop.

```python
# Good
async def fetch_documents(kb_id: str) -> list[Document]:
    return await repository.get_by_kb(kb_id)

# Bad - blocking call in async context
async def fetch_documents(kb_id: str) -> list[Document]:
    return repository.get_by_kb_sync(kb_id)  # Blocks!
```

### Exception Handling

Use the centralized exception pattern from architecture.md:

```python
# Define exceptions in app/core/exceptions.py
class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with ID {resource_id} not found",
            status_code=404
        )

# In services - just raise, never catch and re-raise
async def get(self, kb_id: str) -> KnowledgeBase:
    kb = await self.repo.get(kb_id)
    if not kb:
        raise NotFoundError("knowledge_base", kb_id)
    return kb
```

### Pydantic Models

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class DocumentCreate(BaseModel):
    """Request model for creating a document."""
    model_config = ConfigDict(strict=True)

    name: str = Field(..., min_length=1, max_length=255)
    kb_id: str

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

class DocumentResponse(BaseModel):
    """Response model for document."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    created_at: datetime
```

### FastAPI Routes

```python
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Create a new document."""
    return await service.create(data)

@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Get document by ID."""
    return await service.get(doc_id)
```

### Logging

Use structlog with the request context pattern:

```python
from app.core.logging import get_logger

async def process_document(doc_id: str) -> None:
    logger = get_logger()  # Automatically includes request_id, user_id
    logger.info("processing_started", document_id=doc_id)

    # ... processing ...

    logger.info("processing_completed", document_id=doc_id, chunks=chunk_count)
```

---

## TypeScript Standards (Frontend)

### Version & Environment

- **Node.js 20+** (LTS)
- **TypeScript** in strict mode
- **Next.js 15** with App Router

### Code Style

```typescript
// Use Prettier with default settings
// Use single quotes for strings (Prettier default for TS)
// Semicolons: yes

// Imports: grouped
import { useState, useEffect } from 'react';  // react
import { useRouter } from 'next/navigation';   // next
import { Button } from '@/components/ui/button'; // internal ui
import { useAuth } from '@/lib/hooks/use-auth'; // internal lib
import type { Document } from '@/types';        // types last
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files (components) | kebab-case | `citation-card.tsx` |
| Files (hooks) | kebab-case with use- | `use-auth.ts` |
| Components | PascalCase | `CitationCard` |
| Functions | camelCase | `fetchDocuments()` |
| Constants | SCREAMING_SNAKE | `MAX_FILE_SIZE` |
| Types/Interfaces | PascalCase | `DocumentResponse` |

### Component Structure

```typescript
// citation-card.tsx
import type { Citation } from '@/types';

interface CitationCardProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
}

export function CitationCard({ citation, onClick }: CitationCardProps) {
  return (
    <div
      className="rounded-lg border p-4"
      onClick={() => onClick?.(citation)}
    >
      <span className="font-mono">[{citation.number}]</span>
      <span className="ml-2">{citation.documentName}</span>
    </div>
  );
}
```

### Hooks

```typescript
// use-documents.ts
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Document } from '@/types';

export function useDocuments(kbId: string) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchDocuments() {
      try {
        setIsLoading(true);
        const data = await api.documents.list(kbId);
        setDocuments(data);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    }
    fetchDocuments();
  }, [kbId]);

  return { documents, isLoading, error };
}
```

### State Management (Zustand)

```typescript
// stores/auth-store.ts
import { create } from 'zustand';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
```

### Type Definitions

```typescript
// types/document.ts
export interface Document {
  id: string;
  name: string;
  kbId: string;
  status: DocumentStatus;
  createdAt: string;  // ISO 8601 from API
  updatedAt: string;
}

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';

// Use type for unions, interface for objects that may be extended
export type ApiResponse<T> = {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
};
```

### Error Boundaries

```typescript
// error.tsx (Next.js App Router)
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <h2>Something went wrong</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

---

## API Design Standards

### URL Structure

```
/api/v1/{resource}           # Collection
/api/v1/{resource}/{id}      # Individual resource
/api/v1/{resource}/{id}/{sub-resource}  # Nested resource
```

### HTTP Methods

| Method | Usage | Success Code |
|--------|-------|--------------|
| GET | Retrieve resource(s) | 200 |
| POST | Create resource | 201 |
| PATCH | Partial update | 200 |
| DELETE | Remove resource | 204 |

### Request/Response Format

```json
// Success response
{
  "data": { ... },
  "meta": {
    "requestId": "req-abc-123",
    "timestamp": "2025-11-23T10:30:00Z"
  }
}

// Error response
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document with ID xyz not found",
    "details": { "documentId": "xyz" },
    "requestId": "req-abc-123"
  }
}

// Paginated response
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "perPage": 20,
    "totalPages": 8
  }
}
```

### Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (DELETE) |
| 400 | Validation error |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Conflict |
| 422 | Business logic error |
| 500 | Internal server error |
| 503 | Service unavailable |

---

## Database Standards

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Tables | snake_case, plural | `knowledge_bases` |
| Columns | snake_case | `created_at` |
| Primary keys | `id` | `id UUID PRIMARY KEY` |
| Foreign keys | `{table}_id` | `user_id`, `kb_id` |
| Indexes | `idx_{table}_{column}` | `idx_documents_kb_id` |

### Standard Columns

Every table should have:

```sql
CREATE TABLE example (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- ... other columns ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Migrations

- One migration per logical change
- Migrations must be reversible
- Never modify existing migrations
- Use descriptive names: `20251123_add_status_to_documents.py`

```python
# alembic/versions/20251123_add_status_to_documents.py
def upgrade():
    op.add_column('documents', sa.Column('status', sa.String(20), default='pending'))

def downgrade():
    op.drop_column('documents', 'status')
```

---

## Testing Standards

Testing conventions, folder structure, and framework configuration are documented separately in the test framework specification.

**Reference:** See `docs/testing/` (generated by Test Architect) for:
- Test architecture and folder structure
- Naming conventions by test level (unit, integration, component, E2E)
- Fixture patterns and data factory guidelines
- CI/CD quality gates and burn-in strategy

> **Rationale:** Test framework decisions depend on tooling choices (Playwright, pytest, Vitest) and require dedicated documentation to avoid drift between sources. The Test Architect workflow (`*framework`) generates authoritative test documentation aligned with project architecture.

---

## Git & Version Control

### Branch Naming

```
feature/add-citation-export
fix/document-upload-timeout
refactor/auth-service-cleanup
docs/update-api-reference
```

### Commit Messages

```
type(scope): short description

Longer description if needed.

Refs: #123
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

**Examples:**
```
feat(citations): add export to PDF functionality

fix(upload): increase timeout for large documents

refactor(auth): simplify token validation logic

docs(api): update search endpoint examples
```

### Pull Request Guidelines

1. **One PR = One Feature/Fix** - Keep PRs focused
2. **Include tests** - No PR without tests for new functionality
3. **Update docs** - If API changes, update documentation
4. **Self-review first** - Check your own diff before requesting review

---

## Documentation Standards

### Code Comments

```python
# Good: Explain WHY, not WHAT
# Retry with exponential backoff because Qdrant occasionally
# returns 503 during index optimization
for attempt in range(max_retries):
    ...

# Bad: Explains what the code obviously does
# Loop through documents
for doc in documents:
    ...
```

### Docstrings

```python
async def search_documents(
    query: str,
    kb_ids: list[str],
    limit: int = 10,
) -> list[SearchResult]:
    """Search documents across knowledge bases.

    Args:
        query: Natural language search query.
        kb_ids: List of knowledge base IDs to search.
        limit: Maximum results to return.

    Returns:
        List of search results with citations.

    Raises:
        NotFoundError: If any kb_id doesn't exist.
        PermissionDeniedError: If user lacks read access.
    """
```

### README Files

- Each major directory should have a README if purpose isn't obvious
- Keep READMEs minimal and up-to-date
- Link to detailed docs rather than duplicating

---

## Security Standards

### Input Validation

- **Always validate** at API boundaries
- Use Pydantic for all request validation
- Never trust client input

```python
# Good: Pydantic validates automatically
@router.post("/")
async def create(data: DocumentCreate):  # Validated!
    return await service.create(data)

# Bad: Manual validation in service
async def create(self, name: str, kb_id: str):
    if not name:  # Should be in Pydantic
        raise ValueError("Name required")
```

### Secrets Management

- **Never commit secrets** to version control
- Use environment variables for all secrets
- Use `.env.example` to document required variables (without values)

```bash
# .env.example
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
JWT_SECRET=your-secret-here
MINIO_ACCESS_KEY=minioadmin
```

### SQL Injection Prevention

- **Always use parameterized queries** via SQLAlchemy
- Never construct SQL strings manually

```python
# Good: SQLAlchemy handles escaping
await session.execute(
    select(Document).where(Document.id == doc_id)
)

# Bad: String concatenation
await session.execute(f"SELECT * FROM documents WHERE id = '{doc_id}'")
```

### Authentication & Authorization

- Check permissions at the service layer
- Use dependency injection for current user
- Log all authorization failures

```python
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
) -> Document:
    doc = await self.repo.get(doc_id)
    if not await self.can_access(current_user, doc):
        raise PermissionDeniedError("read", "document")
    return doc
```

---

## Quick Reference

### File Checklist

Before committing, verify:

- [ ] Type hints on all functions (Python)
- [ ] Types on all exports (TypeScript)
- [ ] No `any` types without justification
- [ ] Tests for new functionality
- [ ] No secrets in code
- [ ] Logging for important operations
- [ ] Error handling follows centralized pattern

### Linting Commands

```bash
# Backend
cd backend
ruff check .          # Linting
ruff format .         # Formatting
mypy .                # Type checking

# Frontend
cd frontend
npm run lint          # ESLint
npm run format        # Prettier
npm run type-check    # TypeScript
```

---

_Last Updated: 2025-11-23_
_For: LumiKB Project_
