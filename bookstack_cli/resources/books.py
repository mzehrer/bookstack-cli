"""Books resource CRUD."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import Book, BookCreate


async def list_books(
    client: BookStackClient,
    page_size: int = 100,
    sort: str | None = None,
    order: str | None = None,
) -> AsyncIterator[Book]:
    """Iterate all books."""
    params: dict[str, Any] = {}
    if sort:
        params["sort"] = sort
    if order:
        params["order"] = order

    async for item in client.paginate("books", params=params, page_size=page_size):
        yield Book(**item)


async def get_book(client: BookStackClient, book_id: int) -> Book:
    """Get a single book by ID."""
    data = await client.get(f"books/{book_id}")
    return Book(**data)


async def create_book(client: BookStackClient, payload: BookCreate) -> Book:
    """Create a new book."""
    data = await client.post("books", json=payload.model_dump(exclude_unset=True))
    return Book(**data)


async def update_book(client: BookStackClient, book_id: int, payload: BookCreate) -> Book:
    """Update an existing book."""
    data = await client.put(f"books/{book_id}", json=payload.model_dump(exclude_unset=True))
    return Book(**data)


async def delete_book(client: BookStackClient, book_id: int) -> None:
    """Delete a book."""
    await client.delete(f"books/{book_id}")


async def upload_book_cover(
    client: BookStackClient,
    book_id: int,
    file_content: bytes,
    filename: str,
) -> dict[str, Any]:
    """Upload a cover image for a book using multipart PUT."""
    old_ct = client._client.headers.pop("Content-Type", None)
    try:
        files = {"image": (filename, file_content)}
        resp = await client._client.put(f"/api/books/{book_id}", files=files)
        return resp.json()
    finally:
        if old_ct is not None:
            client._client.headers["Content-Type"] = old_ct
