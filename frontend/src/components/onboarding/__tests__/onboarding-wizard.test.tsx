import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OnboardingWizard } from '../onboarding-wizard';
import { describe, it, expect, vi } from 'vitest';

describe('OnboardingWizard', () => {
  it('renders with Step 1 content (Welcome screen)', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();
    expect(screen.getByText(/Your AI-powered knowledge management platform/i)).toBeInTheDocument();
  });

  it('Next button advances to next step', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Start on Step 1
    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();

    // Click Next
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    // Should be on Step 2
    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();
    expect(screen.getByText('Explore the Sample Knowledge Base')).toBeInTheDocument();
  });

  it('Back button returns to previous step', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Go to Step 2
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();

    // Click Back
    fireEvent.click(screen.getByRole('button', { name: /back/i }));

    // Should be back on Step 1
    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
    expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();
  });

  it('Back button is disabled on Step 1', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    expect(backButton).toBeDisabled();
  });

  it('progress dots update on step change', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Check initial progress dots (5 dots total)
    // Dialog renders in portal, so query document.body
    // Use specific selector for progress dots (h-2 w-2 rounded-full)
    const dots = document.body.querySelectorAll('.h-2.w-2.rounded-full');
    expect(dots).toHaveLength(5);

    // First dot should be highlighted (bg-primary)
    expect(dots[0]).toHaveClass('bg-primary');

    // Click Next to go to Step 2
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    // Second dot should now be highlighted
    const updatedDots = document.body.querySelectorAll('.h-2.w-2.rounded-full');
    expect(updatedDots[1]).toHaveClass('bg-primary');
  });

  it('Skip Tutorial opens confirmation dialog', async () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Click Skip Tutorial link
    fireEvent.click(screen.getByText('Skip Tutorial'));

    // Confirmation dialog should appear
    await waitFor(() => {
      expect(screen.getByText('Skip Tutorial?')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to skip/i)).toBeInTheDocument();
    });
  });

  it('skip confirmation Cancel returns to wizard', async () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Click Skip Tutorial
    fireEvent.click(screen.getByText('Skip Tutorial'));

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(screen.getByText('Skip Tutorial?')).toBeInTheDocument();
    });

    // Click Cancel
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

    // Should return to wizard (Step 1 still visible)
    await waitFor(() => {
      expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();
    });

    // onComplete should not have been called
    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('skip confirmation Skip closes wizard and calls onComplete', async () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Click Skip Tutorial
    fireEvent.click(screen.getByText('Skip Tutorial'));

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(screen.getByText('Skip Tutorial?')).toBeInTheDocument();
    });

    // Click Skip button in confirmation
    const skipButtons = screen.getAllByRole('button', { name: /skip/i });
    fireEvent.click(skipButtons[skipButtons.length - 1]); // Last Skip button

    // onComplete should be called
    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  it('Start Exploring button closes wizard on Step 5', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Navigate to Step 5
    for (let i = 0; i < 4; i++) {
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
    }

    // Should be on Step 5
    expect(screen.getByText('Step 5 of 5')).toBeInTheDocument();
    expect(screen.getByText("You're All Set!")).toBeInTheDocument();

    // Click Start Exploring
    fireEvent.click(screen.getByRole('button', { name: /start exploring/i }));

    // onComplete should be called
    expect(mockOnComplete).toHaveBeenCalled();
  });

  it('displays all 5 step contents correctly', () => {
    const mockOnComplete = vi.fn();
    render(<OnboardingWizard onComplete={mockOnComplete} />);

    // Step 1: Welcome
    expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();

    // Step 2: Explore KB
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Explore the Sample Knowledge Base')).toBeInTheDocument();

    // Step 3: Try Search
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Ask Your First Question')).toBeInTheDocument();

    // Step 4: Citations
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Citations Build Trust')).toBeInTheDocument();

    // Step 5: Completion
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText("You're All Set!")).toBeInTheDocument();
  });

  describe('Edge Cases and Keyboard Navigation', () => {
    it('should handle rapid clicking of Next button without breaking', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Rapidly click Next button 10 times
      const nextButton = screen.getByRole('button', { name: /next/i });
      for (let i = 0; i < 10; i++) {
        if (nextButton && !nextButton.hasAttribute('disabled')) {
          fireEvent.click(nextButton);
        }
      }

      // Should stop at Step 5 (not crash or go beyond)
      expect(screen.getByText('Step 5 of 5')).toBeInTheDocument();
      expect(screen.getByText("You're All Set!")).toBeInTheDocument();
    });

    it('should handle rapid clicking of Back button without breaking', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Navigate to Step 3
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(screen.getByText('Step 3 of 5')).toBeInTheDocument();

      // Rapidly click Back button 10 times
      const backButton = screen.getByRole('button', { name: /back/i });
      for (let i = 0; i < 10; i++) {
        if (backButton && !backButton.hasAttribute('disabled')) {
          fireEvent.click(backButton);
        }
      }

      // Should stop at Step 1 (not crash or go below 1)
      expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
      expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();
    });

    it('should navigate backward and forward multiple times consistently', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Forward to Step 3
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(screen.getByText('Step 3 of 5')).toBeInTheDocument();

      // Back to Step 1
      fireEvent.click(screen.getByRole('button', { name: /back/i }));
      fireEvent.click(screen.getByRole('button', { name: /back/i }));
      expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();

      // Forward to Step 4
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(screen.getByText('Step 4 of 5')).toBeInTheDocument();

      // Back to Step 2
      fireEvent.click(screen.getByRole('button', { name: /back/i }));
      fireEvent.click(screen.getByRole('button', { name: /back/i }));
      expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();
    });

    it('should not call onComplete when clicking Next before Step 5', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Click Next on Steps 1-4 (should NOT call onComplete)
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(mockOnComplete).not.toHaveBeenCalled();

      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(mockOnComplete).not.toHaveBeenCalled();

      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(mockOnComplete).not.toHaveBeenCalled();

      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(mockOnComplete).not.toHaveBeenCalled();

      // Now on Step 5 - should have Start Exploring button
      expect(screen.getByRole('button', { name: /start exploring/i })).toBeInTheDocument();
    });

    it('should show Skip Tutorial link on every step', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Check all 5 steps
      for (let step = 1; step <= 5; step++) {
        expect(screen.getByText('Skip Tutorial')).toBeInTheDocument();

        // Navigate to next step (except on Step 5)
        if (step < 5) {
          fireEvent.click(screen.getByRole('button', { name: /next/i }));
        }
      }
    });

    it('should not show Next button on Step 5', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Navigate to Step 5
      for (let i = 0; i < 4; i++) {
        fireEvent.click(screen.getByRole('button', { name: /next/i }));
      }

      // Should be on Step 5
      expect(screen.getByText('Step 5 of 5')).toBeInTheDocument();

      // Next button should NOT exist
      expect(screen.queryByRole('button', { name: /next/i })).not.toBeInTheDocument();

      // Start Exploring button should exist
      expect(screen.getByRole('button', { name: /start exploring/i })).toBeInTheDocument();
    });

    it('should enable Back button on all steps except Step 1', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Step 1: Back button disabled
      let backButton = screen.getByRole('button', { name: /back/i });
      expect(backButton).toBeDisabled();

      // Step 2-5: Back button enabled
      for (let step = 2; step <= 5; step++) {
        fireEvent.click(screen.getByRole('button', { name: /next|start exploring/i }));
        backButton = screen.getByRole('button', { name: /back/i });
        expect(backButton).toBeEnabled();
      }
    });

    it('should handle multiple skip and cancel cycles', async () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // First skip attempt - cancel
      fireEvent.click(screen.getByText('Skip Tutorial'));
      await waitFor(() => {
        expect(screen.getByText('Skip Tutorial?')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      // Second skip attempt - cancel
      await waitFor(() => {
        expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Skip Tutorial'));
      await waitFor(() => {
        expect(screen.getByText('Skip Tutorial?')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      // Third skip attempt - confirm
      await waitFor(() => {
        expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Skip Tutorial'));
      await waitFor(() => {
        expect(screen.getByText('Skip Tutorial?')).toBeInTheDocument();
      });

      const skipButtons = screen.getAllByRole('button', { name: /skip/i });
      fireEvent.click(skipButtons[skipButtons.length - 1]);

      // onComplete should be called (only once, on the third attempt)
      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledTimes(1);
      });
    });

    it('should call onComplete when clicking Start Exploring', async () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Navigate to Step 5
      for (let i = 0; i < 4; i++) {
        fireEvent.click(screen.getByRole('button', { name: /next/i }));
      }

      // Click Start Exploring
      const startButton = screen.getByRole('button', { name: /start exploring/i });
      fireEvent.click(startButton);

      // onComplete should be called
      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalled();
      });
    });

    it('should maintain step state when navigating back and forth', () => {
      const mockOnComplete = vi.fn();
      render(<OnboardingWizard onComplete={mockOnComplete} />);

      // Navigate to Step 3
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(screen.getByText('Step 3 of 5')).toBeInTheDocument();
      expect(screen.getByText('Ask Your First Question')).toBeInTheDocument();

      // Navigate back to Step 1
      fireEvent.click(screen.getByRole('button', { name: /back/i }));
      fireEvent.click(screen.getByRole('button', { name: /back/i }));
      expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
      expect(screen.getByText('Welcome to LumiKB!')).toBeInTheDocument();

      // Navigate forward to Step 3 again (should render correctly)
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      fireEvent.click(screen.getByRole('button', { name: /next/i }));
      expect(screen.getByText('Step 3 of 5')).toBeInTheDocument();
      expect(screen.getByText('Ask Your First Question')).toBeInTheDocument();
    });
  });
});
