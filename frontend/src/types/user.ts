/**
 * Permission levels from RBAC system (Story 7.11)
 * Higher levels inherit lower-level permissions (cumulative)
 */
export enum PermissionLevel {
  USER = 1, // Basic access - search, view, generate
  OPERATOR = 2, // + upload/delete documents, create KBs
  ADMINISTRATOR = 3, // + delete KBs, manage users/groups
}

export interface UserRead {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  created_at: string;
  onboarding_completed: boolean;
  last_active: string | null;
  /** Computed permission level from user's groups (Story 7.11) */
  permission_level: PermissionLevel;
}

export interface UserCreate {
  email: string;
  password: string;
  is_superuser?: boolean;
}

export interface AdminUserUpdate {
  is_active?: boolean;
}

export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface ApiError {
  detail: string;
}
