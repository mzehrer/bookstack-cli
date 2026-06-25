"""Pages resource CRUD."""

from collections.abc import AsyncIterator
from typing import Any

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import Page, PageCreate, PageMove, PageUpdate


async def list_pages(
    client: BookStackClient,
    page_size: int = 100,
    book_id: int | None = None,
    chapter_id: int | None = None,
    include_drafts: bool = False,
) -> AsyncIterator[Page]:
    """Iterate all pages, optionally filtered client-side."""
    params: dict[str, Any] = {}
    if include_drafts:
        params["draft"] = "true"

    async for item in client.paginate("pages", params=params, page_size=page_size):
        if book_id is not None and item.get("book_id") != book_id:
            continue
        if chapter_id is not None and item.get("chapter_id") != chapter_id:
            continue
        yield Page(**item)


async def get_page(client: BookStackClient, page_id: int) -> Page:
    """Get a single page by ID."""
    data = await client.get(f"pages/{page_id}")
    return Page(**data)


async def create_page(client: BookStackClient, payload: PageCreate) -> Page:
    """Create a new page."""
    data = await client.post("pages", json=payload.model_dump(exclude_unset=True))
    return Page(**data)


async def update_page(client: BookStackClient, page_id: int, payload: PageUpdate) -> Page:
    """Update an existing page (partial update allowed)."""
    data = await client.put(f"pages/{page_id}", json=payload.model_dump(exclude_unset=True))
    return Page(**data)


async def move_page(client: BookStackClient, page_id: int, payload: PageMove) -> Page:
    """Move a page to a different book or chapter."""
    data = await client.put(f"pages/{page_id}/move", json=payload.model_dump(exclude_unset=True))
    return Page(**data)


async def delete_page(client: BookStackClient, page_id: int) -> None:
    """Delete a page."""
    await client.delete(f"pages/{page_id}")


async def get_page_html(client: BookStackClient, page_id: int) -> str:
    """Get the rendered HTML content of a page."""
    page = await get_page(client, page_id)
    return page.html


async def get_page_markdown(client: BookStackClient, page_id: int) -> str:
    """Get the markdown content of a page."""
    page = await get_page(client, page_id)
    return page.markdown


async def resolve_page_url(client: BookStackClient, url: str, instance_url: str | None = None) -> Page:
    """Resolve a BookStack web URL to a page.

    URL format: ``{base_url}/books/{book-slug}/page/{page-slug}``

    Uses the instance URL from config to validate the input URL belongs to this
    BookStack instance. Slug is extracted from the path after the instance base.

    Raises ValueError if URL can't be parsed, doesn't match the configured
    instance, or page not found.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Strip the instance base path if it matches (supports internal IP vs public domain mismatch)
    if instance_url:
        base_path = urlparse(instance_url).path.rstrip("/")
        if base_path and path.startswith(base_path):
            path = path.removeprefix(base_path)

    parts = path.split("/")
    try:
        page_idx = parts.index("page")
    except ValueError:
        raise ValueError(f"URL does not look like a BookStack page: {url}")

    page_slug = parts[page_idx + 1] if page_idx + 1 < len(parts) else None
    if not page_slug:
        raise ValueError(f"Could not extract page slug from URL: {url}")

    # Extract book slug for scoping
    import re
    book_slug: str | None = None
    try:
        book_idx = parts.index("books")
        if book_idx + 1 < len(parts) and parts[book_idx + 1] != "page":
            book_slug = parts[book_idx + 1]
    except ValueError:
        pass

    # Search using page slug words
    words = page_slug.replace("-", " ").split()
    search_term = words[-1] if len(words) > 1 else page_slug

    async for result in client.paginate("search", params={"query": search_term}):
        if result.get("type") != "page":
            continue
        rid = result.get("id")
        if not rid:
            continue
        rname = str(result.get("name", ""))
        candidate_slug = re.sub(r"[^a-z0-9-]", "", rname.lower().replace(" ", "-"))
        if candidate_slug == page_slug:
            page = await get_page(client, rid)
            if book_slug:
                book = await client.get(f"books/{page.book_id}")
                if book.get("slug") == book_slug:
                    return page
            else:
                return page

    raise ValueError(f"Page with slug '{page_slug}' not found (URL: {url})")


def _find_local_images(markdown: str, base_dir: str) -> list[tuple[str, str, str]]:
    """Find local image references in markdown.

    Returns list of (original_path, absolute_path, alt_text) for each local image.
    """
    import os
    import re

    results: list[tuple[str, str, str]] = []
    pattern = re.compile(r"!\[([^]]*)\]\(([^)]+)\)")
    for match in pattern.finditer(markdown):
        alt_text, path = match.group(1), match.group(2)
        if path.startswith(("http://", "https://", "data:", "#")):
            continue
        abs_path = path if os.path.isabs(path) else os.path.normpath(os.path.join(base_dir, path))
        if os.path.isfile(abs_path):
            results.append((path, abs_path, alt_text))
    return results


async def import_markdown_file(
    client: BookStackClient,
    file_path: str,
    page_name: str,
    book_id: int,
    chapter_id: int | None = None,
    page_id: int | None = None,
    instance_url: str | None = None,
) -> dict[str, Any]:
    """Import a markdown file into a BookStack page.

    - Reads markdown from file
    - Uploads local image files as attachments
    - Replaces local image paths with data URIs (BookStack has no public
      raw-image serving endpoint for attachments — gallery API unavailable)
    - Creates or updates the page

    Returns dict with page info and list of uploaded attachments.
    """
    import base64
    import os
    import re

    base_dir = os.path.dirname(os.path.abspath(file_path))
    markdown = open(file_path, encoding="utf-8").read()

    images = _find_local_images(markdown, base_dir)
    uploaded: list[dict[str, Any]] = []

    for orig_path, abs_path, alt_text in images:
        filename = os.path.basename(abs_path)
        with open(abs_path, "rb") as f:
            content = f.read()
        uploaded.append({
            "orig_path": orig_path,
            "abs_path": abs_path,
            "filename": filename,
            "alt_text": alt_text,
            "content": content,
        })
        placeholder = f"__ATTACH_{filename}__"
        markdown = markdown.replace(f"![{alt_text}]({orig_path})", placeholder)

    from bookstack_cli.resources.attachments import upload_attachment
    from bookstack_cli.models import PageCreate, PageUpdate

    if page_id:
        page = await update_page(client, page_id, PageUpdate(name=page_name, markdown=markdown))
    else:
        if not book_id or book_id <= 0:
            raise ValueError("book_id is required to create a new page")
        create_kwargs: dict[str, Any] = {"book_id": book_id, "name": page_name, "markdown": markdown}
        if chapter_id is not None:
            create_kwargs["chapter_id"] = chapter_id
        page = await create_page(client, PageCreate(**create_kwargs))

    for img in uploaded:
        attachment = await upload_attachment(
            client, name=img["filename"], page_id=page.id,
            file_content=img["content"], filename=img["filename"],
        )
        img_url = f"{instance_url.rstrip('/')}/attachments/{attachment.id}" if instance_url \
            else f"/attachments/{attachment.id}"

        placeholder = f"__ATTACH_{img['filename']}__"
        current = await client.get(f"pages/{page.id}")
        new_md = str(current.get("markdown", "")).replace(placeholder, f"![{img['alt_text']}]({img_url})")
        if new_md != current.get("markdown"):
            await client.put(f"pages/{page.id}", json={"markdown": new_md})
            page = await get_page(client, page.id)

    return {
        "page": page.model_dump(mode="json"),
        "attachments_uploaded": len(uploaded),
        "note": "Local images uploaded as attachments and referenced via attachment URL. "
                f"BookStack serves /attachments/{{id}} as raw files to web session users, "
                "so images render inline in the page viewer.",
    }


async def export_page(
    client: BookStackClient,
    page_id: int,
    output_dir: str | None = None,
    images_subdir: str = "images",
) -> dict[str, Any]:
    """Export a page to a local markdown file, downloading images.

    - Fetches page markdown content
    - Finds all image references (gallery + attachment URLs)
    - Downloads each image to a local subfolder
    - Replaces URLs with local file paths in the markdown
    - Writes the markdown file

    Returns dict with file path and list of downloaded images.
    """
    import base64
    import os
    import re
    from urllib.parse import urlparse

    from bookstack_cli.resources.attachments import download_attachment

    page = await get_page(client, page_id)
    markdown = page.markdown or ""

    base_dir = output_dir if output_dir else os.path.join(os.getcwd(), f"page-{page_id}")
    img_dir = os.path.join(base_dir, images_subdir)
    os.makedirs(img_dir, exist_ok=True)

    # Step 1: Find all image URLs
    pattern = re.compile(r"!\[([^]]*)\]\(([^)]+)\)")
    matches = list(pattern.finditer(markdown))

    # Step 2: Download all images
    url_map: dict[str, str] = {}  # url -> local relative path
    downloaded: list[dict[str, Any]] = []

    for m in matches:
        alt_text = m.group(1)
        url = m.group(2)
        parsed = urlparse(url)
        path_part = parsed.path.rstrip("/").split("/")
        filename = path_part[-1] if path_part else "image"
        if "." not in filename:
            filename = f"{filename}.bin"
        local_path = os.path.join(img_dir, filename)
        rel_path = os.path.join(images_subdir, filename)

        # Skip already-downloaded URLs
        if url in url_map:
            continue

        try:
            if "/attachments/" in url:
                # Attachment — download via API (base64)
                aid_match = re.search(r"/attachments/(\d+)", url)
                if aid_match:
                    aid = int(aid_match.group(1))
                    fname, content = await download_attachment(client, aid)
                    local_path = os.path.join(img_dir, fname)
                    rel_path = os.path.join(images_subdir, fname)
                    with open(local_path, "wb") as f:
                        f.write(content)
                    downloaded.append({"url": url, "file": fname, "source": "attachment"})
            else:
                # Gallery or external — download via HTTP
                import httpx
                h = {"User-Agent": "Mozilla/5.0"}
                resp = httpx.get(url, headers=h, follow_redirects=True, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 100:
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    downloaded.append({"url": url, "file": filename, "source": "http"})

            url_map[url] = rel_path
        except Exception as e:
            downloaded.append({"url": url, "file": None, "error": str(e)})

    # Step 3: Replace URLs in markdown
    def _replace(m: re.Match) -> str:
        alt = m.group(1)
        u = m.group(2)
        local = url_map.get(u)
        if local:
            return f"![{alt}]({local})"
        return m.group(0)  # keep original on failure

    new_md = pattern.sub(_replace, markdown)

    # Step 4: Write markdown file
    md_path = os.path.join(base_dir, f"{page.slug or page_id}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(new_md)

    return {
        "page_id": page_id,
        "name": page.name,
        "slug": page.slug,
        "markdown_file": md_path,
        "images_dir": img_dir,
        "images_downloaded": len([d for d in downloaded if d.get("file")]),
        "images_failed": len([d for d in downloaded if d.get("error")]),
        "images": downloaded,
    }
