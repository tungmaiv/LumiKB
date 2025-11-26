import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { CitationMarker } from '../citation-marker';

describe('CitationMarker', () => {
  it('renders citation number', () => {
    const onClick = vi.fn();
    render(<CitationMarker number={1} onClick={onClick} />);

    expect(screen.getByText('[1]')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();

    render(<CitationMarker number={1} onClick={onClick} />);

    await user.click(screen.getByText('[1]'));

    expect(onClick).toHaveBeenCalledWith(1);
  });

  it('calls onClick when Enter key is pressed', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();

    render(<CitationMarker number={1} onClick={onClick} />);

    const marker = screen.getByRole('button');
    marker.focus();
    await user.keyboard('{Enter}');

    expect(onClick).toHaveBeenCalledWith(1);
  });

  it('has correct ARIA label with document name', () => {
    const onClick = vi.fn();

    render(<CitationMarker number={2} onClick={onClick} documentName="Architecture Guide.pdf" />);

    const marker = screen.getByRole('button');
    expect(marker).toHaveAccessibleName('Citation 2 from Architecture Guide.pdf');
  });
});
