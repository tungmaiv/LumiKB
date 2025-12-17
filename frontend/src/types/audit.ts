/**
 * Audit log types for admin audit log viewer
 * Story 5.2: Audit Log Viewer
 * Story 5.3: Audit Log Export
 */

export interface AuditEvent {
  id: string;
  timestamp: string; // ISO 8601
  action: string; // Backend uses 'action' not 'event_type'
  user_id: string | null;
  user_email: string | null;
  resource_type: string | null;
  resource_id: string | null;
  status: string | null; // Backend returns string | null, not just 'success' | 'failed'
  duration_ms: number | null;
  ip_address: string | null; // Redacted in default view ("XXX.XXX.XXX.XXX")
  details: Record<string, unknown> | null; // JSON object with event-specific data
}

export interface AuditLogFilter {
  start_date?: string; // ISO 8601 datetime
  end_date?: string; // ISO 8601 datetime
  user_email?: string; // Case-insensitive partial match
  event_type?: string; // Enum value (e.g., "search", "generation.request")
  resource_type?: string; // Enum value (e.g., "document", "draft", "search")
  page?: number; // Page number (1-indexed, default 1)
  page_size?: number; // Results per page (default 50, max 10000)
}

/**
 * Filters for audit log export (Story 5.3)
 */
export interface AuditLogFilters {
  startDate?: string;
  endDate?: string;
  userEmail?: string;
  eventType?: string;
  resourceType?: string;
}

export interface PaginatedAuditResponse {
  events: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * Event type enum values (from backend AuditEventType)
 */
export const EVENT_TYPES = [
  'search',
  'generation.request',
  'generation.complete',
  'generation.failed',
  'generation.feedback',
  'document.uploaded',
  'document.retry',
  'document.deleted',
  'document.replaced',
  'document.export',
  'kb.created',
  'kb.updated',
  'kb.archived',
  'kb.permission_granted',
  'kb.permission_revoked',
  'user.login',
  'user.logout',
  'user.login_failed',
  'change_search',
  'add_context',
  'new_draft',
  'select_template',
  'regenerate_with_structure',
  'regenerate_detailed',
  'add_sections',
  'search_better_sources',
  'review_citations',
  'regenerate_with_feedback',
  'adjust_parameters',
] as const;

/**
 * Resource type enum values (from backend AuditResourceType)
 */
export const RESOURCE_TYPES = ['document', 'knowledge_base', 'draft', 'search', 'user'] as const;

export type EventType = (typeof EVENT_TYPES)[number];
export type ResourceType = (typeof RESOURCE_TYPES)[number];
