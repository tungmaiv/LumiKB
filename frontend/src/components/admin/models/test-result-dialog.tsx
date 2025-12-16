/**
 * Dialog for displaying connection test results
 * Story 7-9: LLM Model Registry (AC-7.9.7)
 */

'use client';

import { CheckCircle, XCircle, Clock, Info, Hash, MessageSquare, Cpu, CheckCheck, AlertCircle, Brain } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { ConnectionTestResult } from '@/types/llm-model';

// Helper to format detail keys for display
function formatDetailKey(key: string): string {
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Get icon for specific detail keys
function getDetailIcon(key: string) {
  const iconMap: Record<string, React.ReactNode> = {
    dimensions: <Hash className="h-4 w-4 text-blue-500" />,
    expected_dimensions: <Hash className="h-4 w-4 text-muted-foreground" />,
    dimensions_match: <CheckCheck className="h-4 w-4 text-green-500" />,
    model_name: <Cpu className="h-4 w-4 text-purple-500" />,
    response_preview: <MessageSquare className="h-4 w-4 text-blue-500" />,
    tokens_used: <Hash className="h-4 w-4 text-orange-500" />,
    error_type: <AlertCircle className="h-4 w-4 text-red-500" />,
    has_reasoning: <Brain className="h-4 w-4 text-indigo-500" />,
    is_json_response: <CheckCheck className="h-4 w-4 text-green-500" />,
  };
  return iconMap[key] || <Info className="h-4 w-4 text-muted-foreground" />;
}

// Format detail value for display
function formatDetailValue(key: string, value: unknown): React.ReactNode {
  if (typeof value === 'boolean') {
    return value ? (
      <span className="text-green-600 font-medium">Yes</span>
    ) : (
      <span className="text-red-600 font-medium">No</span>
    );
  }
  if (typeof value === 'number') {
    return <span className="font-mono text-sm">{value.toLocaleString()}</span>;
  }
  if (key === 'response_preview' && typeof value === 'string') {
    // Show response preview in a special format
    return (
      <span className="text-sm italic text-muted-foreground">
        &quot;{value.length > 80 ? `${value.slice(0, 80)}...` : value}&quot;
      </span>
    );
  }
  if (key === 'model_name' && typeof value === 'string') {
    return <code className="text-sm bg-muted px-1.5 py-0.5 rounded">{value}</code>;
  }
  return <span className="text-sm">{String(value)}</span>;
}

interface TestResultDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: ConnectionTestResult | null;
  modelName: string;
}

export function TestResultDialog({
  open,
  onOpenChange,
  result,
  modelName,
}: TestResultDialogProps) {
  if (!result) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {result.success ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-destructive" />
            )}
            Connection Test {result.success ? 'Passed' : 'Failed'}
          </DialogTitle>
          <DialogDescription>
            Test results for {modelName}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status Message */}
          <div
            className={`p-4 rounded-lg ${
              result.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <p className={result.success ? 'text-green-800' : 'text-red-800'}>
              {result.message}
            </p>
          </div>

          {/* Latency */}
          {result.latency_ms !== null && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Response time: {result.latency_ms.toFixed(0)}ms</span>
            </div>
          )}

          {/* Details */}
          {result.details && Object.keys(result.details).length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Info className="h-4 w-4" />
                <span>Details</span>
              </div>
              <div className="bg-muted/50 border rounded-lg divide-y">
                {Object.entries(result.details).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-start gap-3 px-3 py-2.5"
                  >
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="mt-0.5 shrink-0">
                          {getDetailIcon(key)}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="left">
                        <p>{key}</p>
                      </TooltipContent>
                    </Tooltip>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-muted-foreground mb-0.5">
                        {formatDetailKey(key)}
                      </div>
                      <div className="break-words">
                        {formatDetailValue(key, value)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
