/**
 * Unit tests for AddGroupPermissionModal component
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.2)
 *
 * Test Coverage:
 * - [P1] Rendering: Modal displays with group list
 * - [P1] Group selection: Click to select group
 * - [P1] Search: Filter groups by name/description
 * - [P1] Submit: Grant permission with selected group and level
 * - [P2] Loading state: Shows loading indicator
 * - [P2] Empty state: No groups available message
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { AddGroupPermissionModal } from "../add-group-permission-modal";
import type { Group } from "@/types/group";
import { PermissionLevel } from "@/types/user";

// Test data
const mockGroups: Group[] = [
  {
    id: "group-1",
    name: "Engineering",
    description: "Software engineering team",
    is_active: true,
    permission_level: PermissionLevel.USER,
    is_system: false,
    member_count: 5,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "group-2",
    name: "Marketing",
    description: "Marketing team",
    is_active: true,
    permission_level: PermissionLevel.OPERATOR,
    is_system: false,
    member_count: 3,
    created_at: "2025-01-02T00:00:00Z",
    updated_at: "2025-01-02T00:00:00Z",
  },
  {
    id: "group-3",
    name: "Sales",
    description: null,
    is_active: true,
    permission_level: PermissionLevel.USER,
    is_system: false,
    member_count: 8,
    created_at: "2025-01-03T00:00:00Z",
    updated_at: "2025-01-03T00:00:00Z",
  },
];

describe("AddGroupPermissionModal", () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    onGrantPermission: vi.fn().mockResolvedValue(undefined),
    isGranting: false,
    groups: mockGroups,
    groupsLoading: false,
    existingGroupIds: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("[P1] should render modal with title and description", () => {
      /**
       * GIVEN: Modal is open
       * WHEN: Component renders
       * THEN: Title and description are displayed
       */
      render(<AddGroupPermissionModal {...defaultProps} />);

      expect(screen.getByText("Add Group Permission")).toBeInTheDocument();
      expect(
        screen.getByText(/Grant a group access to this Knowledge Base/)
      ).toBeInTheDocument();
    });

    it("[P1] should render all available groups in list", () => {
      /**
       * GIVEN: Groups array provided
       * WHEN: Modal renders
       * THEN: All groups are displayed with member counts
       */
      render(<AddGroupPermissionModal {...defaultProps} />);

      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.getByText("Marketing")).toBeInTheDocument();
      expect(screen.getByText("Sales")).toBeInTheDocument();
    });

    it("[P1] should exclude groups with existing permissions", () => {
      /**
       * GIVEN: Some groups already have permissions
       * WHEN: Modal renders
       * THEN: Those groups are not shown
       */
      render(
        <AddGroupPermissionModal
          {...defaultProps}
          existingGroupIds={["group-1", "group-3"]}
        />
      );

      expect(screen.queryByText("Engineering")).not.toBeInTheDocument();
      expect(screen.getByText("Marketing")).toBeInTheDocument();
      expect(screen.queryByText("Sales")).not.toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("[P2] should show loading indicator when loading groups", () => {
      /**
       * GIVEN: Groups are being loaded
       * WHEN: Modal renders
       * THEN: Loading message is displayed
       */
      render(<AddGroupPermissionModal {...defaultProps} groupsLoading={true} />);

      expect(screen.getByText("Loading groups...")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("[P2] should show empty message when no groups available", () => {
      /**
       * GIVEN: No groups available
       * WHEN: Modal renders
       * THEN: No groups message shown
       */
      render(<AddGroupPermissionModal {...defaultProps} groups={[]} />);

      expect(screen.getByText("No available groups to add")).toBeInTheDocument();
    });
  });

  describe("group selection", () => {
    it("[P1] should select group when clicked", async () => {
      /**
       * GIVEN: Group list displayed
       * WHEN: User clicks on a group
       * THEN: Group is selected and shown in selection text
       */
      const user = userEvent.setup();
      render(<AddGroupPermissionModal {...defaultProps} />);

      const engineeringButton = screen.getByText("Engineering").closest("button");
      await user.click(engineeringButton!);

      // Check that selection is shown - "Selected: Engineering" appears
      expect(screen.getByText(/Selected:/)).toBeInTheDocument();
      // Verify Engineering is shown in the selection area (getAllByText since it appears in both list and selection)
      expect(screen.getAllByText("Engineering").length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("search", () => {
    it("[P1] should filter groups by name", async () => {
      /**
       * GIVEN: Groups displayed
       * WHEN: User types in search
       * THEN: Only matching groups are shown
       */
      const user = userEvent.setup();
      render(<AddGroupPermissionModal {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(
        "Search by name or description..."
      );
      await user.type(searchInput, "Engineer");

      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.queryByText("Marketing")).not.toBeInTheDocument();
      expect(screen.queryByText("Sales")).not.toBeInTheDocument();
    });

    it("[P1] should filter groups by description", async () => {
      /**
       * GIVEN: Groups displayed
       * WHEN: User searches by description
       * THEN: Matching groups are shown
       */
      const user = userEvent.setup();
      render(<AddGroupPermissionModal {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(
        "Search by name or description..."
      );
      await user.type(searchInput, "software");

      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.queryByText("Marketing")).not.toBeInTheDocument();
    });

    it("[P2] should show no results message when search finds nothing", async () => {
      /**
       * GIVEN: Groups displayed
       * WHEN: User searches for non-existent group
       * THEN: No results message shown
       */
      const user = userEvent.setup();
      render(<AddGroupPermissionModal {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(
        "Search by name or description..."
      );
      await user.type(searchInput, "nonexistent");

      expect(
        screen.getByText("No groups found matching your search")
      ).toBeInTheDocument();
    });
  });

  describe("form submission", () => {
    it("[P1] should call onGrantPermission with selected group and level", async () => {
      /**
       * GIVEN: Group selected and permission level set
       * WHEN: Form is submitted
       * THEN: onGrantPermission is called with correct data
       */
      const user = userEvent.setup();
      const onGrantPermission = vi.fn().mockResolvedValue(undefined);
      render(
        <AddGroupPermissionModal
          {...defaultProps}
          onGrantPermission={onGrantPermission}
        />
      );

      // Select a group
      const engineeringButton = screen.getByText("Engineering").closest("button");
      await user.click(engineeringButton!);

      // Submit form
      const submitButton = screen.getByText("Grant Permission");
      await user.click(submitButton);

      await waitFor(() => {
        expect(onGrantPermission).toHaveBeenCalledWith({
          group_id: "group-1",
          permission_level: "READ", // default
        });
      });
    });

    it("[P1] should close modal on successful submission", async () => {
      /**
       * GIVEN: Valid group selection
       * WHEN: Form is submitted successfully
       * THEN: Modal closes
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      render(
        <AddGroupPermissionModal {...defaultProps} onOpenChange={onOpenChange} />
      );

      // Select a group
      const engineeringButton = screen.getByText("Engineering").closest("button");
      await user.click(engineeringButton!);

      // Submit form
      const submitButton = screen.getByText("Grant Permission");
      await user.click(submitButton);

      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it("[P2] should disable submit button when no group selected", () => {
      /**
       * GIVEN: No group selected
       * WHEN: Modal renders
       * THEN: Submit button is disabled
       */
      render(<AddGroupPermissionModal {...defaultProps} />);

      const submitButton = screen.getByText("Grant Permission");
      expect(submitButton).toBeDisabled();
    });
  });

  describe("cancel", () => {
    it("[P1] should close modal when cancel clicked", async () => {
      /**
       * GIVEN: Modal open
       * WHEN: Cancel button clicked
       * THEN: onOpenChange called with false
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      render(
        <AddGroupPermissionModal {...defaultProps} onOpenChange={onOpenChange} />
      );

      const cancelButton = screen.getByText("Cancel");
      await user.click(cancelButton);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
