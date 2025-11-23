# Frontend Test Framework Specification

**Version:** 1.0
**Last Updated:** 2024-01-XX
**Status:** Active
**Applies To:** All frontend code in `frontend/` directory

---

## 1. Overview

This document establishes the frontend testing standards for LumiKB. All frontend development must adhere to these guidelines to ensure consistent, maintainable, and reliable test coverage.

### 1.1 Core Principles

1. **Co-location**: Tests live alongside the code they test in `__tests__` directories
2. **User-Centric**: Test behavior as users experience it, not implementation details
3. **Fast Feedback**: Unit tests must execute quickly for rapid iteration
4. **Isolation**: Each test must be independent and deterministic
5. **Accessibility**: Testing Library queries encourage accessible component design

### 1.2 Tech Stack

| Tool | Purpose | Version |
|------|---------|---------|
| Vitest | Test runner and assertion library | ^4.0.0 |
| @testing-library/react | Component testing utilities | ^16.3.0 |
| @testing-library/user-event | User interaction simulation | ^14.6.0 |
| @testing-library/jest-dom | Custom DOM matchers | ^6.9.0 |
| jsdom | Browser environment simulation | Built into Vitest |

---

## 2. Test Levels

### 2.1 Unit Tests (Primary Focus)

**Purpose**: Test individual components, hooks, and utilities in isolation.

**Characteristics**:
- Execute in <100ms per test
- No network requests (all mocked)
- No external dependencies
- Run on every file save in watch mode

**What to Test**:
- Component rendering logic
- User interactions (clicks, typing, form submissions)
- State changes and conditional rendering
- Hook behavior
- Utility functions
- Form validation

### 2.2 Integration Tests

**Purpose**: Test multiple components working together.

**Characteristics**:
- Execute in <500ms per test
- May include provider wrappers
- Test component composition
- Verify data flow between components

**What to Test**:
- Page-level component compositions
- Context provider interactions
- Store integrations with components
- Multi-step user flows within a page

### 2.3 E2E Tests (Separate Concern)

**Note**: End-to-end tests use Playwright and are documented separately in [testing-e2e-specification.md](testing-e2e-specification.md). They test full user journeys through the actual application.

---

## 3. Directory Structure

```
frontend/src/
├── components/
│   └── auth/
│       ├── __tests__/                 # Co-located tests
│       │   ├── login-form.test.tsx
│       │   └── register-form.test.tsx
│       ├── login-form.tsx
│       └── register-form.tsx
├── hooks/
│   └── __tests__/
│       └── use-responsive-layout.test.ts
├── lib/
│   └── stores/
│       └── __tests__/
│           └── auth-store.test.ts
├── test/                              # Shared test infrastructure
│   ├── setup.ts                       # Global test setup
│   ├── test-utils.tsx                 # Custom render and utilities
│   ├── mocks/                         # Shared mock definitions
│   │   ├── handlers.ts                # MSW handlers (if used)
│   │   └── stores.ts                  # Store mock factories
│   └── factories/                     # Test data factories
│       └── user-factory.ts
└── app/                               # Next.js App Router pages
    └── (dashboard)/
        └── __tests__/
            └── page.test.tsx
```

### 3.1 Key Directories

| Directory | Purpose |
|-----------|---------|
| `__tests__/` | Co-located test files for each module |
| `src/test/` | Shared test infrastructure |
| `src/test/setup.ts` | Global setup (DOM matchers, global mocks) |
| `src/test/test-utils.tsx` | Custom render function with providers |
| `src/test/mocks/` | Reusable mock definitions |
| `src/test/factories/` | Test data generation utilities |

---

## 4. Configuration

### 4.1 Vitest Configuration

**File**: `frontend/vitest.config.ts`

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["node_modules", "e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      exclude: [
        "node_modules/",
        "src/test/",
        "**/*.d.ts",
        "**/*.config.{ts,js}",
      ],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
    },
    testTimeout: 10000,
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
});
```

### 4.2 Global Setup

**File**: `frontend/src/test/setup.ts`

```typescript
import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// Mock next/navigation globally
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

// Mock next/image
vi.mock("next/image", () => ({
  default: ({ src, alt, ...props }: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src} alt={alt} {...props} />;
  },
}));

// Clean up after each test
afterEach(() => {
  vi.clearAllMocks();
});
```

### 4.3 Custom Render Function

**File**: `frontend/src/test/test-utils.tsx`

```typescript
import { render, RenderOptions } from "@testing-library/react";
import { ReactElement, ReactNode } from "react";

// Add providers here as needed
interface AllProvidersProps {
  children: ReactNode;
}

function AllProviders({ children }: AllProvidersProps) {
  return (
    // Wrap with providers (QueryClient, Theme, etc.) as needed
    <>{children}</>
  );
}

function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

// Re-export everything
export * from "@testing-library/react";
export { userEvent } from "@testing-library/user-event";

// Override render method
export { customRender as render };
```

---

## 5. Testing Patterns

### 5.1 Component Testing

**Pattern**: Test user-visible behavior, not implementation details.

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "../login-form";

// Mock dependencies
const mockLogin = vi.fn();
vi.mock("@/lib/stores/auth-store", () => ({
  useAuthStore: () => ({
    login: mockLogin,
    isLoading: false,
    error: null,
  }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email and password fields", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("submits form with valid credentials", async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce(undefined);

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("test@example.com", "password123");
    });
  });

  it("displays validation errors for empty fields", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
  });
});
```

### 5.2 Hook Testing

**Pattern**: Use `renderHook` for testing custom hooks.

```typescript
import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCounter } from "../use-counter";

describe("useCounter", () => {
  it("initializes with default value", () => {
    const { result } = renderHook(() => useCounter());

    expect(result.current.count).toBe(0);
  });

  it("increments counter", () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it("accepts initial value", () => {
    const { result } = renderHook(() => useCounter(10));

    expect(result.current.count).toBe(10);
  });
});
```

### 5.3 Zustand Store Testing

**Pattern**: Test stores in isolation and mock them in component tests.

```typescript
// Store isolation test
import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "../auth-store";

describe("authStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("sets user on successful login", async () => {
    const mockUser = { id: "1", email: "test@example.com" };

    // Mock the API call
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUser),
    } as Response);

    await useAuthStore.getState().login("test@example.com", "password");

    expect(useAuthStore.getState().user).toEqual(mockUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
});
```

### 5.4 Mocking Patterns

#### Mocking Next.js Router

```typescript
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
  }),
}));
```

#### Mocking Zustand Stores

```typescript
// Mock entire store
vi.mock("@/lib/stores/auth-store", () => ({
  useAuthStore: () => ({
    user: { id: "1", email: "test@example.com" },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

// Mock with selector support
vi.mock("@/lib/stores/auth-store", () => ({
  useAuthStore: vi.fn((selector) => {
    const state = {
      user: null,
      isAuthenticated: false,
    };
    return selector ? selector(state) : state;
  }),
}));
```

#### Mocking API Calls

```typescript
// Direct fetch mock
vi.spyOn(global, "fetch").mockResolvedValueOnce({
  ok: true,
  json: () => Promise.resolve({ data: "test" }),
} as Response);

// Or use MSW for more realistic API mocking
// See: https://mswjs.io/
```

#### Mocking Browser APIs

```typescript
// matchMedia
const createMatchMedia = (matches: Record<string, boolean>) => {
  return (query: string): MediaQueryList => ({
    matches: matches[query] ?? false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(() => true),
  });
};

window.matchMedia = createMatchMedia({
  "(min-width: 1024px)": true,
});

// localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });
```

---

## 6. Query Priority

Follow Testing Library's query priority to encourage accessible implementations:

### 6.1 Priority Order (Most to Least Preferred)

1. **Accessible to Everyone**
   - `getByRole` - Most preferred, queries by ARIA role
   - `getByLabelText` - For form fields
   - `getByPlaceholderText` - When label is not available
   - `getByText` - For non-interactive elements
   - `getByDisplayValue` - For inputs with values

2. **Semantic Queries**
   - `getByAltText` - For images
   - `getByTitle` - For elements with title attribute

3. **Test IDs (Last Resort)**
   - `getByTestId` - Only when no other query works

### 6.2 Examples

```typescript
// PREFERRED: Query by role
screen.getByRole("button", { name: /submit/i });
screen.getByRole("textbox", { name: /email/i });
screen.getByRole("link", { name: /sign up/i });

// GOOD: Query by label (form fields)
screen.getByLabelText(/email address/i);

// ACCEPTABLE: Query by text
screen.getByText(/welcome back/i);

// LAST RESORT: Query by test ID
screen.getByTestId("custom-dropdown");
```

---

## 7. Assertions

### 7.1 Common Assertions

```typescript
// Presence
expect(element).toBeInTheDocument();
expect(element).not.toBeInTheDocument();

// Visibility
expect(element).toBeVisible();
expect(element).not.toBeVisible();

// Attributes
expect(element).toHaveAttribute("disabled");
expect(element).toHaveClass("active");
expect(input).toHaveValue("test@example.com");

// Text content
expect(element).toHaveTextContent(/welcome/i);

// Accessibility
expect(element).toHaveAccessibleName("Submit form");
expect(element).toHaveAccessibleDescription("Click to submit");

// Form state
expect(input).toBeRequired();
expect(input).toBeInvalid();
expect(input).toBeValid();
```

### 7.2 Async Assertions

```typescript
// Wait for element to appear
await waitFor(() => {
  expect(screen.getByText(/success/i)).toBeInTheDocument();
});

// Wait for element to disappear
await waitFor(() => {
  expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
});

// Find (built-in waiting)
const element = await screen.findByText(/loaded content/i);
expect(element).toBeInTheDocument();
```

---

## 8. User Interactions

Always use `userEvent` over `fireEvent` for realistic user simulation:

```typescript
import userEvent from "@testing-library/user-event";

describe("UserInteractions", () => {
  it("handles user interactions correctly", async () => {
    // IMPORTANT: Setup userEvent at the start of each test
    const user = userEvent.setup();

    render(<MyComponent />);

    // Click
    await user.click(screen.getByRole("button"));

    // Type
    await user.type(screen.getByLabelText(/name/i), "John Doe");

    // Clear and type
    await user.clear(screen.getByLabelText(/email/i));
    await user.type(screen.getByLabelText(/email/i), "new@email.com");

    // Select option
    await user.selectOptions(screen.getByRole("combobox"), "option1");

    // Checkbox/Radio
    await user.click(screen.getByRole("checkbox"));

    // Keyboard
    await user.keyboard("{Enter}");
    await user.keyboard("{Tab}");

    // Hover
    await user.hover(screen.getByText(/hover me/i));
    await user.unhover(screen.getByText(/hover me/i));
  });
});
```

---

## 9. Test Data Factories

### 9.1 Factory Pattern

**File**: `frontend/src/test/factories/user-factory.ts`

```typescript
import { faker } from "@faker-js/faker";

interface User {
  id: string;
  email: string;
  name: string;
  role: "user" | "admin";
  createdAt: string;
}

export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    role: "user",
    createdAt: faker.date.past().toISOString(),
    ...overrides,
  };
}

export function createAdminUser(overrides: Partial<User> = {}): User {
  return createUser({ role: "admin", ...overrides });
}

// List factory
export function createUsers(count: number, overrides: Partial<User> = {}): User[] {
  return Array.from({ length: count }, () => createUser(overrides));
}
```

### 9.2 Usage

```typescript
import { createUser, createAdminUser } from "@/test/factories/user-factory";

describe("UserProfile", () => {
  it("displays user information", () => {
    const user = createUser({ name: "John Doe" });
    render(<UserProfile user={user} />);

    expect(screen.getByText("John Doe")).toBeInTheDocument();
  });

  it("shows admin badge for admin users", () => {
    const admin = createAdminUser();
    render(<UserProfile user={admin} />);

    expect(screen.getByText(/admin/i)).toBeInTheDocument();
  });
});
```

---

## 10. Running Tests

### 10.1 Commands

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test

# Run tests once (CI mode)
npm run test:run

# Run with coverage
npm run test:coverage

# Run specific file
npm test -- src/components/auth/__tests__/login-form.test.tsx

# Run tests matching pattern
npm test -- -t "LoginForm"

# Run with UI
npm test -- --ui
```

### 10.2 Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui"
  }
}
```

### 10.3 Makefile Integration

```makefile
test-frontend:
	cd frontend && npm run test:run

test-frontend-watch:
	cd frontend && npm test

test-frontend-coverage:
	cd frontend && npm run test:coverage
```

---

## 11. CI Integration

### 11.1 GitHub Actions

```yaml
frontend-test:
  name: Frontend Tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: "20"
        cache: "npm"
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: cd frontend && npm ci

    - name: Run lint
      run: cd frontend && npm run lint

    - name: Run type check
      run: cd frontend && npm run type-check

    - name: Run tests
      run: cd frontend && npm run test:run

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        files: frontend/coverage/lcov.info
        fail_ci_if_error: false
```

---

## 12. Quality Standards

### 12.1 Coverage Thresholds

| Metric | Minimum | Target |
|--------|---------|--------|
| Statements | 70% | 80% |
| Branches | 70% | 80% |
| Functions | 70% | 80% |
| Lines | 70% | 80% |

### 12.2 Test Quality Checklist

- [ ] Tests are deterministic (no random failures)
- [ ] Tests are isolated (no shared mutable state)
- [ ] Tests use accessible queries (role, label, text)
- [ ] Tests verify user-visible behavior, not implementation
- [ ] Tests have clear, descriptive names
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Async operations use proper waiting utilities
- [ ] Mocks are reset between tests

### 12.3 Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| Testing implementation details | Brittle tests that break on refactoring | Test observable behavior |
| Using `fireEvent` | Doesn't simulate real user behavior | Use `userEvent` |
| Using `container.querySelector` | Not accessible | Use Testing Library queries |
| Hardcoded waits (`setTimeout`) | Flaky and slow | Use `waitFor` or `findBy` |
| Testing third-party libraries | Waste of effort | Mock external dependencies |
| Giant test files | Hard to maintain | Co-locate with components |

---

## 13. Snapshot Testing

### 13.1 When to Use

- Testing static content that rarely changes
- Detecting unintended UI changes
- Testing complex output structures

### 13.2 When NOT to Use

- Dynamic content
- User interactions
- As a replacement for assertions

### 13.3 Example

```typescript
import { render } from "@/test/test-utils";
import { Icon } from "../icon";

describe("Icon", () => {
  it("renders home icon correctly", () => {
    const { container } = render(<Icon name="home" />);
    expect(container).toMatchSnapshot();
  });
});
```

### 13.4 Updating Snapshots

```bash
# Update all snapshots
npm test -- -u

# Update specific snapshots
npm test -- --update-snapshot src/components/icon/__tests__/icon.test.tsx
```

---

## 14. Debugging Tests

### 14.1 Debug Output

```typescript
import { render, screen } from "@/test/test-utils";

it("debugs component output", () => {
  render(<MyComponent />);

  // Print DOM to console
  screen.debug();

  // Print specific element
  screen.debug(screen.getByRole("button"));

  // Print with options
  screen.debug(undefined, Infinity); // Full output
});
```

### 14.2 Testing Playground

```typescript
import { render, screen } from "@/test/test-utils";

it("uses testing playground", () => {
  render(<MyComponent />);

  // Opens Testing Playground in browser
  screen.logTestingPlaygroundURL();
});
```

### 14.3 Vitest UI

```bash
# Run with interactive UI
npm test -- --ui
```

---

## 15. Accessibility Testing

### 15.1 Basic A11y Checks

```typescript
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

describe("Accessibility", () => {
  it("has no accessibility violations", async () => {
    const { container } = render(<MyComponent />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });
});
```

### 15.2 Setup

```bash
npm install --save-dev jest-axe @types/jest-axe
```

Add to `vitest.config.ts`:

```typescript
test: {
  setupFiles: ["./src/test/setup.ts", "./src/test/a11y-setup.ts"],
}
```

---

## 16. Migration Guide

### 16.1 From Jest to Vitest

| Jest | Vitest |
|------|--------|
| `jest.fn()` | `vi.fn()` |
| `jest.mock()` | `vi.mock()` |
| `jest.spyOn()` | `vi.spyOn()` |
| `jest.clearAllMocks()` | `vi.clearAllMocks()` |
| `jest.useFakeTimers()` | `vi.useFakeTimers()` |
| `beforeAll/afterAll` | Same |
| `beforeEach/afterEach` | Same |

### 16.2 Import Updates

```typescript
// Before (Jest)
import { jest } from "@jest/globals";

// After (Vitest)
import { vi } from "vitest";
```

---

## Appendix A: File Templates

### A.1 Component Test Template

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { ComponentName } from "../component-name";

// Mock dependencies if needed
vi.mock("@/lib/stores/some-store", () => ({
  useSomeStore: () => ({
    value: "test",
    action: vi.fn(),
  }),
}));

describe("ComponentName", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders correctly", () => {
    render(<ComponentName />);

    expect(screen.getByRole("heading")).toBeInTheDocument();
  });

  it("handles user interaction", async () => {
    const user = userEvent.setup();
    render(<ComponentName />);

    await user.click(screen.getByRole("button", { name: /click me/i }));

    await waitFor(() => {
      expect(screen.getByText(/clicked/i)).toBeInTheDocument();
    });
  });
});
```

### A.2 Hook Test Template

```typescript
import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useHookName } from "../use-hook-name";

describe("useHookName", () => {
  it("returns initial state", () => {
    const { result } = renderHook(() => useHookName());

    expect(result.current.value).toBe(initialValue);
  });

  it("updates state on action", () => {
    const { result } = renderHook(() => useHookName());

    act(() => {
      result.current.action();
    });

    expect(result.current.value).toBe(updatedValue);
  });
});
```

---

## Appendix B: Common Issues and Solutions

### B.1 "Cannot find module '@/...'"

**Solution**: Ensure `vitest.config.ts` has the correct alias:

```typescript
resolve: {
  alias: {
    "@": resolve(__dirname, "./src"),
  },
},
```

### B.2 "act() warning"

**Solution**: Wrap state updates in `act()` or use `waitFor`:

```typescript
// Using waitFor
await waitFor(() => {
  expect(screen.getByText(/updated/i)).toBeInTheDocument();
});

// Using act (for hooks)
act(() => {
  result.current.update();
});
```

### B.3 "Unable to find element with role..."

**Solution**: Use `screen.debug()` to see actual DOM, or check element roles:

```typescript
// Debug to see what's rendered
screen.debug();

// Check available roles
screen.getByRole(""); // Will show all available roles
```

### B.4 Tests Timing Out

**Solution**: Increase timeout in config or per-test:

```typescript
// Per-test
it("long running test", async () => {
  // test code
}, 30000);

// Or in vitest.config.ts
test: {
  testTimeout: 30000,
}
```

---

**Document End**
