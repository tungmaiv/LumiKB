# Data & API Architecture

← Back to [Architecture Index](index.md) | **Previous**: [05 - Implementation Patterns](05-implementation-patterns.md)

---

## Data Architecture

### Core Entities

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    User     │────<│ KBPermission    │>────│KnowledgeBase│
└─────────────┘     └─────────────────┘     └──────┬──────┘
                                                   │
                                                   │ 1:N
                                                   ▼
                                            ┌─────────────┐
                                            │  Document   │
                                            └──────┬──────┘
                                                   │
                                                   │ 1:N (Qdrant)
                                                   ▼
                                            ┌─────────────┐
                                            │   Chunk     │
                                            │  (Vector)   │
                                            └─────────────┘
```

### PostgreSQL Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | User accounts | id, email, hashed_password, is_active |
| `knowledge_bases` | KB metadata | id, name, description, owner_id, status |
| `kb_permissions` | Access control | user_id, kb_id, permission_level |
| `documents` | Document metadata | id, kb_id, name, file_path, status, chunk_count |
| `outbox` | Event queue | event_type, aggregate_id, payload, processed_at |
| `audit.events` | Audit trail | user_id, action, resource_type, resource_id, details |

### Qdrant Collections

- One collection per Knowledge Base: `kb_{kb_id}`
- Vector dimension: 1536 (OpenAI ada-002) or configurable
- Payload includes: document_id, document_name, page, section, char_start, char_end, text

---

## API Contracts

### Route Structure

```
/api/v1/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   ├── POST /logout
│   └── POST /reset-password
├── /users
│   ├── GET /me
│   └── PATCH /me
├── /knowledge-bases
│   ├── GET /
│   ├── POST /
│   ├── GET /{kb_id}
│   ├── PATCH /{kb_id}
│   ├── DELETE /{kb_id}
│   └── GET /{kb_id}/stats
├── /documents
│   ├── GET /
│   ├── POST /
│   ├── GET /{doc_id}
│   ├── DELETE /{doc_id}
│   └── GET /{doc_id}/content
├── /search
│   ├── POST /
│   └── POST /quick
├── /chat
│   ├── POST /                    # SSE streaming
│   └── GET /history
├── /generate
│   └── POST /                    # SSE streaming
└── /admin
    ├── GET /audit-logs
    ├── GET /stats
    └── GET /health
```

### Response Format

```python
# Success
{
    "data": { ... },
    "meta": {
        "requestId": "req-abc",
        "timestamp": "2025-11-22T10:30:00Z"
    }
}

# Paginated
{
    "data": [ ... ],
    "meta": {
        "total": 150,
        "page": 1,
        "perPage": 20,
        "totalPages": 8
    }
}
```

---

**Previous**: [05 - Implementation Patterns](05-implementation-patterns.md) | **Next**: [07 - Security](07-security.md) | **Index**: [Architecture](index.md)
