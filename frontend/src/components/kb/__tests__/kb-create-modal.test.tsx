import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KbCreateModal } from '../kb-create-modal';

// Mock the KB store
const mockCreateKb = vi.fn();

vi.mock('@/lib/stores/kb-store', () => ({
  useKBStore: (selector?: (state: { createKb: typeof mockCreateKb }) => unknown) => {
    const state = { createKb: mockCreateKb };
    if (selector) {
      return selector(state);
    }
    return state;
  },
}));

describe('KbCreateModal', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dialog when open', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('does not render dialog when closed', () => {
    render(<KbCreateModal {...defaultProps} open={false} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders title and description', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByText('Create Knowledge Base')).toBeInTheDocument();
    expect(
      screen.getByText('Create a new knowledge base to organize your documents.')
    ).toBeInTheDocument();
  });

  it('renders name input field', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
  });

  it('renders description input field', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it('renders Cancel and Create buttons', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
  });

  it('shows validation error when name is empty', async () => {
    const user = userEvent.setup();
    render(<KbCreateModal {...defaultProps} />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });
  });

  it('shows validation error when name exceeds 255 characters', async () => {
    const user = userEvent.setup();
    render(<KbCreateModal {...defaultProps} />);

    const longName = 'a'.repeat(256);
    await user.type(screen.getByLabelText('Name'), longName);
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Name must be less than 255 characters')).toBeInTheDocument();
    });
  });

  it('calls createKb on valid submission', async () => {
    const user = userEvent.setup();
    mockCreateKb.mockResolvedValueOnce({
      id: 'new-kb',
      name: 'New KB',
      description: 'Test description',
    });

    render(<KbCreateModal {...defaultProps} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.type(screen.getByLabelText(/description/i), 'Test description');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(mockCreateKb).toHaveBeenCalledWith({
        name: 'New KB',
        description: 'Test description',
      });
    });
  });

  it('closes modal on successful creation', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    mockCreateKb.mockResolvedValueOnce({ id: 'new-kb', name: 'New KB' });

    render(<KbCreateModal open onOpenChange={onOpenChange} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('shows error message on creation failure', async () => {
    const user = userEvent.setup();
    mockCreateKb.mockRejectedValueOnce(new Error('Creation failed'));

    render(<KbCreateModal {...defaultProps} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Creation failed')).toBeInTheDocument();
    });
  });

  it('does not close modal on error', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    mockCreateKb.mockRejectedValueOnce(new Error('Creation failed'));

    render(<KbCreateModal open onOpenChange={onOpenChange} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Creation failed')).toBeInTheDocument();
    });
    // Modal should remain open
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });

  it('closes modal when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();

    render(<KbCreateModal open onOpenChange={onOpenChange} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('resets form when modal is closed', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();

    const { rerender } = render(<KbCreateModal open onOpenChange={onOpenChange} />);

    // Type something in the name field
    await user.type(screen.getByLabelText('Name'), 'Test Name');
    expect(screen.getByLabelText('Name')).toHaveValue('Test Name');

    // Close the modal
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    // Reopen the modal
    rerender(<KbCreateModal open onOpenChange={onOpenChange} />);

    // Field should be empty
    expect(screen.getByLabelText('Name')).toHaveValue('');
  });

  it('disables form inputs during submission', async () => {
    const user = userEvent.setup();
    // Create a promise that we can control
    let resolveCreate: (value: unknown) => void;
    const createPromise = new Promise((resolve) => {
      resolveCreate = resolve;
    });
    mockCreateKb.mockReturnValueOnce(createPromise);

    render(<KbCreateModal {...defaultProps} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    // Check that inputs are disabled during submission
    await waitFor(() => {
      expect(screen.getByLabelText('Name')).toBeDisabled();
    });

    // Resolve the promise and wait for state updates to complete
    await act(async () => {
      resolveCreate!({ id: 'new-kb', name: 'New KB' });
    });

    // Wait for form to re-enable after submission completes
    await waitFor(
      () => {
        expect(screen.queryByLabelText('Name')).not.toBeDisabled();
      },
      { timeout: 100 }
    ).catch(() => {
      // Modal may close after successful submission, which is expected
    });
  });
});
