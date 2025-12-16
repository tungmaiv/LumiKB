/**
 * FilterTabs Component (Story 7-27, AC-7.27.11-14)
 *
 * Tab-based filter for queue tasks:
 * - All: Show all tasks
 * - Active: Show currently processing tasks
 * - Pending: Show queued/waiting tasks
 * - Failed: Show failed tasks with count badge
 */

export type FilterType = 'all' | 'active' | 'pending' | 'failed';

export interface FilterCounts {
  all: number;
  active: number;
  pending: number;
  failed: number;
}

interface FilterTabsProps {
  activeFilter: FilterType;
  onFilterChange: (filter: FilterType) => void;
  counts: FilterCounts;
}

const tabs: { key: FilterType; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'pending', label: 'Pending' },
  { key: 'failed', label: 'Failed' },
];

export function FilterTabs({ activeFilter, onFilterChange, counts }: FilterTabsProps) {
  return (
    <div role="tablist" data-testid="filter-tabs" className="flex border-b border-gray-200 mb-4">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          role="tab"
          aria-selected={activeFilter === key}
          aria-controls={`${key}-panel`}
          data-testid={`tab-${key}`}
          onClick={() => onFilterChange(key)}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeFilter === key
              ? 'active-tab border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          {label}
          {key === 'failed' && counts.failed > 0 && (
            <span
              data-testid="failed-count-badge"
              className="badge ml-2 px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full"
            >
              ({counts.failed})
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
