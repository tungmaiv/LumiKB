/**
 * Unit tests for TemplateSelector component
 *
 * Story 4.9: Generation Templates
 * Tests AC-1 (UI templates), AC-3 (example previews)
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, test, vi, beforeEach } from 'vitest';
import { TemplateSelector } from '../template-selector';

describe('TemplateSelector', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  test('[P1] renders all four templates', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // THEN: All four template names are visible
    expect(screen.getByText('RFP Response Section')).toBeInTheDocument();
    expect(screen.getByText('Technical Checklist')).toBeInTheDocument();
    expect(screen.getByText('Gap Analysis')).toBeInTheDocument();
    expect(screen.getByText('Custom Prompt')).toBeInTheDocument();
  });

  test('[P1] highlights selected template', () => {
    // GIVEN: TemplateSelector with rfp_response selected
    render(<TemplateSelector value="rfp_response" onChange={mockOnChange} />);

    // WHEN: Finding the selected template card
    const rfpCard = screen.getByTestId('template-rfp_response');

    // THEN: Card has border-primary class indicating selection
    expect(rfpCard).toHaveClass('border-primary');
    expect(rfpCard).toHaveClass('bg-primary/5');

    // AND: Other templates are not highlighted
    const checklistCard = screen.getByTestId('template-checklist');
    expect(checklistCard).not.toHaveClass('border-primary');
  });

  test('[P1] calls onChange when template clicked', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // WHEN: User clicks on Technical Checklist card
    const checklistCard = screen.getByTestId('template-checklist');
    fireEvent.click(checklistCard);

    // THEN: onChange is called with correct template ID
    expect(mockOnChange).toHaveBeenCalledWith('checklist');
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  test('[P1] displays template descriptions', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // THEN: All template descriptions are visible
    expect(
      screen.getByText(/Generate a structured RFP response with executive summary/)
    ).toBeInTheDocument();
    expect(screen.getByText(/Create a requirement checklist from sources/)).toBeInTheDocument();
    expect(
      screen.getByText(/Compare requirements against current capabilities/)
    ).toBeInTheDocument();
    expect(screen.getByText(/Generate content based on your own instructions/)).toBeInTheDocument();
  });

  test('[P1] shows example preview for non-custom templates', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // THEN: Example preview is shown for rfp_response
    expect(screen.getAllByText('Example preview:').length).toBeGreaterThan(0);
    expect(screen.getByText(/Executive Summary/)).toBeInTheDocument();

    // AND: Example preview is shown for checklist
    expect(screen.getByText(/Authentication Requirements/)).toBeInTheDocument();

    // AND: Example preview is shown for gap_analysis
    expect(screen.getByText(/Requirement \| Current State/)).toBeInTheDocument();

    // AND: Custom template has NO example preview (empty string)
    const customCard = screen.getByTestId('template-custom');
    const customPre = customCard.querySelector('pre');
    expect(customPre).not.toBeInTheDocument(); // No pre element for empty string
  });

  test('[P1] displays appropriate icons for each template', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // THEN: Each template card contains an icon SVG
    const rfpCard = screen.getByTestId('template-rfp_response');
    const checklistCard = screen.getByTestId('template-checklist');
    const gapCard = screen.getByTestId('template-gap_analysis');
    const customCard = screen.getByTestId('template-custom');

    // Each card should have an svg icon (lucide-react components render as SVG)
    expect(rfpCard.querySelector('svg')).toBeInTheDocument();
    expect(checklistCard.querySelector('svg')).toBeInTheDocument();
    expect(gapCard.querySelector('svg')).toBeInTheDocument();
    expect(customCard.querySelector('svg')).toBeInTheDocument();
  });

  test('[P2] supports keyboard navigation with Enter key', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // WHEN: User presses Enter on checklist card
    const checklistCard = screen.getByTestId('template-checklist');
    fireEvent.keyDown(checklistCard, { key: 'Enter' });

    // THEN: onChange is called
    expect(mockOnChange).toHaveBeenCalledWith('checklist');
  });

  test('[P2] supports keyboard navigation with Space key', () => {
    // GIVEN: TemplateSelector is mounted
    render(<TemplateSelector value="" onChange={mockOnChange} />);

    // WHEN: User presses Space on gap_analysis card
    const gapCard = screen.getByTestId('template-gap_analysis');
    fireEvent.keyDown(gapCard, { key: ' ' });

    // THEN: onChange is called
    expect(mockOnChange).toHaveBeenCalledWith('gap_analysis');
  });

  test('[P2] has proper ARIA attributes for accessibility', () => {
    // GIVEN: TemplateSelector is mounted with a selected template
    render(<TemplateSelector value="rfp_response" onChange={mockOnChange} />);

    // THEN: Container has radiogroup role
    expect(screen.getByRole('radiogroup')).toBeInTheDocument();
    expect(screen.getByLabelText('Template selection')).toBeInTheDocument();

    // AND: Each template has radio role
    const rfpRadio = screen.getByTestId('template-rfp_response');
    expect(rfpRadio).toHaveAttribute('role', 'radio');
    expect(rfpRadio).toHaveAttribute('aria-checked', 'true');

    // AND: Non-selected templates are not checked
    const checklistRadio = screen.getByTestId('template-checklist');
    expect(checklistRadio).toHaveAttribute('aria-checked', 'false');
  });
});
