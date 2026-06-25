"""Revisions resource (read-only for most)."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient


async def list_revisions(
    client: BookStackClient,
    page_size: int = 100,
    page_id: int | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Iterate page revisions."""
    params: dict[str, Any] = {}
    if page_id is not None:
        params["page_id"] = page_id

    async for item in client.paginate("revisions", params=params, page_size=page_size):
        yield item


async def get_revision(client: BookStackClient, revision_id: int) -> dict[str, Any]:
    """Get a single revision by ID."""
    return await client.get(f"revisions/{revision_id}")


async def delete_revision(client: BookStackClient, revision_id: int) -> None:
    """Delete a revision."""
    await client.delete(f"revisions/{revision_id}")
