"""Attachments resource CRUD."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import Attachment, AttachmentCreate


async def list_attachments(
    client: BookStackClient,
    page_size: int = 100,
    page_id: int | None = None,
) -> AsyncIterator[Attachment]:
    """Iterate all attachments, optionally filtered by page."""
    params: dict[str, Any] = {}
    if page_id is not None:
        params["page_id"] = page_id

    async for item in client.paginate("attachments", params=params, page_size=page_size):
        yield Attachment(**item)


async def get_attachment(client: BookStackClient, attachment_id: int) -> Attachment:
    """Get a single attachment by ID."""
    data = await client.get(f"attachments/{attachment_id}")
    return Attachment(**data)


async def create_attachment_link(
    client: BookStackClient, payload: AttachmentCreate
) -> Attachment:
    """Create a link-type attachment."""
    data = await client.post("attachments", json=payload.model_dump(exclude_unset=True))
    return Attachment(**data)


async def upload_attachment(
    client: BookStackClient,
    name: str,
    page_id: int,
    file_content: bytes,
    filename: str,
) -> Attachment:
    """Upload a file attachment using multipart."""
    data = {
        "name": name,
        "uploaded_to": str(page_id),
    }
    files = {
        "file": (filename, file_content),
    }
    response = await client._request("POST", "attachments", data=data, files=files)
    return Attachment(**response.json())


async def update_attachment(
    client: BookStackClient, attachment_id: int, payload: AttachmentCreate
) -> Attachment:
    """Update an attachment."""
    data = await client.put(
        f"attachments/{attachment_id}", json=payload.model_dump(exclude_unset=True)
    )
    return Attachment(**data)


async def delete_attachment(client: BookStackClient, attachment_id: int) -> None:
    """Delete an attachment."""
    await client.delete(f"attachments/{attachment_id}")


async def download_attachment(
    client: BookStackClient,
    attachment_id: int,
) -> tuple[str, bytes]:
    """Download an attachment's file content.

    Returns (filename, file_bytes).
    The API returns file content as base64-encoded string in the ``content`` field.
    """
    import base64

    data = await client.get(f"attachments/{attachment_id}")
    name: str = data.get("name", f"attachment-{attachment_id}")
    raw_content: str = data.get("content", "")
    ext: str = data.get("extension", "")
    if ext and not name.endswith(f".{ext}"):
        name = f"{name}.{ext}"
    file_bytes = base64.b64decode(raw_content)
    return (name, file_bytes)
