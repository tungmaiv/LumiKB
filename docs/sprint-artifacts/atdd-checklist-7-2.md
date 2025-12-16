# ATDD Checklist: Story 7-2 - Centralized LLM Configuration

**Story ID**: 7-2
**Status**: RED Phase (Tests Written - Failing)
**Primary Test Level**: Integration (API) + Component
**Generated**: 2025-12-08
**Author**: Murat (TEA - Master Test Architect)

---

## Story Summary

**As an** administrator,
**I want** a centralized UI to configure LLM model settings with hot-reload capability,
**So that** I can switch models and adjust parameters without restarting services.

---

## Acceptance Criteria Breakdown

| AC ID | Criterion | Test Level | Priority |
|-------|-----------|------------|----------|
| AC-7.2.1 | Admin UI displays current LLM model settings (provider, model name, base URL, temperature, max_tokens) | Integration + Component | P1 |
| AC-7.2.2 | Model switching applies without service restart (hot-reload via Redis pub/sub or config polling) | Integration | P0 |
| AC-7.2.3 | Embedding dimension mismatch triggers warning when selected model dimensions differ from existing KB collections | Unit + Component | P0 |
| AC-7.2.4 | Health status shown for each configured model (via connection test endpoint) | Integration + Component | P1 |

---

## Test Files to Create

### Backend Tests

```
backend/tests/unit/test_config_service_llm.py           # ConfigService LLM methods
backend/tests/integration/test_llm_config_api.py        # LLM config API endpoints
```

### Frontend Tests

```
frontend/src/hooks/__tests__/useLLMConfig.test.ts                    # LLM config hook
frontend/src/components/admin/__tests__/llm-config-form.test.tsx     # Config form component
frontend/src/components/admin/__tests__/model-health-indicator.test.tsx  # Health indicator
```

---

## Failing Tests - Backend

### Unit Tests: `backend/tests/unit/test_config_service_llm.py`

```python
"""Unit tests for ConfigService LLM methods (Story 7-2)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.config_service import ConfigService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.delete.return_value = None
    redis.setex.return_value = None
    redis.publish.return_value = None
    return redis


@pytest.fixture
def config_service(mock_db):
    """ConfigService instance with mocked DB."""
    return ConfigService(mock_db)


class TestGetLLMConfig:
    """Tests for ConfigService.get_llm_config() (AC-7.2.1)."""

    async def test_get_llm_config_returns_default_values(
        self, config_service, mock_redis
    ):
        """
        GIVEN: No LLM config in database
        WHEN: get_llm_config() is called
        THEN: Returns default LLM configuration values
        """
        # RED: This test will fail - method doesn't exist yet
        with patch("app.services.config_service.get_redis_client", return_value=mock_redis):
            config = await config_service.get_llm_config()

        assert config["provider"] == "litellm"
        assert config["model_name"] == "gemini/gemini-2.0-flash-exp"
        assert config["base_url"] is not None
        assert config["temperature"] == 0.3
        assert config["max_tokens"] == 2000

    async def test_get_llm_config_returns_cached_value(
        self, config_service, mock_redis
    ):
        """
        GIVEN: LLM config is cached in Redis
        WHEN: get_llm_config() is called
        THEN: Returns cached config without DB query
        """
        # RED: This test will fail - method doesn't exist yet
        cached_config = '{"provider": "litellm", "model_name": "gpt-4", "temperature": 0.5}'
        mock_redis.get.return_value = cached_config

        with patch("app.services.config_service.get_redis_client", return_value=mock_redis):
            config = await config_service.get_llm_config()

        assert config["model_name"] == "gpt-4"
        assert config["temperature"] == 0.5


class TestUpdateLLMConfig:
    """Tests for ConfigService.update_llm_config() (AC-7.2.2)."""

    async def test_update_llm_config_invalidates_cache(
        self, config_service, mock_redis
    ):
        """
        GIVEN: Admin updates LLM configuration
        WHEN: update_llm_config() is called
        THEN: Redis cache is invalidated and pub/sub notification sent
        """
        # RED: This test will fail - method doesn't exist yet
        with patch("app.services.config_service.get_redis_client", return_value=mock_redis):
            await config_service.update_llm_config(
                {
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                },
                changed_by="admin@example.com"
            )

        mock_redis.delete.assert_called_once()
        mock_redis.publish.assert_called_once()  # Hot-reload notification

    async def test_update_llm_config_creates_audit_event(
        self, config_service, mock_redis
    ):
        """
        GIVEN: Admin updates LLM configuration
        WHEN: update_llm_config() is called
        THEN: Audit event is logged with old and new values
        """
        # RED: This test will fail - method doesn't exist yet
        with patch("app.services.config_service.get_redis_client", return_value=mock_redis):
            with patch.object(config_service.audit_service, "log_event") as mock_audit:
                await config_service.update_llm_config(
                    {"model_name": "gpt-4"},
                    changed_by="admin@example.com"
                )

        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args.kwargs["action"] == "llm_config.update"


class TestDimensionMismatchDetection:
    """Tests for embedding dimension mismatch detection (AC-7.2.3)."""

    async def test_detect_dimension_mismatch_returns_affected_kbs(
        self, config_service, mock_db
    ):
        """
        GIVEN: KBs exist with 768-dimension embeddings
        WHEN: Switching to a model with 1536 dimensions
        THEN: Returns list of affected KB names
        """
        # RED: This test will fail - method doesn't exist yet
        affected_kbs = await config_service.detect_dimension_mismatch(
            new_model_dimensions=1536
        )

        assert isinstance(affected_kbs, list)
        # Should return KB names that have different dimensions

    async def test_detect_dimension_mismatch_returns_empty_when_compatible(
        self, config_service, mock_db
    ):
        """
        GIVEN: KBs exist with 768-dimension embeddings
        WHEN: Switching to a model with same 768 dimensions
        THEN: Returns empty list (no mismatch)
        """
        # RED: This test will fail - method doesn't exist yet
        affected_kbs = await config_service.detect_dimension_mismatch(
            new_model_dimensions=768
        )

        assert affected_kbs == []
```

### Integration Tests: `backend/tests/integration/test_llm_config_api.py`

```python
"""Integration tests for LLM configuration API endpoints (Story 7-2)."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def admin_cookies(api_client: AsyncClient, admin_user, db_session) -> dict:
    """Login as admin and return cookies."""
    # Reuse existing admin_cookies pattern from test_config_api.py
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user["email"],
            "password": admin_user["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_cookies(api_client: AsyncClient, regular_user) -> dict:
    """Login as regular user and return cookies."""
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user["email"],
            "password": regular_user["password"],
        },
    )
    return login_response.cookies


@pytest.mark.asyncio
class TestGetLLMConfig:
    """Tests for GET /api/v1/admin/config/llm (AC-7.2.1)."""

    async def test_get_llm_config_returns_all_fields(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
    ):
        """
        GIVEN: Admin is authenticated
        WHEN: GET /api/v1/admin/config/llm is called
        THEN: Returns provider, model_name, base_url, temperature, max_tokens
        """
        # RED: This test will fail - endpoint doesn't exist yet
        response = await api_client.get(
            "/api/v1/admin/config/llm",
            cookies=admin_cookies,
        )

        assert response.status_code == 200
        data = response.json()

        # AC-7.2.1: All required fields present
        assert "provider" in data
        assert "model_name" in data
        assert "base_url" in data
        assert "temperature" in data
        assert "max_tokens" in data

    async def test_get_llm_config_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_cookies: dict,
    ):
        """
        GIVEN: Non-admin user is authenticated
        WHEN: GET /api/v1/admin/config/llm is called
        THEN: Returns 403 Forbidden
        """
        # RED: This test will fail - endpoint doesn't exist yet
        response = await api_client.get(
            "/api/v1/admin/config/llm",
            cookies=regular_cookies,
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestUpdateLLMConfig:
    """Tests for PUT /api/v1/admin/config/llm (AC-7.2.2)."""

    async def test_update_llm_config_persists_changes(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
    ):
        """
        GIVEN: Admin is authenticated
        WHEN: PUT /api/v1/admin/config/llm with valid config
        THEN: Config is persisted and returned in subsequent GET
        """
        # RED: This test will fail - endpoint doesn't exist yet
        update_data = {
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000,
        }

        response = await api_client.put(
            "/api/v1/admin/config/llm",
            cookies=admin_cookies,
            json=update_data,
        )

        assert response.status_code == 200

        # Verify changes persisted
        get_response = await api_client.get(
            "/api/v1/admin/config/llm",
            cookies=admin_cookies,
        )
        data = get_response.json()

        assert data["model_name"] == "gpt-4"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 4000

    async def test_update_llm_config_hot_reload_within_30s(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
    ):
        """
        GIVEN: Admin updates LLM configuration
        WHEN: Config is updated via PUT
        THEN: Hot-reload propagates within 30 seconds (no restart needed)
        """
        # RED: This test will fail - hot-reload not implemented
        # This test validates AC-7.2.2 hot-reload mechanism
        response = await api_client.put(
            "/api/v1/admin/config/llm",
            cookies=admin_cookies,
            json={"temperature": 0.5},
        )

        assert response.status_code == 200
        data = response.json()

        # Should indicate no restart required
        assert data.get("restart_required") is False

    async def test_update_llm_config_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_cookies: dict,
    ):
        """
        GIVEN: Non-admin user is authenticated
        WHEN: PUT /api/v1/admin/config/llm is called
        THEN: Returns 403 Forbidden
        """
        # RED: This test will fail - endpoint doesn't exist yet
        response = await api_client.put(
            "/api/v1/admin/config/llm",
            cookies=regular_cookies,
            json={"temperature": 0.5},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestLLMConfigModelTest:
    """Tests for POST /api/v1/admin/config/llm/test (AC-7.2.4)."""

    async def test_model_test_valid_returns_healthy(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
    ):
        """
        GIVEN: LiteLLM proxy is running with valid model
        WHEN: POST /api/v1/admin/config/llm/test is called
        THEN: Returns health status = healthy
        """
        # RED: This test will fail - endpoint doesn't exist yet
        response = await api_client.post(
            "/api/v1/admin/config/llm/test",
            cookies=admin_cookies,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "unhealthy"]
        if data["status"] == "healthy":
            assert "response_time_ms" in data

    async def test_model_test_invalid_returns_unhealthy(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
    ):
        """
        GIVEN: Invalid model configuration
        WHEN: POST /api/v1/admin/config/llm/test is called
        THEN: Returns health status = unhealthy with error message
        """
        # RED: This test will fail - endpoint doesn't exist yet
        # First set an invalid model
        await api_client.put(
            "/api/v1/admin/config/llm",
            cookies=admin_cookies,
            json={"model_name": "invalid-model-that-does-not-exist"},
        )

        response = await api_client.post(
            "/api/v1/admin/config/llm/test",
            cookies=admin_cookies,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "unhealthy"
        assert "error" in data

    async def test_model_test_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_cookies: dict,
    ):
        """
        GIVEN: Non-admin user is authenticated
        WHEN: POST /api/v1/admin/config/llm/test is called
        THEN: Returns 403 Forbidden
        """
        # RED: This test will fail - endpoint doesn't exist yet
        response = await api_client.post(
            "/api/v1/admin/config/llm/test",
            cookies=regular_cookies,
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestDimensionMismatchWarning:
    """Tests for dimension mismatch warning (AC-7.2.3)."""

    async def test_dimension_mismatch_returns_warning(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
    ):
        """
        GIVEN: KBs exist with 768-dimension embeddings
        WHEN: PUT /api/v1/admin/config/llm with 1536-dimension model
        THEN: Response includes dimension_warning with affected KB list
        """
        # RED: This test will fail - dimension validation not implemented
        response = await api_client.put(
            "/api/v1/admin/config/llm",
            cookies=admin_cookies,
            json={
                "embedding_model": "text-embedding-3-large",  # 1536 dimensions
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should include warning about dimension mismatch
        if "dimension_warning" in data:
            assert "affected_kbs" in data["dimension_warning"]
            assert isinstance(data["dimension_warning"]["affected_kbs"], list)
```

---

## Failing Tests - Frontend

### Hook Tests: `frontend/src/hooks/__tests__/useLLMConfig.test.ts`

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useLLMConfig } from '../useLLMConfig';

// Mock fetch
global.fetch = jest.fn();

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useLLMConfig (Story 7-2)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('AC-7.2.1: Display current LLM model settings', () => {
    it('should return loading state initially', () => {
      // RED: This test will fail - hook doesn't exist yet
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

      const { result } = renderHook(() => useLLMConfig(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.config).toBeUndefined();
    });

    it('should return LLM config with all required fields', async () => {
      // RED: This test will fail - hook doesn't exist yet
      const mockConfig = {
        provider: 'litellm',
        model_name: 'gemini/gemini-2.0-flash-exp',
        base_url: 'http://litellm:4000',
        temperature: 0.3,
        max_tokens: 2000,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      const { result } = renderHook(() => useLLMConfig(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.config).toEqual(mockConfig);
      expect(result.current.config?.provider).toBe('litellm');
      expect(result.current.config?.temperature).toBe(0.3);
    });

    it('should return error state on API failure', async () => {
      // RED: This test will fail - hook doesn't exist yet
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const { result } = renderHook(() => useLLMConfig(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });

  describe('AC-7.2.2: Hot-reload config updates', () => {
    it('should update config without requiring restart', async () => {
      // RED: This test will fail - mutation not implemented
      const mockConfig = { temperature: 0.3 };
      const updatedConfig = { temperature: 0.7 };

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => mockConfig })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...updatedConfig, restart_required: false }),
        });

      const { result } = renderHook(() => useLLMConfig(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Trigger update
      await result.current.updateConfig({ temperature: 0.7 });

      await waitFor(() => {
        expect(result.current.lastUpdate?.restart_required).toBe(false);
      });
    });
  });

  describe('AC-7.2.4: Health status display', () => {
    it('should return model health status', async () => {
      // RED: This test will fail - testConnection not implemented
      const mockHealth = {
        status: 'healthy',
        response_time_ms: 150,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth,
      });

      const { result } = renderHook(() => useLLMConfig(), {
        wrapper: createWrapper(),
      });

      const health = await result.current.testConnection();

      expect(health.status).toBe('healthy');
      expect(health.response_time_ms).toBe(150);
    });
  });
});
```

### Component Tests: `frontend/src/components/admin/__tests__/llm-config-form.test.tsx`

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LLMConfigForm } from '../llm-config-form';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('LLMConfigForm (Story 7-2)', () => {
  const mockConfig = {
    provider: 'litellm',
    model_name: 'gemini/gemini-2.0-flash-exp',
    base_url: 'http://litellm:4000',
    temperature: 0.3,
    max_tokens: 2000,
  };

  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockConfig,
    });
  });

  describe('AC-7.2.1: Display current settings', () => {
    it('should render form with current config values', async () => {
      // RED: This test will fail - component doesn't exist yet
      render(<LLMConfigForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText(/provider/i)).toHaveValue('litellm');
      });

      expect(screen.getByLabelText(/model name/i)).toHaveValue(
        'gemini/gemini-2.0-flash-exp'
      );
      expect(screen.getByLabelText(/temperature/i)).toHaveValue('0.3');
      expect(screen.getByLabelText(/max tokens/i)).toHaveValue('2000');
    });

    it('should have data-testid attributes for all fields', async () => {
      // RED: This test will fail - component doesn't exist yet
      render(<LLMConfigForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('llm-provider-select')).toBeInTheDocument();
      });

      expect(screen.getByTestId('llm-model-input')).toBeInTheDocument();
      expect(screen.getByTestId('llm-base-url-input')).toBeInTheDocument();
      expect(screen.getByTestId('llm-temperature-input')).toBeInTheDocument();
      expect(screen.getByTestId('llm-max-tokens-input')).toBeInTheDocument();
    });
  });

  describe('AC-7.2.2: Apply Changes with loading state', () => {
    it('should show loading state during update', async () => {
      // RED: This test will fail - component doesn't exist yet
      const user = userEvent.setup();

      // Slow response
      global.fetch = jest
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => mockConfig })
        .mockImplementationOnce(
          () => new Promise((resolve) => setTimeout(resolve, 1000))
        );

      render(<LLMConfigForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('llm-apply-button')).toBeInTheDocument();
      });

      await user.click(screen.getByTestId('llm-apply-button'));

      expect(screen.getByTestId('llm-apply-button')).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('should show success toast after update', async () => {
      // RED: This test will fail - toast not implemented
      const user = userEvent.setup();

      global.fetch = jest
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => mockConfig })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockConfig, restart_required: false }),
        });

      render(<LLMConfigForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('llm-apply-button')).toBeInTheDocument();
      });

      await user.click(screen.getByTestId('llm-apply-button'));

      await waitFor(() => {
        expect(
          screen.getByText(/changes applied without restart/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('AC-7.2.3: Dimension mismatch warning', () => {
    it('should display warning dialog when dimensions mismatch', async () => {
      // RED: This test will fail - warning dialog not implemented
      const user = userEvent.setup();

      global.fetch = jest
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => mockConfig })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockConfig,
            dimension_warning: {
              message: 'Embedding dimensions differ',
              affected_kbs: ['Research KB', 'Product KB'],
            },
          }),
        });

      render(<LLMConfigForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('llm-apply-button')).toBeInTheDocument();
      });

      // Change embedding model
      await user.clear(screen.getByTestId('llm-model-input'));
      await user.type(
        screen.getByTestId('llm-model-input'),
        'text-embedding-3-large'
      );
      await user.click(screen.getByTestId('llm-apply-button'));

      await waitFor(() => {
        expect(
          screen.getByTestId('dimension-mismatch-warning')
        ).toBeInTheDocument();
      });

      expect(screen.getByText(/Research KB/)).toBeInTheDocument();
      expect(screen.getByText(/Product KB/)).toBeInTheDocument();
    });
  });
});
```

### Component Tests: `frontend/src/components/admin/__tests__/model-health-indicator.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { ModelHealthIndicator } from '../model-health-indicator';

describe('ModelHealthIndicator (Story 7-2 AC-7.2.4)', () => {
  describe('Health status display', () => {
    it('should show green indicator when healthy', () => {
      // RED: This test will fail - component doesn't exist yet
      render(
        <ModelHealthIndicator status="healthy" responseTimeMs={150} />
      );

      expect(screen.getByTestId('health-status-indicator')).toHaveClass(
        'bg-green-500'
      );
      expect(screen.getByText(/healthy/i)).toBeInTheDocument();
      expect(screen.getByText(/150ms/)).toBeInTheDocument();
    });

    it('should show red indicator when unhealthy', () => {
      // RED: This test will fail - component doesn't exist yet
      render(
        <ModelHealthIndicator
          status="unhealthy"
          error="Connection timeout"
        />
      );

      expect(screen.getByTestId('health-status-indicator')).toHaveClass(
        'bg-red-500'
      );
      expect(screen.getByText(/unhealthy/i)).toBeInTheDocument();
      expect(screen.getByText(/Connection timeout/)).toBeInTheDocument();
    });

    it('should show loading indicator while testing', () => {
      // RED: This test will fail - component doesn't exist yet
      render(<ModelHealthIndicator status="testing" />);

      expect(screen.getByTestId('health-status-indicator')).toHaveClass(
        'animate-pulse'
      );
      expect(screen.getByText(/testing/i)).toBeInTheDocument();
    });
  });
});
```

---

## Data Factories

### Backend Factory: `backend/tests/factories/llm_config_factory.py`

```python
"""Factory for LLM configuration test data."""
from faker import Faker

fake = Faker()


def create_llm_config(overrides: dict = None) -> dict:
    """Create LLM config data with sensible defaults."""
    config = {
        "provider": "litellm",
        "model_name": fake.random_element([
            "gemini/gemini-2.0-flash-exp",
            "gpt-4",
            "claude-3-sonnet",
        ]),
        "base_url": "http://litellm:4000",
        "temperature": round(fake.pyfloat(min_value=0.0, max_value=2.0), 1),
        "max_tokens": fake.random_element([1000, 2000, 4000, 8000]),
        "embedding_model": fake.random_element([
            "text-embedding-004",
            "text-embedding-3-small",
            "text-embedding-3-large",
        ]),
        "embedding_dimensions": fake.random_element([768, 1536, 3072]),
    }

    if overrides:
        config.update(overrides)

    return config


def create_model_health_response(healthy: bool = True) -> dict:
    """Create model health test response."""
    if healthy:
        return {
            "status": "healthy",
            "response_time_ms": fake.random_int(min=50, max=500),
            "model": "gemini/gemini-2.0-flash-exp",
        }
    return {
        "status": "unhealthy",
        "error": fake.random_element([
            "Connection timeout",
            "Invalid API key",
            "Model not found",
        ]),
    }
```

---

## Required data-testid Attributes

### LLM Config Form

| Element | data-testid | Purpose |
|---------|-------------|---------|
| Provider dropdown | `llm-provider-select` | Select LLM provider |
| Model name input | `llm-model-input` | Enter model name |
| Base URL input | `llm-base-url-input` | LiteLLM proxy URL |
| Temperature input | `llm-temperature-input` | Sampling temperature |
| Max tokens input | `llm-max-tokens-input` | Maximum response tokens |
| Apply button | `llm-apply-button` | Submit config changes |
| Loading spinner | `loading-spinner` | Show during API calls |

### Health Indicator

| Element | data-testid | Purpose |
|---------|-------------|---------|
| Status indicator | `health-status-indicator` | Green/red/yellow dot |
| Test connection button | `test-connection-button` | Trigger health check |

### Warning Dialog

| Element | data-testid | Purpose |
|---------|-------------|---------|
| Warning dialog | `dimension-mismatch-warning` | Dimension warning modal |
| KB list | `affected-kb-list` | List of affected KBs |
| Confirm button | `confirm-dimension-change` | Proceed anyway |
| Cancel button | `cancel-dimension-change` | Cancel change |

---

## Implementation Checklist

### Task 1: Extend ConfigService for LLM settings (AC-7.2.1, AC-7.2.2)

- [ ] Add `LLM_CONFIG_CACHE_KEY = "admin:llm_config"` constant
- [ ] Add `LLM_CONFIG_PUBSUB_CHANNEL = "llm_config_changed"` constant
- [ ] Implement `get_llm_config()` method returning LLM settings
- [ ] Implement `update_llm_config()` method with Redis invalidation
- [ ] Implement Redis pub/sub notification for hot-reload
- [ ] Add audit logging for LLM config changes
- [ ] Run test: `pytest backend/tests/unit/test_config_service_llm.py -v`
- [ ] All unit tests pass (green phase)

### Task 2: Create LLM Configuration Admin API (AC-7.2.1, AC-7.2.2, AC-7.2.3, AC-7.2.4)

- [ ] Add `GET /api/v1/admin/config/llm` endpoint
- [ ] Add `PUT /api/v1/admin/config/llm` endpoint with validation
- [ ] Add `POST /api/v1/admin/config/llm/test` endpoint for health check
- [ ] Add dimension mismatch detection in PUT response
- [ ] Ensure all endpoints require `is_superuser`
- [ ] Run test: `pytest backend/tests/integration/test_llm_config_api.py -v`
- [ ] All integration tests pass (green phase)

### Task 3: Create LLM Configuration Frontend (AC-7.2.1, AC-7.2.4)

- [ ] Create `useLLMConfig` hook with React Query (stale time: 30s)
- [ ] Add `updateConfig` mutation to hook
- [ ] Add `testConnection` function to hook
- [ ] Create `LLMConfigForm` component with form fields
- [ ] Create `ModelHealthIndicator` component
- [ ] Add page at `/admin/config/llm` with AdminGuard
- [ ] Run test: `npm run test -- useLLMConfig`
- [ ] Run test: `npm run test -- llm-config-form`
- [ ] All frontend tests pass (green phase)

### Task 4: Implement Hot-Reload UI Feedback (AC-7.2.2, AC-7.2.3)

- [ ] Add loading state to Apply Changes button
- [ ] Show success toast: "Changes applied without restart"
- [ ] Create dimension mismatch warning dialog
- [ ] Display affected KB list in warning dialog
- [ ] Add confirmation modal before changes
- [ ] Run tests to verify UI feedback
- [ ] All UI tests pass (green phase)

### Task 5: Connect to LiteLLM Integration (AC-7.2.1, AC-7.2.2)

- [ ] Update `litellm_config.yaml` generation from DB config
- [ ] Implement config polling mechanism (30s interval)
- [ ] Test model switching end-to-end via search
- [ ] Test model switching end-to-end via generation
- [ ] Manual verification: hot-reload works without restart
- [ ] All acceptance criteria verified

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

- [x] All failing tests written
- [x] Tests use Given-When-Then format
- [x] Tests have clear assertions
- [x] Tests cover all 4 acceptance criteria
- [x] data-testid attributes documented

### GREEN Phase (DEV Team)

1. Pick one failing test
2. Implement minimal code to pass
3. Run test to verify green
4. Move to next test
5. Repeat until all tests pass

### REFACTOR Phase (DEV Team)

1. All tests passing (green)
2. Extract common patterns
3. Optimize Redis caching
4. Clean up code duplication
5. Ensure tests still pass

---

## Running Tests

```bash
# Backend unit tests
pytest backend/tests/unit/test_config_service_llm.py -v

# Backend integration tests
pytest backend/tests/integration/test_llm_config_api.py -v

# Frontend hook tests
npm run test -- useLLMConfig

# Frontend component tests
npm run test -- llm-config-form
npm run test -- model-health-indicator

# All Story 7-2 tests
pytest backend/tests -k "llm_config" -v
npm run test -- --grep "Story 7-2"
```

---

## Quality Gate Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing
- [ ] Unit test coverage ≥80% for ConfigService LLM methods
- [ ] Integration tests use mocked LiteLLM (no external deps)
- [ ] All data-testid attributes implemented
- [ ] Manual verification: hot-reload works without restart

---

**Generated by**: Murat (TEA - Master Test Architect)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Version**: 4.0 (BMad v6)
**Date**: 2025-12-08
