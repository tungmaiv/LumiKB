/**
 * Component Tests: StatCard (Story 5-1, AC1, AC2)
 *
 * Test Coverage:
 * - Rendering with basic props
 * - Sparkline chart display
 * - Click handling for drill-down
 * - Icon display
 * - Description display
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Users } from 'lucide-react';
import { StatCard } from '../stat-card';

// Track Line component props for verification
let lastLineProps: Record<string, unknown> | null = null;

// Mock recharts since it doesn't render properly in JSDOM
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div className="recharts-responsive-container">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div className="recharts-line-chart">{children}</div>
  ),
  Line: (props: Record<string, unknown>) => {
    lastLineProps = props;
    return <div className="recharts-line" data-stroke={props.stroke} />;
  },
}));

describe('StatCard Component (Story 5-1)', () => {
  describe('[P1] Basic Rendering', () => {
    it('should render title and value', () => {
      render(<StatCard title="Total Users" value={100} />);

      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('should render numeric value correctly', () => {
      render(<StatCard title="Total KBs" value={50} />);

      expect(screen.getByText('50')).toBeInTheDocument();
    });

    it('should render string value correctly', () => {
      render(<StatCard title="Storage" value="1.5 GB" />);

      expect(screen.getByText('1.5 GB')).toBeInTheDocument();
    });

    it('should display description when provided', () => {
      render(<StatCard title="Active Users" value={80} description="+10 from last week" />);

      expect(screen.getByText('+10 from last week')).toBeInTheDocument();
    });

    it('should not display description when not provided', () => {
      const { container } = render(<StatCard title="Total Users" value={100} />);

      const description = container.querySelector('.text-xs.text-muted-foreground');
      expect(description).not.toBeInTheDocument();
    });
  });

  describe('[P1] Icon Display', () => {
    it('should display icon when provided', () => {
      const { container } = render(<StatCard title="Total Users" value={100} icon={Users} />);

      // Icon should be rendered (lucide-react renders as SVG)
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should not display icon when not provided', () => {
      const { container } = render(<StatCard title="Total Users" value={100} />);

      // Header should exist but no icon
      const icon = container.querySelector('.h-4.w-4');
      expect(icon).not.toBeInTheDocument();
    });
  });

  describe('[P1] Trend Chart Display (AC2)', () => {
    it('should display sparkline chart when trend data provided', () => {
      const trendData = Array.from({ length: 30 }, (_, i) => 90 + i);

      const { container } = render(<StatCard title="Searches" value={3000} trend={trendData} />);

      // Recharts renders chart container
      const chart = container.querySelector('.recharts-responsive-container');
      expect(chart).toBeInTheDocument();
    });

    it('should not display chart when trend data not provided', () => {
      const { container } = render(<StatCard title="Total Users" value={100} />);

      const chart = container.querySelector('.recharts-responsive-container');
      expect(chart).not.toBeInTheDocument();
    });

    it('should not display chart when trend is empty array', () => {
      const { container } = render(<StatCard title="Total Users" value={100} trend={[]} />);

      const chart = container.querySelector('.recharts-responsive-container');
      expect(chart).not.toBeInTheDocument();
    });

    it('should use custom trend color when provided', () => {
      const trendData = [1, 2, 3, 4, 5];
      const customColor = '#10b981'; // green
      lastLineProps = null;

      render(<StatCard title="Searches" value={100} trend={trendData} trendColor={customColor} />);

      // Line component should receive custom color as stroke prop
      expect(lastLineProps).not.toBeNull();
      expect((lastLineProps as unknown as Record<string, unknown>)?.stroke).toBe(customColor);
    });

    it('should use default trend color when not provided', () => {
      const trendData = [1, 2, 3, 4, 5];
      lastLineProps = null;

      render(<StatCard title="Searches" value={100} trend={trendData} />);

      // Line component should receive default blue as stroke prop
      expect(lastLineProps).not.toBeNull();
      expect((lastLineProps as unknown as Record<string, unknown>)?.stroke).toBe('#3b82f6');
    });
  });

  describe('[P2] Click Handling (AC3)', () => {
    it('should call onClick handler when clicked', () => {
      const handleClick = vi.fn();

      render(<StatCard title="Total Users" value={100} onClick={handleClick} />);

      const card = screen.getByText('Total Users').closest('.cursor-pointer');
      expect(card).toBeInTheDocument();

      fireEvent.click(card!);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should apply cursor-pointer class when onClick provided', () => {
      const handleClick = vi.fn();

      const { container } = render(
        <StatCard title="Total Users" value={100} onClick={handleClick} />
      );

      const card = container.querySelector('.cursor-pointer');
      expect(card).toBeInTheDocument();
    });

    it('should not apply cursor-pointer class when onClick not provided', () => {
      const { container } = render(<StatCard title="Total Users" value={100} />);

      const card = container.querySelector('.cursor-pointer');
      expect(card).not.toBeInTheDocument();
    });

    it('should apply hover styles when onClick provided', () => {
      const handleClick = vi.fn();

      const { container } = render(
        <StatCard title="Total Users" value={100} onClick={handleClick} />
      );

      const card = container.querySelector('.hover\\:bg-accent');
      expect(card).toBeInTheDocument();
    });
  });

  describe('[P2] Data Formatting', () => {
    it('should handle large numbers correctly', () => {
      render(<StatCard title="Total Documents" value={1000000} />);

      expect(screen.getByText('1000000')).toBeInTheDocument();
    });

    it('should handle zero value correctly', () => {
      render(<StatCard title="Failed Docs" value={0} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle formatted string values', () => {
      render(<StatCard title="Storage" value="1.5 GB" />);

      expect(screen.getByText('1.5 GB')).toBeInTheDocument();
    });
  });

  describe('[P2] Accessibility', () => {
    it('should have proper card structure', () => {
      const { container } = render(<StatCard title="Total Users" value={100} />);

      // Should use shadcn/ui Card component
      const card = container.querySelector('[class*="card"]');
      expect(card).toBeInTheDocument();
    });

    it('should have readable text hierarchy', () => {
      render(<StatCard title="Total Users" value={100} description="Active users count" />);

      // Title should be visible
      expect(screen.getByText('Total Users')).toBeVisible();

      // Value should be prominent (font-bold)
      const value = screen.getByText('100');
      expect(value).toHaveClass('text-2xl', 'font-bold');
    });
  });

  describe('[P2] Edge Cases', () => {
    it('should handle trend with single data point', () => {
      const { container } = render(<StatCard title="Searches" value={100} trend={[50]} />);

      const chart = container.querySelector('.recharts-responsive-container');
      expect(chart).toBeInTheDocument();
    });

    it('should handle very long titles', () => {
      const longTitle = 'This is a very long title that might wrap to multiple lines in the card';

      render(<StatCard title={longTitle} value={100} />);

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('should handle very long values', () => {
      const longValue = '123,456,789 documents processed';

      render(<StatCard title="Documents" value={longValue} />);

      expect(screen.getByText(longValue)).toBeInTheDocument();
    });
  });
});
