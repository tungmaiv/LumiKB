/**
 * Component tests for ModelTable
 * Story 7-9: LLM Model Registry (AC-7.9.1, AC-7.9.10, AC-7.9.11)
 *
 * Test Coverage:
 * - [P1] Table renders with model data and correct columns
 * - [P1] Loading state displays skeleton UI
 * - [P1] Empty state displays message
 * - [P1] Edit, delete, set-default, test actions work
 * - [P2] Status badges show correct colors
 * - [P2] Type/provider badges display correctly
 * - [P2] Default model indicator (star) displays
 * - [P2] API key indicator displays
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelTable } from '../model-table';
import type { LLMModelSummary } from '@/types/llm-model';

// Mock model data
const mockModels: LLMModelSummary[] = [
  {
    id: 'model-1',
    type: 'embedding',
    provider: 'openai',
    name: 'OpenAI Ada',
    model_id: 'text-embedding-ada-002',
    status: 'active',
    is_default: true,
    has_api_key: true,
  },
  {
    id: 'model-2',
    type: 'generation',
    provider: 'anthropic',
    name: 'Claude 3',
    model_id: 'claude-3-sonnet',
    status: 'active',
    is_default: false,
    has_api_key: true,
  },
  {
    id: 'model-3',
    type: 'embedding',
    provider: 'ollama',
    name: 'Local Nomic',
    model_id: 'nomic-embed-text',
    status: 'inactive',
    is_default: false,
    has_api_key: false,
  },
  {
    id: 'model-4',
    type: 'generation',
    provider: 'openai',
    name: 'GPT-4 Deprecated',
    model_id: 'gpt-4-0314',
    status: 'deprecated',
    is_default: false,
    has_api_key: true,
  },
];

describe('ModelTable', () => {
  const defaultProps = {
    models: mockModels,
    isLoading: false,
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onSetDefault: vi.fn(),
    onTest: vi.fn(),
    testingModelId: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] renders table with all models and correct columns', () => {
      /**
       * GIVEN: ModelTable component with model data
       * WHEN: Component renders
       * THEN: All models are displayed with correct columns (AC-7.9.1)
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: Table headers are visible
      expect(screen.getByRole('columnheader', { name: /name/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /type/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /provider/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /model id/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /status/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /api key/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /actions/i })).toBeInTheDocument();

      // THEN: All models are displayed
      expect(screen.getByText('OpenAI Ada')).toBeInTheDocument();
      expect(screen.getByText('Claude 3')).toBeInTheDocument();
      expect(screen.getByText('Local Nomic')).toBeInTheDocument();
      expect(screen.getByText('GPT-4 Deprecated')).toBeInTheDocument();
    });

    it('[P1] displays loading state with skeleton UI', () => {
      /**
       * GIVEN: ModelTable with isLoading=true
       * WHEN: Component renders
       * THEN: Skeleton rows are displayed
       */

      // WHEN: Render with loading state
      render(<ModelTable {...defaultProps} isLoading={true} />);

      // THEN: Table is present but with skeletons
      expect(screen.getByRole('table')).toBeInTheDocument();

      // THEN: No model names are visible
      expect(screen.queryByText('OpenAI Ada')).not.toBeInTheDocument();
    });

    it('[P1] displays empty state when no models', () => {
      /**
       * GIVEN: ModelTable with empty models array
       * WHEN: Component renders
       * THEN: Empty state message is displayed
       */

      // WHEN: Render with no models
      render(<ModelTable {...defaultProps} models={[]} />);

      // THEN: Empty state message is visible
      expect(screen.getByText(/no models configured/i)).toBeInTheDocument();
      expect(screen.getByText(/add a model to get started/i)).toBeInTheDocument();

      // THEN: Table is not visible
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('[P2] displays correct status badges', () => {
      /**
       * GIVEN: ModelTable with models having different statuses
       * WHEN: Component renders
       * THEN: Status badges show correct labels
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: Status badges are present
      expect(screen.getAllByText('Active')).toHaveLength(2);
      expect(screen.getByText('Inactive')).toBeInTheDocument();
      expect(screen.getByText('Deprecated')).toBeInTheDocument();
    });

    it('[P2] displays correct type badges', () => {
      /**
       * GIVEN: ModelTable with embedding and generation models
       * WHEN: Component renders
       * THEN: Type badges show correct labels
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: Type badges are present
      expect(screen.getAllByText('Embedding')).toHaveLength(2);
      expect(screen.getAllByText('Generation')).toHaveLength(2);
    });

    it('[P2] displays provider info with icons', () => {
      /**
       * GIVEN: ModelTable with models from different providers
       * WHEN: Component renders
       * THEN: Provider names are displayed
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: Provider names are present
      expect(screen.getAllByText('OpenAI')).toHaveLength(2);
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('Ollama')).toBeInTheDocument();
    });

    it('[P2] displays model IDs in code format', () => {
      /**
       * GIVEN: ModelTable with models
       * WHEN: Component renders
       * THEN: Model IDs are displayed
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: Model IDs are present
      expect(screen.getByText('text-embedding-ada-002')).toBeInTheDocument();
      expect(screen.getByText('claude-3-sonnet')).toBeInTheDocument();
      expect(screen.getByText('nomic-embed-text')).toBeInTheDocument();
      expect(screen.getByText('gpt-4-0314')).toBeInTheDocument();
    });

    it('[P2] displays default model indicator (star) for default models (AC-7.9.10)', () => {
      /**
       * GIVEN: ModelTable with a default model
       * WHEN: Component renders
       * THEN: Star icon is displayed next to default model name
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: Default model row has star indicator
      const defaultModelRow = screen.getByText('OpenAI Ada').closest('tr');
      expect(defaultModelRow).toBeInTheDocument();

      // The star is rendered as an SVG with fill-yellow-500 class
      const starIcon = defaultModelRow?.querySelector('svg.fill-yellow-500');
      expect(starIcon).toBeInTheDocument();
    });

    it('[P2] displays API key status indicators', () => {
      /**
       * GIVEN: ModelTable with models having/not having API keys
       * WHEN: Component renders
       * THEN: Check/X icons indicate API key status
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // Get all rows
      const rows = screen.getAllByRole('row');

      // Model with API key should have green check (models 1, 2, 4)
      // Model without API key should have gray X (model 3)
      const greenChecks = document.querySelectorAll('svg.text-green-500');
      const grayXs = document.querySelectorAll('svg.text-gray-300');

      expect(greenChecks.length).toBe(3); // 3 models have API keys
      expect(grayXs.length).toBe(1); // 1 model doesn't have API key
    });
  });

  describe('actions', () => {
    it('[P1] calls onTest when test button is clicked (AC-7.9.8)', async () => {
      /**
       * GIVEN: ModelTable with test buttons
       * WHEN: User clicks test button for a model
       * THEN: onTest is called with that model
       */
      const user = userEvent.setup();
      const onTest = vi.fn();

      // WHEN: Render component
      render(<ModelTable {...defaultProps} onTest={onTest} />);

      // Find the row with Claude 3 and click its test button (Zap icon)
      const modelRow = screen.getByText('Claude 3').closest('tr');
      const testButton = within(modelRow!).getAllByRole('button')[0]; // First button is test
      await user.click(testButton);

      // THEN: onTest called with Claude 3 model
      expect(onTest).toHaveBeenCalledWith(mockModels[1]);
    });

    it('[P1] disables test button when testing is in progress', () => {
      /**
       * GIVEN: ModelTable with a model being tested
       * WHEN: Component renders
       * THEN: Test button for that model is disabled
       */

      // WHEN: Render with model-2 being tested
      render(<ModelTable {...defaultProps} testingModelId="model-2" />);

      // THEN: Test button for model-2 should be disabled
      const modelRow = screen.getByText('Claude 3').closest('tr');
      const testButton = within(modelRow!).getAllByRole('button')[0];
      expect(testButton).toBeDisabled();
    });

    it('[P1] calls onEdit when edit menu item is clicked (AC-7.9.11)', async () => {
      /**
       * GIVEN: ModelTable with actions dropdown
       * WHEN: User clicks Edit from dropdown
       * THEN: onEdit is called with that model
       */
      const user = userEvent.setup();
      const onEdit = vi.fn();

      // WHEN: Render component
      render(<ModelTable {...defaultProps} onEdit={onEdit} />);

      // Find the row and open dropdown menu
      const modelRow = screen.getByText('Claude 3').closest('tr');
      const menuButton = within(modelRow!).getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // Click Edit option
      const editOption = screen.getByRole('menuitem', { name: /edit/i });
      await user.click(editOption);

      // THEN: onEdit called with Claude 3 model
      expect(onEdit).toHaveBeenCalledWith(mockModels[1]);
    });

    it('[P1] calls onSetDefault when set default menu item is clicked (AC-7.9.10)', async () => {
      /**
       * GIVEN: ModelTable with non-default model
       * WHEN: User clicks Set as Default from dropdown
       * THEN: onSetDefault is called with that model
       */
      const user = userEvent.setup();
      const onSetDefault = vi.fn();

      // WHEN: Render component
      render(<ModelTable {...defaultProps} onSetDefault={onSetDefault} />);

      // Find a non-default model row and open dropdown
      const modelRow = screen.getByText('Claude 3').closest('tr');
      const menuButton = within(modelRow!).getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // Click Set as Default option
      const setDefaultOption = screen.getByRole('menuitem', { name: /set as default/i });
      await user.click(setDefaultOption);

      // THEN: onSetDefault called with Claude 3 model
      expect(onSetDefault).toHaveBeenCalledWith(mockModels[1]);
    });

    it('[P1] hides set default option for already default model', async () => {
      /**
       * GIVEN: ModelTable with a default model
       * WHEN: User opens dropdown for default model
       * THEN: Set as Default option is not visible
       */
      const user = userEvent.setup();

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // Find the default model row (OpenAI Ada) and open dropdown
      const modelRow = screen.getByText('OpenAI Ada').closest('tr');
      const menuButton = within(modelRow!).getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // THEN: Set as Default option should not be present
      expect(screen.queryByRole('menuitem', { name: /set as default/i })).not.toBeInTheDocument();
    });

    it('[P1] calls onDelete when delete menu item is clicked (AC-7.9.11)', async () => {
      /**
       * GIVEN: ModelTable with delete option
       * WHEN: User clicks Delete from dropdown
       * THEN: onDelete is called with that model
       */
      const user = userEvent.setup();
      const onDelete = vi.fn();

      // WHEN: Render component
      render(<ModelTable {...defaultProps} onDelete={onDelete} />);

      // Find a non-default model row and open dropdown
      const modelRow = screen.getByText('Claude 3').closest('tr');
      const menuButton = within(modelRow!).getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // Click Delete option
      const deleteOption = screen.getByRole('menuitem', { name: /delete/i });
      await user.click(deleteOption);

      // THEN: onDelete called with Claude 3 model
      expect(onDelete).toHaveBeenCalledWith(mockModels[1]);
    });

    it('[P1] disables delete option for default model', async () => {
      /**
       * GIVEN: ModelTable with a default model
       * WHEN: User opens dropdown for default model
       * THEN: Delete option is disabled
       */
      const user = userEvent.setup();

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // Find the default model row (OpenAI Ada) and open dropdown
      const modelRow = screen.getByText('OpenAI Ada').closest('tr');
      const menuButton = within(modelRow!).getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // THEN: Delete option should be disabled (Radix uses empty string for truthy data-disabled)
      const deleteOption = screen.getByRole('menuitem', { name: /delete/i });
      expect(deleteOption).toHaveAttribute('data-disabled');
    });
  });

  describe('visual states', () => {
    it('[P2] shows loading spinner on test button when testing', () => {
      /**
       * GIVEN: ModelTable with a model being tested
       * WHEN: Component renders
       * THEN: Test button shows spinner
       */

      // WHEN: Render with model-2 being tested
      render(<ModelTable {...defaultProps} testingModelId="model-2" />);

      // THEN: Spinner emoji is visible in the test button area (hourglass with flowing sand)
      const modelRow = screen.getByText('Claude 3').closest('tr');
      expect(within(modelRow!).getByText('\u23F3')).toBeInTheDocument(); // hourglass not done emoji ⏳
    });

    it('[P2] renders correct number of rows', () => {
      /**
       * GIVEN: ModelTable with 4 models
       * WHEN: Component renders
       * THEN: 4 data rows plus header row exist
       */

      // WHEN: Render component
      render(<ModelTable {...defaultProps} />);

      // THEN: 5 rows total (1 header + 4 data)
      const rows = screen.getAllByRole('row');
      expect(rows).toHaveLength(5);
    });
  });
});
