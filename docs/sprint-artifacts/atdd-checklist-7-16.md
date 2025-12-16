# ATDD Checklist: Story 7-16 KB Settings Presets

**Story ID:** 7.16
**Title:** KB Settings Presets
**Generated:** 2025-12-09
**Generator:** TEA (Test Engineering Architect)
**Status:** RED (Failing Tests - Implementation Required)

---

## Story Summary

**As a** KB owner
**I want** preset configurations to quickly optimize my KB for common use cases
**So that** I don't have to manually configure each individual setting

---

## Acceptance Criteria Coverage

| AC ID | Description | Test Level | Test File |
|-------|-------------|------------|-----------|
| 7.16.1 | Quick Preset dropdown with Custom, Legal, Technical, Creative, Code, General | Component, E2E | `preset-selector.test.tsx`, `kb-settings-presets.spec.ts` |
| 7.16.2 | Legal preset: temp 0.3, chunk 1000, overlap 200, footnote, acknowledge | Unit, Component | `test_kb_presets.py`, `preset-selector.test.tsx` |
| 7.16.3 | Technical preset: temp 0.5, chunk 800, overlap 100, inline | Unit, Component | `test_kb_presets.py`, `preset-selector.test.tsx` |
| 7.16.4 | Creative preset: temp 0.9, top_p 0.95, chunk 500, best_effort | Unit, Component | `test_kb_presets.py`, `preset-selector.test.tsx` |
| 7.16.5 | Code preset: temp 0.2, chunk 600, overlap 50 | Unit, Component | `test_kb_presets.py`, `preset-selector.test.tsx` |
| 7.16.6 | General preset: system defaults | Unit, Component | `test_kb_presets.py`, `preset-selector.test.tsx` |
| 7.16.7 | Confirmation dialog warns about overwriting custom settings | Component, E2E | `preset-selector.test.tsx`, `kb-settings-presets.spec.ts` |
| 7.16.8 | Preset indicator shows matching preset or "Custom" | Component, E2E | `preset-selector.test.tsx`, `kb-settings-presets.spec.ts` |

---

## Test Files to Create

### 1. Backend Unit Tests (pytest)

**File:** `backend/tests/unit/test_kb_presets.py`

```python
"""
Story 7-16 ATDD: KB Presets Unit Tests
Generated: 2025-12-09
Status: RED - Implementation required to pass

Required implementation:
- backend/app/core/kb_presets.py
"""

import pytest
from app.core.kb_presets import (
    get_preset,
    list_presets,
    detect_preset,
    PRESET_LEGAL,
    PRESET_TECHNICAL,
    PRESET_CREATIVE,
    PRESET_CODE,
    PRESET_GENERAL,
)
from app.schemas.kb_settings import KBSettings, ChunkingConfig, GenerationConfig


class TestGetPreset:
    """[P0] Test preset retrieval by name."""

    def test_get_legal_preset_returns_correct_config(self):
        """
        GIVEN: Request for 'legal' preset
        WHEN: get_preset('legal') is called
        THEN: Returns config with temperature=0.3, chunk_size=1000, etc.
        AC-7.16.2
        """
        preset = get_preset("legal")

        assert preset is not None
        assert preset.generation.temperature == 0.3
        assert preset.chunking.chunk_size == 1000
        assert preset.chunking.chunk_overlap == 200
        assert preset.prompts.citation_style == "footnote"
        assert preset.prompts.uncertainty_handling == "acknowledge"

    def test_get_technical_preset_returns_correct_config(self):
        """
        GIVEN: Request for 'technical' preset
        WHEN: get_preset('technical') is called
        THEN: Returns config with temperature=0.5, chunk_size=800, etc.
        AC-7.16.3
        """
        preset = get_preset("technical")

        assert preset is not None
        assert preset.generation.temperature == 0.5
        assert preset.chunking.chunk_size == 800
        assert preset.chunking.chunk_overlap == 100
        assert preset.prompts.citation_style == "inline"

    def test_get_creative_preset_returns_correct_config(self):
        """
        GIVEN: Request for 'creative' preset
        WHEN: get_preset('creative') is called
        THEN: Returns config with temperature=0.9, top_p=0.95, etc.
        AC-7.16.4
        """
        preset = get_preset("creative")

        assert preset is not None
        assert preset.generation.temperature == 0.9
        assert preset.generation.top_p == 0.95
        assert preset.chunking.chunk_size == 500
        assert preset.prompts.uncertainty_handling == "best_effort"

    def test_get_code_preset_returns_correct_config(self):
        """
        GIVEN: Request for 'code' preset
        WHEN: get_preset('code') is called
        THEN: Returns config with temperature=0.2, chunk_size=600, etc.
        AC-7.16.5
        """
        preset = get_preset("code")

        assert preset is not None
        assert preset.generation.temperature == 0.2
        assert preset.chunking.chunk_size == 600
        assert preset.chunking.chunk_overlap == 50

    def test_get_general_preset_returns_defaults(self):
        """
        GIVEN: Request for 'general' preset
        WHEN: get_preset('general') is called
        THEN: Returns system default config
        AC-7.16.6
        """
        preset = get_preset("general")
        default = KBSettings()

        assert preset is not None
        assert preset.generation.temperature == default.generation.temperature
        assert preset.chunking.chunk_size == default.chunking.chunk_size

    def test_get_preset_invalid_name_returns_none(self):
        """
        GIVEN: Request for unknown preset
        WHEN: get_preset('unknown') is called
        THEN: Returns None
        """
        preset = get_preset("unknown")
        assert preset is None


class TestListPresets:
    """[P0] Test preset listing functionality."""

    def test_list_presets_returns_all_presets(self):
        """
        GIVEN: Preset system initialized
        WHEN: list_presets() is called
        THEN: Returns all 5 presets with metadata
        AC-7.16.1
        """
        presets = list_presets()

        assert len(presets) == 5
        preset_ids = [p["id"] for p in presets]
        assert "legal" in preset_ids
        assert "technical" in preset_ids
        assert "creative" in preset_ids
        assert "code" in preset_ids
        assert "general" in preset_ids

    def test_list_presets_includes_descriptions(self):
        """
        GIVEN: Preset system initialized
        WHEN: list_presets() is called
        THEN: Each preset has name and description
        """
        presets = list_presets()

        for preset in presets:
            assert "id" in preset
            assert "name" in preset
            assert "description" in preset
            assert len(preset["description"]) > 10  # Meaningful description


class TestDetectPreset:
    """[P1] Test preset detection from settings."""

    def test_detect_preset_matches_legal(self):
        """
        GIVEN: Settings matching legal preset exactly
        WHEN: detect_preset(settings) is called
        THEN: Returns 'legal'
        AC-7.16.8
        """
        legal_preset = get_preset("legal")
        detected = detect_preset(legal_preset)

        assert detected == "legal"

    def test_detect_preset_matches_technical(self):
        """
        GIVEN: Settings matching technical preset exactly
        WHEN: detect_preset(settings) is called
        THEN: Returns 'technical'
        """
        technical_preset = get_preset("technical")
        detected = detect_preset(technical_preset)

        assert detected == "technical"

    def test_detect_preset_returns_custom_for_modified_settings(self):
        """
        GIVEN: Settings modified from any preset
        WHEN: detect_preset(settings) is called
        THEN: Returns 'custom'
        AC-7.16.8
        """
        # Start with legal preset but modify one value
        settings = get_preset("legal")
        settings.generation.temperature = 0.35  # Slightly different

        detected = detect_preset(settings)

        assert detected == "custom"

    def test_detect_preset_returns_custom_for_empty_settings(self):
        """
        GIVEN: Default empty settings (not matching any preset)
        WHEN: detect_preset(settings) is called
        THEN: Returns 'custom' or 'general' based on match
        """
        settings = KBSettings()
        detected = detect_preset(settings)

        # Should match general (defaults) or be custom
        assert detected in ["general", "custom"]


class TestPresetConstants:
    """[P2] Test preset constant definitions."""

    def test_preset_legal_constant_defined(self):
        """AC-7.16.2: Legal preset exists."""
        assert PRESET_LEGAL is not None
        assert PRESET_LEGAL["id"] == "legal"

    def test_preset_technical_constant_defined(self):
        """AC-7.16.3: Technical preset exists."""
        assert PRESET_TECHNICAL is not None
        assert PRESET_TECHNICAL["id"] == "technical"

    def test_preset_creative_constant_defined(self):
        """AC-7.16.4: Creative preset exists."""
        assert PRESET_CREATIVE is not None
        assert PRESET_CREATIVE["id"] == "creative"

    def test_preset_code_constant_defined(self):
        """AC-7.16.5: Code preset exists."""
        assert PRESET_CODE is not None
        assert PRESET_CODE["id"] == "code"

    def test_preset_general_constant_defined(self):
        """AC-7.16.6: General preset exists."""
        assert PRESET_GENERAL is not None
        assert PRESET_GENERAL["id"] == "general"
```

### 2. Backend Integration Tests (pytest)

**File:** `backend/tests/integration/test_kb_presets_api.py`

```python
"""
Story 7-16 ATDD: KB Presets API Integration Tests
Generated: 2025-12-09
Status: RED - Implementation required to pass

Required implementation:
- backend/app/api/v1/kb_presets.py (or extend knowledge_bases.py)
"""

import pytest
from httpx import AsyncClient


class TestGetPresetsEndpoint:
    """[P0] Test GET /api/v1/kb-presets endpoint."""

    @pytest.mark.asyncio
    async def test_get_presets_returns_all_presets(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        GIVEN: Authenticated user
        WHEN: GET /api/v1/kb-presets
        THEN: Returns list of all 5 presets
        AC-7.16.1
        """
        response = await client.get(
            "/api/v1/kb-presets",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert len(data["presets"]) == 5

    @pytest.mark.asyncio
    async def test_get_presets_includes_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        GIVEN: Authenticated user
        WHEN: GET /api/v1/kb-presets
        THEN: Each preset has id, name, description
        """
        response = await client.get(
            "/api/v1/kb-presets",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for preset in data["presets"]:
            assert "id" in preset
            assert "name" in preset
            assert "description" in preset

    @pytest.mark.asyncio
    async def test_get_presets_unauthenticated_returns_401(
        self, client: AsyncClient
    ):
        """
        GIVEN: Unauthenticated request
        WHEN: GET /api/v1/kb-presets
        THEN: Returns 401 Unauthorized
        """
        response = await client.get("/api/v1/kb-presets")

        assert response.status_code == 401


class TestGetPresetByIdEndpoint:
    """[P1] Test GET /api/v1/kb-presets/{preset_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_legal_preset_returns_full_config(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        GIVEN: Authenticated user
        WHEN: GET /api/v1/kb-presets/legal
        THEN: Returns full legal preset configuration
        AC-7.16.2
        """
        response = await client.get(
            "/api/v1/kb-presets/legal",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "legal"
        assert data["config"]["generation"]["temperature"] == 0.3
        assert data["config"]["chunking"]["chunk_size"] == 1000
        assert data["config"]["chunking"]["chunk_overlap"] == 200
        assert data["config"]["prompts"]["citation_style"] == "footnote"

    @pytest.mark.asyncio
    async def test_get_unknown_preset_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        GIVEN: Authenticated user
        WHEN: GET /api/v1/kb-presets/unknown
        THEN: Returns 404 Not Found
        """
        response = await client.get(
            "/api/v1/kb-presets/unknown",
            headers=auth_headers,
        )

        assert response.status_code == 404
```

### 3. Frontend Component Tests (Vitest + RTL)

**File:** `frontend/src/components/kb/settings/__tests__/preset-selector.test.tsx`

```typescript
/**
 * Story 7-16 ATDD: PresetSelector Component Tests
 * Generated: 2025-12-09
 * Status: RED - Implementation required to pass
 *
 * Required implementation:
 * - frontend/src/components/kb/settings/preset-selector.tsx
 * - frontend/src/lib/kb-presets.ts
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PresetSelector } from '../preset-selector';
import { PRESETS } from '@/lib/kb-presets';

interface KBSettings {
  chunking: {
    strategy: string;
    chunk_size: number;
    chunk_overlap: number;
  };
  generation: {
    temperature: number;
    top_p: number;
    max_tokens: number;
  };
  prompts: {
    citation_style: string;
    uncertainty_handling: string;
  };
  preset?: string | null;
}

const defaultSettings: KBSettings = {
  chunking: {
    strategy: 'recursive',
    chunk_size: 512,
    chunk_overlap: 50,
  },
  generation: {
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
  },
  prompts: {
    citation_style: 'inline',
    uncertainty_handling: 'acknowledge',
  },
  preset: null,
};

describe('PresetSelector', () => {
  const mockOnPresetSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] AC-7.16.1: Preset Dropdown', () => {
    it('renders preset dropdown with all options', async () => {
      /**
       * GIVEN: PresetSelector rendered
       * WHEN: User opens dropdown
       * THEN: All preset options are visible (Custom, Legal, Technical, Creative, Code, General)
       */
      const user = userEvent.setup();
      render(
        <PresetSelector
          currentSettings={defaultSettings}
          onPresetSelect={mockOnPresetSelect}
        />
      );

      await user.click(screen.getByTestId('preset-selector-trigger'));

      expect(screen.getByRole('option', { name: /custom/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /legal/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /technical/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /creative/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /code/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /general/i })).toBeInTheDocument();
    });

    it('displays preset descriptions in dropdown', async () => {
      /**
       * GIVEN: PresetSelector rendered
       * WHEN: Dropdown is open
       * THEN: Each preset shows description
       */
      const user = userEvent.setup();
      render(
        <PresetSelector
          currentSettings={defaultSettings}
          onPresetSelect={mockOnPresetSelect}
        />
      );

      await user.click(screen.getByTestId('preset-selector-trigger'));

      // Legal preset description mentions legal documents
      expect(screen.getByText(/legal document/i)).toBeInTheDocument();
      // Creative preset description mentions creativity
      expect(screen.getByText(/creative|creativity/i)).toBeInTheDocument();
    });
  });

  describe('[P0] AC-7.16.2-6: Preset Values', () => {
    it('Legal preset has correct values', () => {
      /**
       * AC-7.16.2: Legal preset configuration
       */
      const legalPreset = PRESETS.find((p) => p.id === 'legal');

      expect(legalPreset).toBeDefined();
      expect(legalPreset?.config.generation.temperature).toBe(0.3);
      expect(legalPreset?.config.chunking.chunk_size).toBe(1000);
      expect(legalPreset?.config.chunking.chunk_overlap).toBe(200);
      expect(legalPreset?.config.prompts.citation_style).toBe('footnote');
      expect(legalPreset?.config.prompts.uncertainty_handling).toBe('acknowledge');
    });

    it('Technical preset has correct values', () => {
      /**
       * AC-7.16.3: Technical preset configuration
       */
      const technicalPreset = PRESETS.find((p) => p.id === 'technical');

      expect(technicalPreset).toBeDefined();
      expect(technicalPreset?.config.generation.temperature).toBe(0.5);
      expect(technicalPreset?.config.chunking.chunk_size).toBe(800);
      expect(technicalPreset?.config.chunking.chunk_overlap).toBe(100);
      expect(technicalPreset?.config.prompts.citation_style).toBe('inline');
    });

    it('Creative preset has correct values', () => {
      /**
       * AC-7.16.4: Creative preset configuration
       */
      const creativePreset = PRESETS.find((p) => p.id === 'creative');

      expect(creativePreset).toBeDefined();
      expect(creativePreset?.config.generation.temperature).toBe(0.9);
      expect(creativePreset?.config.generation.top_p).toBe(0.95);
      expect(creativePreset?.config.chunking.chunk_size).toBe(500);
      expect(creativePreset?.config.prompts.uncertainty_handling).toBe('best_effort');
    });

    it('Code preset has correct values', () => {
      /**
       * AC-7.16.5: Code preset configuration
       */
      const codePreset = PRESETS.find((p) => p.id === 'code');

      expect(codePreset).toBeDefined();
      expect(codePreset?.config.generation.temperature).toBe(0.2);
      expect(codePreset?.config.chunking.chunk_size).toBe(600);
      expect(codePreset?.config.chunking.chunk_overlap).toBe(50);
    });

    it('General preset has default values', () => {
      /**
       * AC-7.16.6: General preset uses system defaults
       */
      const generalPreset = PRESETS.find((p) => p.id === 'general');

      expect(generalPreset).toBeDefined();
      // General should have default values
      expect(generalPreset?.config.generation.temperature).toBe(0.7);
      expect(generalPreset?.config.chunking.chunk_size).toBe(512);
    });
  });

  describe('[P0] AC-7.16.7: Confirmation Dialog', () => {
    it('shows confirmation when selecting preset with custom settings', async () => {
      /**
       * GIVEN: User has custom (modified) settings
       * WHEN: User selects a preset
       * THEN: Confirmation dialog appears
       */
      const user = userEvent.setup();
      const customSettings = {
        ...defaultSettings,
        generation: { ...defaultSettings.generation, temperature: 0.5 },
      };

      render(
        <PresetSelector
          currentSettings={customSettings}
          onPresetSelect={mockOnPresetSelect}
          hasUnsavedChanges={true}
        />
      );

      await user.click(screen.getByTestId('preset-selector-trigger'));
      await user.click(screen.getByRole('option', { name: /legal/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });
      expect(screen.getByText(/overwrite|replace/i)).toBeInTheDocument();
    });

    it('does not show confirmation when no custom changes', async () => {
      /**
       * GIVEN: User has default settings (no changes)
       * WHEN: User selects a preset
       * THEN: Preset is applied immediately without confirmation
       */
      const user = userEvent.setup();
      render(
        <PresetSelector
          currentSettings={defaultSettings}
          onPresetSelect={mockOnPresetSelect}
          hasUnsavedChanges={false}
        />
      );

      await user.click(screen.getByTestId('preset-selector-trigger'));
      await user.click(screen.getByRole('option', { name: /legal/i }));

      // Should apply immediately
      expect(mockOnPresetSelect).toHaveBeenCalledWith('legal');
      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    });

    it('applies preset when user confirms', async () => {
      /**
       * GIVEN: Confirmation dialog is shown
       * WHEN: User clicks confirm
       * THEN: Preset is applied
       */
      const user = userEvent.setup();
      render(
        <PresetSelector
          currentSettings={defaultSettings}
          onPresetSelect={mockOnPresetSelect}
          hasUnsavedChanges={true}
        />
      );

      await user.click(screen.getByTestId('preset-selector-trigger'));
      await user.click(screen.getByRole('option', { name: /legal/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /confirm|apply/i }));

      expect(mockOnPresetSelect).toHaveBeenCalledWith('legal');
    });

    it('cancels preset selection when user cancels', async () => {
      /**
       * GIVEN: Confirmation dialog is shown
       * WHEN: User clicks cancel
       * THEN: Preset is NOT applied
       */
      const user = userEvent.setup();
      render(
        <PresetSelector
          currentSettings={defaultSettings}
          onPresetSelect={mockOnPresetSelect}
          hasUnsavedChanges={true}
        />
      );

      await user.click(screen.getByTestId('preset-selector-trigger'));
      await user.click(screen.getByRole('option', { name: /legal/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockOnPresetSelect).not.toHaveBeenCalled();
    });
  });

  describe('[P0] AC-7.16.8: Preset Indicator', () => {
    it('shows "Custom" when settings do not match any preset', () => {
      /**
       * GIVEN: Settings that do not match any preset
       * WHEN: Component renders
       * THEN: Shows "Custom" indicator
       */
      const customSettings = {
        ...defaultSettings,
        generation: { ...defaultSettings.generation, temperature: 0.42 },
      };

      render(
        <PresetSelector
          currentSettings={customSettings}
          onPresetSelect={mockOnPresetSelect}
        />
      );

      expect(screen.getByTestId('preset-indicator')).toHaveTextContent(/custom/i);
    });

    it('shows preset name when settings match a preset', () => {
      /**
       * GIVEN: Settings matching legal preset exactly
       * WHEN: Component renders
       * THEN: Shows "Legal" indicator
       */
      const legalSettings: KBSettings = {
        chunking: {
          strategy: 'recursive',
          chunk_size: 1000,
          chunk_overlap: 200,
        },
        generation: {
          temperature: 0.3,
          top_p: 0.9,
          max_tokens: 2048,
        },
        prompts: {
          citation_style: 'footnote',
          uncertainty_handling: 'acknowledge',
        },
        preset: 'legal',
      };

      render(
        <PresetSelector
          currentSettings={legalSettings}
          onPresetSelect={mockOnPresetSelect}
        />
      );

      expect(screen.getByTestId('preset-indicator')).toHaveTextContent(/legal/i);
    });

    it('updates indicator when settings are modified', async () => {
      /**
       * GIVEN: Settings matching a preset
       * WHEN: onSettingsChange is triggered with modified values
       * THEN: Indicator updates to "Custom"
       */
      const { rerender } = render(
        <PresetSelector
          currentSettings={{ ...defaultSettings, preset: 'general' }}
          onPresetSelect={mockOnPresetSelect}
        />
      );

      expect(screen.getByTestId('preset-indicator')).toHaveTextContent(/general/i);

      // Simulate settings change
      rerender(
        <PresetSelector
          currentSettings={{
            ...defaultSettings,
            generation: { ...defaultSettings.generation, temperature: 0.99 },
            preset: null,
          }}
          onPresetSelect={mockOnPresetSelect}
        />
      );

      expect(screen.getByTestId('preset-indicator')).toHaveTextContent(/custom/i);
    });
  });

  describe('[P2] Disabled State', () => {
    it('disables selector when disabled prop is true', () => {
      /**
       * GIVEN: PresetSelector with disabled=true
       * WHEN: Rendering
       * THEN: Selector is disabled
       */
      render(
        <PresetSelector
          currentSettings={defaultSettings}
          onPresetSelect={mockOnPresetSelect}
          disabled={true}
        />
      );

      expect(screen.getByTestId('preset-selector-trigger')).toBeDisabled();
    });
  });
});
```

### 4. E2E Tests (Playwright)

**File:** `frontend/e2e/tests/kb/kb-settings-presets.spec.ts`

```typescript
/**
 * Story 7-16 ATDD: KB Settings Presets E2E Tests
 * Generated: 2025-12-09
 * Status: RED - Implementation required to pass
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { createKBSettings } from '../../fixtures/kb-settings.factory';

const mockKbId = 'test-kb-uuid-7-16';

test.describe('KB Settings - Presets', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    // Network-first: Intercept BEFORE navigation
    await page.route(`**/api/v1/knowledge-bases/${mockKbId}`, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: mockKbId,
          name: 'Test Knowledge Base',
        }),
      });
    });

    await page.route('**/api/v1/kb-presets', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          presets: [
            { id: 'legal', name: 'Legal', description: 'Optimized for legal documents' },
            { id: 'technical', name: 'Technical', description: 'Optimized for technical documentation' },
            { id: 'creative', name: 'Creative', description: 'Higher creativity for content generation' },
            { id: 'code', name: 'Code', description: 'Optimized for code repositories' },
            { id: 'general', name: 'General', description: 'Balanced defaults' },
          ],
        }),
      });
    });

    await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createKBSettings()),
        });
      } else {
        route.fulfill({ status: 200, body: '{}' });
      }
    });
  });

  test('[AC-7.16.1] displays Quick Preset dropdown at top of settings', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User opens KB settings
     * WHEN: Settings modal loads
     * THEN: Quick Preset dropdown is visible at the top
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');

    const presetSelector = page.getByTestId('preset-selector-trigger');
    await expect(presetSelector).toBeVisible();

    // Should be positioned at top (before tabs)
    const selectorBounds = await presetSelector.boundingBox();
    const tabsBounds = await page.getByRole('tablist').boundingBox();

    expect(selectorBounds?.y).toBeLessThan(tabsBounds?.y ?? 0);
  });

  test('[AC-7.16.1] dropdown shows all preset options', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User opens KB settings
     * WHEN: User opens preset dropdown
     * THEN: All 6 options visible (Custom, Legal, Technical, Creative, Code, General)
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="preset-selector-trigger"]');

    await expect(page.getByRole('option', { name: /custom/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /legal/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /technical/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /creative/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /code/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /general/i })).toBeVisible();
  });

  test('[AC-7.16.2] selecting Legal preset applies correct values', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User opens KB settings
     * WHEN: User selects Legal preset
     * THEN: Settings show temp=0.3, chunk_size=1000, overlap=200, citation=footnote
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="preset-selector-trigger"]');
    await page.click('[role="option"]:has-text("Legal")');

    // Check General tab values
    await page.click('[data-testid="tab-general"]');

    const tempSlider = page.getByTestId('generation-temperature-slider');
    await expect(tempSlider).toHaveAttribute('aria-valuenow', '0.3');

    const chunkSizeSlider = page.getByTestId('chunking-size-slider');
    await expect(chunkSizeSlider).toHaveAttribute('aria-valuenow', '1000');

    // Check Prompts tab values
    await page.click('[data-testid="tab-prompts"]');

    const citationStyle = page.getByTestId('citation-style-select');
    await expect(citationStyle).toHaveTextContent(/footnote/i);
  });

  test('[AC-7.16.7] confirmation dialog when overwriting custom settings', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User has modified settings
     * WHEN: User selects a preset
     * THEN: Confirmation dialog warns about overwriting
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');

    // Make a custom change first
    await page.click('[data-testid="tab-general"]');
    const tempSlider = page.getByTestId('generation-temperature-slider');
    await tempSlider.fill('1.5');

    // Now try to select a preset
    await page.click('[data-testid="preset-selector-trigger"]');
    await page.click('[role="option"]:has-text("Legal")');

    // Confirmation should appear
    await expect(page.getByRole('alertdialog')).toBeVisible();
    await expect(page.getByText(/overwrite|custom settings/i)).toBeVisible();
  });

  test('[AC-7.16.8] preset indicator shows current preset or Custom', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User opens KB settings
     * WHEN: Settings load
     * THEN: Indicator shows current preset or "Custom"
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');

    // Initial indicator
    const indicator = page.getByTestId('preset-indicator');
    await expect(indicator).toBeVisible();

    // After selecting Legal preset
    await page.click('[data-testid="preset-selector-trigger"]');
    await page.click('[role="option"]:has-text("Legal")');

    await expect(indicator).toHaveTextContent(/legal/i);

    // After modifying a value
    await page.click('[data-testid="tab-general"]');
    const tempSlider = page.getByTestId('generation-temperature-slider');
    await tempSlider.fill('0.35'); // Slight change from Legal's 0.3

    await expect(indicator).toHaveTextContent(/custom/i);
  });

  test('preset selection persists after save', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User selects a preset
     * WHEN: User saves settings
     * THEN: Preset is saved and persists on reload
     */
    let savedSettings: Record<string, unknown> | null = null;
    await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
      if (route.request().method() === 'PUT') {
        savedSettings = JSON.parse(route.request().postData() || '{}');
        route.fulfill({ status: 200, body: JSON.stringify(savedSettings) });
      } else {
        route.fulfill({
          status: 200,
          body: JSON.stringify(savedSettings || createKBSettings()),
        });
      }
    });

    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="preset-selector-trigger"]');
    await page.click('[role="option"]:has-text("Technical")');
    await page.click('[data-testid="save-settings-button"]');

    await expect(page.getByText(/saved/i)).toBeVisible();
    expect(savedSettings).not.toBeNull();
    expect((savedSettings as Record<string, unknown>)?.preset).toBe('technical');
  });
});
```

---

## Required data-testid Attributes

| Component | data-testid | Purpose |
|-----------|-------------|---------|
| Preset selector trigger | `preset-selector-trigger` | Open dropdown |
| Preset indicator | `preset-indicator` | Current preset display |
| General tab | `tab-general` | Tab navigation |
| Prompts tab | `tab-prompts` | Tab navigation |
| Temperature slider | `generation-temperature-slider` | Generation setting |
| Chunk size slider | `chunking-size-slider` | Chunking setting |
| Citation style select | `citation-style-select` | Prompt setting |
| Save button | `save-settings-button` | Save settings |
| KB settings button | `kb-settings-button` | Open modal |

---

## Implementation Checklist for DEV

### Files to Create

- [ ] `backend/app/core/kb_presets.py` - Preset definitions and functions
- [ ] `backend/app/api/v1/kb_presets.py` - API endpoints (or extend knowledge_bases.py)
- [ ] `frontend/src/lib/kb-presets.ts` - Frontend preset definitions
- [ ] `frontend/src/components/kb/settings/preset-selector.tsx` - Selector component

### Files to Modify

- [ ] `frontend/src/components/kb/kb-settings-modal.tsx` - Add PresetSelector at top
- [ ] `backend/app/schemas/kb_settings.py` - Ensure preset field exists
- [ ] `backend/app/main.py` - Include kb_presets router if separate

### Preset Values Reference

| Preset | temperature | chunk_size | chunk_overlap | citation_style | uncertainty_handling |
|--------|-------------|------------|---------------|----------------|---------------------|
| Legal | 0.3 | 1000 | 200 | footnote | acknowledge |
| Technical | 0.5 | 800 | 100 | inline | - |
| Creative | 0.9 | 500 | - | - | best_effort |
| Code | 0.2 | 600 | 50 | - | - |
| General | 0.7 (default) | 512 (default) | 50 (default) | inline | acknowledge |

---

## Test Execution

```bash
# Backend unit tests
cd backend && .venv/bin/pytest tests/unit/test_kb_presets.py -v

# Backend integration tests
cd backend && .venv/bin/pytest tests/integration/test_kb_presets_api.py -v

# Frontend component tests
npm run test:run -- preset-selector.test.tsx

# E2E tests
npx playwright test kb-settings-presets.spec.ts

# Run all 7-16 tests
npm run test:run -- --grep "7-16|preset"
```

---

## Definition of Done

- [ ] All backend unit tests pass (0 → green)
- [ ] All backend integration tests pass (0 → green)
- [ ] All component tests pass (0 → green)
- [ ] All E2E tests pass (0 → green)
- [ ] GET /api/v1/kb-presets endpoint returns all 5 presets
- [ ] PresetSelector component displays at top of KB settings
- [ ] All preset values match AC specifications
- [ ] Confirmation dialog appears when overwriting custom settings
- [ ] Preset indicator correctly shows current preset or "Custom"
- [ ] Preset detection works for all 5 presets
- [ ] Preset selection persists after save
