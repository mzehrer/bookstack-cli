"""Users resource CRUD (admin-only for mutations)."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import User


async def list_users(
    client: BookStackClient,
    page_size: int = 100,
) -> AsyncIterator[User]:
    """Iterate all users (admin)."""
    async for item in client.paginate("users", page_size=page_size):
        yield User(**item)


async def get_user(client: BookStackClient, user_id: int) -> User:
    """Get a single user by ID."""
    data = await client.get(f"users/{user_id}")
    return User(**data)


async def create_user(client: BookStackClient, payload: dict[str, Any]) -> User:
    """Create a user (admin)."""
    data = await client.post("users", json=payload)
    return User(**data)


async def update_user(client: BookStackClient, user_id: int, payload: dict[str, Any]) -> User:
    """Update a user (admin)."""
    data = await client.put(f"users/{user_id}", json=payload)
    return User(**data)


async def delete_user(client: BookStackClient, user_id: int) -> None:
    """Delete a user (admin)."""
    await client.delete(f"users/{user_id}")
