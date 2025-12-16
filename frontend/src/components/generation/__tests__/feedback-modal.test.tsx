/**
 * FeedbackModal Component Tests (Story 4-8)
 *
 * Test Coverage: AC2 (Feedback Modal Submission)
 * Priority: P1 (Core UI functionality)
 *
 * Tests:
 * 1. Category selection enables submit button
 * 2. "Other" text area shown when "other" selected
 * 3. Submit button disabled until category selected
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FeedbackModal } from '../feedback-modal';

describe('FeedbackModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P1] should enable submit button after category selection', async () => {
    // GIVEN: FeedbackModal is rendered
    const onSubmit = vi.fn();
    render(<FeedbackModal {...defaultProps} onSubmit={onSubmit} />);

    // THEN: Submit button is initially disabled
    const submitButton = screen.getByRole('button', { name: /submit/i });
    expect(submitButton).toBeDisabled();

    // WHEN: User selects "not_relevant" category (click the label text)
    // Note: Component uses &apos; HTML entity in string literals
    const notRelevantLabel = screen.getByText((content) =>
      content.toLowerCase().includes('results aren') && content.toLowerCase().includes('relevant')
    );
    await userEvent.click(notRelevantLabel);

    // THEN: Submit button is enabled
    await waitFor(() => {
      expect(submitButton).toBeEnabled();
    });

    // WHEN: User clicks submit
    await userEvent.click(submitButton);

    // THEN: onSubmit called with correct feedback type
    expect(onSubmit).toHaveBeenCalledWith('not_relevant', undefined);
  });

  it('[P1] should show text area when "other" category selected', async () => {
    // GIVEN: FeedbackModal is rendered
    render(<FeedbackModal {...defaultProps} />);

    // WHEN: User selects "other" category
    const otherLabel = screen.getByText(/other issue/i);
    await userEvent.click(otherLabel);

    // THEN: Comments text area is visible (label linked via htmlFor)
    const commentsTextArea = screen.getByLabelText(/comments/i);
    expect(commentsTextArea).toBeVisible();
    expect(commentsTextArea).toHaveAttribute('maxlength', '500');

    // WHEN: User types in text area
    await userEvent.type(commentsTextArea, 'Custom feedback message');

    // THEN: Text area contains user input
    expect(commentsTextArea).toHaveValue('Custom feedback message');

    // WHEN: User submits
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    // THEN: onSubmit called with comments
    expect(defaultProps.onSubmit).toHaveBeenCalledWith('other', 'Custom feedback message');
  });

  it('[P1] should keep submit button disabled until category selected', async () => {
    // GIVEN: FeedbackModal is rendered
    const onSubmit = vi.fn();
    render(<FeedbackModal {...defaultProps} onSubmit={onSubmit} />);

    const submitButton = screen.getByRole('button', { name: /submit/i });

    // THEN: Submit button disabled initially
    expect(submitButton).toBeDisabled();

    // WHEN: User tries to submit without selection (should not work)
    await userEvent.click(submitButton);

    // THEN: onSubmit not called
    expect(onSubmit).not.toHaveBeenCalled();

    // WHEN: User selects "wrong_format" category
    const wrongFormatLabel = screen.getByText(/wrong format or structure/i);
    await userEvent.click(wrongFormatLabel);

    // THEN: Submit button enabled
    await waitFor(() => {
      expect(submitButton).toBeEnabled();
    });

    // WHEN: User submits
    await userEvent.click(submitButton);

    // THEN: onSubmit called
    expect(onSubmit).toHaveBeenCalledWith('wrong_format', undefined);
  });

  it('[P1] should display all 5 feedback categories', () => {
    // GIVEN: FeedbackModal is rendered
    render(<FeedbackModal {...defaultProps} />);

    // THEN: All 5 feedback types are visible as labels
    // Note: Component uses &apos; HTML entity in some strings
    expect(screen.getByText((content) =>
      content.toLowerCase().includes('results aren') && content.toLowerCase().includes('relevant')
    )).toBeInTheDocument();
    expect(screen.getByText(/wrong format or structure/i)).toBeInTheDocument();
    expect(screen.getByText(/needs more detail/i)).toBeInTheDocument();
    expect(screen.getByText(/low confidence sources/i)).toBeInTheDocument();
    expect(screen.getByText(/other issue/i)).toBeInTheDocument();
  });

  it('[P1] should close modal when cancel button clicked', async () => {
    // GIVEN: FeedbackModal is open
    const onClose = vi.fn();
    render(<FeedbackModal {...defaultProps} onClose={onClose} />);

    // WHEN: User clicks Cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await userEvent.click(cancelButton);

    // THEN: onClose called
    expect(onClose).toHaveBeenCalled();
  });

  it('[P1] should enforce 500 character limit on comments', async () => {
    // GIVEN: FeedbackModal with "other" selected
    render(<FeedbackModal {...defaultProps} />);

    const otherLabel = screen.getByText(/other issue/i);
    await userEvent.click(otherLabel);

    const commentsTextArea = screen.getByLabelText(/comments/i);

    // THEN: Text area has maxlength attribute
    expect(commentsTextArea).toHaveAttribute('maxlength', '500');
  });
});
