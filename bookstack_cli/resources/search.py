"""Search resource."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import SearchResult


async def search(
    client: BookStackClient,
    query: str,
    page_size: int = 100,
) -> AsyncIterator[SearchResult]:
    """Search across all BookStack content.

    Yields search results matching the query.
    """
    params: dict[str, Any] = {"query": query}
    async for item in client.paginate("search", params=params, page_size=page_size):
        yield SearchResult(**item)
