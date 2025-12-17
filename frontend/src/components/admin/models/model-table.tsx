/**
 * Model table component for displaying LLM models
 * Story 7-9: LLM Model Registry (AC-7.9.4)
 */

'use client';

import { MoreHorizontal, Pencil, Trash2, Star, Zap, CheckCircle, XCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { LLMModelSummary } from '@/types/llm-model';
import { PROVIDER_INFO, MODEL_STATUS_INFO, MODEL_TYPE_INFO } from '@/types/llm-model';
import { ProviderLogo, PROVIDER_COLORS } from './provider-logo';

interface ModelTableProps {
  models: LLMModelSummary[];
  isLoading: boolean;
  onEdit: (model: LLMModelSummary) => void;
  onDelete: (model: LLMModelSummary) => void;
  onSetDefault: (model: LLMModelSummary) => void;
  onTest: (model: LLMModelSummary) => void;
  testingModelId: string | null;
}

function getStatusBadgeVariant(
  status: string
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'active':
      return 'default';
    case 'inactive':
      return 'secondary';
    case 'deprecated':
      return 'destructive';
    default:
      return 'outline';
  }
}

export function ModelTable({
  models,
  isLoading,
  onEdit,
  onDelete,
  onSetDefault,
  onTest,
  testingModelId,
}: ModelTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Model ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>API Key</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell>
                  <Skeleton className="h-4 w-32" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-20" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-24" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-36" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-16" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-12" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-8" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground">No models configured yet.</p>
        <p className="text-sm text-muted-foreground mt-1">
          Add a model to get started with the LLM registry.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Provider</TableHead>
            <TableHead>Model ID</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>API Key</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {models.map((model) => (
            <TableRow key={model.id}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  {model.name}
                  {model.is_default && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline">{MODEL_TYPE_INFO[model.type]?.name || model.type}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <ProviderLogo
                    provider={model.provider}
                    size={18}
                    className={PROVIDER_COLORS[model.provider] || 'text-gray-500'}
                  />
                  <span>{PROVIDER_INFO[model.provider]?.name || model.provider}</span>
                </div>
              </TableCell>
              <TableCell>
                <code className="text-xs bg-muted px-1 py-0.5 rounded">{model.model_id}</code>
              </TableCell>
              <TableCell>
                <Badge variant={getStatusBadgeVariant(model.status)}>
                  {MODEL_STATUS_INFO[model.status]?.name || model.status}
                </Badge>
              </TableCell>
              <TableCell>
                {model.has_api_key ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-gray-300" />
                )}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  {/* Test Connection Button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onTest(model)}
                    disabled={testingModelId === model.id}
                    className="h-8 w-8 p-0"
                  >
                    {testingModelId === model.id ? (
                      <span className="animate-spin">⏳</span>
                    ) : (
                      <Zap className="h-4 w-4" />
                    )}
                  </Button>

                  {/* Actions Dropdown */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onEdit(model)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      {!model.is_default && (
                        <DropdownMenuItem onClick={() => onSetDefault(model)}>
                          <Star className="mr-2 h-4 w-4" />
                          Set as Default
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => onDelete(model)}
                        className="text-destructive focus:text-destructive"
                        disabled={model.is_default}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
