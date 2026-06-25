"""Tags resource (read-only list)."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient


async def list_tags(
    client: BookStackClient,
    page_size: int = 100,
) -> AsyncIterator[dict[str, Any]]:
    """Iterate all tags across the system."""
    async for item in client.paginate("tags", page_size=page_size):
        yield item
