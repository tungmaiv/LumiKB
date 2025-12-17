/**
 * Component Tests: ExportModal
 *
 * Story: 4-7 Document Export
 * Coverage: AC1 (Export format selection)
 *
 * Test Count: 2 tests
 * Priority: P1
 *
 * Test Framework: Vitest + React Testing Library
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ExportModal } from '../export-modal';

describe('ExportModal - AC1: Format Selection', () => {
  it('[P1] should display all three format options with descriptions', () => {
    // GIVEN: ExportModal is rendered
    const onExport = vi.fn();
    const onClose = vi.fn();

    render(<ExportModal open={true} onClose={onClose} onExport={onExport} citationCount={5} />);

    // THEN: All format options are visible
    expect(screen.getByTestId('format-option-docx')).toBeInTheDocument();
    expect(screen.getByTestId('format-option-pdf')).toBeInTheDocument();
    expect(screen.getByTestId('format-option-markdown')).toBeInTheDocument();

    // THEN: Each option has description
    expect(screen.getByText(/Best for editing and collaboration/i)).toBeInTheDocument();
    expect(screen.getByText(/Best for sharing and printing/i)).toBeInTheDocument();
    expect(screen.getByText(/Best for developers and version control/i)).toBeInTheDocument();

    // THEN: Each option shows file size estimate
    expect(screen.getByText(/~50KB/i)).toBeInTheDocument(); // DOCX estimate
    expect(screen.getByText(/~75KB/i)).toBeInTheDocument(); // PDF estimate
    expect(screen.getByText(/~10KB/i)).toBeInTheDocument(); // MD estimate
  });

  it('[P1] should enforce single format selection and call onExport', async () => {
    // GIVEN: ExportModal is rendered
    const onExport = vi.fn();
    const onClose = vi.fn();

    render(<ExportModal open={true} onClose={onClose} onExport={onExport} citationCount={3} />);

    // WHEN: User selects DOCX format
    const docxOption = screen.getByTestId('format-option-docx');
    fireEvent.click(docxOption);

    // THEN: DOCX is selected (check the radio button inside)
    const docxRadio = screen.getByRole('radio', { name: /Microsoft Word/i });
    expect(docxRadio).toHaveAttribute('aria-checked', 'true');

    // WHEN: User selects PDF format (should deselect DOCX)
    const pdfOption = screen.getByTestId('format-option-pdf');
    fireEvent.click(pdfOption);

    // THEN: PDF is selected, DOCX is deselected (radio behavior)
    const pdfRadio = screen.getByRole('radio', { name: /^PDF$/i });
    expect(pdfRadio).toHaveAttribute('aria-checked', 'true');
    expect(docxRadio).toHaveAttribute('aria-checked', 'false');

    // WHEN: User clicks export button
    const exportButton = screen.getByTestId('export-modal-submit');
    fireEvent.click(exportButton);

    // THEN: onExport is called with selected format
    await waitFor(() => {
      expect(onExport).toHaveBeenCalledWith('pdf');
    });
  });
});
