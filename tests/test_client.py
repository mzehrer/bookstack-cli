"""Tests for BookStackClient — auth, CRUD, retry, pagination, error mapping."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from bookstack_cli.client import BookStackClient, _parse_retry_after
from bookstack_cli.exceptions import (
    BookStackAuthError,
    BookStackConfigError,
    BookStackNotFoundError,
    BookStackRateLimitError,
    BookStackServerError,
    BookStackValidationError,
)


class TestInit:
    """Client construction."""

    def test_explicit_params_skip_config(self):
        """Given explicit creds, client does not call get_config()."""
        c = BookStackClient(
            base_url="http://test.local",
            token_id="tid",
            token_secret="ts",
        )
        assert c._base_url == "http://test.local"
        assert c._token_id == "tid"
        assert c._token_secret == "ts"

    def test_no_params_raises_config_error(self):
        """When env and yaml both absent, raises BookStackConfigError."""
        with patch("bookstack_cli.client.get_config") as mock_get:
            mock_get.side_effect = BookStackConfigError("no config")
            with pytest.raises(BookStackConfigError):
                BookStackClient()

    def test_auth_header_format(self, client: BookStackClient, auth_header: str):
        """Auth header is 'Token <id>:<secret>'."""
        h = client._client.headers["Authorization"]
        assert h == auth_header

    def test_base_url_has_no_trailing_slash(self):
        """Trailing slash stripped from base_url."""
        c = BookStackClient(
            base_url="http://test.local/",
            token_id="tid",
            token_secret="ts",
        )
        assert c._base_url == "http://test.local"


class TestRequestRetry:
    """Rate-limit retry logic."""

    async def test_200_passthrough(self, client: BookStackClient, httpx_mock):
        """Non-error response returned directly."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="GET",
            json={"data": [], "total": 0},
        )
        result = await client.get("books")
        assert result == {"data": [], "total": 0}

    async def test_rate_limit_retries_then_succeeds(self, client: BookStackClient, httpx_mock):
        """429 triggers retry; eventually succeeds."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="GET",
            status_code=429,
            headers={"Retry-After": "0"},
        )
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="GET",
            json={"data": [{"id": 1}], "total": 1},
        )
        result = await client.get("books")
        assert result["data"][0]["id"] == 1

    async def test_rate_limit_exhausts_retries(self, client: BookStackClient, httpx_mock):
        """All retries exhausted → raises BookStackRateLimitError."""
        for _ in range(6):
            httpx_mock.add_response(
                url="http://test.bookstack.local/api/books",
                method="GET",
                status_code=429,
                headers={"Retry-After": "0"},
            )
        with pytest.raises(BookStackRateLimitError):
            await client.get("books")


class TestErrorMapping:
    """HTTP errors map to typed exceptions."""

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, BookStackAuthError),
            (404, BookStackNotFoundError),
            (422, BookStackValidationError),
            (500, BookStackServerError),
            (503, BookStackServerError),
        ],
    )
    async def test_status_maps_to_exception(
        self, client: BookStackClient, httpx_mock, status: int, expected: type
    ):
        """Each HTTP status raises the correct exception type."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="GET",
            status_code=status,
            json={"error": {"message": "test error"}},
        )
        with pytest.raises(expected):
            await client.get("books")

    async def test_429_maps_to_rate_limit_after_retries_exhausted(
        self, client: BookStackClient, httpx_mock
    ):
        """429 retries 5 times, then raises BookStackRateLimitError."""
        for _ in range(6):  # 1 initial + 5 retries
            httpx_mock.add_response(
                url="http://test.bookstack.local/api/books",
                method="GET",
                status_code=429,
                headers={"Retry-After": "0"},
                json={"error": {"message": "Too fast"}},
            )
        with pytest.raises(BookStackRateLimitError, match="Too fast"):
            await client.get("books")

    async def test_error_message_from_response(self, client: BookStackClient, httpx_mock):
        """Exception message comes from response JSON."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="GET",
            status_code=404,
            json={"error": {"message": "Book not found"}},
        )
        with pytest.raises(BookStackNotFoundError, match="Book not found"):
            await client.get("books")


class TestCRUD:
    """CRUD helper methods."""

    async def test_get(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="GET",
            json={"id": 1, "name": "Test"},
        )
        result = await client.get("books/1")
        assert result["name"] == "Test"

    async def test_post(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="POST",
            json={"id": 2, "name": "New"},
        )
        result = await client.post("books", json={"name": "New"})
        assert result["id"] == 2

    async def test_put(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="PUT",
            json={"id": 1, "name": "Updated"},
        )
        result = await client.put("books/1", json={"name": "Updated"})
        assert result["name"] == "Updated"

    async def test_delete(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="DELETE",
            status_code=204,
        )
        # Should not raise
        await client.delete("books/1")

    async def test_get_raw(self, client: BookStackClient, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="GET",
            content=b"binary data",
        )
        resp = await client.get_raw("books/1")
        assert resp.content == b"binary data"


class TestPagination:
    """Auto-pagination iterator."""

    async def test_single_page(self, client: BookStackClient, httpx_mock):
        """Single page returns all items."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=100&page=1",
            method="GET",
            json={
                "data": [{"id": 1}, {"id": 2}],
                "total": 2,
                "per_page": 100,
            },
        )
        items = [item async for item in client.paginate("books", page_size=100)]
        assert len(items) == 2
        assert items[0]["id"] == 1
        assert items[1]["id"] == 2

    async def test_multiple_pages(self, client: BookStackClient, httpx_mock):
        """Multiple pages are auto-fetched."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=1&page=1",
            method="GET",
            json={
                "data": [{"id": 1}],
                "total": 2,
                "per_page": 1,
                "current_page": 1,
                "last_page": 2,
            },
        )
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=1&page=2",
            method="GET",
            json={
                "data": [{"id": 2}],
                "total": 2,
                "per_page": 1,
                "current_page": 2,
                "last_page": 2,
            },
        )
        items = [item async for item in client.paginate("books", page_size=1)]
        assert len(items) == 2
        assert [i["id"] for i in items] == [1, 2]

    async def test_empty_page(self, client: BookStackClient, httpx_mock):
        """Empty list stops iteration immediately."""
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100},
        )
        items = [item async for item in client.paginate("books")]
        assert items == []


class TestContextManager:
    """Async context manager."""

    async def test_context_manager_closes(self):
        """__aexit__ closes the underlying httpx client."""
        async with BookStackClient(
            base_url="http://test.local", token_id="t", token_secret="s"
        ) as c:
            assert not c._client.is_closed
        assert c._client.is_closed


class TestParseRetryAfter:
    """_parse_retry_after helper."""

    def test_valid_header(self):
        resp = httpx.Response(429, headers={"Retry-After": "5"})
        assert _parse_retry_after(resp) == 5.0

    def test_invalid_header_defaults_to_one(self):
        resp = httpx.Response(429, headers={"Retry-After": "abc"})
        assert _parse_retry_after(resp) == 1.0

    def test_missing_header_defaults_to_one(self):
        resp = httpx.Response(429)
        assert _parse_retry_after(resp) == 1.0
