import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  DocumentTagInput,
  DocumentTagsDisplay,
  MAX_TAGS_PER_DOCUMENT,
  MAX_TAG_LENGTH,
} from '../document-tag-input';

describe('DocumentTagInput', () => {
  describe('rendering', () => {
    it('renders input field', () => {
      render(<DocumentTagInput tags={[]} onTagsChange={() => {}} />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with custom placeholder', () => {
      render(
        <DocumentTagInput tags={[]} onTagsChange={() => {}} placeholder="Custom placeholder" />
      );
      expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
    });

    it('displays existing tags as chips', () => {
      render(<DocumentTagInput tags={['python', 'api', 'testing']} onTagsChange={() => {}} />);
      expect(screen.getByText('python')).toBeInTheDocument();
      expect(screen.getByText('api')).toBeInTheDocument();
      expect(screen.getByText('testing')).toBeInTheDocument();
    });

    it('shows remove button for each tag', () => {
      render(<DocumentTagInput tags={['python']} onTagsChange={() => {}} />);
      expect(screen.getByRole('button', { name: /remove python/i })).toBeInTheDocument();
    });
  });

  describe('adding tags', () => {
    it('adds tag when Enter is pressed', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      expect(onTagsChange).toHaveBeenCalledWith(['newtag']);
    });

    it('adds tag when comma is pressed', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag,');

      expect(onTagsChange).toHaveBeenCalledWith(['newtag']);
    });

    it('adds tag on blur', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag');
      fireEvent.blur(input);

      expect(onTagsChange).toHaveBeenCalledWith(['newtag']);
    });

    it('normalizes tags to lowercase', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'UPPERCASE{Enter}');

      expect(onTagsChange).toHaveBeenCalledWith(['uppercase']);
    });

    it('trims whitespace from tags', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, '  trimmed  {Enter}');

      expect(onTagsChange).toHaveBeenCalledWith(['trimmed']);
    });

    it('prevents duplicate tags', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={['existing']} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'existing{Enter}');

      // Should not be called since tag already exists
      expect(onTagsChange).not.toHaveBeenCalled();
    });

    it('does not add empty tags', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, '   {Enter}');

      expect(onTagsChange).not.toHaveBeenCalled();
    });

    it('truncates tags to max length', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();
      const longTag = 'a'.repeat(100);

      render(<DocumentTagInput tags={[]} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, `${longTag}{Enter}`);

      expect(onTagsChange).toHaveBeenCalledWith(['a'.repeat(MAX_TAG_LENGTH)]);
    });
  });

  describe('removing tags', () => {
    it('removes tag when X button is clicked', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={['python', 'api']} onTagsChange={onTagsChange} />);

      const removeButton = screen.getByRole('button', { name: /remove python/i });
      await user.click(removeButton);

      expect(onTagsChange).toHaveBeenCalledWith(['api']);
    });

    it('removes last tag on Backspace when input is empty', async () => {
      const onTagsChange = vi.fn();
      const user = userEvent.setup();

      render(<DocumentTagInput tags={['first', 'second']} onTagsChange={onTagsChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, '{Backspace}');

      expect(onTagsChange).toHaveBeenCalledWith(['first']);
    });
  });

  describe('max tags limit', () => {
    it('disables input when max tags reached', () => {
      const tags = Array.from({ length: MAX_TAGS_PER_DOCUMENT }, (_, i) => `tag${i}`);
      render(<DocumentTagInput tags={tags} onTagsChange={() => {}} />);

      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });

    it('shows max tags message when limit reached', () => {
      const tags = Array.from({ length: MAX_TAGS_PER_DOCUMENT }, (_, i) => `tag${i}`);
      render(<DocumentTagInput tags={tags} onTagsChange={() => {}} />);

      expect(screen.getByPlaceholderText('Maximum tags reached')).toBeInTheDocument();
    });

    it('does not add tag when at max', async () => {
      const onTagsChange = vi.fn();
      const tags = Array.from({ length: MAX_TAGS_PER_DOCUMENT }, (_, i) => `tag${i}`);

      render(<DocumentTagInput tags={tags} onTagsChange={onTagsChange} />);

      // Input should be disabled at max
      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });
  });

  describe('disabled state', () => {
    it('disables input when disabled prop is true', () => {
      render(<DocumentTagInput tags={[]} onTagsChange={() => {}} disabled />);

      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });

    it('disables remove buttons when disabled', () => {
      render(<DocumentTagInput tags={['python']} onTagsChange={() => {}} disabled />);

      const removeButton = screen.getByRole('button', { name: /remove python/i });
      expect(removeButton).toBeDisabled();
    });
  });
});

describe('DocumentTagsDisplay', () => {
  it('renders nothing when tags is empty', () => {
    const { container } = render(<DocumentTagsDisplay tags={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('displays all tags when under maxVisible', () => {
    render(<DocumentTagsDisplay tags={['python', 'api']} maxVisible={5} />);

    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText('api')).toBeInTheDocument();
  });

  it('shows +N more when over maxVisible', () => {
    render(<DocumentTagsDisplay tags={['tag1', 'tag2', 'tag3', 'tag4', 'tag5']} maxVisible={3} />);

    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
    expect(screen.getByText('tag3')).toBeInTheDocument();
    expect(screen.getByText('+2 more')).toBeInTheDocument();
    expect(screen.queryByText('tag4')).not.toBeInTheDocument();
    expect(screen.queryByText('tag5')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<DocumentTagsDisplay tags={['python']} className="custom-class" />);

    const container = screen.getByText('python').parentElement;
    expect(container).toHaveClass('custom-class');
  });
});
