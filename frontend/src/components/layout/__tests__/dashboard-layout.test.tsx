import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardLayout } from '../dashboard-layout';

// Mock child components
vi.mock('@/components/layout/header', () => ({
  Header: ({ showMenuButton }: { showMenuButton?: boolean }) => (
    <header data-testid="header" data-show-menu={showMenuButton}>
      Header
    </header>
  ),
}));

vi.mock('@/components/layout/kb-sidebar', () => ({
  KbSidebar: () => <nav data-testid="kb-sidebar">KbSidebar</nav>,
}));

vi.mock('@/components/layout/citations-panel', () => ({
  CitationsPanel: ({ isCollapsed }: { isCollapsed?: boolean }) => (
    <aside data-testid="citations-panel" data-collapsed={isCollapsed}>
      CitationsPanel
    </aside>
  ),
}));

vi.mock('@/components/layout/mobile-nav', () => ({
  MobileNav: () => <nav data-testid="mobile-nav">MobileNav</nav>,
}));

// Mock responsive layout hook
const mockResponsive = {
  isDesktop: true,
  isLaptop: false,
  isTablet: false,
  isMobile: false,
};

vi.mock('@/hooks/use-responsive-layout', () => ({
  useResponsiveLayout: () => mockResponsive,
}));

describe('DashboardLayout', () => {
  beforeEach(() => {
    // Reset to desktop by default
    mockResponsive.isDesktop = true;
    mockResponsive.isLaptop = false;
    mockResponsive.isTablet = false;
    mockResponsive.isMobile = false;
  });

  it('renders header', () => {
    render(<DashboardLayout>Content</DashboardLayout>);

    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  it('renders children content', () => {
    render(<DashboardLayout>Test Content</DashboardLayout>);

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders sidebar on desktop', () => {
    mockResponsive.isDesktop = true;
    mockResponsive.isLaptop = false;

    render(<DashboardLayout>Content</DashboardLayout>);

    expect(screen.getByTestId('kb-sidebar')).toBeInTheDocument();
  });

  it('renders citations panel on desktop', () => {
    mockResponsive.isDesktop = true;

    render(<DashboardLayout>Content</DashboardLayout>);

    expect(screen.getByTestId('citations-panel')).toBeInTheDocument();
  });

  it('hides mobile nav on desktop', () => {
    mockResponsive.isDesktop = true;
    mockResponsive.isMobile = false;

    render(<DashboardLayout>Content</DashboardLayout>);

    expect(screen.queryByTestId('mobile-nav')).not.toBeInTheDocument();
  });

  it('shows mobile nav on mobile viewport', () => {
    mockResponsive.isDesktop = false;
    mockResponsive.isLaptop = false;
    mockResponsive.isTablet = false;
    mockResponsive.isMobile = true;

    render(<DashboardLayout>Content</DashboardLayout>);

    expect(screen.getByTestId('mobile-nav')).toBeInTheDocument();
  });

  it('shows menu button on tablet', () => {
    mockResponsive.isDesktop = false;
    mockResponsive.isLaptop = false;
    mockResponsive.isTablet = true;
    mockResponsive.isMobile = false;

    render(<DashboardLayout>Content</DashboardLayout>);

    const header = screen.getByTestId('header');
    expect(header).toHaveAttribute('data-show-menu', 'true');
  });
});
