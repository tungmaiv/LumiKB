/**
 * Export Dialog Component
 *
 * Story 9-9: Chat History Viewer UI
 * AC8: Export conversation as JSON or CSV (single session or bulk export)
 */
'use client';

import { useState } from 'react';
import { Download, FileJson, FileSpreadsheet } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import type { ChatMessageItem } from '@/hooks/useChatHistory';

interface ExportDialogProps {
  messages: ChatMessageItem[];
  sessionId: string;
  trigger?: React.ReactNode;
}

type ExportFormat = 'json' | 'csv';

/**
 * Download file utility
 */
function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export messages as JSON
 */
function exportAsJSON(messages: ChatMessageItem[], sessionId: string) {
  const data = {
    session_id: sessionId,
    exported_at: new Date().toISOString(),
    message_count: messages.length,
    messages: messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      created_at: m.created_at,
      token_count: m.token_count,
      response_time_ms: m.response_time_ms,
      citations: m.citations,
    })),
  };
  const json = JSON.stringify(data, null, 2);
  downloadFile(json, `chat-session-${sessionId.slice(0, 8)}.json`, 'application/json');
}

/**
 * Export messages as CSV
 * AC8: CSV format with escaped quotes
 */
function exportAsCSV(messages: ChatMessageItem[], sessionId: string) {
  const headers = [
    'id',
    'role',
    'content',
    'created_at',
    'token_count',
    'response_time_ms',
    'citation_count',
  ];

  const escapeCSV = (value: string | number | null): string => {
    if (value === null || value === undefined) return '';
    const str = String(value);
    // Escape quotes by doubling them
    if (str.includes('"') || str.includes(',') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const rows = messages.map((m) => [
    escapeCSV(m.id),
    escapeCSV(m.role),
    escapeCSV(m.content),
    escapeCSV(m.created_at),
    escapeCSV(m.token_count),
    escapeCSV(m.response_time_ms),
    escapeCSV(m.citations?.length || 0),
  ]);

  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
  downloadFile(csv, `chat-session-${sessionId.slice(0, 8)}.csv`, 'text/csv');
}

export function ExportDialog({
  messages,
  sessionId,
  trigger,
}: ExportDialogProps) {
  const [open, setOpen] = useState(false);
  const [format, setFormat] = useState<ExportFormat>('json');

  const handleExport = () => {
    if (format === 'json') {
      exportAsJSON(messages, sessionId);
    } else {
      exportAsCSV(messages, sessionId);
    }
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" data-testid="export-button">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Export Conversation</DialogTitle>
          <DialogDescription>
            Export {messages.length} messages from this conversation.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Label className="text-sm font-medium mb-3 block">Export Format</Label>
          <RadioGroup
            value={format}
            onValueChange={(value) => setFormat(value as ExportFormat)}
            className="space-y-3"
          >
            <div className="flex items-center space-x-3">
              <RadioGroupItem value="json" id="format-json" />
              <Label
                htmlFor="format-json"
                className="flex items-center gap-2 cursor-pointer"
              >
                <FileJson className="h-4 w-4 text-blue-500" />
                <div>
                  <div className="font-medium">JSON</div>
                  <div className="text-xs text-muted-foreground">
                    Full fidelity with all metadata and citations
                  </div>
                </div>
              </Label>
            </div>
            <div className="flex items-center space-x-3">
              <RadioGroupItem value="csv" id="format-csv" />
              <Label
                htmlFor="format-csv"
                className="flex items-center gap-2 cursor-pointer"
              >
                <FileSpreadsheet className="h-4 w-4 text-green-500" />
                <div>
                  <div className="font-medium">CSV</div>
                  <div className="text-xs text-muted-foreground">
                    Spreadsheet-compatible format for analysis
                  </div>
                </div>
              </Label>
            </div>
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleExport} data-testid="confirm-export">
            <Download className="h-4 w-4 mr-2" />
            Export {format.toUpperCase()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
