# Brainstorm Session: Navigation Restructure with RBAC Default Groups

**Date:** 2025-12-08
**Session Type:** Party-mode collaborative brainstorm
**Participants:** Tung Vu (User), SM Agent (Bob), PM Agent, Architect Agent, Dev Agent
**Output:** Story 7-11 drafted

---

## Problem Statement

The current LumiKB application has a single "Admin" navigation section that requires `is_superuser` for visibility. This creates a binary access model (admin vs. non-admin) that doesn't support intermediate roles like "Operators" who need access to operational tools (audit logs, queue status, KB statistics) without full administrative privileges.

Additionally, there's no built-in group-based permission system with sensible defaults for common enterprise role patterns.

---

## Key Insights from Brainstorm

### 1. Navigation Split: Operations vs Admin

The team identified that current "admin" functions actually fall into two categories:

**Operations (Day-to-day operational tasks):**
- Audit Logs - viewing system activity
- Processing Queue - monitoring document processing
- KB Statistics - viewing knowledge base health

**Administration (System configuration):**
- User Management - creating/modifying users
- Group Management - managing user groups
- KB Permissions - assigning access rights
- System Config - platform settings
- Model Registry - LLM configuration

### 2. Three-Tier Permission Model

Rather than a complex RBAC system, a simple three-tier cumulative model covers most enterprise needs:

| Level | Role | Capabilities |
|-------|------|--------------|
| 1 | User | Search, view documents, chat, generate documents |
| 2 | Operator | + Upload/delete documents, create KBs, view Operations menu |
| 3 | Administrator | + Delete KBs, manage users/groups, Admin menu |

**Key insight:** Cumulative permissions (`level >= required`) are simpler to implement and reason about than discrete permission checks.

### 3. System Default Groups

Every installation should have three protected groups:
- **Users** (level 1) - Auto-assigned to new registrations
- **Operators** (level 2) - For content managers
- **Administrators** (level 3) - For system admins

These groups:
- Cannot be deleted (`is_system = true`)
- Can have membership modified
- Provide sensible defaults without requiring initial configuration

### 4. Route Protection Strategy

```
/operations/*  → requires level >= 2 (Operator)
/admin/*       → requires level >= 3 (Administrator)
/search, /chat, /dashboard  → requires level >= 1 (User)
```

### 5. Hub Dashboard Pattern

Each menu section should have a "hub" landing page with:
- Card-based navigation to sub-sections
- Live metrics/counts (e.g., "12 users", "3 processing")
- Quick access to common actions

---

## Design Decisions Made

1. **Single permission_level column on groups** - Simpler than a full permission matrix
2. **MAX aggregation for multi-group users** - User gets highest level across all groups
3. **Dropdown menus vs sidebar** - Cleaner UI, less screen real estate
4. **Non-breaking route migration** - Add redirects from old routes to new
5. **Auto-assign to Users group** - Simplifies onboarding flow

---

## Risks Identified

1. **Breaking change for existing users** - Existing is_superuser users need migration to Administrators group
2. **UI complexity** - Need to ensure dropdowns don't clutter header on mobile
3. **Permission caching** - Permission checks should be cached to avoid repeated queries

---

## Output

Story 7-11 was drafted with:
- 20 acceptance criteria covering all identified requirements
- 10 tasks with 40+ subtasks
- Clear permission matrix documentation
- File structure mapping for implementation

---

## References

- [docs/sprint-artifacts/5-17-main-navigation.md] - Existing navigation structure
- [docs/sprint-artifacts/5-19-group-management.md] - Existing group model
- [docs/sprint-artifacts/tech-spec-epic-7.md] - Epic 7 technical context
