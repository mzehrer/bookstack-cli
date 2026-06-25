"""Async HTTP client for BookStack API with auth, retry, pagination."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from bookstack_cli.config import get_config
from bookstack_cli.exceptions import (
    BookStackRateLimitError,
    map_status_to_error,
)

logger = logging.getLogger(__name__)

BASE_DELAY = 1.0
MAX_RETRIES = 5
MAX_PAGE_SIZE = 500


class BookStackClient:
    """Async HTTP client for BookStack REST API.

    Handles:
    - Auth header injection (Token token_id:token_secret)
    - Rate-limit retry with exponential backoff
    - Auto-pagination via async generator
    - Error mapping to typed exceptions
    """

    def __init__(
        self,
        base_url: str | None = None,
        token_id: str | None = None,
        token_secret: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if base_url and token_id and token_secret:
            self._base_url = base_url.rstrip("/")
            self._token_id = token_id
            self._token_secret = token_secret
        else:
            cfg = get_config()
            self._base_url = cfg.url
            self._token_id = cfg.token_id
            self._token_secret = cfg.token_secret

        auth_header_value = f"Token {self._token_id}:{self._token_secret}"

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": auth_header_value,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "BookStackClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __enter__(self) -> "BookStackClient":
        return self

    def __exit__(self, *args: Any) -> None:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.close())

    # ------------------------------------------------------------------
    # Request with retry
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        retry_count: int = 0,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send HTTP request with rate-limit retry."""
        url = f"/api/{path.lstrip('/')}"
        # Remove Content-Type for multipart (httpx sets correct boundary)
        has_files = "files" in kwargs
        if has_files:
            old_ct = self._client.headers.pop("Content-Type", None)
        try:
            response = await self._client.request(method, url, **kwargs)
        finally:
            if has_files and old_ct is not None:
                self._client.headers["Content-Type"] = old_ct

        if response.status_code == 429 and retry_count < MAX_RETRIES:
            retry_after = _parse_retry_after(response)
            delay = max(retry_after, BASE_DELAY * (2**retry_count))
            logger.warning(
                "Rate limited. Retry %d/%d after %.1fs",
                retry_count + 1,
                MAX_RETRIES,
                delay,
            )
            await asyncio.sleep(delay)
            return await self._request(method, path, retry_count + 1, **kwargs)

        if response.is_error:
            _raise_for_status(response)

        return response

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET request returning parsed JSON."""
        response = await self._request("GET", path, params=params)
        return response.json()

    async def get_raw(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """GET request returning raw response (e.g. for binary downloads)."""
        return await self._request("GET", path, params=params)

    async def post(
        self, path: str, json: dict[str, Any] | None = None, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST request returning parsed JSON."""
        response = await self._request("POST", path, json=json, data=data)
        return response.json()

    async def put(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """PUT request returning parsed JSON."""
        response = await self._request("PUT", path, json=json)
        return response.json()

    async def delete(self, path: str) -> None:
        """DELETE request."""
        await self._request("DELETE", path)

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[dict[str, Any]]:
        """Iterate over all pages of a list endpoint.

        Yields individual items from ``data`` across all pages.
        """
        params = dict(params or {})
        params.setdefault("count", min(page_size, MAX_PAGE_SIZE))
        page = 1

        while True:
            params["page"] = page
            data = await self.get(path, params=params)
            items: list[dict[str, Any]] = data.get("data", [])
            for item in items:
                yield item

            total: int = data.get("total", 0)
            per_page = data.get("per_page")
            if per_page is None:
                per_page = len(items) or page_size
            if page * per_page >= total:
                break
            page += 1


def _parse_retry_after(response: httpx.Response) -> float:
    """Extract Retry-After header value as float."""
    val = response.headers.get("Retry-After", "1")
    try:
        return float(val)
    except ValueError:
        return 1.0


def _raise_for_status(response: httpx.Response) -> None:
    """Map HTTP status to typed BookStack exception."""
    try:
        body = response.json()
        error = body.get("error", {})
        message = str(error.get("message", response.reason_phrase))
        validation = error.get("validation")
        if validation:
            details = "; ".join(
                f"{k}: {', '.join(v)}" for k, v in validation.items()
            )
            message = f"{message} ({details})"
    except Exception:
        message = response.reason_phrase or "Unknown error"

    raise map_status_to_error(response.status_code, message)
