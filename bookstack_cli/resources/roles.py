"""Roles resource CRUD (admin-only)."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import Role


async def list_roles(
    client: BookStackClient,
    page_size: int = 100,
) -> AsyncIterator[Role]:
    """Iterate all roles (admin)."""
    async for item in client.paginate("roles", page_size=page_size):
        yield Role(**item)


async def create_role(client: BookStackClient, payload: dict[str, Any]) -> Role:
    """Create a role (admin)."""
    data = await client.post("roles", json=payload)
    return Role(**data)


async def update_role(client: BookStackClient, role_id: int, payload: dict[str, Any]) -> Role:
    """Update a role (admin)."""
    data = await client.put(f"roles/{role_id}", json=payload)
    return Role(**data)


async def delete_role(client: BookStackClient, role_id: int) -> None:
    """Delete a role (admin)."""
    await client.delete(f"roles/{role_id}")
