#!/usr/bin/env python3
"""Seed test users for pagination testing.

This script creates 50 test users to validate pagination functionality.

Usage:
    python seed-test-users.py [--count N]

Environment Variables:
    LUMIKB_DATABASE_URL: PostgreSQL connection string
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import random

# Add backend to path for imports
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from argon2 import PasswordHasher  # noqa: E402
from sqlalchemy import select, func  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

# Import models after path setup
from app.models.user import User  # noqa: E402

# Default password for test users
DEFAULT_TEST_PASSWORD = "testuser123"


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.environ.get(
        "LUMIKB_DATABASE_URL",
        "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb",
    )


# Sample first names and last names for generating realistic emails
FIRST_NAMES = [
    "alice", "bob", "charlie", "diana", "edward", "fiona", "george", "hannah",
    "ivan", "julia", "kevin", "linda", "michael", "nancy", "oliver", "patricia",
    "quinn", "rachel", "steven", "tina", "ulysses", "victoria", "walter", "xena",
    "yolanda", "zachary", "emma", "liam", "sophia", "noah", "olivia", "william",
    "ava", "james", "isabella", "benjamin", "mia", "lucas", "charlotte", "henry",
    "amelia", "alexander", "harper", "sebastian", "evelyn", "jack", "abigail",
    "daniel", "emily", "matthew"
]

LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
    "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin", "lee", "perez", "thompson",
    "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
    "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell",
    "carter", "roberts"
]

DOMAINS = ["example.com", "testmail.org", "lumikb.dev", "company.org", "enterprise.io"]


def generate_user_data(index: int) -> dict:
    """Generate realistic user data for testing."""
    first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
    last_name = LAST_NAMES[index % len(LAST_NAMES)]
    domain = DOMAINS[index % len(DOMAINS)]

    # Make email unique by adding index
    email = f"{first_name}.{last_name}{index}@{domain}"

    # Randomize active status (90% active, 10% inactive for testing)
    is_active = random.random() > 0.1

    # Random created_at within the last 365 days
    days_ago = random.randint(0, 365)
    created_at = datetime.utcnow() - timedelta(days=days_ago)

    # Random last_active (some None, some recent)
    if random.random() > 0.3:  # 70% have last_active
        last_active = datetime.utcnow() - timedelta(days=random.randint(0, 30))
    else:
        last_active = None

    return {
        "email": email,
        "is_active": is_active,
        "created_at": created_at,
        "last_active": last_active,
    }


async def get_existing_user_count(session: AsyncSession) -> int:
    """Get count of existing users."""
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def seed_test_users(count: int = 50) -> None:
    """Create test users for pagination testing.

    Args:
        count: Number of test users to create.
    """
    print(f"Connecting to database...")
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    ph = PasswordHasher()
    hashed_password = ph.hash(DEFAULT_TEST_PASSWORD)

    async with async_session() as session:
        # Check existing user count
        existing_count = await get_existing_user_count(session)
        print(f"  Existing users: {existing_count}")

        # Check for test users that already exist
        result = await session.execute(
            select(User.email).where(User.email.like("%.%@%.%"))
        )
        existing_emails = set(row[0] for row in result.fetchall())

        created_count = 0
        skipped_count = 0

        print(f"\nCreating {count} test users...")
        for i in range(count):
            user_data = generate_user_data(i + 1)

            if user_data["email"] in existing_emails:
                skipped_count += 1
                continue

            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                hashed_password=hashed_password,
                is_active=user_data["is_active"],
                is_superuser=False,
                is_verified=True,
            )
            # Set created_at and last_active manually after creation
            user.created_at = user_data["created_at"]
            if user_data["last_active"]:
                user.last_active = user_data["last_active"]

            session.add(user)
            created_count += 1

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{count}")

        await session.commit()

        # Get final count
        final_count = await get_existing_user_count(session)

        print("\n" + "=" * 50)
        print("Seeding complete!")
        print("=" * 50)
        print(f"\nUsers created: {created_count}")
        print(f"Users skipped (already exist): {skipped_count}")
        print(f"Total users in database: {final_count}")
        print(f"\nTest user password: {DEFAULT_TEST_PASSWORD}")
        print("\nYou can now test pagination at http://localhost:3000/admin/users")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed test users for pagination testing")
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of test users to create (default: 50)",
    )
    args = parser.parse_args()

    asyncio.run(seed_test_users(count=args.count))


if __name__ == "__main__":
    main()
