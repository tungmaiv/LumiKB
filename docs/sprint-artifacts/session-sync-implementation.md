# Session Sync Implementation

Date: 2025-12-08
Status: Implemented
Related Stories: Epic 5 Infrastructure Enhancement

---

## Overview

This document describes the **sliding session** implementation that keeps JWT tokens alive while users are actively using the application. The feature prevents session timeout during active use, providing a seamless user experience without sacrificing security.

## Problem Statement

Previously, JWT tokens could expire while the user was actively using the application:
1. Backend issued JWT with configurable `session_timeout_minutes` (default: 720 min = 12 hours)
2. Frontend had no token refresh mechanism
3. When JWT expired, API calls returned 401 Unauthorized
4. Users experienced unexpected logouts or errors during active sessions

## Solution: Sliding Sessions

The implementation extends JWT expiry on user activity, preventing timeout while users are active while still expiring sessions for truly idle users.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                          │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │ useSessionRefresh │────▶│ Activity Tracker │                  │
│  │      Hook        │     │ (mouse, keyboard, │                  │
│  └────────┬─────────┘     │  touch, scroll)   │                  │
│           │               └─────────────────┘                   │
│           │ Every 5 min check                                    │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ If active within │────▶ POST /api/v1/auth/refresh            │
│  │   30 min idle    │                                            │
│  │   threshold      │                                            │
│  └─────────────────┘                                            │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌─────────────────┐                                            │
│  │ POST /auth/refresh │                                          │
│  │   - Validate JWT   │                                          │
│  │   - Issue new JWT  │                                          │
│  │   - Update Redis   │                                          │
│  │   - Audit log      │                                          │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Backend: Session Refresh Endpoint

**File:** `backend/app/api/v1/auth.py`

```python
@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Session refreshed, new JWT cookie set"},
        401: {"description": "Not authenticated or session expired"},
    },
)
async def refresh_session(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(current_active_user),
) -> Response:
    """Refresh the current session, extending its lifetime.

    This endpoint is called by the frontend to implement sliding sessions.
    When the user is active, the frontend periodically calls this endpoint
    to get a new JWT token with full session lifetime, preventing timeout
    while the user is actively using the application.
    """
    session_store = await _get_session_store()
    ip_address = get_client_ip(request)

    # Update session data in Redis with refreshed timestamp
    session_data = create_session_data(ip_address)
    await session_store.store_session(user.id, session_data)

    # Generate new JWT with full session lifetime
    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(user)
    response = await auth_backend.transport.get_login_response(token)

    # Audit logging
    background_tasks.add_task(
        _log_audit_event, "user.session_refreshed", user.id, ip_address
    )

    return response
```

### Frontend: Session Refresh Hook

**File:** `frontend/src/hooks/useSessionRefresh.ts`

The hook tracks user activity and periodically refreshes the session:

| Configuration | Value | Purpose |
|---------------|-------|---------|
| CHECK_INTERVAL_MS | 5 minutes | How often to check if refresh is needed |
| MIN_REFRESH_INTERVAL_MS | 2 minutes | Minimum time between refresh calls |
| IDLE_THRESHOLD_MS | 30 minutes | Stop refreshing if user is idle this long |
| ACTIVITY_DEBOUNCE_MS | 1 second | Debounce activity event updates |

**Activity Detection:**
- Mouse movement
- Keyboard input
- Touch events
- Scroll events
- Window focus

**Refresh Logic:**
1. Check every 5 minutes if user is authenticated
2. If user has been active within the last 30 minutes, call refresh endpoint
3. Minimum 2 minutes between refresh calls to prevent excessive requests
4. Refresh immediately when user returns to tab (visibility change)

### Frontend: Global 401 Handler

**File:** `frontend/src/lib/api/client.ts`

Centralized handling of session expiry:

```typescript
export const SESSION_EXPIRED_EVENT = 'lumikb:session-expired';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // Global 401 handler - dispatch session expired event
    if (response.status === 401) {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
      }
    }
    throw new ApiError(response.status, errorData.detail || 'Request failed');
  }
  // ...
}
```

The `useSessionRefresh` hook listens for this event and clears user state, triggering redirect to login.

### Frontend: Integration

**File:** `frontend/src/components/providers.tsx`

The hook is integrated at the app level in the Providers component:

```typescript
export function Providers({ children }: ProvidersProps) {
  // ... existing code

  // Session refresh hook - keeps session alive while user is active
  useSessionRefresh();

  // ...
}
```

## Configuration

Session timeout is controlled by the admin-configurable `session_timeout_minutes` setting in the SystemConfig database table (default: 720 minutes = 12 hours).

| Setting | Location | Default |
|---------|----------|---------|
| Session timeout | `system_config.session_timeout_minutes` | 720 (12 hours) |
| JWT expiry | Same as session timeout | 720 minutes |
| Cookie max-age | httpOnly cookie | 30 days |
| Redis session TTL | Same as JWT expiry | 720 minutes |

## Security Considerations

1. **JWT Validation**: Refresh endpoint requires valid (not expired) JWT before issuing new token
2. **Redis Session**: Session data is validated in Redis alongside JWT
3. **IP Tracking**: Session refresh updates IP address in session data
4. **Audit Logging**: All refresh events are logged for security auditing
5. **Idle Expiry**: Sessions still expire if user is truly idle (no activity for 30+ minutes without refresh)

## Testing

### Unit Tests
- Hook logic for activity tracking
- Debouncing behavior
- Refresh interval logic

### Integration Tests
- End-to-end session refresh flow
- 401 handling and logout

### Manual Testing
1. Set short timeout (e.g., 5 min), verify refresh extends session
2. Leave idle beyond threshold, verify session eventually expires
3. Verify 401 triggers proper logout and redirect

## Files Modified

| File | Change |
|------|--------|
| `backend/app/api/v1/auth.py` | Added `/refresh` endpoint |
| `frontend/src/hooks/useSessionRefresh.ts` | New file - session refresh hook |
| `frontend/src/lib/api/auth.ts` | Added `refreshSession()` function |
| `frontend/src/lib/api/client.ts` | Added global 401 handler with custom event |
| `frontend/src/components/providers.tsx` | Integrated `useSessionRefresh` hook |

## Related Documentation

- [architecture.md](../architecture.md) - Security Architecture section
- [tech-spec-epic-5.md](tech-spec-epic-5.md) - Epic 5 technical specification

---

*Document created: 2025-12-08*
