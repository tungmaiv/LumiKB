# Security Architecture

← Back to [Architecture Index](index.md) | **Previous**: [06 - Data & API](06-data-and-api.md)

---

## Authentication Flow

```
Frontend → POST /auth/login → FastAPI-Users → PostgreSQL
    ↓
JWT token (httpOnly cookie) + Redis session
    ↓
Subsequent requests include cookie
    ↓
FastAPI middleware validates JWT on each request
    ↓
Active users: POST /auth/refresh extends session (sliding sessions)
```

---

## Authorization Model

| Role | Capabilities |
|------|--------------|
| **Admin** | All operations, audit logs, system config |
| **User** | Access assigned KBs only |

| KB Permission | Capabilities |
|---------------|--------------|
| **Read** | Search, view documents |
| **Write** | Upload, delete documents |
| **Admin** | Manage KB settings, permissions |

---

## Security Measures

| Measure | Implementation |
|---------|----------------|
| Password Hashing | argon2 (memory-hard) |
| Session Tokens | JWT with short expiry |
| CSRF Protection | SameSite cookies |
| Rate Limiting | Redis-based, per endpoint |
| Input Validation | Pydantic schemas |
| SQL Injection | SQLAlchemy parameterized queries |
| Encryption at Rest | PostgreSQL TDE, MinIO encryption |
| Encryption in Transit | TLS 1.3 everywhere |
| Audit Logging | Immutable append-only table |

---

## Session Management (Sliding Sessions)

LumiKB implements **sliding sessions** to keep JWT tokens alive while users are actively using the application, preventing session timeout during active use.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SESSION REFRESH FLOW                         │
│                                                                  │
│  User Activity     Frontend Hook        Backend Endpoint         │
│  (mouse, keys)  →  useSessionRefresh  →  POST /auth/refresh     │
│                         │                      │                 │
│                         │ Every 5 min          │                 │
│                         │ if active            │                 │
│                         ▼                      ▼                 │
│                    Check idle time      Issue new JWT            │
│                    < 30 min?            Update Redis session     │
│                         │                      │                 │
│                         └──────────────────────┘                 │
│                              New cookie with                     │
│                              full session lifetime               │
└─────────────────────────────────────────────────────────────────┘
```

| Configuration | Value | Description |
|---------------|-------|-------------|
| Session Timeout | Configurable (default: 720 min) | Admin-configurable via SystemConfig |
| Check Interval | 5 minutes | Frontend checks if refresh needed |
| Idle Threshold | 30 minutes | Stop refreshing if user idle this long |
| Min Refresh Gap | 2 minutes | Prevent excessive refresh calls |

**Key Components:**
- `POST /api/v1/auth/refresh` - Backend endpoint that issues new JWT
- `useSessionRefresh` hook - Frontend activity tracking and refresh logic
- `SESSION_EXPIRED_EVENT` - Global 401 handler for session expiry

**Security Properties:**
- Requires valid JWT to refresh (can't extend expired sessions)
- Sessions still expire when user is truly idle
- All refresh events are audit logged
- IP address tracking per session

See [session-sync-implementation.md](../sprint-artifacts/session-sync-implementation.md) for full implementation details.

---

## Audit Schema

```sql
CREATE SCHEMA audit;

CREATE TABLE audit.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET
);

-- INSERT-only permissions for application
CREATE ROLE audit_writer;
GRANT USAGE ON SCHEMA audit TO audit_writer;
GRANT INSERT ON audit.events TO audit_writer;

-- Indexes for common queries
CREATE INDEX idx_audit_user ON audit.events (user_id);
CREATE INDEX idx_audit_timestamp ON audit.events (timestamp);
CREATE INDEX idx_audit_resource ON audit.events (resource_type, resource_id);
```

**Retention Policy:**
- Archive to MinIO after 90 days
- Delete from database after 1 year

---

**Previous**: [06 - Data & API](06-data-and-api.md) | **Next**: [08 - Deployment](08-deployment.md) | **Index**: [Architecture](index.md)
