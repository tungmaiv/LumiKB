/**
 * Queue status card component for displaying queue metrics.
 *
 * Shows:
 * - Queue name
 * - Pending tasks count
 * - Active tasks count
 * - Workers online/offline count
 * - Visual status indicators (green/yellow/red)
 *
 * Clickable to open TaskListModal with task details.
 */

import { Server, Activity, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { QueueStatus } from "@/types/queue";

interface QueueStatusCardProps {
  queue: QueueStatus;
  onClick?: () => void;
}

export function QueueStatusCard({ queue, onClick }: QueueStatusCardProps) {
  // Calculate workers online/offline
  const workersOnline = queue.workers.filter((w) => w.status === "online").length;
  const workersOffline = queue.workers.filter((w) => w.status === "offline").length;
  const totalWorkers = queue.workers.length;

  // Determine status color
  const getStatusColor = () => {
    if (queue.status === "unavailable") return "destructive";
    if (totalWorkers === 0) return "destructive"; // No workers
    if (queue.pending_tasks > 100) return "secondary"; // Warning: high backlog
    return "default"; // Healthy
  };

  const statusColor = getStatusColor();

  return (
    <Card
      className={`cursor-pointer hover:bg-accent transition-colors ${
        queue.status === "unavailable" ? "border-destructive" : ""
      }`}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {queue.queue_name}
        </CardTitle>
        <Server className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {queue.status === "unavailable" ? (
          <div className="flex items-center gap-2 text-sm text-destructive">
            <AlertTriangle className="h-4 w-4" />
            <span>Unavailable</span>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-4 mb-3">
              <div>
                <div className="text-2xl font-bold">{queue.pending_tasks}</div>
                <p className="text-xs text-muted-foreground">Pending</p>
              </div>
              <div>
                <div className="text-2xl font-bold">{queue.active_tasks}</div>
                <p className="text-xs text-muted-foreground">Active</p>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {workersOnline > 0 && (
                    <span className="text-green-600 font-medium">
                      {workersOnline} online
                    </span>
                  )}
                  {workersOnline > 0 && workersOffline > 0 && ", "}
                  {workersOffline > 0 && (
                    <span className="text-destructive font-medium">
                      {workersOffline} offline
                    </span>
                  )}
                  {totalWorkers === 0 && (
                    <span className="text-muted-foreground">No workers</span>
                  )}
                </span>
              </div>

              <Badge variant={statusColor}>
                {totalWorkers === 0
                  ? "No Workers"
                  : queue.pending_tasks > 100
                  ? "High Load"
                  : "Healthy"}
              </Badge>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
