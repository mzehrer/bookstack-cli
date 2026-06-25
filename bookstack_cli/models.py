"""Pydantic models for BookStack API entities."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, BeforeValidator


# ------------------------------------------------------------------
# Shared / Nested
# ------------------------------------------------------------------


class Tag(BaseModel):
    """A key-value tag attached to content entities."""

    name: str
    value: str | None = None


class UserSummary(BaseModel):
    """Minimal user reference (created_by / updated_by)."""

    id: int
    name: str


def _coerce_user_ref(v: Any) -> Any:
    """BookStack sometimes returns user ID int instead of {id, name} object."""
    if isinstance(v, int):
        return UserSummary(id=v, name="")
    return v


UserRef = Annotated[UserSummary | None, BeforeValidator(_coerce_user_ref)]


# ------------------------------------------------------------------
# Paginated List Response
# ------------------------------------------------------------------


class PaginatedList(BaseModel):
    """Wrapper for paginated list responses from the API."""

    data: list[dict[str, Any]]
    total: int
    count: int
    per_page: int = Field(alias="per_page")
    current_page: int = Field(alias="current_page")
    last_page: int = Field(alias="last_page")
    next_page_url: str | None = Field(default=None, alias="next_page_url")
    prev_page_url: str | None = Field(default=None, alias="prev_page_url")

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------------------------------------
# Shelves (Bookshelves)
# ------------------------------------------------------------------


class Shelf(BaseModel):
    """A bookshelf containing books."""

    id: int
    name: str
    description: str = ""
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UserRef = None
    updated_by: UserRef = None


class ShelfCreate(BaseModel):
    """Payload for creating/updating a shelf."""

    name: str
    description: str = ""
    books: list[int] = []
    tags: list[Tag] = []


# ------------------------------------------------------------------
# Books
# ------------------------------------------------------------------


class Book(BaseModel):
    """A book containing chapters and pages."""

    id: int
    name: str
    description: str = ""
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UserRef = None
    updated_by: UserRef = None


class BookCreate(BaseModel):
    """Payload for creating/updating a book."""

    name: str
    description: str = ""
    tags: list[Tag] = []


# ------------------------------------------------------------------
# Chapters
# ------------------------------------------------------------------


class Chapter(BaseModel):
    """A chapter within a book."""

    id: int
    book_id: int
    name: str
    description: str = ""
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UserRef = None
    updated_by: UserRef = None


class ChapterCreate(BaseModel):
    """Payload for creating/updating a chapter."""

    book_id: int
    name: str
    description: str = ""
    tags: list[Tag] = []


# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------


class Page(BaseModel):
    """A wiki page."""

    id: int
    book_id: int
    chapter_id: int | None = None
    name: str
    slug: str = ""
    html: str = ""
    markdown: str = ""
    draft: bool = False
    tags: list[Tag] = []
    priority: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UserRef = None
    updated_by: UserRef = None


class PageCreate(BaseModel):
    """Payload for creating a page."""

    book_id: int
    chapter_id: int | None = None
    name: str
    html: str = ""
    markdown: str = ""
    tags: list[Tag] = []
    draft: bool = False
    priority: int = 0


class PageUpdate(BaseModel):
    """Payload for updating a page."""

    name: str | None = None
    html: str | None = None
    markdown: str | None = None
    tags: list[Tag] | None = None
    draft: bool | None = None
    priority: int | None = None


class PageMove(BaseModel):
    """Payload for moving a page."""

    book_id: int
    chapter_id: int | None = None


# ------------------------------------------------------------------
# Attachments
# ------------------------------------------------------------------


class Attachment(BaseModel):
    """A file or link attachment on a page."""

    id: int
    name: str
    page_id: int = Field(alias="uploaded_to", default=0)
    link: str | None = None
    file_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UserRef = None
    updated_by: UserRef = None

    model_config = ConfigDict(populate_by_name=True)


class AttachmentCreate(BaseModel):
    """Payload for creating a link or file attachment."""

    name: str
    page_id: int
    link: str | None = None
    # For file uploads, use multipart with ``uploaded_file``


# ------------------------------------------------------------------
# Users
# ------------------------------------------------------------------


class User(BaseModel):
    """A BookStack user."""

    id: int
    name: str
    email: str = ""
    language: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ------------------------------------------------------------------
# Roles
# ------------------------------------------------------------------


class Role(BaseModel):
    """A user role."""

    id: int
    name: str
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------


class SearchResult(BaseModel):
    """A single search result."""

    id: int
    name: str
    type: str  # page, book, chapter, shelf
    url: str = ""
    preview_html: dict[str, str] | str = ""
    tags: list[Tag] = []
    score: float = 0.0

    @property
    def preview_text(self) -> str:
        """Get preview text regardless of whether API returns string or object."""
        if isinstance(self.preview_html, dict):
            return self.preview_html.get("content", "")
        return self.preview_html
