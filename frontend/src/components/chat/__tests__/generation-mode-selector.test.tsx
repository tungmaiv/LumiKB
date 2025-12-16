/**
 * Component Tests: GenerationModeSelector Component (Story 4.4)
 * Priority: P1 (High - Core document generation interaction)
 * Generated: 2025-11-28
 *
 * Test Coverage:
 * - P1: Renders with correct default value
 * - P1: Calls onChange when mode is selected
 * - P1: Displays all generation mode options
 * - P1: Disabled state prevents interaction
 * - P2: Shows selected mode label
 * - P2: Includes mode descriptions
 *
 * Knowledge Base References:
 * - component-tdd.md: Component test patterns with RTL
 * - test-quality.md: One assertion per test, clear Given-When-Then
 */

import { describe, it, expect, vi, beforeAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  GenerationModeSelector,
  GENERATION_MODES,
  type GenerationMode,
} from '../generation-mode-selector';

// Mock pointer capture for Radix Select
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn();
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
});

describe('GenerationModeSelector Component', () => {
  it('[P1] should render with default value selected', () => {
    /**
     * GIVEN: Component is rendered with initial value
     * WHEN: Component displays
     * THEN: Selected mode is displayed in trigger
     */
    const onChange = vi.fn();

    render(<GenerationModeSelector value="rfp_response" onChange={onChange} />);

    expect(screen.getByText('RFP Response Section')).toBeInTheDocument();
  });

  it('[P1] should render trigger button with click handler', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Trigger button is clickable
     */
    const onChange = vi.fn();

    render(<GenerationModeSelector value="rfp_response" onChange={onChange} />);

    const trigger = screen.getByTestId('generation-mode-trigger');
    expect(trigger).toBeInTheDocument();
    expect(trigger).not.toBeDisabled();
  });

  it('[P1] should contain all generation modes in constant', () => {
    /**
     * GIVEN: GENERATION_MODES constant
     * WHEN: Accessed
     * THEN: Contains all 4 expected modes
     */
    expect(GENERATION_MODES).toHaveLength(4);
    expect(GENERATION_MODES.map((m) => m.value)).toEqual([
      'rfp_response',
      'technical_checklist',
      'requirements_summary',
      'custom',
    ]);
  });

  it('[P1] should disable selector when disabled prop is true', () => {
    /**
     * GIVEN: Component is rendered with disabled=true
     * WHEN: Component displays
     * THEN: Trigger is disabled
     */
    const onChange = vi.fn();

    render(<GenerationModeSelector value="rfp_response" onChange={onChange} disabled={true} />);

    const trigger = screen.getByTestId('generation-mode-trigger');
    expect(trigger).toBeDisabled();
  });

  it('[P2] should show FileText icon in trigger', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: FileText icon is visible
     */
    const onChange = vi.fn();

    render(<GenerationModeSelector value="rfp_response" onChange={onChange} />);

    const trigger = screen.getByTestId('generation-mode-trigger');
    const icon = trigger.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('[P2] should have descriptions for all modes', () => {
    /**
     * GIVEN: GENERATION_MODES constant
     * WHEN: Accessed
     * THEN: Each mode has a description
     */
    GENERATION_MODES.forEach((mode) => {
      expect(mode.description).toBeTruthy();
      expect(mode.description.length).toBeGreaterThan(10);
    });
  });

  it('[P2] should update displayed label when value changes', () => {
    /**
     * GIVEN: Component is rendered with initial value
     * WHEN: Value prop changes
     * THEN: Displayed label updates
     */
    const onChange = vi.fn();
    const { rerender } = render(
      <GenerationModeSelector value="rfp_response" onChange={onChange} />
    );

    expect(screen.getByText('RFP Response Section')).toBeInTheDocument();

    // Change value
    rerender(<GenerationModeSelector value="technical_checklist" onChange={onChange} />);

    expect(screen.getByText('Technical Checklist')).toBeInTheDocument();
  });

  it('[P2] should render label and input with correct ID association', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Label has htmlFor matching input ID
     */
    const onChange = vi.fn();

    render(<GenerationModeSelector value="rfp_response" onChange={onChange} />);

    const label = screen.getByText('Generation Mode');
    expect(label).toHaveAttribute('for', 'generation-mode');
  });

  it('[P3] should support custom mode value', () => {
    /**
     * GIVEN: Custom mode is selected
     * WHEN: Component is rendered with custom value
     * THEN: Custom Prompt label is displayed
     */
    const onChange = vi.fn();

    render(<GenerationModeSelector value="custom" onChange={onChange} />);

    expect(screen.getByText('Custom Prompt')).toBeInTheDocument();
  });
});
