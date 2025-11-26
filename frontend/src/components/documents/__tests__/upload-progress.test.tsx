import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UploadProgress } from '../upload-progress';
import type { UploadFile } from '@/lib/hooks/use-file-upload';

// Helper to create mock files
function createMockFile(overrides: Partial<UploadFile> = {}): UploadFile {
  const file = new File(['test content'], 'test-file.pdf', {
    type: 'application/pdf',
  });

  return {
    id: 'test-id-1',
    file,
    status: 'pending',
    progress: 0,
    ...overrides,
  };
}

describe('UploadProgress', () => {
  it('renders nothing when files array is empty', () => {
    const { container } = render(<UploadProgress files={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('displays file name for pending file', () => {
    const mockFile = createMockFile({ status: 'pending' });
    render(<UploadProgress files={[mockFile]} />);

    expect(screen.getByText('test-file.pdf')).toBeInTheDocument();
  });

  it('displays file size for file', () => {
    const file = new File(['x'.repeat(1024)], 'test.pdf', {
      type: 'application/pdf',
    });
    const mockFile = createMockFile({ file, status: 'pending' });

    render(<UploadProgress files={[mockFile]} />);

    // File size should be displayed (approximately 1 KB)
    expect(screen.getByText(/KB|B/)).toBeInTheDocument();
  });

  it('displays progress percentage for uploading file', () => {
    const mockFile = createMockFile({ status: 'uploading', progress: 45 });
    render(<UploadProgress files={[mockFile]} />);

    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('displays progress bar for uploading file', () => {
    const mockFile = createMockFile({ status: 'uploading', progress: 50 });
    render(<UploadProgress files={[mockFile]} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('shows cancel button for pending files', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    const mockFile = createMockFile({ status: 'pending' });

    render(<UploadProgress files={[mockFile]} onCancel={onCancel} />);

    const cancelButton = screen.getByTitle('Cancel upload');
    expect(cancelButton).toBeInTheDocument();

    await user.click(cancelButton);
    expect(onCancel).toHaveBeenCalledWith('test-id-1');
  });

  it('shows retry button for failed files', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    const mockFile = createMockFile({
      status: 'failed',
      error: 'Network error',
    });

    render(<UploadProgress files={[mockFile]} onRetry={onRetry} />);

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();

    await user.click(retryButton);
    expect(onRetry).toHaveBeenCalledWith('test-id-1');
  });

  it('displays error message for failed files', () => {
    const mockFile = createMockFile({
      status: 'failed',
      error: 'File too large',
    });

    render(<UploadProgress files={[mockFile]} />);

    // Error message appears in multiple places (error paragraph + status text)
    const errorMessages = screen.getAllByText('File too large');
    expect(errorMessages.length).toBeGreaterThan(0);
  });

  it('shows success state for completed files', () => {
    const mockFile = createMockFile({
      status: 'completed',
      progress: 100,
    });

    render(<UploadProgress files={[mockFile]} />);

    expect(screen.getByText('Complete')).toBeInTheDocument();
  });

  it('renders multiple files', () => {
    const files: UploadFile[] = [
      createMockFile({ id: '1', file: new File([''], 'file1.pdf') }),
      createMockFile({ id: '2', file: new File([''], 'file2.docx') }),
      createMockFile({ id: '3', file: new File([''], 'file3.md') }),
    ];

    render(<UploadProgress files={files} />);

    expect(screen.getByText('file1.pdf')).toBeInTheDocument();
    expect(screen.getByText('file2.docx')).toBeInTheDocument();
    expect(screen.getByText('file3.md')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const mockFile = createMockFile();
    render(<UploadProgress files={[mockFile]} className="custom-class" />);

    const wrapper = screen.getByText('test-file.pdf').closest('.space-y-2');
    expect(wrapper).toHaveClass('custom-class');
  });
});
