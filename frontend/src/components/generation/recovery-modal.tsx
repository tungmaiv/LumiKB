"use client";

import { Lightbulb } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export interface Alternative {
  type: string;
  description: string;
  action: string;
}

interface RecoveryModalProps {
  isOpen: boolean;
  onClose: () => void;
  alternatives: Alternative[];
  onActionSelect: (action: string) => void;
}

export function RecoveryModal({
  isOpen,
  onClose,
  alternatives,
  onActionSelect,
}: RecoveryModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-blue-500" />
            Let&apos;s try something different
          </DialogTitle>
          <DialogDescription>
            Based on your feedback, here are some options to improve your draft:
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {alternatives.map((alt, index) => (
            <div
              key={alt.action}
              className="flex items-start justify-between gap-4 rounded-lg border p-4"
            >
              <div className="flex-1">
                <div className="font-medium text-sm mb-1">
                  {index + 1}. {alt.description}
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onActionSelect(alt.action);
                  onClose();
                }}
              >
                Try this
              </Button>
            </div>
          ))}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
