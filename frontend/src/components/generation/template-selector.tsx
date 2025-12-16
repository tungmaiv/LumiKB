/**
 * TemplateSelector component - Template selection grid
 *
 * Story 4.9: Generation Templates
 * Displays 4 templates in 2x2 grid with selection state
 */

import {
  CheckSquare,
  Edit,
  FileText,
  GitCompare,
  type LucideIcon,
} from "lucide-react";
import React from "react";

export interface TemplateSelectorProps {
  value: string;
  onChange: (templateId: string) => void;
}

interface TemplateCard {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  exampleOutput: string;
}

const TEMPLATE_CARDS: TemplateCard[] = [
  {
    id: "rfp_response",
    name: "RFP Response Section",
    description:
      "Generate a structured RFP response with executive summary and technical approach",
    icon: FileText,
    exampleOutput:
      "## Executive Summary\n\nOur authentication solution leverages OAuth 2.0 [1] with industry-standard security practices...",
  },
  {
    id: "checklist",
    name: "Technical Checklist",
    description: "Create a requirement checklist from sources",
    icon: CheckSquare,
    exampleOutput:
      "## Authentication Requirements\n\n- [ ] **OAuth 2.0 Support**: System must support OAuth 2.0 authentication flow [1]\n  - **Status**: To be assessed\n  - **Notes**: PKCE extension required for mobile clients [1]",
  },
  {
    id: "gap_analysis",
    name: "Gap Analysis",
    description: "Compare requirements against current capabilities",
    icon: GitCompare,
    exampleOutput:
      "| Requirement | Current State | Gap | Recommendation | Source |\n|---|---|---|---|---|\n| OAuth 2.0 compliance | Partial | PKCE flow missing | Implement RFC 7636 PKCE | [1] |",
  },
  {
    id: "custom",
    name: "Custom Prompt",
    description: "Generate content based on your own instructions",
    icon: Edit,
    exampleOutput: "",
  },
];

export function TemplateSelector({ value, onChange }: TemplateSelectorProps) {
  const handleKeyDown = (templateId: string, e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onChange(templateId);
    }
  };

  return (
    <div
      className="grid grid-cols-2 gap-4"
      role="radiogroup"
      aria-label="Template selection"
    >
      {TEMPLATE_CARDS.map((template) => {
        const Icon = template.icon;
        const isSelected = value === template.id;

        return (
          <div
            key={template.id}
            onClick={() => onChange(template.id)}
            onKeyDown={(e) => handleKeyDown(template.id, e)}
            className={`relative cursor-pointer rounded-lg border-2 p-4 transition-colors ${
              isSelected
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            }`}
            role="radio"
            aria-checked={isSelected}
            tabIndex={0}
            data-testid={`template-${template.id}`}
          >
            <div className="flex items-start gap-3">
              <Icon
                className={`h-6 w-6 flex-shrink-0 ${
                  isSelected ? "text-primary" : "text-muted-foreground"
                }`}
              />
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1">{template.name}</h3>
                <p className="text-xs text-muted-foreground">
                  {template.description}
                </p>
                {template.exampleOutput && (
                  <div className="mt-2">
                    <p className="text-xs text-muted-foreground italic">
                      Example preview:
                    </p>
                    <pre className="mt-1 text-xs text-muted-foreground truncate overflow-hidden">
                      {template.exampleOutput.split("\n")[0]}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
