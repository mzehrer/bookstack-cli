"""Tests for resource modules — each CRUD operation with mocked HTTP."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from bookstack_cli.client import BookStackClient
from bookstack_cli.models import (
    Attachment,
    Book,
    BookCreate,
    Chapter,
    ChapterCreate,
    Page,
    PageCreate,
    PageMove,
    Role,
    Shelf,
    ShelfCreate,
    User,
)


class TestBookCover:
    async def test_upload_cover(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="PUT",
            json={"id": 1, "name": "Test", "image_id": 42},
        )
        from bookstack_cli.resources.books import upload_book_cover

        result = await upload_book_cover(client, 1, file_content=b"img", filename="cover.jpg")
        assert result["image_id"] == 42


class TestShelfCover:
    async def test_upload_cover(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves/1",
            method="PUT",
            json={"id": 1, "name": "Test", "image_id": 99},
        )
        from bookstack_cli.resources.shelves import upload_shelf_cover

        result = await upload_shelf_cover(client, 1, file_content=b"img", filename="cover.png")
        assert result["image_id"] == 99



from tests.conftest import (
    SAMPLE_ATTACHMENT,
    SAMPLE_BOOK,
    SAMPLE_CHAPTER,
    SAMPLE_LIST_RESPONSE,
    SAMPLE_PAGE,
    SAMPLE_ROLE,
    SAMPLE_SHELF,
    SAMPLE_USER,
)


# ------------------------------------------------------------------
# Books
# ------------------------------------------------------------------


class TestBooks:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=100&page=1",
            method="GET",
            json=SAMPLE_LIST_RESPONSE,
        )
        from bookstack_cli.resources.books import list_books

        items = [b async for b in list_books(client)]
        assert len(items) == 1
        assert isinstance(items[0], Book)
        assert items[0].name == "Dev Handbook"

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="GET",
            json=SAMPLE_BOOK,
        )
        from bookstack_cli.resources.books import get_book

        b = await get_book(client, 1)
        assert b.id == 1
        assert b.name == "Dev Handbook"

    async def test_create(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="POST",
            json=SAMPLE_BOOK,
        )
        from bookstack_cli.resources.books import create_book

        b = await create_book(client, BookCreate(name="Dev Handbook"))
        assert b.id == 1

    async def test_delete(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="DELETE",
            status_code=204,
        )
        from bookstack_cli.resources.books import delete_book

        await delete_book(client, 1)  # should not raise


# ------------------------------------------------------------------
# Chapters
# ------------------------------------------------------------------


class TestChapters:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/chapters?count=100&page=1",
            method="GET",
            json={"data": [SAMPLE_CHAPTER], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.chapters import list_chapters

        items = [c async for c in list_chapters(client)]
        assert len(items) == 1
        assert isinstance(items[0], Chapter)

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/chapters/10",
            method="GET",
            json=SAMPLE_CHAPTER,
        )
        from bookstack_cli.resources.chapters import get_chapter

        c = await get_chapter(client, 10)
        assert c.id == 10

    async def test_create(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/chapters",
            method="POST",
            json=SAMPLE_CHAPTER,
        )
        from bookstack_cli.resources.chapters import create_chapter

        c = await create_chapter(client, ChapterCreate(book_id=1, name="Intro"))
        assert c.id == 10

    async def test_delete(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/chapters/10",
            method="DELETE",
            status_code=204,
        )
        from bookstack_cli.resources.chapters import delete_chapter

        await delete_chapter(client, 10)


# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------


class TestPages:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages?count=100&page=1",
            method="GET",
            json={"data": [SAMPLE_PAGE], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.pages import list_pages

        items = [p async for p in list_pages(client)]
        assert len(items) == 1
        assert isinstance(items[0], Page)

    async def test_list_filtered_by_book_id(self, client: BookStackClient, httpx_mock):
        """Client-side book_id filter returns only matching pages."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages?count=100&page=1",
            method="GET",
            json={
                "data": [
                    {"id": 1, "book_id": 10, "name": "Page A", "slug": "page-a",
                     "created_at": None, "updated_at": None,
                     "created_by": None, "updated_by": None},
                    {"id": 2, "book_id": 20, "name": "Page B", "slug": "page-b",
                     "created_at": None, "updated_at": None,
                     "created_by": None, "updated_by": None},
                ],
                "total": 2, "per_page": 100,
            },
        )
        from bookstack_cli.resources.pages import list_pages

        items = [p async for p in list_pages(client, book_id=10)]
        assert len(items) == 1
        assert items[0].name == "Page A"

    async def test_list_with_drafts(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages?count=100&page=1&draft=true",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100},
        )
        from bookstack_cli.resources.pages import list_pages

        items = [p async for p in list_pages(client, include_drafts=True)]
        assert items == []

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/42",
            method="GET",
            json=SAMPLE_PAGE,
        )
        from bookstack_cli.resources.pages import get_page

        p = await get_page(client, 42)
        assert p.id == 42
        assert p.markdown == "# Hello"

    async def test_create(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages",
            method="POST",
            json=SAMPLE_PAGE,
        )
        from bookstack_cli.resources.pages import create_page

        p = await create_page(client, PageCreate(book_id=1, name="Getting Started", markdown="# Hello"))
        assert p.id == 42

    async def test_move(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/42/move",
            method="PUT",
            json={**SAMPLE_PAGE, "book_id": 2},
        )
        from bookstack_cli.resources.pages import move_page

        p = await move_page(client, 42, PageMove(book_id=2))
        assert p.id == 42
        # The move is considered successful if no exception

    async def test_delete(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/42",
            method="DELETE",
            status_code=204,
        )
        from bookstack_cli.resources.pages import delete_page

        await delete_page(client, 42)


# ------------------------------------------------------------------
# Shelves
# ------------------------------------------------------------------


class TestShelves:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves?count=100&page=1",
            method="GET",
            json={"data": [SAMPLE_SHELF], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.shelves import list_shelves

        items = [s async for s in list_shelves(client)]
        assert len(items) == 1
        assert isinstance(items[0], Shelf)

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves/5",
            method="GET",
            json=SAMPLE_SHELF,
        )
        from bookstack_cli.resources.shelves import get_shelf

        s = await get_shelf(client, 5)
        assert s.id == 5

    async def test_create(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves",
            method="POST",
            json=SAMPLE_SHELF,
        )
        from bookstack_cli.resources.shelves import create_shelf

        s = await create_shelf(client, ShelfCreate(name="Docs"))
        assert s.id == 5

    async def test_delete(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves/5",
            method="DELETE",
            status_code=204,
        )
        from bookstack_cli.resources.shelves import delete_shelf

        await delete_shelf(client, 5)


# ------------------------------------------------------------------
# Attachments
# ------------------------------------------------------------------


class TestAttachments:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments?count=100&page=1",
            method="GET",
            json={"data": [SAMPLE_ATTACHMENT], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.attachments import list_attachments

        items = [a async for a in list_attachments(client)]
        assert len(items) == 1
        assert isinstance(items[0], Attachment)

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments/100",
            method="GET",
            json=SAMPLE_ATTACHMENT,
        )
        from bookstack_cli.resources.attachments import get_attachment

        a = await get_attachment(client, 100)
        assert a.id == 100

    async def test_list_filtered_by_page(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments?count=100&page=1&page_id=42",
            method="GET",
            json={"data": [SAMPLE_ATTACHMENT], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.attachments import list_attachments

        items = [a async for a in list_attachments(client, page_id=42)]
        assert len(items) == 1
        assert items[0].page_id == 42

    async def test_create_link(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments",
            method="POST",
            json=SAMPLE_ATTACHMENT,
        )
        from bookstack_cli.models import AttachmentCreate
        from bookstack_cli.resources.attachments import create_attachment_link

        a = await create_attachment_link(
            client, AttachmentCreate(name="Screenshot", page_id=42, link="https://x.com/img.png")
        )
        assert a.id == 100

    async def test_download(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments/100",
            method="GET",
            json={
                "id": 100,
                "name": "photo",
                "extension": "jpg",
                "uploaded_to": 42,
                "external": False,
                "order": 1,
                "created_by": None,
                "updated_by": None,
                "created_at": None,
                "updated_at": None,
                "content": "/9j/4AAQSkZJRg==",
            },
        )
        from bookstack_cli.resources.attachments import download_attachment

        name, content = await download_attachment(client, 100)
        assert name == "photo.jpg"
        assert len(content) > 0


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------


class TestSearch:
    async def test_query(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/search?count=100&page=1&query=hello",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100},
        )
        from bookstack_cli.resources.search import search

        results = [r async for r in search(client, query="hello")]
        assert results == []

    async def test_query_with_results(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/search?count=100&page=1&query=dev",
            method="GET",
            json={
                "data": [
                    {"id": 1, "name": "Dev Handbook", "type": "book", "url": "/books/1", "tags": [], "score": 0.9}
                ],
                "total": 1,
                "per_page": 100,
            },
        )
        from bookstack_cli.resources.search import search

        results = [r async for r in search(client, query="dev")]
        assert len(results) == 1
        assert results[0].type == "book"


# ------------------------------------------------------------------
# Users
# ------------------------------------------------------------------


class TestUsers:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/users?count=100&page=1",
            method="GET",
            json={"data": [SAMPLE_USER], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.users import list_users

        items = [u async for u in list_users(client)]
        assert len(items) == 1
        assert isinstance(items[0], User)

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/users/1",
            method="GET",
            json=SAMPLE_USER,
        )
        from bookstack_cli.resources.users import get_user

        u = await get_user(client, 1)
        assert u.id == 1


# ------------------------------------------------------------------
# Roles
# ------------------------------------------------------------------


class TestRoles:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/roles?count=100&page=1",
            method="GET",
            json={"data": [SAMPLE_ROLE], "total": 1, "per_page": 100},
        )
        from bookstack_cli.resources.roles import list_roles

        items = [r async for r in list_roles(client)]
        assert len(items) == 1
        assert isinstance(items[0], Role)

    async def test_get_not_supported(self):
        """Roles resource has no get, only list/create/update/delete."""
        pass


# ------------------------------------------------------------------
# Revisions
# ------------------------------------------------------------------


class TestRevisions:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/revisions?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100},
        )
        from bookstack_cli.resources.revisions import list_revisions

        items = [r async for r in list_revisions(client)]
        assert items == []


# ------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------


class TestTags:
    async def test_list(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/tags?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100},
        )
        from bookstack_cli.resources.tags import list_tags

        items = [t async for t in list_tags(client)]
        assert items == []
