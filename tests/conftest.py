"""Shared fixtures and sample data for all tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from bookstack_cli.client import BookStackClient


# ------------------------------------------------------------------
# Sample API response data
# ------------------------------------------------------------------

SAMPLE_BOOK: dict[str, Any] = {
    "id": 1,
    "name": "Dev Handbook",
    "description": "Engineering guide",
    "tags": [{"name": "dept", "value": "eng"}],
    "created_at": "2024-01-15T10:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
    "created_by": {"id": 1, "name": "Admin"},
    "updated_by": {"id": 1, "name": "Admin"},
}

SAMPLE_PAGE: dict[str, Any] = {
    "id": 42,
    "book_id": 1,
    "chapter_id": None,
    "name": "Getting Started",
    "slug": "getting-started",
    "html": "<h1>Hello</h1>",
    "markdown": "# Hello",
    "draft": False,
    "tags": [],
    "priority": 1,
    "created_at": "2024-01-15T10:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
    "created_by": {"id": 1, "name": "Admin"},
    "updated_by": {"id": 1, "name": "Admin"},
}

SAMPLE_SHELF: dict[str, Any] = {
    "id": 5,
    "name": "Documentation",
    "description": "All docs",
    "tags": [],
    "created_at": "2024-01-15T10:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
    "created_by": {"id": 1, "name": "Admin"},
    "updated_by": {"id": 1, "name": "Admin"},
}

SAMPLE_CHAPTER: dict[str, Any] = {
    "id": 10,
    "book_id": 1,
    "name": "Introduction",
    "description": "First chapter",
    "tags": [],
    "created_at": "2024-01-15T10:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
    "created_by": {"id": 1, "name": "Admin"},
    "updated_by": {"id": 1, "name": "Admin"},
}

SAMPLE_ATTACHMENT: dict[str, Any] = {
    "id": 100,
    "name": "Screenshot.png",
    "page_id": 42,
    "link": None,
    "file_path": "uploads/2024/01/screenshot.png",
    "created_at": "2024-01-15T10:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
    "created_by": {"id": 1, "name": "Admin"},
    "updated_by": {"id": 1, "name": "Admin"},
}

SAMPLE_USER: dict[str, Any] = {
    "id": 1,
    "name": "Admin",
    "email": "admin@example.com",
    "language": "en",
    "created_at": "2023-01-01T00:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
}

SAMPLE_ROLE: dict[str, Any] = {
    "id": 1,
    "name": "Admin",
    "description": "Full access",
    "created_at": "2023-01-01T00:00:00.000000Z",
    "updated_at": "2024-06-01T12:00:00.000000Z",
}

SAMPLE_SEARCH_RESULT: dict[str, Any] = {
    "id": 42,
    "name": "Getting Started",
    "type": "page",
    "url": "/books/1/page/getting-started",
    "preview_html": "<p>Hello</p>",
    "tags": [],
    "score": 0.95,
}

SAMPLE_LIST_RESPONSE: dict[str, Any] = {
    "data": [SAMPLE_BOOK],
    "total": 1,
    "count": 1,
    "per_page": 20,
    "current_page": 1,
    "last_page": 1,
    "next_page_url": None,
    "prev_page_url": None,
}


SAMPLE_PAGINATED_TWO_PAGES: dict[str, Any] = {
    "data": [SAMPLE_BOOK],
    "total": 2,
    "count": 1,
    "per_page": 1,
    "current_page": 1,
    "last_page": 2,
    "next_page_url": "/api/books?page=2",
    "prev_page_url": None,
}

SAMPLE_PAGINATED_PAGE_TWO: dict[str, Any] = {
    "data": [{**SAMPLE_BOOK, "id": 2, "name": "Second Book"}],
    "total": 2,
    "count": 1,
    "per_page": 1,
    "current_page": 2,
    "last_page": 2,
    "next_page_url": None,
    "prev_page_url": "/api/books?page=1",
}


# ------------------------------------------------------------------
# Client fixture
# ------------------------------------------------------------------


@pytest.fixture
def client() -> BookStackClient:
    """A BookStackClient with explicit creds (no config file needed)."""
    return BookStackClient(
        base_url="http://test.bookstack.local",
        token_id="test-token-id",
        token_secret="test-token-secret",
    )


@pytest.fixture
def auth_header() -> str:
    """Expected Authorization header value."""
    return "Token test-token-id:test-token-secret"


# ------------------------------------------------------------------
# Sample data fixtures (for model tests)
# ------------------------------------------------------------------


@pytest.fixture
def sample_book_dict() -> dict[str, Any]:
    return dict(SAMPLE_BOOK)


@pytest.fixture
def sample_page_dict() -> dict[str, Any]:
    return dict(SAMPLE_PAGE)


@pytest.fixture
def sample_shelf_dict() -> dict[str, Any]:
    return dict(SAMPLE_SHELF)


@pytest.fixture
def sample_chapter_dict() -> dict[str, Any]:
    return dict(SAMPLE_CHAPTER)


@pytest.fixture
def sample_attachment_dict() -> dict[str, Any]:
    return dict(SAMPLE_ATTACHMENT)


@pytest.fixture
def sample_user_dict() -> dict[str, Any]:
    return dict(SAMPLE_USER)


@pytest.fixture
def sample_role_dict() -> dict[str, Any]:
    return dict(SAMPLE_ROLE)


@pytest.fixture
def sample_search_dict() -> dict[str, Any]:
    return dict(SAMPLE_SEARCH_RESULT)


@pytest.fixture
def sample_list_response() -> dict[str, Any]:
    return dict(SAMPLE_LIST_RESPONSE)
