# API Reference

Based on BookStack v23–v24 API surface. All endpoints under `/api/`.
Full interactive docs at `<bookstack_url>/api/docs`.

## Common Patterns

### Headers
```
Content-Type: application/json
Accept: application/json
Authorization: Token <token_id>:<token_secret>
```

### List Response
```json
{
  "data": [ ... ],
  "total": 42,
  "count": 20,
  "per_page": 20,
  "current_page": 1,
  "last_page": 3,
  "next_page_url": "/api/books?page=2",
  "prev_page_url": null
}
```

### Single Entity Response
```json
{
  "id": 1,
  "name": "...",
  "description": "...",
  "created_at": "2024-01-01T00:00:00.000000Z",
  "updated_at": "...",
  "created_by": { "id": 1, "name": "..." },
  "updated_by": { "id": 1, "name": "..." },
  "tags": [{ "name": "...", "value": "..." }]
}
```

### Error Response
```json
{
  "error": { "code": 401, "message": "Unauthorized" }
}
```

### Pagination
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number (1-indexed) |
| `count` | int | 20 | Items per page (max ~100-500, server configurable) |

### Sorting
```
GET /api/books?sort=name&order=asc
```
| Param | Values |
|---|---|
| `sort` | `name`, `created_at`, `updated_at`, `id` |
| `order` | `asc`, `desc` |

---

## Shelves (Bookshelves)

Base: `/api/shelves`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/shelves` | List shelves |
| `GET` | `/api/shelves/{id}` | Get shelf (includes books list) |
| `POST` | `/api/shelves` | Create shelf |
| `PUT` | `/api/shelves/{id}` | Update shelf |
| `DELETE` | `/api/shelves/{id}` | Delete shelf |

### POST/PUT Body
```json
{
  "name": "Shelf Name",
  "description": "Optional description",
  "books": [1, 2, 3],
  "tags": [{ "name": "category", "value": "tech" }]
}
```

Cover image: use `multipart/form-data` with `image` field.

---

## Books

Base: `/api/books`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/books` | List books |
| `GET` | `/api/books/{id}` | Get book (includes shelves, chapters) |
| `POST` | `/api/books` | Create book |
| `PUT` | `/api/books/{id}` | Update book |
| `DELETE` | `/api/books/{id}` | Delete book |

### POST/PUT Body
```json
{
  "name": "Book Name",
  "description": "Optional description",
  "tags": [{ "name": "topic", "value": "api" }]
}
```

Cover image: `multipart/form-data` with `image` field.

---

## Chapters

Base: `/api/chapters`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/chapters` | List chapters |
| `GET` | `/api/chapters/{id}` | Get chapter (includes pages list) |
| `POST` | `/api/chapters` | Create chapter |
| `PUT` | `/api/chapters/{id}` | Update chapter |
| `DELETE` | `/api/chapters/{id}` | Delete chapter |

### POST/PUT Body
```json
{
  "book_id": 1,
  "name": "Chapter Name",
  "description": "Optional description",
  "tags": [{ "name": "priority", "value": "high" }]
}
```

---

## Pages

Base: `/api/pages`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/pages` | List pages (`?draft=true` includes drafts) |
| `GET` | `/api/pages/{id}` | Get page |
| `POST` | `/api/pages` | Create page |
| `PUT` | `/api/pages/{id}` | Update page |
| `DELETE` | `/api/pages/{id}` | Delete page |
| `PUT` | `/api/pages/{id}/move` | Move page to different book/chapter |

### Web URLs

BookStack page web URLs use slugs, not IDs:

```
https://wiki.example.com/books/{book-slug}/page/{page-slug}
```

Use the CLI's `resolve-url` command to convert:

```bash
bookstack pages resolve-url "https://wiki.example.com/books/my-book/page/my-page"
```

### POST Body
```json
{
  "book_id": 1,
  "chapter_id": null,
  "name": "Page Title",
  "html": "<p>Content in HTML</p>",
  "markdown": "# Content in Markdown",
  "tags": [{ "name": "status", "value": "draft" }],
  "priority": 1,
  "draft": false
}
```

Note: Provide EITHER `html` OR `markdown`, not both.

### Move Body
```json
{
  "book_id": 2,
  "chapter_id": 5
}
```
Omit `chapter_id` to move to book root.

---

## Attachments

Base: `/api/attachments`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/attachments` | List attachments (`?page_id=X` filters) |
| `GET` | `/api/attachments/{id}` | Get attachment |
| `POST` | `/api/attachments` | Create attachment |
| `PUT` | `/api/attachments/{id}` | Update attachment |
| `DELETE` | `/api/attachments/{id}` | Delete attachment |

### Link Attachment (JSON)
```json
{
  "name": "Reference Link",
  "page_id": 1,
  "link": "https://example.com/doc"
}
```

### File Upload (multipart/form-data)
| Field | Value |
|---|---|
| `name` | "Screenshot" |
| `page_id` | 1 |
| `uploaded_file` | (binary file data) |

---

## Search

Base: `/api/search`

| Method | Path | Params |
|---|---|---|
| `GET` | `/api/search` | `?query=<search_term>` |

Returns standard paginated response across all content types.
No tag-based filtering at API level.

---

## Users

Base: `/api/users`

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/users` | List users (admin) |
| `GET` | `/api/users/{id}` | Get user |
| `POST` | `/api/users` | Create user (admin) |
| `PUT` | `/api/users/{id}` | Update user (admin) |
| `DELETE` | `/api/users/{id}` | Delete user (admin) |

---

## Roles

Base: `/api/roles`

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/roles` | List roles (admin) |
| `POST` | `/api/roles` | Create role (admin) |
| `PUT` | `/api/roles/{id}` | Update role (admin) |
| `DELETE` | `/api/roles/{id}` | Delete role (admin) |

---

## Tags

Base: `/api/tags`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tags` | List all tags across system |

---

## Revisions

Base: `/api/revisions`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/revisions` | List revisions |
| `GET` | `/api/revisions/{id}` | Get revision |
| `DELETE` | `/api/revisions/{id}` | Delete revision |

---

## Rate Limiting

- Default: ~120 requests/min per IP (Laravel throttle, configurable)
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- HTTP 429 with `Retry-After` header when exceeded

## OpenAPI Spec

Full machine-readable spec available at `<bookstack_url>/api/docs.json`.
Interactive Swagger UI at `<bookstack_url>/api/docs`.
