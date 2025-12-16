# Bugfix Session: Authentication and Onboarding Issues

**Date**: 2025-12-04
**Session Focus**: Login failures and onboarding wizard functionality

---

## Issue 1: Login Failure with `.local` Email Domain

### Symptoms
- Users could not log in with `admin@lumikb.local` or `demo@lumikb.local`
- Login form showed "An error occurred during login"

### Root Cause
The backend login endpoint (`POST /api/v1/auth/login`) returned 204 with auth cookie successfully, but the subsequent `GET /api/v1/users/me` endpoint returned **500 Internal Server Error**.

The underlying cause was **Pydantic email validation** in the `UserRead` schema. Pydantic's `email-validator` library rejects `.local` as a valid TLD because it's a reserved/special-use domain (RFC 6761).

Error message:
```
value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email
```

### Fix
1. Updated `infrastructure/scripts/seed-data.py` to use `.example` domain instead of `.local`:
   ```python
   DEMO_USER_EMAIL = "demo@lumikb.example"
   ADMIN_USER_EMAIL = "admin@lumikb.example"
   ```

2. Updated existing database records:
   ```sql
   UPDATE users SET email = 'admin@lumikb.example' WHERE email = 'admin@lumikb.local';
   UPDATE users SET email = 'demo@lumikb.example' WHERE email = 'demo@lumikb.local';
   ```

### Files Changed
- `infrastructure/scripts/seed-data.py`

### Valid Credentials After Fix
- **Admin**: `admin@lumikb.example` / `BilHam30`
- **Demo**: `demo@lumikb.example` / `demo123`

---

## Issue 2: React Query Provider Error

### Symptoms
After successful login, the dashboard page crashed with:
```
Runtime Error: No QueryClient set, use QueryClientProvider to set one
```

Stack trace pointed to `src/hooks/useOnboarding.ts` line 7.

### Root Cause
The `useOnboarding` hook called `useQueryClient()` from `@tanstack/react-query`, but the application's `Providers` component did not include `QueryClientProvider`.

### Fix
Updated `frontend/src/components/providers.tsx` to include `QueryClientProvider`:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    return makeQueryClient();
  } else {
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

export function Providers({ children }: ProvidersProps) {
  // ... existing code ...
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
  );
}
```

### Files Changed
- `frontend/src/components/providers.tsx`

---

## Issue 3: Missing User Type Fields

### Symptoms
TypeScript error: `Property 'onboarding_completed' does not exist on type 'UserRead'`

### Root Cause
The frontend `UserRead` type was missing fields that exist in the backend schema.

### Fix
Updated `frontend/src/types/user.ts` to include missing fields:

```typescript
export interface UserRead {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  created_at: string;
  onboarding_completed: boolean;  // Added
  last_active: string | null;     // Added
}
```

### Files Changed
- `frontend/src/types/user.ts`

---

## Issue 4: Onboarding "Start Exploring" Button Not Working

### Symptoms
Clicking "Start Exploring" on the final step of the onboarding wizard did nothing.

### Root Cause
The `useOnboarding` hook used incorrect authentication method:
```typescript
// WRONG: App uses httpOnly cookie auth, not Bearer tokens
const token = localStorage.getItem('token');
const res = await fetch(`${API_BASE_URL}/api/v1/users/me/onboarding`, {
  method: 'PUT',
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

### Fix
Updated `frontend/src/hooks/useOnboarding.ts` to use the proper API client with cookie credentials:

```typescript
import { apiClient } from '@/lib/api/client';
import { useUser, useAuthStore } from '@/lib/stores/auth-store';
import type { UserRead } from '@/types/user';

export function useOnboarding() {
  const queryClient = useQueryClient();
  const user = useUser();
  const setUser = useAuthStore((state) => state.setUser);

  const markOnboardingCompleteMutation = useMutation({
    mutationFn: async () => {
      return apiClient<UserRead>('/api/v1/users/me/onboarding', {
        method: 'PUT',
      });
    },
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });
  // ...
}
```

### Files Changed
- `frontend/src/hooks/useOnboarding.ts`

---

## Summary of All Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `infrastructure/scripts/seed-data.py` | Modified | Changed email domain from `.local` to `.example` |
| `frontend/src/components/providers.tsx` | Modified | Added QueryClientProvider wrapper |
| `frontend/src/types/user.ts` | Modified | Added `onboarding_completed` and `last_active` fields |
| `frontend/src/hooks/useOnboarding.ts` | Modified | Fixed to use cookie-based auth via apiClient |

---

## Technical Notes

### Authentication Architecture
LumiKB uses **httpOnly cookie-based JWT authentication** via FastAPI-Users:
- Login sets an httpOnly cookie named `lumikb_auth`
- All API requests must include `credentials: 'include'` to send cookies
- Bearer token authentication is NOT used

### Email Domain Best Practices
- Use `.example` for test/demo emails (RFC 2606 reserved for documentation)
- Avoid `.local` as it's reserved for mDNS/Bonjour (RFC 6761)
- Production should use real validated domains

### React Query Setup for Next.js
The QueryClient instantiation pattern used handles SSR correctly:
- Server: Creates a new client per request
- Browser: Reuses a single client instance
