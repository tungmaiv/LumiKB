/**
 * KB Permission management types
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.1, AC-5.20.2)
 */

export type PermissionLevel = "READ" | "WRITE" | "ADMIN";
export type EntityType = "user" | "group";
export type PermissionSourceType = "direct" | "group";

/**
 * Permission response for a single entity (user or group)
 */
export interface PermissionExtended {
  id: string;
  entity_type: EntityType;
  entity_id: string;
  entity_name: string;
  kb_id: string;
  permission_level: PermissionLevel;
  created_at: string;
}

/**
 * Source of a permission (for effective permissions view)
 */
export interface PermissionSource {
  source_type: PermissionSourceType;
  source_id: string;
  source_name: string;
  permission_level: PermissionLevel;
}

/**
 * Effective permission for a user (computed from direct + group)
 */
export interface EffectivePermission {
  user_id: string;
  user_email: string;
  effective_level: PermissionLevel;
  sources: PermissionSource[];
}

/**
 * Create permission request (supports user or group)
 */
export interface PermissionCreate {
  user_id?: string;
  group_id?: string;
  permission_level: PermissionLevel;
}

/**
 * Update permission request
 */
export interface PermissionUpdate {
  permission_level: PermissionLevel;
}

/**
 * Paginated permission list response
 */
export interface PaginatedPermissionResponse {
  data: PermissionExtended[];
  total: number;
  page: number;
  limit: number;
}

/**
 * Effective permissions list response
 */
export interface EffectivePermissionListResponse {
  data: EffectivePermission[];
}

/**
 * Permission level hierarchy for UI display and validation
 */
export const PERMISSION_LEVELS: { value: PermissionLevel; label: string; description: string }[] = [
  { value: "READ", label: "Read", description: "Can view documents and search" },
  { value: "WRITE", label: "Write", description: "Can upload and edit documents" },
  { value: "ADMIN", label: "Admin", description: "Full control including permissions" },
];

/**
 * Get permission level numeric value for comparison
 */
export function getPermissionHierarchy(level: PermissionLevel): number {
  const hierarchy: Record<PermissionLevel, number> = {
    READ: 1,
    WRITE: 2,
    ADMIN: 3,
  };
  return hierarchy[level];
}

/**
 * Check if a permission level meets a required level
 */
export function hasPermissionLevel(
  userLevel: PermissionLevel,
  requiredLevel: PermissionLevel
): boolean {
  return getPermissionHierarchy(userLevel) >= getPermissionHierarchy(requiredLevel);
}
