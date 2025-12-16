# Frontend Go Migration Guide

> **Status:** Proposed
> **Author:** Architecture Team (Party Mode Session)
> **Date:** 2025-12-09
> **Related:** [Go API Gateway](10-go-api-gateway.md), [System Overview](01-system-overview.md)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [API Contract Requirements](#api-contract-requirements)
3. [Migration Validation Checklist](#migration-validation-checklist)
4. [Frontend Optimization Opportunities](#frontend-optimization-opportunities)
5. [Risk Matrix](#risk-matrix)
6. [Implementation Timeline](#implementation-timeline)

---

## Executive Summary

This document provides the complete guide for frontend teams during the Go API Gateway migration. The key principle: **the frontend requires ZERO code changes** if the Go implementation maintains API contract fidelity.

### Impact Summary

| Area | Impact Level | Details |
|------|-------------|---------|
| API Endpoints | None | Same `/api/v1/*` routes |
| SSE Streaming | None | Identical event format |
| Authentication | None | Same httpOnly cookie handling |
| Type Definitions | None | JSON schemas unchanged |
| Error Handling | None | Same error response structure |

---

## API Contract Requirements

### 1. Authentication Endpoints

Go must implement these endpoints with **exact** behavior:

#### POST `/api/v1/auth/login`

**Request Format:**
```
Content-Type: application/x-www-form-urlencoded

username=email@example.com&password=secret123
```

**Response Headers (CRITICAL):**
```
Set-Cookie: lumikb_auth=<jwt_token>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
```

**Response Body:**
```json
null  // or empty 204 response
```

**Cookie Requirements:**
| Attribute | Value | Notes |
|-----------|-------|-------|
| Name | `lumikb_auth` | MUST match exactly |
| HttpOnly | `true` | Security requirement |
| Secure | `true` | Production only |
| SameSite | `Lax` | CORS protection |
| Path | `/` | All routes |
| Max-Age | `86400` | 24 hours (configurable) |

#### POST `/api/v1/auth/logout`

**Response:**
```
Set-Cookie: lumikb_auth=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0
```

#### POST `/api/v1/auth/refresh`

**Response Headers:**
```
Set-Cookie: lumikb_auth=<new_jwt_token>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
```

#### GET `/api/v1/users/me`

**Response Body:**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": true,
  "created_at": "2025-01-15T10:30:00Z",
  "onboarding_completed": true,
  "last_active": "2025-01-15T14:22:00Z",
  "permission_level": 2
}
```

**Note:** `permission_level` is added by Story 7-11 (1=User, 2=Operator, 3=Admin).

---

### 2. SSE Streaming Endpoints

#### POST `/api/v1/chat/stream`

**Request:**
```json
{
  "kb_id": "uuid-string",
  "message": "user question",
  "conversation_id": "uuid-string-or-null"
}
```

**Response Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**SSE Event Format (EXACT):**

```
data: {"type":"status","content":"Searching knowledge base..."}\n\n
data: {"type":"token","content":"The"}\n\n
data: {"type":"token","content":" answer"}\n\n
data: {"type":"token","content":" is"}\n\n
data: {"type":"citation","data":{"number":1,"documentId":"uuid","documentName":"doc.pdf","pageNumber":5,"sectionHeader":"Introduction","excerpt":"relevant text...","confidence":0.92}}\n\n
data: {"type":"done","confidence":0.87,"conversationId":"new-uuid"}\n\n
```

**Event Types:**

| Event Type | JSON Shape | Purpose |
|------------|------------|---------|
| `status` | `{"type":"status","content":"..."}` | Progress indicator |
| `token` | `{"type":"token","content":"..."}` | Streamed text token |
| `citation` | `{"type":"citation","data":{...}}` | Source reference |
| `done` | `{"type":"done","confidence":0.87,"conversationId":"..."}` | Stream complete |
| `error` | `{"type":"error","message":"..."}` | Error occurred |

**Citation Object Shape:**
```typescript
interface Citation {
  number: number;           // 1-indexed citation number
  documentId: string;       // UUID of source document
  documentName: string;     // Display name
  pageNumber?: number;      // Optional page reference
  sectionHeader?: string;   // Optional section title
  excerpt: string;          // Relevant text snippet
  confidence?: number;      // 0.0-1.0 relevance score
}
```

#### GET `/api/v1/search?query=...&stream=true&kb_ids=...`

**SSE Events (different format from chat):**

```
event: status\ndata: {"content":"Searching..."}\n\n
event: token\ndata: {"content":"The"}\n\n
event: citation\ndata: {"number":1,"document_id":"...","document_name":"...","page_number":5,"section_header":"...","excerpt":"...","char_start":100,"char_end":200}\n\n
event: done\ndata: {"confidence":0.85}\n\n
```

**Key Difference:** Search uses named events (`event: token\n`), Chat uses typed JSON.

---

### 3. REST Endpoints (Non-Streaming)

#### Knowledge Base CRUD

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/api/v1/knowledge-bases` | - | `KnowledgeBase[]` |
| POST | `/api/v1/knowledge-bases` | `{name, description}` | `KnowledgeBase` |
| GET | `/api/v1/knowledge-bases/{id}` | - | `KnowledgeBase` |
| PATCH | `/api/v1/knowledge-bases/{id}` | `{name?, description?}` | `KnowledgeBase` |
| DELETE | `/api/v1/knowledge-bases/{id}` | - | 204 No Content |

**KnowledgeBase Shape:**
```json
{
  "id": "uuid",
  "name": "KB Name",
  "description": "Description",
  "owner_id": "user-uuid",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "document_count": 42,
  "permission_level": "owner",
  "embedding_model_id": "uuid-or-null",
  "chat_model_id": "uuid-or-null",
  "generation_model_id": "uuid-or-null"
}
```

#### Document Generation

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | `/api/v1/generate` | `GenerationRequest` | `GenerationResponse` |
| POST | `/api/v1/generate/stream` | `GenerationRequest` | SSE stream |

**GenerationRequest:**
```json
{
  "kb_id": "uuid",
  "mode": "rfp_response|technical_checklist|requirements_summary|custom",
  "additional_prompt": "optional user instructions",
  "selected_chunk_ids": ["chunk-uuid-1", "chunk-uuid-2"]
}
```

**GenerationResponse:**
```json
{
  "document": "Generated markdown content...",
  "citations": [...],
  "confidence": 0.89,
  "generation_id": "uuid",
  "mode": "rfp_response",
  "sources_used": 5
}
```

---

### 4. Error Response Format

**All errors MUST use this format:**

```json
{
  "detail": "Human-readable error message"
}
```

**HTTP Status Code Mapping:**

| Status | Meaning | Frontend Behavior |
|--------|---------|-------------------|
| 400 | Bad Request | Show validation error |
| 401 | Unauthorized | Trigger logout + redirect |
| 403 | Forbidden | Show permission denied |
| 404 | Not Found | Show not found UI |
| 422 | Validation Error | Show field errors |
| 500 | Server Error | Show generic error |

**401 Handling (Critical):**
Frontend dispatches `lumikb:session-expired` event on 401. Go must return 401 for:
- Missing cookie
- Expired JWT
- Invalid JWT signature
- Revoked session

---

### 5. CORS Configuration

Go must set these headers:

```
Access-Control-Allow-Origin: https://lumikb.example.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Accept
Access-Control-Max-Age: 86400
```

---

## Migration Validation Checklist

### Phase 1: Pre-Migration Testing

#### Authentication Tests

- [ ] **AUTH-001**: Login with valid credentials returns 200 + cookie
- [ ] **AUTH-002**: Login with invalid credentials returns 401
- [ ] **AUTH-003**: Cookie has correct attributes (HttpOnly, Secure, SameSite)
- [ ] **AUTH-004**: Logout clears cookie (Max-Age=0)
- [ ] **AUTH-005**: `/users/me` returns user object with all fields
- [ ] **AUTH-006**: `/users/me` returns 401 without cookie
- [ ] **AUTH-007**: Refresh extends session (new cookie issued)
- [ ] **AUTH-008**: Expired JWT triggers 401

#### SSE Streaming Tests

- [ ] **SSE-001**: Chat stream returns `Content-Type: text/event-stream`
- [ ] **SSE-002**: Chat stream emits `status` event first
- [ ] **SSE-003**: Chat stream emits `token` events with content
- [ ] **SSE-004**: Chat stream emits `citation` events with valid data
- [ ] **SSE-005**: Chat stream ends with `done` event
- [ ] **SSE-006**: Chat stream emits `error` event on failure
- [ ] **SSE-007**: Search stream uses named events (`event: token\n`)
- [ ] **SSE-008**: Search stream emits citations with char_start/char_end
- [ ] **SSE-009**: SSE reconnection works after network interruption
- [ ] **SSE-010**: Abort controller cancels stream properly

#### REST Endpoint Tests

- [ ] **REST-001**: KB list returns array with all fields
- [ ] **REST-002**: KB create returns new KB with ID
- [ ] **REST-003**: KB update returns modified KB
- [ ] **REST-004**: KB delete returns 204
- [ ] **REST-005**: Document upload returns processing status
- [ ] **REST-006**: Document list returns paginated results
- [ ] **REST-007**: Generation returns document with citations
- [ ] **REST-008**: Admin endpoints require is_superuser

#### Error Handling Tests

- [ ] **ERR-001**: 400 returns `{"detail": "..."}` format
- [ ] **ERR-002**: 401 triggers session-expired event
- [ ] **ERR-003**: 403 returns permission denied message
- [ ] **ERR-004**: 404 returns not found message
- [ ] **ERR-005**: 500 returns generic server error

### Phase 2: Parallel Deployment

- [ ] **DEPLOY-001**: Feature flag routes 10% traffic to Go
- [ ] **DEPLOY-002**: Compare response times (Go should be faster)
- [ ] **DEPLOY-003**: Compare error rates (should be equal or lower)
- [ ] **DEPLOY-004**: Verify session continuity (cookie valid for both)
- [ ] **DEPLOY-005**: Monitor memory usage (Go should use less)

### Phase 3: Full Migration

- [ ] **FULL-001**: 100% traffic to Go gateway
- [ ] **FULL-002**: Python API containers removed
- [ ] **FULL-003**: All E2E tests pass
- [ ] **FULL-004**: Performance metrics meet targets
- [ ] **FULL-005**: No frontend code changes required

---

## Frontend Optimization Opportunities

Once Go is deployed, these frontend optimizations become possible:

### 1. HTTP/2 Server Push (Low Effort)

**Current State:** HTTP/1.1 connections, one request at a time per connection
**With Go:** HTTP/2 multiplexing, server push for critical resources

**Implementation:**
```go
// Go can push CSS/JS during initial HTML request
w.Push("/assets/main.css", nil)
w.Push("/assets/app.js", nil)
```

**Frontend Benefit:** 100-200ms faster initial page load

### 2. WebSocket Upgrade for Chat (Medium Effort)

**Current State:** SSE (one-way streaming)
**Opportunity:** WebSocket (bidirectional)

**Benefits:**
- Typing indicators
- Real-time collaboration
- Connection state management

**Frontend Changes Required:**
```typescript
// New hook: useWebSocketChat
const { sendMessage, messages, isTyping } = useWebSocketChat(kbId);
```

**Effort:** 2-3 days frontend, 1 day Go backend

### 3. Response Compression (Zero Effort)

**Current State:** gzip compression
**With Go:** Brotli compression (20% smaller)

**Go Implementation:**
```go
router.Use(middleware.Compress(5, "application/json", "text/html"))
```

**Frontend Benefit:** Faster response parsing, reduced bandwidth

### 4. Connection Pooling for AI Services (Zero Frontend Effort)

**Current State:** Python creates gRPC connection per request
**With Go:** Connection pool with keepalive

**Result:** 50-100ms reduction in AI response latency

### 5. Prefetching API (Low Effort)

**Opportunity:** Go can expose prefetch hints

**Go Implementation:**
```go
// Response header for KB page
Link: </api/v1/knowledge-bases/{id}/documents>; rel=prefetch
```

**Frontend Implementation:**
```typescript
// useEffect to trigger prefetch
useEffect(() => {
  const link = response.headers.get('Link');
  if (link?.includes('prefetch')) {
    fetch(extractUrl(link), { priority: 'low' });
  }
}, [kbId]);
```

### 6. ETag Caching (Medium Effort)

**Current State:** No caching, always fetch fresh
**With Go:** ETag-based conditional requests

**Go Implementation:**
```go
func (h *Handler) GetKB(w http.ResponseWriter, r *http.Request) {
    kb := h.service.GetKB(id)
    etag := fmt.Sprintf(`"%s"`, kb.UpdatedAt.Unix())

    if r.Header.Get("If-None-Match") == etag {
        w.WriteHeader(http.StatusNotModified)
        return
    }

    w.Header().Set("ETag", etag)
    json.NewEncoder(w).Encode(kb)
}
```

**Frontend Implementation:**
```typescript
const { data } = useQuery({
  queryKey: ['kb', kbId],
  queryFn: async () => {
    const res = await fetch(url, {
      headers: { 'If-None-Match': cachedEtag }
    });
    if (res.status === 304) return cachedData;
    return res.json();
  }
});
```

**Effort:** 1 day frontend, 1 day Go backend

### 7. Request Coalescing (Zero Frontend Effort)

**Opportunity:** Go can batch duplicate requests

**Scenario:** 10 users request same KB simultaneously
**Current:** 10 database queries
**With Go:** 1 query, 10 responses (singleflight pattern)

```go
import "golang.org/x/sync/singleflight"

var group singleflight.Group

func (h *Handler) GetKB(id string) (*KB, error) {
    result, err, _ := group.Do(id, func() (interface{}, error) {
        return h.repo.FindByID(id)
    })
    return result.(*KB), err
}
```

---

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cookie format mismatch | Low | Critical | Test cookie parsing with exact Python output |
| SSE event ordering | Low | High | Integration tests with captured Python streams |
| CORS header mismatch | Low | High | Copy exact headers from Python config |
| Date format difference | Low | Medium | Use RFC3339 consistently |
| Error message changes | Medium | Low | Compare error responses side-by-side |
| Session state split | Low | Critical | Single Redis instance for both |
| gRPC timeout handling | Medium | Medium | Match Python timeout values |

---

## Implementation Timeline

### Sprint 1: Foundation (Week 1-2)

- [ ] Go project setup with chi router
- [ ] Database connection with sqlc
- [ ] Auth middleware (JWT parsing)
- [ ] Cookie handling (exact Python match)

### Sprint 2: Authentication (Week 3-4)

- [ ] Login/logout/register endpoints
- [ ] Session refresh
- [ ] `/users/me` endpoint
- [ ] Permission level integration (Story 7-11)

### Sprint 3: CRUD Endpoints (Week 5-6)

- [ ] Knowledge Base CRUD
- [ ] Document metadata endpoints
- [ ] Audit logging
- [ ] System configuration

### Sprint 4: Streaming Proxy (Week 7-8)

- [ ] gRPC client to Python AI services
- [ ] SSE streaming handlers
- [ ] Search streaming proxy
- [ ] Chat streaming proxy

### Sprint 5: Validation (Week 9-10)

- [ ] Run migration validation checklist
- [ ] Performance benchmarking
- [ ] Parallel deployment testing
- [ ] Full migration cutover

---

## Appendix: File-by-File Frontend Analysis

### Files Requiring NO Changes

| File | Purpose | Risk Level |
|------|---------|------------|
| `lib/api/client.ts` | Base fetch wrapper | None |
| `lib/api/auth.ts` | Auth API calls | None |
| `lib/api/chat.ts` | Chat SSE handling | None |
| `lib/api/search.ts` | Search API calls | None |
| `lib/api/generation.ts` | Generation API | None |
| `lib/api/knowledge-bases.ts` | KB CRUD | None |
| `lib/api/drafts.ts` | Draft management | None |
| `lib/hooks/use-search-stream.ts` | Search SSE hook | None |
| `lib/hooks/use-chat-stream.ts` | Chat SSE hook | None |
| `hooks/useGenerationStream.ts` | Generation SSE | None |
| `types/user.ts` | User type definitions | None |
| `types/citation.ts` | Citation types | None |

### Files to Monitor During Migration

| File | Reason | Action |
|------|--------|--------|
| `lib/stores/auth-store.ts` | Session handling | Verify 401 dispatch |
| `hooks/useSessionRefresh.ts` | Token refresh | Verify cookie update |
| `components/auth/auth-guard.tsx` | Route protection | Verify redirect |

---

*This guide is maintained as the definitive reference for frontend teams during the Go API Gateway migration.*
*Last updated: 2025-12-09*
