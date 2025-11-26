"""User factory with sensible defaults and explicit overrides.

Factory functions generate unique, parallel-safe test data using faker.
Override specific fields to make test intent explicit.
"""

import uuid
from typing import Any

from faker import Faker

fake = Faker()


def create_user(**overrides: Any) -> dict:
    """Factory function for user test data.

    Usage:
        user = create_user()  # All defaults
        admin = create_user(is_superuser=True)  # Override specific fields
        specific = create_user(email="test@example.com")  # Explicit email

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: User data matching User model schema
    """
    defaults = {
        "id": str(uuid.uuid4()),
        "email": fake.email(),
        "hashed_password": "hashed_test_password_123",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
    }

    # Apply overrides
    defaults.update(overrides)
    return defaults


def create_admin_user(**overrides: Any) -> dict:
    """Convenience factory for admin users.

    Creates a user with is_superuser=True by default.

    Usage:
        admin = create_admin_user()
        admin_with_email = create_admin_user(email="admin@example.com")
    """
    return create_user(is_superuser=True, **overrides)


def create_registration_data(**overrides: Any) -> dict:
    """Factory for user registration API payload.

    Generates unique email using UUID to guarantee no conflicts in parallel tests.

    Usage:
        data = create_registration_data()  # Random email, default password
        data = create_registration_data(email="specific@example.com")
        data = create_registration_data(password="custom123")

    Returns:
        dict: Registration payload with email and password
    """
    # Use UUID to guarantee uniqueness across parallel test runs
    unique_id = uuid.uuid4().hex[:12]
    defaults = {
        "email": f"testuser_{unique_id}@example.com",
        "password": "securepassword123",
    }
    defaults.update(overrides)
    return defaults
