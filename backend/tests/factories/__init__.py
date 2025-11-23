"""Test data factories for parallel-safe, schema-resilient test data.

Usage:
    from tests.factories import create_user, create_registration_data

    # Default user model data
    user = create_user()

    # Registration API payload (unique email each time)
    reg_data = create_registration_data()

    # Override specific fields
    admin = create_user(is_superuser=True, email="admin@example.com")
"""

from .user_factory import create_admin_user, create_registration_data, create_user

__all__ = ["create_user", "create_admin_user", "create_registration_data"]
