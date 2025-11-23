"""Authentication fixtures with automatic cleanup.

These fixtures create test users and authenticated clients for integration tests.
They depend on db_session from integration/conftest.py for database access.
"""

import pytest

from tests.factories import create_admin_user, create_user


@pytest.fixture
async def test_user_data() -> dict:
    """Generate test user data using factory.

    Returns dict with user data ready for registration or direct DB insert.
    """
    return create_user()


@pytest.fixture
async def admin_user_data() -> dict:
    """Generate admin user data using factory."""
    return create_admin_user()


# Note: The following fixtures require db_session from integration/conftest.py
# and app-specific imports. They are templates that should be customized
# based on your User model and auth implementation.

# @pytest.fixture
# async def test_user(db_session: AsyncSession, test_user_data: dict) -> dict:
#     """Create test user in database with automatic rollback cleanup.
#
#     Returns dict with user data + raw password for auth testing.
#     """
#     from app.models.user import User
#     from app.core.security import get_password_hash
#
#     raw_password = "test_password_123"
#
#     user = User(
#         id=test_user_data["id"],
#         email=test_user_data["email"],
#         hashed_password=get_password_hash(raw_password),
#         is_active=test_user_data["is_active"],
#         is_superuser=test_user_data["is_superuser"],
#     )
#     db_session.add(user)
#     await db_session.flush()
#
#     return {**test_user_data, "raw_password": raw_password}


# @pytest.fixture
# async def authenticated_client(client: AsyncClient, test_user: dict) -> AsyncClient:
#     """AsyncClient with Bearer token injected.
#
#     Usage:
#         async def test_protected_endpoint(authenticated_client):
#             response = await authenticated_client.get("/api/v1/protected")
#             assert response.status_code == 200
#     """
#     from app.core.security import create_access_token
#
#     token = create_access_token(subject=test_user["id"])
#     client.headers["Authorization"] = f"Bearer {token}"
#     return client
