/**
 * Component Tests: VerificationDialog
 *
 * Story: 4-7 Document Export
 * Coverage: AC2 (Source verification prompt)
 *
 * Test Count: 3 tests
 * Priority: P1
 *
 * Test Framework: Vitest + React Testing Library
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import VerificationDialog from '../verification-dialog';

describe('VerificationDialog - AC2: Source Verification Prompt', () => {
  const mockDraftId = 'test-draft-123';

  beforeEach(() => {
    // Clear session storage before each test
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it('[P1] should display unchecked checkbox by default', () => {
    // GIVEN: VerificationDialog is rendered
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <VerificationDialog
        open={true}
        onConfirm={onConfirm}
        onCancel={onCancel}
        draftId={mockDraftId}
        citationCount={5}
        documentCount={3}
      />
    );

    // THEN: Verification message is displayed
    expect(screen.getByTestId('verification-message')).toHaveTextContent(
      /Have you verified the sources?/i
    );

    // THEN: Citation count is displayed
    expect(screen.getByTestId('citation-count')).toHaveTextContent('5 citations');
    expect(screen.getByTestId('document-count')).toHaveTextContent('3 documents');

    // THEN: Checkbox is unchecked by default
    const checkbox = screen.getByTestId('verification-checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);

    // THEN: Both buttons are visible
    expect(screen.getByTestId('go-back-button')).toBeInTheDocument();
    expect(screen.getByTestId('export-anyway-button')).toBeInTheDocument();
  });

  it('[P1] should call onCancel when "Go Back" is clicked', async () => {
    // GIVEN: VerificationDialog is rendered
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <VerificationDialog
        open={true}
        onConfirm={onConfirm}
        onCancel={onCancel}
        draftId={mockDraftId}
        citationCount={3}
        documentCount={2}
      />
    );

    // WHEN: User clicks "Go Back"
    const goBackButton = screen.getByTestId('go-back-button');
    fireEvent.click(goBackButton);

    // THEN: onCancel is called
    await waitFor(() => {
      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    // THEN: onConfirm is NOT called
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('[P1] should call onConfirm and persist checkbox state when "Export Anyway" is clicked', async () => {
    // GIVEN: VerificationDialog is rendered
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <VerificationDialog
        open={true}
        onConfirm={onConfirm}
        onCancel={onCancel}
        draftId={mockDraftId}
        citationCount={8}
        documentCount={4}
      />
    );

    // WHEN: User checks the verification checkbox
    const checkbox = screen.getByTestId('verification-checkbox') as HTMLInputElement;
    fireEvent.click(checkbox);

    // THEN: Checkbox is checked
    await waitFor(() => {
      expect(checkbox.checked).toBe(true);
    });

    // WHEN: User clicks "Export Anyway"
    const exportButton = screen.getByTestId('export-anyway-button');
    fireEvent.click(exportButton);

    // THEN: onConfirm is called
    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    // THEN: Verification state is saved to session storage
    const storageKey = `draft_export_verified_${mockDraftId}`;
    expect(sessionStorage.getItem(storageKey)).toBe('true');

    // THEN: onCancel is NOT called
    expect(onCancel).not.toHaveBeenCalled();
  });

  it('[P2] should allow export without checking checkbox (user can skip verification)', async () => {
    // GIVEN: VerificationDialog is rendered
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <VerificationDialog
        open={true}
        onConfirm={onConfirm}
        onCancel={onCancel}
        draftId={mockDraftId}
        citationCount={2}
        documentCount={1}
      />
    );

    // WHEN: User clicks "Export Anyway" WITHOUT checking checkbox
    const checkbox = screen.getByTestId('verification-checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(false); // Not checked

    const exportButton = screen.getByTestId('export-anyway-button');
    fireEvent.click(exportButton);

    // THEN: onConfirm is still called (user can skip verification)
    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    // THEN: Checkbox state is NOT saved to session storage (user didn't verify)
    const storageKey = `draft_export_verified_${mockDraftId}`;
    expect(sessionStorage.getItem(storageKey)).toBeNull();
  });

  it('[P2] should restore checkbox state from session storage on mount', () => {
    // GIVEN: Session storage has verification state for this draft
    const storageKey = `draft_export_verified_${mockDraftId}`;
    sessionStorage.setItem(storageKey, 'true');

    // WHEN: VerificationDialog is rendered
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <VerificationDialog
        open={true}
        onConfirm={onConfirm}
        onCancel={onCancel}
        draftId={mockDraftId}
        citationCount={3}
        documentCount={2}
      />
    );

    // THEN: Checkbox should be pre-checked (restored from session storage)
    const checkbox = screen.getByTestId('verification-checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
  });
});
