/**
 * GenerationModal component - Modal dialog for initiating draft generation
 *
 * Story 4.9: Generation Templates
 * Task 5: Integrate TemplateSelector into modal UI workflow
 */

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { TemplateSelector } from "./template-selector";

interface GenerationModalProps {
  open: boolean;
  onClose: () => void;
  onGenerate: (params: { templateId: string; context: string }) => void;
}

export function GenerationModal({
  open,
  onClose,
  onGenerate,
}: GenerationModalProps) {
  const [templateId, setTemplateId] = useState("rfp_response");
  const [context, setContext] = useState("");

  const handleGenerate = () => {
    onGenerate({ templateId, context });
    onClose();
    // Reset state after generation
    setTemplateId("rfp_response");
    setContext("");
  };

  const handleClose = () => {
    onClose();
    // Reset state on close
    setTemplateId("rfp_response");
    setContext("");
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Generate Draft</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium mb-2">Select Template</h3>
            <TemplateSelector value={templateId} onChange={setTemplateId} />
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Generation Context</h3>
            <Textarea
              placeholder={
                templateId === "custom"
                  ? "Provide your custom instructions for document generation..."
                  : "E.g., 'Respond to section 4.2 about authentication requirements'"
              }
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button onClick={handleGenerate} disabled={!context.trim()}>
              Generate Draft
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
