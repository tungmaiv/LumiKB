"use client";

import { useState } from "react";
import { FileDown, FileText, FileCode } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

export type ExportFormat = "docx" | "pdf" | "markdown";

interface FormatOption {
  value: ExportFormat;
  label: string;
  description: string;
  icon: React.ReactNode;
  estimatedSize: string;
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    value: "docx",
    label: "Microsoft Word",
    description: "Best for editing and collaboration",
    icon: <FileText className="h-5 w-5" />,
    estimatedSize: "~50KB",
  },
  {
    value: "pdf",
    label: "PDF",
    description: "Best for sharing and printing",
    icon: <FileDown className="h-5 w-5" />,
    estimatedSize: "~75KB",
  },
  {
    value: "markdown",
    label: "Markdown",
    description: "Best for developers and version control",
    icon: <FileCode className="h-5 w-5" />,
    estimatedSize: "~10KB",
  },
];

interface ExportModalProps {
  open: boolean;
  onClose: () => void;
  onExport: (format: ExportFormat) => void;
  citationCount: number;
  isExporting?: boolean;
}

export function ExportModal({
  open,
  onClose,
  onExport,
  citationCount,
  isExporting = false,
}: ExportModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("docx");

  const handleExport = () => {
    onExport(selectedFormat);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]" data-testid="export-modal">
        <DialogHeader>
          <DialogTitle>Export Draft</DialogTitle>
          <DialogDescription>
            Choose a format to export your draft. Citations ({citationCount}) will be
            preserved.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <RadioGroup
            value={selectedFormat}
            onValueChange={(value) => setSelectedFormat(value as ExportFormat)}
          >
            {FORMAT_OPTIONS.map((option) => (
              <div
                key={option.value}
                data-testid={`format-option-${option.value}`}
                className="flex items-center space-x-3 rounded-lg border p-4 hover:bg-muted/50 cursor-pointer"
                onClick={() => setSelectedFormat(option.value)}
              >
                <RadioGroupItem value={option.value} id={option.value} />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    {option.icon}
                    <Label
                      htmlFor={option.value}
                      className="font-medium cursor-pointer"
                    >
                      {option.label}
                    </Label>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {option.description}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Estimated size: {option.estimatedSize}
                  </p>
                </div>
              </div>
            ))}
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isExporting}
            data-testid="export-modal-cancel"
          >
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            disabled={isExporting}
            data-testid="export-modal-submit"
          >
            {isExporting ? "Exporting..." : "Export"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
