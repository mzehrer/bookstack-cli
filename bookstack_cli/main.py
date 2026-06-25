"""Main CLI entry point — Typer app with subcommands per resource."""

import asyncio
import json
from collections.abc import AsyncIterator, Coroutine
from pathlib import Path
from typing import Any

import typer

from bookstack_cli.client import BookStackClient
from bookstack_cli.config import get_config, save_config
from bookstack_cli.exceptions import BookStackError

app = typer.Typer(
    name="bookstack",
    help="CLI for BookStack wiki API — built for coding agents.",
    pretty_exceptions_enable=False,
)
config_app = typer.Typer(help="Manage connection config.")
shelves_app = typer.Typer(help="Manage bookshelves.")
books_app = typer.Typer(help="Manage books.")
chapters_app = typer.Typer(help="Manage chapters.")
pages_app = typer.Typer(help="Manage pages.")
attachments_app = typer.Typer(help="Manage attachments.")
users_app = typer.Typer(help="Manage users (admin).")
roles_app = typer.Typer(help="Manage roles (admin).")
search_app = typer.Typer(help="Search content.")

app.add_typer(config_app, name="config")
app.add_typer(shelves_app, name="shelves")
app.add_typer(books_app, name="books")
app.add_typer(chapters_app, name="chapters")
app.add_typer(pages_app, name="pages")
app.add_typer(attachments_app, name="attachments")
app.add_typer(users_app, name="users")
app.add_typer(roles_app, name="roles")
app.add_typer(search_app, name="search")


# ------------------------------------------------------------------
# Event-loop helpers
# ------------------------------------------------------------------

_loop: asyncio.AbstractEventLoop | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    """Get or create a global event loop for sync→async bridging."""
    global _loop
    if _loop is None or _loop.is_closed():
        try:
            _loop = asyncio.get_event_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
    return _loop


def _run(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run an async coroutine synchronously."""
    return _get_loop().run_until_complete(coro)


def _collect(ait: AsyncIterator[Any]) -> list[dict[str, Any]]:
    """Collect all items from an async iterator into a list of dicts."""
    loop = _get_loop()
    items: list[Any] = []
    while True:
        try:
            items.append(loop.run_until_complete(ait.__anext__()))
        except StopAsyncIteration:
            break
    return [i.model_dump(mode="json") if hasattr(i, "model_dump") else i for i in items]


# ------------------------------------------------------------------
# JSON output
# ------------------------------------------------------------------


def _print(obj: Any) -> None:
    """Print as JSON for agent consumption."""
    import json as j

    if isinstance(obj, AsyncIterator):
        print(j.dumps(_collect(obj), indent=2))
    elif hasattr(obj, "model_dump"):
        print(j.dumps(obj.model_dump(mode="json"), indent=2))
    elif isinstance(obj, list):
        print(
            j.dumps(
                [i.model_dump(mode="json") if hasattr(i, "model_dump") else i for i in obj],
                indent=2,
            )
        )
    elif isinstance(obj, dict):
        print(j.dumps(obj, indent=2))
    else:
        print(j.dumps({"result": str(obj)}, indent=2))


def _client() -> BookStackClient:
    """Create a client from env/config."""
    return BookStackClient()


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------


@config_app.command("show")
def config_show():
    """Show current connection config."""
    try:
        cfg = get_config()
        _print({"url": cfg.url, "token_id": cfg.token_id})
    except BookStackError as e:
        _print({"error": str(e)})
        raise typer.Exit(1)


@app.command("auth")
def auth_cmd(
    url: str = typer.Option(..., prompt=True, help="BookStack base URL"),
    token_id: str = typer.Option(..., prompt=True, help="API token ID"),
    token_secret: str = typer.Option(..., prompt=True, hide_input=True, help="API token secret"),
):
    """Save connection credentials to ~/.config/bookstack-cli/config.toml."""
    path = save_config(url, token_id, token_secret)
    _print({"ok": True, "message": f"Config saved to {path}"})


# ------------------------------------------------------------------
# Shelf commands
# ------------------------------------------------------------------


@shelves_app.command("list")
def shelves_list():
    """List all shelves."""
    with _client() as c:
        import bookstack_cli.resources.shelves as r

        _print(_collect(r.list_shelves(c)))


@shelves_app.command("get")
def shelves_get(id: int = typer.Argument(..., help="Shelf ID")):
    """Get a shelf by ID."""
    with _client() as c:
        import bookstack_cli.resources.shelves as r

        _print(_run(r.get_shelf(c, id)))


@shelves_app.command("create")
def shelves_create(
    name: str = typer.Argument(..., help="Shelf name"),
    description: str = "",
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags"),
):
    """Create a new shelf."""
    with _client() as c:
        import bookstack_cli.resources.shelves as r
        from bookstack_cli.models import ShelfCreate

        kwargs: dict[str, Any] = {"name": name, "description": description}
        if tags:
            import json as _json
            kwargs["tags"] = _json.loads(tags)

        _print(_run(r.create_shelf(c, ShelfCreate(**kwargs))))


@shelves_app.command("delete")
def shelves_delete(id: int = typer.Argument(..., help="Shelf ID")):
    """Delete a shelf."""
    with _client() as c:
        import bookstack_cli.resources.shelves as r

        _run(r.delete_shelf(c, id))
        _print({"ok": True, "id": id})


@shelves_app.command("update")
def shelves_update(
    id: int = typer.Argument(..., help="Shelf ID"),
    name: str = typer.Argument(..., help="New shelf name"),
    description: str = "",
    books: str | None = typer.Option(None, "--books", help="Comma-separated book IDs to assign to shelf"),
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags e.g. '[{\"name\":\"k\",\"value\":\"v\"}]'"),
):
    """Update a shelf."""
    with _client() as c:
        import bookstack_cli.resources.shelves as r
        from bookstack_cli.models import ShelfCreate

        kwargs: dict[str, Any] = {"name": name, "description": description}
        if books:
            kwargs["books"] = [int(b.strip()) for b in books.split(",") if b.strip()]
        if tags:
            import json as _json
            kwargs["tags"] = _json.loads(tags)

        _print(_run(r.update_shelf(c, id, ShelfCreate(**kwargs))))


# ------------------------------------------------------------------
# Book commands
# ------------------------------------------------------------------


@books_app.command("list")
def books_list(
    sort: str = typer.Option(None, help="Field to sort by (name, created_at, etc.)"),
    order: str = typer.Option(None, help="Sort order (asc, desc)"),
):
    """List all books."""
    with _client() as c:
        import bookstack_cli.resources.books as r

        _print(_collect(r.list_books(c, sort=sort, order=order)))


@books_app.command("get")
def books_get(id: int = typer.Argument(..., help="Book ID")):
    """Get a book by ID."""
    with _client() as c:
        import bookstack_cli.resources.books as r

        _print(_run(r.get_book(c, id)))


@books_app.command("create")
def books_create(
    name: str = typer.Argument(..., help="Book name"),
    description: str = "",
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags"),
):
    """Create a new book."""
    with _client() as c:
        import bookstack_cli.resources.books as r
        from bookstack_cli.models import BookCreate

        kwargs: dict[str, Any] = {"name": name, "description": description}
        if tags:
            import json as _json
            kwargs["tags"] = _json.loads(tags)

        _print(_run(r.create_book(c, BookCreate(**kwargs))))


@books_app.command("delete")
def books_delete(id: int = typer.Argument(..., help="Book ID")):
    """Delete a book."""
    with _client() as c:
        import bookstack_cli.resources.books as r

        _run(r.delete_book(c, id))
        _print({"ok": True, "id": id})


@books_app.command("update")
def books_update(
    id: int = typer.Argument(..., help="Book ID"),
    name: str = typer.Argument(..., help="New book name"),
    description: str = "",
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags e.g. '[{\"name\":\"k\",\"value\":\"v\"}]'"),
):
    """Update a book."""
    with _client() as c:
        import bookstack_cli.resources.books as r
        from bookstack_cli.models import BookCreate

        kwargs: dict[str, Any] = {"name": name, "description": description}
        if tags:
            import json as _json
            kwargs["tags"] = _json.loads(tags)

        _print(_run(r.update_book(c, id, BookCreate(**kwargs))))


# ------------------------------------------------------------------
# Chapter commands
# ------------------------------------------------------------------


@chapters_app.command("list")
def chapters_list(book_id: int = typer.Option(None, help="Filter by book ID")):
    """List chapters."""
    with _client() as c:
        import bookstack_cli.resources.chapters as r

        _print(_collect(r.list_chapters(c, book_id=book_id)))


@chapters_app.command("get")
def chapters_get(id: int = typer.Argument(..., help="Chapter ID")):
    """Get a chapter by ID."""
    with _client() as c:
        import bookstack_cli.resources.chapters as r

        _print(_run(r.get_chapter(c, id)))


@chapters_app.command("create")
def chapters_create(
    book_id: int = typer.Option(..., help="Parent book ID"),
    name: str = typer.Argument(..., help="Chapter name"),
    description: str = "",
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags"),
):
    """Create a new chapter."""
    with _client() as c:
        import bookstack_cli.resources.chapters as r
        from bookstack_cli.models import ChapterCreate

        kwargs: dict[str, Any] = {"book_id": book_id, "name": name, "description": description}
        if tags:
            import json as _json
            kwargs["tags"] = _json.loads(tags)

        _print(_run(r.create_chapter(c, ChapterCreate(**kwargs))))


@chapters_app.command("delete")
def chapters_delete(id: int = typer.Argument(..., help="Chapter ID")):
    """Delete a chapter."""
    with _client() as c:
        import bookstack_cli.resources.chapters as r

        _run(r.delete_chapter(c, id))
        _print({"ok": True, "id": id})


@chapters_app.command("update")
def chapters_update(
    id: int = typer.Argument(..., help="Chapter ID"),
    name: str = typer.Argument(..., help="New chapter name"),
    description: str = "",
    book_id: int = typer.Option(..., "--book-id", help="Parent book ID"),
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags e.g. '[{\"name\":\"k\",\"value\":\"v\"}]'"),
):
    """Update a chapter."""
    with _client() as c:
        import bookstack_cli.resources.chapters as r
        from bookstack_cli.models import ChapterCreate

        kwargs: dict[str, Any] = {"book_id": book_id, "name": name, "description": description}
        if tags:
            import json as _json
            kwargs["tags"] = _json.loads(tags)

        _print(_run(r.update_chapter(c, id, ChapterCreate(**kwargs))))


# ------------------------------------------------------------------
# Page commands
# ------------------------------------------------------------------


@pages_app.command("list")
def pages_list(
    book_id: int = typer.Option(None, help="Filter by book ID"),
    chapter_id: int = typer.Option(None, help="Filter by chapter ID"),
    drafts: bool = typer.Option(False, "--drafts", help="Include drafts"),
):
    """List pages."""
    with _client() as c:
        import bookstack_cli.resources.pages as r

        _print(
            _collect(r.list_pages(c, book_id=book_id, chapter_id=chapter_id, include_drafts=drafts))
        )


@pages_app.command("get")
def pages_get(id: int = typer.Argument(..., help="Page ID")):
    """Get a page by ID."""
    with _client() as c:
        import bookstack_cli.resources.pages as r

        _print(_run(r.get_page(c, id)))


@pages_app.command("create")
def pages_create(
    book_id: int = typer.Option(..., help="Parent book ID"),
    name: str = typer.Argument(..., help="Page title"),
    markdown: str = typer.Option("", help="Content in markdown"),
    html: str = typer.Option("", help="Content in HTML (ignored if markdown given)"),
    markdown_file: Path | None = typer.Option(None, "--markdown-file",
                                               help="Read markdown from file"),
    html_file: Path | None = typer.Option(None, "--html-file",
                                          help="Read HTML from file"),
    chapter_id: int = typer.Option(None, help="Parent chapter ID"),
):
    """Create a new page.

    Content can be provided via:
    - --markdown or --html flags (inline)
    - --markdown-file or --html-file flags (read from file)
    - stdin pipe (auto-detected when stdin is not a TTY)
    """
    import sys

    if markdown_file:
        markdown = markdown_file.read_text()
    elif html_file:
        html = html_file.read_text()
    elif not markdown and not html and not sys.stdin.isatty():
        stdin_content = sys.stdin.read()
        if stdin_content.strip():
            markdown = stdin_content

    # Only pass non-empty content — empty string triggers API validation error
    kwargs: dict[str, Any] = {"book_id": book_id, "name": name}
    if chapter_id is not None:
        kwargs["chapter_id"] = chapter_id
    if markdown:
        kwargs["markdown"] = markdown
    if html and not markdown:
        kwargs["html"] = html

    with _client() as c:
        import bookstack_cli.resources.pages as r
        from bookstack_cli.models import PageCreate

        _print(_run(r.create_page(c, PageCreate(**kwargs))))


@pages_app.command("import")
def pages_import(
    file: Path = typer.Option(..., "--file", help="Path to markdown file"),
    name: str | None = typer.Option(None, "--name", help="Page name (default: filename)"),
    book_id: int | None = typer.Option(None, "--book-id", help="Parent book ID (required for new page)"),
    page_id: int | None = typer.Option(None, "--page-id", help="Update existing page by ID"),
    chapter_id: int | None = typer.Option(None, "--chapter-id", help="Parent chapter ID"),
):
    """Import a markdown file into a BookStack page.

    Handles local image references:
    - Uploads found images as page attachments
    - Replaces local paths with attachment URLs

    Provide --book-id to create a new page, or --page-id to update existing.
    """
    if not book_id and not page_id:
        _print({"error": "Provide --book-id (new page) or --page-id (update existing)"})
        raise typer.Exit(1)

    page_name = name if name else file.stem
    cfg = get_config()

    with _client() as c:
        import bookstack_cli.resources.pages as r

        try:
            result = _run(
                r.import_markdown_file(
                    c,
                    file_path=str(file),
                    page_name=page_name,
                    book_id=book_id if book_id else 0,
                    chapter_id=chapter_id,
                    page_id=page_id,
                    instance_url=cfg.url,
                )
            )
            _print(result)
        except Exception as e:
            _print({"error": str(e)})
            raise typer.Exit(1)


@pages_app.command("delete")
def pages_delete(id: int = typer.Argument(..., help="Page ID")):
    """Delete a page."""
    with _client() as c:
        import bookstack_cli.resources.pages as r

        _run(r.delete_page(c, id))
        _print({"ok": True, "id": id})


@pages_app.command("update")
def pages_update(
    id: int = typer.Argument(..., help="Page ID"),
    name: str | None = typer.Option(None, "--name", help="New page name"),
    markdown: str | None = typer.Option(None, "--markdown", help="New markdown content"),
    html: str | None = typer.Option(None, "--html", help="New HTML content"),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", help="Read markdown from file"),
    html_file: Path | None = typer.Option(None, "--html-file", help="Read HTML from file"),
    tags: str | None = typer.Option(None, "--tags", help="JSON array of tags"),
    append: str | None = typer.Option(None, "--append", help="Text to append to content"),
    append_file: Path | None = typer.Option(None, "--append-file", help="File to append to content"),
):
    """Update a page (partial updates supported — only provided fields change).

    Content can come from --markdown/--html inline, --markdown-file/--html-file,
    or piped stdin (when no content flags given and stdin is not a TTY).

    Use --append or --append-file to add content after existing page content
    without reading and rewriting the whole page.
    """
    import json as _json
    import sys

    # If appending, fetch current content first
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name

    if append is not None or append_file is not None:
        with _client() as fetch_c:
            current = _run(fetch_c.get(f"pages/{id}"))
            current_md = current.get("markdown", "") or ""
        if append_file:
            append = append_file.read_text()
        kwargs["markdown"] = current_md.rstrip() + "\n\n" + append
    elif markdown_file:
        kwargs["markdown"] = markdown_file.read_text()
    elif html_file:
        kwargs["html"] = html_file.read_text()
    elif markdown is not None:
        kwargs["markdown"] = markdown
    elif html is not None:
        kwargs["html"] = html
    elif not sys.stdin.isatty():
        stdin_content = sys.stdin.read()
        if stdin_content.strip():
            kwargs["markdown"] = stdin_content

    if tags is not None:
        kwargs["tags"] = _json.loads(tags)

    if not kwargs:
        _print({"error": "No fields to update. Provide --name, --markdown, --html, --tags, etc."})
        raise typer.Exit(1)

    with _client() as c:
        import bookstack_cli.resources.pages as r
        from bookstack_cli.models import PageUpdate

        _print(_run(r.update_page(c, id, PageUpdate(**kwargs))))


@pages_app.command("resolve-url")
def pages_resolve_url(
    url: str = typer.Argument(..., help="Full BookStack page URL, e.g. https://wiki/books/my-book/page/my-page"),
):
    """Resolve a BookStack web URL to a page ID and content.

    BookStack web URLs differ from API URLs:
    - Web:  https://wiki.example.com/books/my-book/page/my-page
    - API:  GET /api/pages/123

    This command extracts the page slug from the URL and finds the matching page.
    """
    cfg = get_config()
    with _client() as c:
        import bookstack_cli.resources.pages as r

        try:
            page = _run(r.resolve_page_url(c, url, instance_url=cfg.url))
            _print(page)
        except ValueError as e:
            _print({"error": str(e)})
            raise typer.Exit(1)


# ------------------------------------------------------------------
# Attachment commands
# ------------------------------------------------------------------


@attachments_app.command("list")
def attachments_list(page_id: int = typer.Option(None, help="Filter by page ID")):
    """List attachments."""
    with _client() as c:
        import bookstack_cli.resources.attachments as r

        _print(_collect(r.list_attachments(c, page_id=page_id)))


@attachments_app.command("get")
def attachments_get(id: int = typer.Argument(..., help="Attachment ID")):
    """Get attachment by ID."""
    with _client() as c:
        import bookstack_cli.resources.attachments as r

        _print(_run(r.get_attachment(c, id)))


@attachments_app.command("create-link")
def attachments_create_link(
    name: str = typer.Option(..., prompt=True, help="Attachment name"),
    page_id: int = typer.Option(..., prompt=True, help="Parent page ID"),
    link: str = typer.Option(..., prompt=True, help="URL to link"),
):
    """Create a link-type attachment on a page."""
    with _client() as c:
        import bookstack_cli.resources.attachments as r
        from bookstack_cli.models import AttachmentCreate

        _print(
            _run(
                r.create_attachment_link(
                    c, AttachmentCreate(name=name, page_id=page_id, link=link)
                )
            )
        )


@attachments_app.command("upload")
def attachments_upload(
    name: str = typer.Option(..., prompt=True, help="Attachment name"),
    page_id: int = typer.Option(..., prompt=True, help="Parent page ID"),
    file: Path = typer.Option(..., "--file", help="Path to file to upload"),
):
    """Upload a file as attachment on a page."""
    file_content = file.read_bytes()
    with _client() as c:
        import bookstack_cli.resources.attachments as r

        _print(
            _run(
                r.upload_attachment(
                    c, name=name, page_id=page_id,
                    file_content=file_content, filename=file.name,
                )
            )
        )


@attachments_app.command("delete")
def attachments_delete(id: int = typer.Argument(..., help="Attachment ID")):
    """Delete an attachment."""
    with _client() as c:
        import bookstack_cli.resources.attachments as r

        _run(r.delete_attachment(c, id))
        _print({"ok": True, "id": id})


# ------------------------------------------------------------------
# User commands
# ------------------------------------------------------------------


@users_app.command("list")
def users_list():
    """List all users (admin)."""
    with _client() as c:
        import bookstack_cli.resources.users as r

        _print(_collect(r.list_users(c)))


@users_app.command("get")
def users_get(id: int = typer.Argument(..., help="User ID")):
    """Get user by ID."""
    with _client() as c:
        import bookstack_cli.resources.users as r

        _print(_run(r.get_user(c, id)))


# ------------------------------------------------------------------
# Role commands
# ------------------------------------------------------------------


@roles_app.command("list")
def roles_list():
    """List all roles (admin)."""
    with _client() as c:
        import bookstack_cli.resources.roles as r

        _print(_collect(r.list_roles(c)))


# ------------------------------------------------------------------
# Search commands
# ------------------------------------------------------------------


@search_app.command("query")
def search_query(query: str = typer.Argument(..., help="Search term")):
    """Search across all content."""
    with _client() as c:
        import bookstack_cli.resources.search as r

        _print(_collect(r.search(c, query=query)))


# ------------------------------------------------------------------
# Callback
# ------------------------------------------------------------------


@app.command("test")
def config_test():
    """Test connection to the configured BookStack instance."""
    try:
        cfg = get_config()
        with _client() as c:
            result = _run(c.get("books", params={"count": 1}))
            total = result.get("total", 0)
            _print({
                "ok": True,
                "url": cfg.url,
                "token_id": cfg.token_id,
                "accessible": True,
                "total_books": total,
            })
    except BookStackError as e:
        _print({"ok": False, "error": str(e)})
        raise typer.Exit(1)
    except Exception as e:
        _print({"ok": False, "error": f"Connection failed: {e}"})
        raise typer.Exit(1)


@app.callback()
def callback() -> None:
    """BookStack CLI — interact with a BookStack wiki via its REST API.

    Output is always JSON for easy consumption by coding agents.
    """
