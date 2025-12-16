"use client";

import { Download, X } from "lucide-react";
import { useState } from "react";
import { format } from "date-fns";
import { AuditLogFilters } from "@/types/audit";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExportAuditLogsModalProps {
  open: boolean;
  onClose: () => void;
  filters: AuditLogFilters;
  recordCount: number;
}

type ExportFormat = "csv" | "json";

export function ExportAuditLogsModal({
  open,
  onClose,
  filters,
  recordCount,
}: ExportAuditLogsModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("csv");
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          format: selectedFormat,
          filters: {
            start_date: filters.startDate,
            end_date: filters.endDate,
            user_email: filters.userEmail,
            event_type: filters.eventType,
            resource_type: filters.resourceType,
            page: 1,
            page_size: 10000,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Get filename from Content-Disposition header or generate default
      const contentDisposition = response.headers.get("Content-Disposition");
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
      const filename =
        filenameMatch?.[1] ||
        `audit-log-export-${format(new Date(), "yyyyMMdd-HHmmss")}.${selectedFormat}`;

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Close modal on success
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background rounded-lg shadow-xl max-w-md w-full p-6 border">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Export Audit Logs</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
            disabled={isExporting}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Record Count */}
        <div className="mb-4 p-3 bg-primary/10 border border-primary/20 rounded">
          <p className="text-sm text-primary">
            <strong>{recordCount.toLocaleString()}</strong> records will be exported
          </p>
        </div>

        {/* Filter Summary */}
        <div className="mb-4">
          <h3 className="text-sm font-medium mb-2">Applied Filters:</h3>
          <div className="text-sm text-muted-foreground space-y-1">
            {filters.startDate && (
              <p>
                Start Date:{" "}
                {format(new Date(filters.startDate), "MMM dd, yyyy")}
              </p>
            )}
            {filters.endDate && (
              <p>
                End Date: {format(new Date(filters.endDate), "MMM dd, yyyy")}
              </p>
            )}
            {filters.userEmail && <p>User: {filters.userEmail}</p>}
            {filters.eventType && <p>Event Type: {filters.eventType}</p>}
            {filters.resourceType && (
              <p>Resource Type: {filters.resourceType}</p>
            )}
            {!filters.startDate &&
              !filters.endDate &&
              !filters.userEmail &&
              !filters.eventType &&
              !filters.resourceType && <p className="text-muted-foreground/50">No filters applied</p>}
          </div>
        </div>

        {/* Format Selection */}
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-2">Export Format:</h3>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                name="format"
                value="csv"
                checked={selectedFormat === "csv"}
                onChange={() => setSelectedFormat("csv")}
                className="mr-2"
                disabled={isExporting}
              />
              <span className="text-sm">CSV (Comma-Separated Values)</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="format"
                value="json"
                checked={selectedFormat === "json"}
                onChange={() => setSelectedFormat("json")}
                className="mr-2"
                disabled={isExporting}
              />
              <span className="text-sm">JSON (JavaScript Object Notation)</span>
            </label>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium border rounded hover:bg-muted"
            disabled={isExporting}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded hover:bg-primary/90 disabled:bg-primary/50 flex items-center"
          >
            {isExporting ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Download {selectedFormat.toUpperCase()}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
