'use client';

/**
 * Feedback Analytics Dashboard - Story 7-23
 *
 * Admin-only page displaying feedback analytics:
 * - AC-7.23.1: Admin dashboard page at /admin/feedback
 * - AC-7.23.2: Pie chart for feedback type distribution
 * - AC-7.23.3: Line chart for 30-day trend
 * - AC-7.23.4: Table of 20 most recent feedback items
 * - AC-7.23.5: Modal for feedback detail view
 */

import { useState, useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  type PieLabelRenderProps,
} from 'recharts';
import {
  MessageSquare,
  TrendingUp,
  Clock,
  AlertCircle,
  ChevronLeft,
  ExternalLink,
  Calendar,
} from 'lucide-react';
import Link from 'next/link';
import { format, parseISO } from 'date-fns';

import { useFeedbackAnalytics, RecentFeedbackItem } from '@/hooks/useFeedbackAnalytics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Chart colors for pie chart segments
const CHART_COLORS = [
  '#3b82f6', // blue
  '#ef4444', // red
  '#f59e0b', // amber
  '#10b981', // emerald
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
];

// Feedback type display labels
const FEEDBACK_TYPE_LABELS: Record<string, string> = {
  not_relevant: 'Not Relevant',
  inaccurate: 'Inaccurate',
  incomplete: 'Incomplete',
  outdated: 'Outdated',
  other: 'Other',
  unknown: 'Unknown',
};

/**
 * Get human-readable label for feedback type
 */
function getFeedbackTypeLabel(type: string): string {
  return FEEDBACK_TYPE_LABELS[type] || type;
}

/**
 * Format date for display
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy HH:mm');
  } catch {
    return dateStr;
  }
}

/**
 * Aggregate daily data into weekly buckets for trend chart
 */
function aggregateToWeekly(dailyData: Array<{ date: string; count: number }>) {
  const weeklyMap = new Map<string, number>();

  dailyData.forEach(({ date, count }) => {
    const d = parseISO(date);
    // Get the start of the week (Sunday)
    const weekStart = new Date(d);
    weekStart.setDate(d.getDate() - d.getDay());
    const weekKey = format(weekStart, 'MMM d');

    weeklyMap.set(weekKey, (weeklyMap.get(weekKey) || 0) + count);
  });

  return Array.from(weeklyMap.entries()).map(([date, count]) => ({
    date,
    count,
  }));
}

export default function FeedbackAnalyticsPage() {
  const { data, isLoading, error } = useFeedbackAnalytics();
  const [selectedFeedback, setSelectedFeedback] = useState<RecentFeedbackItem | null>(null);
  const [trendView, setTrendView] = useState<'daily' | 'weekly'>('daily');

  // Prepare trend chart data based on view toggle (AC-7.23.3)
  const trendChartData = useMemo(() => {
    if (!data?.by_day) return [];

    if (trendView === 'weekly') {
      return aggregateToWeekly(data.by_day);
    }

    // For daily view, format dates nicely and limit to last 14 days for readability
    return data.by_day.slice(-14).map(({ date, count }) => ({
      date: format(parseISO(date), 'MMM d'),
      count,
    }));
  }, [data?.by_day, trendView]);

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-[300px]" />
          <Skeleton className="h-[300px]" />
        </div>
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : 'Failed to load feedback analytics'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // No data state
  if (!data) {
    return (
      <div className="container mx-auto py-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>No Data</AlertTitle>
          <AlertDescription>No feedback data available yet.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header with back navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin">
            <Button variant="ghost" size="icon">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <MessageSquare className="h-6 w-6" />
              Feedback Analytics
            </h1>
            <p className="text-muted-foreground">
              User feedback on generated documents
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold">{data.total_count}</p>
          <p className="text-sm text-muted-foreground">Total Feedback</p>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Pie Chart - Feedback by Type (AC-7.23.2) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Feedback by Type
            </CardTitle>
            <CardDescription>Distribution of feedback categories</CardDescription>
          </CardHeader>
          <CardContent>
            {data.by_type.length === 0 ? (
              <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                No feedback data
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={data.by_type.map((item) => ({
                      ...item,
                      name: item.type,
                    }))}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(props: PieLabelRenderProps) => {
                      const name = String(props.name ?? '');
                      const percent = typeof props.percent === 'number' ? props.percent : 0;
                      return `${getFeedbackTypeLabel(name)} (${(percent * 100).toFixed(0)}%)`;
                    }}
                    labelLine={false}
                  >
                    {data.by_type.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name) => [
                      value,
                      getFeedbackTypeLabel(String(name)),
                    ]}
                  />
                  <Legend
                    formatter={(value) => getFeedbackTypeLabel(String(value))}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Line Chart - Feedback Trend (AC-7.23.3) */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Feedback Trend
                </CardTitle>
                <CardDescription>Feedback submissions over time</CardDescription>
              </div>
              <Select
                value={trendView}
                onValueChange={(value: 'daily' | 'weekly') => setTrendView(value)}
              >
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {trendChartData.length === 0 ? (
              <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                No trend data
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trendChartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    name="Feedback Count"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', strokeWidth: 2 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Feedback Table (AC-7.23.4) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Recent Feedback
          </CardTitle>
          <CardDescription>Most recent 20 feedback submissions</CardDescription>
        </CardHeader>
        <CardContent>
          {data.recent.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              No recent feedback
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Comments</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.recent.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-3 w-3 text-muted-foreground" />
                        {formatDate(item.timestamp)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {item.user_email || (
                        <span className="text-muted-foreground">Anonymous</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          item.feedback_type === 'inaccurate' ||
                          item.feedback_type === 'not_relevant'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {getFeedbackTypeLabel(item.feedback_type || 'unknown')}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate">
                      {item.feedback_comments || (
                        <span className="text-muted-foreground italic">No comments</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedFeedback(item)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Feedback Detail Modal (AC-7.23.5) */}
      <Dialog
        open={!!selectedFeedback}
        onOpenChange={(open) => !open && setSelectedFeedback(null)}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Feedback Details</DialogTitle>
            <DialogDescription>
              Detailed view of the feedback submission
            </DialogDescription>
          </DialogHeader>
          {selectedFeedback && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Date</p>
                  <p>{formatDate(selectedFeedback.timestamp)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Type</p>
                  <Badge
                    variant={
                      selectedFeedback.feedback_type === 'inaccurate' ||
                      selectedFeedback.feedback_type === 'not_relevant'
                        ? 'destructive'
                        : 'secondary'
                    }
                  >
                    {getFeedbackTypeLabel(selectedFeedback.feedback_type || 'unknown')}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">User</p>
                  <p>{selectedFeedback.user_email || 'Anonymous'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">User ID</p>
                  <p className="text-xs font-mono truncate">
                    {selectedFeedback.user_id || 'N/A'}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Comments</p>
                <p className="bg-muted p-3 rounded-md text-sm">
                  {selectedFeedback.feedback_comments || (
                    <span className="italic text-muted-foreground">No comments provided</span>
                  )}
                </p>
              </div>

              {selectedFeedback.draft_id && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    Related Draft
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-muted px-2 py-1 rounded">
                      {selectedFeedback.draft_id}
                    </code>
                    <Link
                      href={`/drafts/${selectedFeedback.draft_id}`}
                      target="_blank"
                    >
                      <Button variant="ghost" size="sm">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View Draft
                      </Button>
                    </Link>
                  </div>
                </div>
              )}

              {selectedFeedback.related_request_id && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    Request ID
                  </p>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    {selectedFeedback.related_request_id}
                  </code>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
