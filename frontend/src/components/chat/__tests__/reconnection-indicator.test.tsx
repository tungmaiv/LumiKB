/**
 * ReconnectionIndicator Component Tests - Epic 7, Story 7-22
 * Tests for reconnection status display and user interactions
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ReconnectionIndicator, ReconnectionIndicatorInline } from '../reconnection-indicator';

describe('ReconnectionIndicator', () => {
  const defaultProps = {
    isReconnecting: false,
    attemptCount: 0,
    maxRetries: 5,
    maxRetriesExceeded: false,
    error: null,
    nextRetryIn: 0,
    isPolling: false,
    onRetry: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('no render conditions', () => {
    it('renders nothing when connection is normal', () => {
      const { container } = render(<ReconnectionIndicator {...defaultProps} />);
      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('reconnecting state (AC-7.22.1, AC-7.22.2)', () => {
    it('shows reconnecting indicator when isReconnecting is true', () => {
      render(<ReconnectionIndicator {...defaultProps} isReconnecting={true} attemptCount={2} />);

      expect(screen.getByTestId('reconnecting-indicator')).toBeInTheDocument();
      expect(screen.getByText('Reconnecting...')).toBeInTheDocument();
    });

    it('displays attempt count and max retries', () => {
      render(
        <ReconnectionIndicator
          {...defaultProps}
          isReconnecting={true}
          attemptCount={3}
          maxRetries={5}
        />
      );

      expect(screen.getByTestId('attempt-count')).toHaveTextContent('Attempt 3 of 5');
    });

    it('shows countdown timer when nextRetryIn > 0', () => {
      render(
        <ReconnectionIndicator
          {...defaultProps}
          isReconnecting={true}
          attemptCount={2}
          nextRetryIn={3500}
        />
      );

      expect(screen.getByText(/retrying in 4s/)).toBeInTheDocument();
    });

    it('shows progress bar during reconnection', () => {
      render(
        <ReconnectionIndicator
          {...defaultProps}
          isReconnecting={true}
          attemptCount={2}
          maxRetries={5}
        />
      );

      expect(screen.getByTestId('reconnection-progress')).toBeInTheDocument();
    });
  });

  describe('connection lost state (AC-7.22.4)', () => {
    it('shows error when maxRetriesExceeded is true', () => {
      render(
        <ReconnectionIndicator
          {...defaultProps}
          maxRetriesExceeded={true}
          error="Connection lost. Please refresh."
        />
      );

      expect(screen.getByTestId('connection-lost-indicator')).toBeInTheDocument();
      expect(screen.getByText('Connection Lost')).toBeInTheDocument();
      expect(screen.getByText('Connection lost. Please refresh.')).toBeInTheDocument();
    });

    it('shows retry button when connection lost', () => {
      const onRetry = vi.fn();
      render(
        <ReconnectionIndicator {...defaultProps} maxRetriesExceeded={true} onRetry={onRetry} />
      );

      const retryButton = screen.getByTestId('retry-button');
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('shows "Use Polling" button when onEnablePolling provided', () => {
      const onEnablePolling = vi.fn();
      render(
        <ReconnectionIndicator
          {...defaultProps}
          maxRetriesExceeded={true}
          onEnablePolling={onEnablePolling}
        />
      );

      const pollingButton = screen.getByTestId('enable-polling-button');
      expect(pollingButton).toBeInTheDocument();
      expect(pollingButton).toHaveTextContent('Use Polling');

      fireEvent.click(pollingButton);
      expect(onEnablePolling).toHaveBeenCalledTimes(1);
    });

    it('does not show "Use Polling" button when onEnablePolling not provided', () => {
      render(<ReconnectionIndicator {...defaultProps} maxRetriesExceeded={true} />);

      expect(screen.queryByTestId('enable-polling-button')).not.toBeInTheDocument();
    });
  });

  describe('polling state (AC-7.22.5)', () => {
    it('shows polling indicator when isPolling is true', () => {
      render(<ReconnectionIndicator {...defaultProps} isPolling={true} />);

      expect(screen.getByTestId('polling-indicator')).toBeInTheDocument();
      expect(screen.getByText('Polling Mode Active')).toBeInTheDocument();
    });

    it('shows informational message about polling', () => {
      render(<ReconnectionIndicator {...defaultProps} isPolling={true} />);

      expect(
        screen.getByText(/Using polling fallback due to connection issues/)
      ).toBeInTheDocument();
    });

    it('shows "Disable Polling" button when onDisablePolling provided', () => {
      const onDisablePolling = vi.fn();
      render(
        <ReconnectionIndicator
          {...defaultProps}
          isPolling={true}
          onDisablePolling={onDisablePolling}
        />
      );

      const disableButton = screen.getByTestId('disable-polling-button');
      expect(disableButton).toBeInTheDocument();

      fireEvent.click(disableButton);
      expect(onDisablePolling).toHaveBeenCalledTimes(1);
    });
  });

  describe('state priority', () => {
    it('shows polling state over reconnecting state', () => {
      render(<ReconnectionIndicator {...defaultProps} isReconnecting={true} isPolling={true} />);

      expect(screen.getByTestId('polling-indicator')).toBeInTheDocument();
      expect(screen.queryByTestId('reconnecting-indicator')).not.toBeInTheDocument();
    });

    it('shows error state over reconnecting state', () => {
      render(
        <ReconnectionIndicator {...defaultProps} isReconnecting={true} maxRetriesExceeded={true} />
      );

      expect(screen.getByTestId('connection-lost-indicator')).toBeInTheDocument();
      expect(screen.queryByTestId('reconnecting-indicator')).not.toBeInTheDocument();
    });
  });
});

describe('ReconnectionIndicatorInline', () => {
  const defaultProps = {
    isReconnecting: false,
    attemptCount: 0,
    maxRetries: 5,
    maxRetriesExceeded: false,
    isPolling: false,
    onRetry: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when connection is normal', () => {
    const { container } = render(<ReconnectionIndicatorInline {...defaultProps} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows compact reconnecting indicator', () => {
    render(
      <ReconnectionIndicatorInline
        {...defaultProps}
        isReconnecting={true}
        attemptCount={2}
        maxRetries={5}
      />
    );

    expect(screen.getByTestId('reconnecting-indicator-inline')).toBeInTheDocument();
    expect(screen.getByText('Reconnecting (2/5)')).toBeInTheDocument();
  });

  it('shows compact disconnected indicator with retry button', () => {
    const onRetry = vi.fn();
    render(
      <ReconnectionIndicatorInline {...defaultProps} maxRetriesExceeded={true} onRetry={onRetry} />
    );

    expect(screen.getByTestId('connection-lost-inline')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toBeInTheDocument();

    const retryButton = screen.getByTestId('retry-button-inline');
    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('shows compact polling indicator', () => {
    render(<ReconnectionIndicatorInline {...defaultProps} isPolling={true} />);

    expect(screen.getByTestId('polling-indicator-inline')).toBeInTheDocument();
    expect(screen.getByText('Polling')).toBeInTheDocument();
  });
});
