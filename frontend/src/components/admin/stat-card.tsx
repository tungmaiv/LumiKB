import { LucideIcon } from 'lucide-react';
import { Line, LineChart, ResponsiveContainer } from 'recharts';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: number[];
  trendColor?: string;
  onClick?: () => void;
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendColor = '#3b82f6',
  onClick,
}: StatCardProps) {
  const chartData = trend?.map((value, index) => ({ index, value })) || [];

  return (
    <Card
      className={onClick ? 'cursor-pointer hover:bg-accent transition-colors' : ''}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend && trend.length > 0 && (
          <div className="mt-4">
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={chartData}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={trendColor}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
