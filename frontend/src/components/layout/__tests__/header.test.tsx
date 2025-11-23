import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Header } from '../header';

// Mock UserMenu component
vi.mock('@/components/layout/user-menu', () => ({
  UserMenu: () => <div data-testid="user-menu">UserMenu</div>,
}));

// Mock SearchBar component
vi.mock('@/components/search/search-bar', () => ({
  SearchBar: ({ disabled, placeholder }: { disabled?: boolean; placeholder?: string }) => (
    <input
      data-testid="search-bar"
      disabled={disabled}
      placeholder={placeholder}
      aria-label="search"
    />
  ),
}));

describe('Header', () => {
  it('renders the LumiKB logo', () => {
    render(<Header />);

    expect(screen.getByText('LumiKB')).toBeInTheDocument();
  });

  it('renders the search bar placeholder', () => {
    render(<Header />);

    const searchBar = screen.getByTestId('search-bar');
    expect(searchBar).toBeInTheDocument();
    expect(searchBar).toBeDisabled();
  });

  it('renders the user menu', () => {
    render(<Header />);

    expect(screen.getByTestId('user-menu')).toBeInTheDocument();
  });

  it('shows menu button when showMenuButton is true', () => {
    render(<Header showMenuButton={true} />);

    expect(screen.getByRole('button', { name: /toggle sidebar/i })).toBeInTheDocument();
  });

  it('hides menu button by default', () => {
    render(<Header />);

    expect(screen.queryByRole('button', { name: /toggle sidebar/i })).not.toBeInTheDocument();
  });

  it('calls onMenuClick when menu button is clicked', async () => {
    const handleMenuClick = vi.fn();
    const user = userEvent.setup();

    render(<Header showMenuButton={true} onMenuClick={handleMenuClick} />);

    const menuButton = screen.getByRole('button', { name: /toggle sidebar/i });
    await user.click(menuButton);

    expect(handleMenuClick).toHaveBeenCalledTimes(1);
  });
});
