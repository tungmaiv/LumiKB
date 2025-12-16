"""Integration tests for Groups API endpoints.

Story 5.19: Group Management (AC-5.19.1, AC-5.19.4, AC-5.19.6)

Test Coverage:
- [P0] Admin-only access enforcement (403 for non-admin, 401 for unauthenticated)
- [P1] CRUD operations for groups (create, read, update, delete)
- [P1] Pagination and search functionality
- [P1] Membership management (add/remove members)
- [P2] Edge cases (duplicate names, soft delete, empty groups)

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- fixture-architecture.md: Integration test patterns
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.group import Group
from app.models.user import User
from tests.factories import create_group_data, create_registration_data

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def groups_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_groups(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_groups(
    groups_client: AsyncClient, db_session_for_groups: AsyncSession
) -> dict:
    """Create an admin test user for groups tests."""
    user_data = create_registration_data()
    response = await groups_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_groups.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_groups.commit()

    return {**user_data, "user": response_data, "user_id": response_data["id"]}


@pytest.fixture
async def admin_cookies_for_groups(
    groups_client: AsyncClient, admin_user_for_groups: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await groups_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_groups["email"],
            "password": admin_user_for_groups["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_groups(groups_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await groups_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json(), "user_id": response.json()["id"]}


@pytest.fixture
async def regular_user_cookies_for_groups(
    groups_client: AsyncClient, regular_user_for_groups: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await groups_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_groups["email"],
            "password": regular_user_for_groups["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def second_regular_user(groups_client: AsyncClient) -> dict:
    """Create a second regular user for membership tests."""
    user_data = create_registration_data()
    response = await groups_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json(), "user_id": response.json()["id"]}


@pytest.fixture
async def test_group(
    groups_client: AsyncClient, admin_cookies_for_groups: dict
) -> dict:
    """Create a test group for use in other tests."""
    group_data = create_group_data(name="Test Engineering Team")
    response = await groups_client.post(
        "/api/v1/admin/groups",
        json=group_data,
        cookies=admin_cookies_for_groups,
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


# =============================================================================
# Access Control Tests (P0)
# =============================================================================


class TestGroupsAccessControl:
    """[P0] Tests for admin-only access enforcement."""

    @pytest.mark.asyncio
    async def test_list_groups_unauthenticated_returns_401(
        self, groups_client: AsyncClient
    ):
        """
        GIVEN: No authentication
        WHEN: GET /api/v1/admin/groups
        THEN: Returns 401 Unauthorized
        """
        response = await groups_client.get("/api/v1/admin/groups")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_groups_non_admin_returns_403(
        self, groups_client: AsyncClient, regular_user_cookies_for_groups: dict
    ):
        """
        GIVEN: Regular (non-admin) user
        WHEN: GET /api/v1/admin/groups
        THEN: Returns 403 Forbidden
        """
        response = await groups_client.get(
            "/api/v1/admin/groups",
            cookies=regular_user_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_group_non_admin_returns_403(
        self, groups_client: AsyncClient, regular_user_cookies_for_groups: dict
    ):
        """
        GIVEN: Regular (non-admin) user
        WHEN: POST /api/v1/admin/groups
        THEN: Returns 403 Forbidden
        """
        group_data = create_group_data()
        response = await groups_client.post(
            "/api/v1/admin/groups",
            json=group_data,
            cookies=regular_user_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_group_non_admin_returns_403(
        self,
        groups_client: AsyncClient,
        regular_user_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Regular user and existing group
        WHEN: GET /api/v1/admin/groups/{group_id}
        THEN: Returns 403 Forbidden
        """
        response = await groups_client.get(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=regular_user_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_group_non_admin_returns_403(
        self,
        groups_client: AsyncClient,
        regular_user_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Regular user and existing group
        WHEN: PATCH /api/v1/admin/groups/{group_id}
        THEN: Returns 403 Forbidden
        """
        response = await groups_client.patch(
            f"/api/v1/admin/groups/{test_group['id']}",
            json={"name": "Hacked Name"},
            cookies=regular_user_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_group_non_admin_returns_403(
        self,
        groups_client: AsyncClient,
        regular_user_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Regular user and existing group
        WHEN: DELETE /api/v1/admin/groups/{group_id}
        THEN: Returns 403 Forbidden
        """
        response = await groups_client.delete(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=regular_user_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# List Groups Tests (P1)
# =============================================================================


class TestListGroups:
    """[P1] Tests for GET /api/v1/admin/groups."""

    @pytest.mark.asyncio
    async def test_list_groups_admin_returns_200(
        self, groups_client: AsyncClient, admin_cookies_for_groups: dict
    ):
        """
        GIVEN: Admin user
        WHEN: GET /api/v1/admin/groups
        THEN: Returns 200 with paginated response
        """
        response = await groups_client.get(
            "/api/v1/admin/groups",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    @pytest.mark.asyncio
    async def test_list_groups_returns_created_groups(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Admin user and existing group
        WHEN: GET /api/v1/admin/groups
        THEN: Returns list containing the group
        """
        response = await groups_client.get(
            "/api/v1/admin/groups",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        group_ids = [g["id"] for g in data["items"]]
        assert test_group["id"] in group_ids

    @pytest.mark.asyncio
    async def test_list_groups_with_search_filters_results(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
    ):
        """
        GIVEN: Admin user and multiple groups
        WHEN: GET /api/v1/admin/groups?search=Engineering
        THEN: Returns only groups matching search term
        """
        # Create two groups with different names
        await groups_client.post(
            "/api/v1/admin/groups",
            json=create_group_data(name="Engineering Alpha"),
            cookies=admin_cookies_for_groups,
        )
        await groups_client.post(
            "/api/v1/admin/groups",
            json=create_group_data(name="Marketing Beta"),
            cookies=admin_cookies_for_groups,
        )

        # Search for Engineering
        response = await groups_client.get(
            "/api/v1/admin/groups",
            params={"search": "Engineering"},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for group in data["items"]:
            assert "Engineering" in group["name"]

    @pytest.mark.asyncio
    async def test_list_groups_pagination_works(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
    ):
        """
        GIVEN: Admin user and multiple groups
        WHEN: GET /api/v1/admin/groups with pagination
        THEN: Returns correct page of results
        """
        # Create multiple groups
        for i in range(5):
            await groups_client.post(
                "/api/v1/admin/groups",
                json=create_group_data(name=f"Pagination Test Group {i}"),
                cookies=admin_cookies_for_groups,
            )

        # Request page 1 with size 2
        response = await groups_client.get(
            "/api/v1/admin/groups",
            params={"page": 1, "page_size": 2},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2


# =============================================================================
# Create Group Tests (P1)
# =============================================================================


class TestCreateGroup:
    """[P1] Tests for POST /api/v1/admin/groups."""

    @pytest.mark.asyncio
    async def test_create_group_returns_201(
        self, groups_client: AsyncClient, admin_cookies_for_groups: dict
    ):
        """
        GIVEN: Admin user and valid group data
        WHEN: POST /api/v1/admin/groups
        THEN: Returns 201 with created group
        """
        group_data = create_group_data(
            name="New Team", description="A new team for testing"
        )
        response = await groups_client.post(
            "/api/v1/admin/groups",
            json=group_data,
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == group_data["name"]
        assert data["description"] == group_data["description"]
        assert data["is_active"] is True
        assert data["member_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_group_duplicate_name_returns_409(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Admin user and existing group
        WHEN: POST /api/v1/admin/groups with same name
        THEN: Returns 409 Conflict
        """
        group_data = create_group_data(name=test_group["name"])
        response = await groups_client.post(
            "/api/v1/admin/groups",
            json=group_data,
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_create_group_without_description(
        self, groups_client: AsyncClient, admin_cookies_for_groups: dict
    ):
        """
        GIVEN: Admin user and group data without description
        WHEN: POST /api/v1/admin/groups
        THEN: Returns 201 with null description
        """
        group_data = {"name": "Minimal Group"}
        response = await groups_client.post(
            "/api/v1/admin/groups",
            json=group_data,
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == "Minimal Group"
        assert data["description"] is None


# =============================================================================
# Get Group Tests (P1)
# =============================================================================


class TestGetGroup:
    """[P1] Tests for GET /api/v1/admin/groups/{group_id}."""

    @pytest.mark.asyncio
    async def test_get_group_returns_200(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Admin user and existing group
        WHEN: GET /api/v1/admin/groups/{group_id}
        THEN: Returns 200 with group details including members
        """
        response = await groups_client.get(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == test_group["id"]
        assert data["name"] == test_group["name"]
        assert "members" in data
        assert isinstance(data["members"], list)

    @pytest.mark.asyncio
    async def test_get_group_not_found_returns_404(
        self, groups_client: AsyncClient, admin_cookies_for_groups: dict
    ):
        """
        GIVEN: Admin user
        WHEN: GET /api/v1/admin/groups/{non_existent_id}
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await groups_client.get(
            f"/api/v1/admin/groups/{fake_id}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Update Group Tests (P1)
# =============================================================================


class TestUpdateGroup:
    """[P1] Tests for PATCH /api/v1/admin/groups/{group_id}."""

    @pytest.mark.asyncio
    async def test_update_group_name_returns_200(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Admin user and existing group
        WHEN: PATCH /api/v1/admin/groups/{group_id} with new name
        THEN: Returns 200 with updated group
        """
        response = await groups_client.patch(
            f"/api/v1/admin/groups/{test_group['id']}",
            json={"name": "Updated Team Name"},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["name"] == "Updated Team Name"
        assert data["id"] == test_group["id"]

    @pytest.mark.asyncio
    async def test_update_group_deactivate(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Admin user and active group
        WHEN: PATCH /api/v1/admin/groups/{group_id} with is_active=False
        THEN: Returns 200 with deactivated group
        """
        response = await groups_client.patch(
            f"/api/v1/admin/groups/{test_group['id']}",
            json={"is_active": False},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_group_not_found_returns_404(
        self, groups_client: AsyncClient, admin_cookies_for_groups: dict
    ):
        """
        GIVEN: Admin user
        WHEN: PATCH /api/v1/admin/groups/{non_existent_id}
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await groups_client.patch(
            f"/api/v1/admin/groups/{fake_id}",
            json={"name": "New Name"},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Delete Group Tests (P1)
# =============================================================================


class TestDeleteGroup:
    """[P1] Tests for DELETE /api/v1/admin/groups/{group_id}."""

    @pytest.mark.asyncio
    async def test_delete_group_returns_204(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
    ):
        """
        GIVEN: Admin user and existing group
        WHEN: DELETE /api/v1/admin/groups/{group_id}
        THEN: Returns 204 No Content
        """
        # Create a group to delete
        create_response = await groups_client.post(
            "/api/v1/admin/groups",
            json=create_group_data(name="Group To Delete"),
            cookies=admin_cookies_for_groups,
        )
        group_id = create_response.json()["id"]

        # Delete it
        response = await groups_client.delete(
            f"/api/v1/admin/groups/{group_id}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_group_soft_deletes(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        db_session_for_groups: AsyncSession,
    ):
        """
        GIVEN: Admin user and existing group
        WHEN: DELETE /api/v1/admin/groups/{group_id}
        THEN: Group is soft deleted (is_active=False)
        """
        # Create a group
        create_response = await groups_client.post(
            "/api/v1/admin/groups",
            json=create_group_data(name="Soft Delete Test"),
            cookies=admin_cookies_for_groups,
        )
        group_id = create_response.json()["id"]

        # Delete it
        await groups_client.delete(
            f"/api/v1/admin/groups/{group_id}",
            cookies=admin_cookies_for_groups,
        )

        # Verify soft delete in database
        result = await db_session_for_groups.execute(
            select(Group).where(Group.id == group_id)
        )
        group = result.scalar_one_or_none()
        assert group is not None
        assert group.is_active is False

    @pytest.mark.asyncio
    async def test_delete_group_not_found_returns_404(
        self, groups_client: AsyncClient, admin_cookies_for_groups: dict
    ):
        """
        GIVEN: Admin user
        WHEN: DELETE /api/v1/admin/groups/{non_existent_id}
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await groups_client.delete(
            f"/api/v1/admin/groups/{fake_id}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Membership Management Tests (P1)
# =============================================================================


class TestGroupMembership:
    """[P1] Tests for group membership management endpoints."""

    @pytest.mark.asyncio
    async def test_add_members_returns_200(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: Admin user, existing group, and existing user
        WHEN: POST /api/v1/admin/groups/{group_id}/members
        THEN: Returns 200 with added count
        """
        response = await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["added_count"] == 1

    @pytest.mark.asyncio
    async def test_add_multiple_members(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
        second_regular_user: dict,
    ):
        """
        GIVEN: Admin user, existing group, and multiple users
        WHEN: POST /api/v1/admin/groups/{group_id}/members with multiple IDs
        THEN: Returns correct added count
        """
        response = await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={
                "user_ids": [
                    regular_user_for_groups["user_id"],
                    second_regular_user["user_id"],
                ]
            },
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["added_count"] == 2

    @pytest.mark.asyncio
    async def test_add_member_already_exists_skipped(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: User already in group
        WHEN: POST /api/v1/admin/groups/{group_id}/members with same user
        THEN: Returns added_count=0 (skipped)
        """
        # Add user first time
        await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )

        # Try to add again
        response = await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["added_count"] == 0

    @pytest.mark.asyncio
    async def test_add_members_to_nonexistent_group_returns_404(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: Admin user
        WHEN: POST /api/v1/admin/groups/{non_existent_id}/members
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await groups_client.post(
            f"/api/v1/admin/groups/{fake_id}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_remove_member_returns_204(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: User in group
        WHEN: DELETE /api/v1/admin/groups/{group_id}/members/{user_id}
        THEN: Returns 204 No Content
        """
        # Add user first
        await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )

        # Remove user
        response = await groups_client.delete(
            f"/api/v1/admin/groups/{test_group['id']}/members/{regular_user_for_groups['user_id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_remove_member_not_in_group_returns_404(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: User not in group
        WHEN: DELETE /api/v1/admin/groups/{group_id}/members/{user_id}
        THEN: Returns 404 Not Found
        """
        response = await groups_client.delete(
            f"/api/v1/admin/groups/{test_group['id']}/members/{regular_user_for_groups['user_id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_group_member_count_updates(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: Group with no members
        WHEN: Members are added and removed
        THEN: member_count updates correctly
        """
        # Initial count is 0
        response = await groups_client.get(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.json()["member_count"] == 0

        # Add member
        await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )

        # Check count increased
        response = await groups_client.get(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.json()["member_count"] == 1

        # Remove member
        await groups_client.delete(
            f"/api/v1/admin/groups/{test_group['id']}/members/{regular_user_for_groups['user_id']}",
            cookies=admin_cookies_for_groups,
        )

        # Check count decreased
        response = await groups_client.get(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.json()["member_count"] == 0


# =============================================================================
# Edge Case Tests (P2)
# =============================================================================


class TestGroupEdgeCases:
    """[P2] Edge case tests for group management."""

    @pytest.mark.asyncio
    async def test_group_with_members_shows_member_details(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
        regular_user_for_groups: dict,
    ):
        """
        GIVEN: Group with members
        WHEN: GET /api/v1/admin/groups/{group_id}
        THEN: Response includes member details
        """
        # Add member
        await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [regular_user_for_groups["user_id"]]},
            cookies=admin_cookies_for_groups,
        )

        # Get group details
        response = await groups_client.get(
            f"/api/v1/admin/groups/{test_group['id']}",
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["members"]) == 1
        member = data["members"][0]
        assert member["id"] == regular_user_for_groups["user_id"]
        assert member["email"] == regular_user_for_groups["email"]
        assert "is_active" in member
        assert "joined_at" in member

    @pytest.mark.asyncio
    async def test_add_invalid_user_id_ignored(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
        test_group: dict,
    ):
        """
        GIVEN: Group and invalid user ID
        WHEN: POST /api/v1/admin/groups/{group_id}/members
        THEN: Invalid ID is silently ignored, added_count=0
        """
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        response = await groups_client.post(
            f"/api/v1/admin/groups/{test_group['id']}/members",
            json={"user_ids": [fake_user_id]},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["added_count"] == 0

    @pytest.mark.asyncio
    async def test_case_insensitive_search(
        self,
        groups_client: AsyncClient,
        admin_cookies_for_groups: dict,
    ):
        """
        GIVEN: Group with specific name
        WHEN: Searching with different case
        THEN: Group is found
        """
        # Create group
        await groups_client.post(
            "/api/v1/admin/groups",
            json=create_group_data(name="CamelCaseTeam"),
            cookies=admin_cookies_for_groups,
        )

        # Search lowercase
        response = await groups_client.get(
            "/api/v1/admin/groups",
            params={"search": "camelcase"},
            cookies=admin_cookies_for_groups,
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        matching = [g for g in data["items"] if "CamelCase" in g["name"]]
        assert len(matching) >= 1
