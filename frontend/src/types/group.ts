/**
 * Group management types
 * Story 5.19: Group Management (AC-5.19.2)
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 */

import { PermissionLevel } from './user';

export interface GroupMember {
  id: string;
  email: string;
  is_active: boolean;
  joined_at: string;
}

export interface Group {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  /** Permission level: 1=User, 2=Operator, 3=Administrator (AC-7.11.9) */
  permission_level: PermissionLevel;
  /** Whether this is a system group (cannot be deleted/edited) (AC-7.11.8, 7.11.10) */
  is_system: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface GroupWithMembers extends Group {
  members: GroupMember[];
}

export interface GroupCreate {
  name: string;
  description?: string | null;
}

export interface GroupUpdate {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface GroupMemberAdd {
  user_ids: string[];
}

export interface GroupMemberAddResponse {
  added_count: number;
}

export interface PaginatedGroupResponse {
  items: Group[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
