"""Composable test fixtures following pure-function-first pattern.

Import fixtures into conftest.py files where needed:
    from tests.fixtures import test_user, authenticated_client
"""

from .auth_fixtures import admin_user, authenticated_client, test_user

__all__ = ["test_user", "authenticated_client", "admin_user"]
