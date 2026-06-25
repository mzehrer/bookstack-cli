"""Tests for Pydantic model parsing and serialization."""

from __future__ import annotations

from datetime import datetime

import pytest

from bookstack_cli.models import (
    Attachment,
    AttachmentCreate,
    Book,
    BookCreate,
    Chapter,
    ChapterCreate,
    Page,
    PageCreate,
    PageMove,
    PageUpdate,
    PaginatedList,
    Role,
    SearchResult,
    Shelf,
    ShelfCreate,
    Tag,
    User,
    UserSummary,
)


class TestTag:
    def test_minimal(self):
        t = Tag(name="status")
        assert t.name == "status"
        assert t.value is None

    def test_full(self):
        t = Tag(name="status", value="draft")
        assert t.value == "draft"


class TestUserSummary:
    def test_from_dict(self):
        u = UserSummary(id=1, name="Alice")
        assert u.name == "Alice"


class TestUserRef:
    """UserRef coercion from int or dict."""

    def test_from_dict(self):
        b = Book(**{"id": 1, "name": "x", "created_by": {"id": 5, "name": "Alice"}})
        assert b.created_by is not None
        assert b.created_by.id == 5
        assert b.created_by.name == "Alice"

    def test_from_int(self):
        b = Book(**{"id": 1, "name": "x", "created_by": 42})
        assert b.created_by is not None
        assert b.created_by.id == 42
        assert b.created_by.name == ""  # placeholder name

    def test_none(self):
        b = Book(**{"id": 1, "name": "x", "created_by": None})
        assert b.created_by is None


class TestBook:
    def test_from_sample(self, sample_book_dict: dict):
        b = Book(**sample_book_dict)
        assert b.id == 1
        assert b.name == "Dev Handbook"
        assert len(b.tags) == 1
        assert b.tags[0].name == "dept"

    def test_created_at_parsed(self, sample_book_dict: dict):
        b = Book(**sample_book_dict)
        assert isinstance(b.created_at, datetime)

    def test_created_by_parsed(self, sample_book_dict: dict):
        b = Book(**sample_book_dict)
        assert b.created_by is not None
        assert b.created_by.name == "Admin"


class TestBookCreate:
    def test_serializes(self):
        payload = BookCreate(name="New Book", description="Desc")
        data = payload.model_dump(exclude_unset=True)
        assert data["name"] == "New Book"
        assert data["description"] == "Desc"
        assert "tags" not in data  # default, exclude_unset

    def test_with_tags(self):
        payload = BookCreate(name="New", tags=[Tag(name="a", value="b")])
        data = payload.model_dump(exclude_unset=True)
        assert data["tags"] == [{"name": "a", "value": "b"}]


class TestPage:
    def test_from_sample(self, sample_page_dict: dict):
        p = Page(**sample_page_dict)
        assert p.id == 42
        assert p.name == "Getting Started"
        assert p.markdown == "# Hello"
        assert p.draft is False

    def test_chapter_id_none(self, sample_page_dict: dict):
        p = Page(**sample_page_dict)
        assert p.chapter_id is None


class TestPageCreate:
    def test_serializes(self):
        payload = PageCreate(book_id=1, name="Test", markdown="# T")
        data = payload.model_dump(exclude_unset=True)
        assert data["book_id"] == 1
        assert data["name"] == "Test"

    def test_draft_default_false(self):
        payload = PageCreate(book_id=1, name="Test")
        assert payload.draft is False


class TestPageUpdate:
    def test_partial_update(self):
        payload = PageUpdate(name="Renamed")
        data = payload.model_dump(exclude_unset=True)
        assert data == {"name": "Renamed"}

    def test_empty_update(self):
        payload = PageUpdate()
        data = payload.model_dump(exclude_unset=True)
        assert data == {}


class TestPageMove:
    def test_to_book(self):
        m = PageMove(book_id=2)
        data = m.model_dump(exclude_unset=True)
        assert data == {"book_id": 2}

    def test_to_chapter(self):
        m = PageMove(book_id=2, chapter_id=5)
        assert m.chapter_id == 5


class TestShelf:
    def test_from_sample(self, sample_shelf_dict: dict):
        s = Shelf(**sample_shelf_dict)
        assert s.id == 5
        assert s.name == "Documentation"


class TestShelfCreate:
    def test_with_books(self):
        s = ShelfCreate(name="Shelf", books=[1, 2, 3])
        assert s.books == [1, 2, 3]

    def test_default_no_books(self):
        s = ShelfCreate(name="Shelf")
        assert s.books == []


class TestChapter:
    def test_from_sample(self, sample_chapter_dict: dict):
        c = Chapter(**sample_chapter_dict)
        assert c.id == 10
        assert c.book_id == 1


class TestChapterCreate:
    def test_requires_book_id(self):
        c = ChapterCreate(book_id=1, name="Ch1")
        assert c.book_id == 1


class TestAttachment:
    def test_from_sample(self, sample_attachment_dict: dict):
        a = Attachment(**sample_attachment_dict)
        assert a.id == 100
        assert a.page_id == 42
        assert a.link is None

    def test_with_link(self):
        d = {
            "id": 101,
            "name": "Reference",
            "page_id": 42,
            "link": "https://example.com",
            "file_path": None,
            "created_at": None,
            "updated_at": None,
            "created_by": None,
            "updated_by": None,
        }
        a = Attachment(**d)
        assert a.link == "https://example.com"


class TestAttachmentCreate:
    def test_link_type(self):
        a = AttachmentCreate(name="Ref", page_id=42, link="https://x.com")
        data = a.model_dump(exclude_unset=True)
        assert data["link"] == "https://x.com"


class TestUser:
    def test_from_sample(self, sample_user_dict: dict):
        u = User(**sample_user_dict)
        assert u.id == 1
        assert u.email == "admin@example.com"


class TestRole:
    def test_from_sample(self, sample_role_dict: dict):
        r = Role(**sample_role_dict)
        assert r.id == 1
        assert r.name == "Admin"


class TestSearchResult:
    def test_from_sample(self, sample_search_dict: dict):
        s = SearchResult(**sample_search_dict)
        assert s.id == 42
        assert s.type == "page"
        assert s.score == 0.95


class TestPaginatedList:
    def test_from_sample(self, sample_list_response: dict):
        pl = PaginatedList(**sample_list_response)
        assert pl.total == 1
        assert pl.per_page == 20
        assert pl.current_page == 1
        assert pl.next_page_url is None

    def test_populate_by_name(self, sample_list_response: dict):
        pl = PaginatedList(**sample_list_response)
        assert pl.per_page == 20
        assert pl.current_page == 1
