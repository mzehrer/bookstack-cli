"""Shelves (bookshelves) resource CRUD."""

from collections.abc import AsyncIterator

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import Shelf, ShelfCreate


async def list_shelves(
    client: BookStackClient,
    page_size: int = 100,
) -> AsyncIterator[Shelf]:
    """Iterate all shelves."""
    async for item in client.paginate("shelves", page_size=page_size):
        yield Shelf(**item)


async def get_shelf(client: BookStackClient, shelf_id: int) -> Shelf:
    """Get a single shelf by ID."""
    data = await client.get(f"shelves/{shelf_id}")
    return Shelf(**data)


async def create_shelf(client: BookStackClient, payload: ShelfCreate) -> Shelf:
    """Create a new shelf."""
    data = await client.post("shelves", json=payload.model_dump(exclude_unset=True))
    return Shelf(**data)


async def update_shelf(client: BookStackClient, shelf_id: int, payload: ShelfCreate) -> Shelf:
    """Update an existing shelf."""
    data = await client.put(f"shelves/{shelf_id}", json=payload.model_dump(exclude_unset=True))
    return Shelf(**data)


async def delete_shelf(client: BookStackClient, shelf_id: int) -> None:
    """Delete a shelf."""
    await client.delete(f"shelves/{shelf_id}")
