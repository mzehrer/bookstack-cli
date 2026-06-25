"""Chapters resource CRUD."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import Chapter, ChapterCreate


async def list_chapters(
    client: BookStackClient,
    page_size: int = 100,
    book_id: int | None = None,
) -> AsyncIterator[Chapter]:
    """Iterate all chapters, optionally filtered by book."""
    params: dict[str, Any] = {}
    if book_id is not None:
        params["book_id"] = book_id

    async for item in client.paginate("chapters", params=params, page_size=page_size):
        yield Chapter(**item)


async def get_chapter(client: BookStackClient, chapter_id: int) -> Chapter:
    """Get a single chapter by ID."""
    data = await client.get(f"chapters/{chapter_id}")
    return Chapter(**data)


async def create_chapter(client: BookStackClient, payload: ChapterCreate) -> Chapter:
    """Create a new chapter."""
    data = await client.post("chapters", json=payload.model_dump(exclude_unset=True))
    return Chapter(**data)


async def update_chapter(
    client: BookStackClient, chapter_id: int, payload: ChapterCreate
) -> Chapter:
    """Update an existing chapter."""
    data = await client.put(f"chapters/{chapter_id}", json=payload.model_dump(exclude_unset=True))
    return Chapter(**data)


async def delete_chapter(client: BookStackClient, chapter_id: int) -> None:
    """Delete a chapter."""
    await client.delete(f"chapters/{chapter_id}")
