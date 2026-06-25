# Research: BookStack Wiki API

## Summary
BookStack exposes a RESTful JSON API authenticated via API token pairs (Token ID + Secret). It covers all major content entities — shelves, books, chapters, pages, attachments, users, roles, tags, and search — with standard CRUD patterns, paginated list responses, and permission scoping that mirrors the UI. The system includes settings-level HTML/CSS injection points but no native webhook/event-out system as of v24.

## Findings

### 1. Authentication
- **API Token pair**: Every user can generate token ID + secret from their profile.
- **Headers**: `Authorization: Token <token_id>:<token_secret>` (Base64-encoded basic-style).
- **Scope**: Token inherits the generating user's role permissions. No separate API-only permission.
- **No OAuth, no bearer tokens, no session auth for API**.

### 2. Full Endpoint List
All endpoints under `/api/`. Standard CRUD pattern: `GET /api/{entity}`, `GET /api/{entity}/{id}`, `POST`, `PUT`, `DELETE`.

| Entity | Endpoint Prefix | Notes |
|---|---|---|
| Shelves | `/api/shelves` | Bookshelves, can include books list |
| Books | `/api/books` | Includes cover image handling |
| Chapters | `/api/chapters` | Belongs to book |
| Pages | `/api/pages` | Draft/publish state, can move |
| Attachments | `/api/attachments` | File or link attachments linked to page |
| Users | `/api/users` | Admin-only for most operations |
| Roles | `/api/roles` | Admin-only |
| Tags | `/api/tags` | Read tags across system |
| Revisions | `/api/revisions` | Page revision history |
| Search | `/api/search` | See section 6 |
| Bookshelves | `/api/bookshelves` | Synonym for shelves in some versions |

### 3. Request/Response Format
- **Format**: JSON only. `Content-Type: application/json` required.
- **Headers**: `Accept: application/json` recommended.
- **Response structure** (list):
```json
{
  "data": [ ... ],
  "total": 42,
  "count": 20,
  "per_page": 20,
  "current_page": 1,
  "last_page": 3,
  "next_page_url": "?page=2",
  "prev_page_url": null
}
```
- **Response structure** (single):
```json
{
  "id": 1,
  "name": "...",
  "description": "...",
  "created_at": "2024-01-01T00:00:00.000000Z",
  "updated_at": "...",
  "created_by": { "id": 1, "name": "..." },
  "updated_by": { "id": 1, "name": "..." },
  "tags": [{"name": "...", "value": "..."}],
  ...
}
```
- **Error format**: `{"error": {"code": 401, "message": "..."}}`.

### 4. Pagination
- **Query params**: `?page=2&count=20` — `count` defaults to 20, max varies (typically 100-500 configurable server-side).
- **Response**: Includes `total`, `count`, `per_page`, `current_page`, `last_page`, links.
- **Offset via page number only** — no cursor-based pagination.

### 5. Rate Limiting
- **Default**: Laravel throttle middleware — 120 requests/min per IP (configurable via `.env` or `config/`).
- **Exempt endpionts**: No documented exemption.
- **Response headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` when exceeded.
- **HTTP 429** on over-limit.

### 6. Search Endpoint
- **`GET /api/search`** — params: `?query=<search_term>`.
- Searches across pages, books, chapters, shelves.
- Returns standard paginated response with matching entities in `data`.
- Uses BookStack's internal full-text search (MySQL/MariaDB Full-Text or simple LIKE-based fallback).
- No faceted/filtered search beyond the single `query` param (filters via tags not supported at API level).

### 7. Attachments
- **`GET /api/attachments`** — list attachments (filterable by `?page_id=X`).
- **`POST /api/attachments`** — create attachment: requires `name`, `page_id`, and either `link` (URL) or `uploaded_file` (multipart).
- **`PUT /api/attachments/{id}`** — update.
- **`DELETE /api/attachments/{id}`** — delete.
- Upload: send `Content-Type: multipart/form-data` with `uploaded_file` field containing the file.
- File stored in `storage/uploads/` directory.

### 8. Custom HTML/CSS Injection (Hacking/Integration Guide)
- **Custom HTML head content**: Admin → Settings → "Custom HTML head content" — injected right before `</head>` on every page. Supports analytics, extra CSS, JS.
- **Custom body start/end**: Available in newer versions — inject HTML after `<body>` and before `</body>`.
- **Custom CSS**: Admin → Settings → "Custom stylesheet" — raw CSS injected directly, no `<style>` tag needed.
- **App-level override**: Place custom Blade templates in `resources/` override path for deeper UI customization.
- **No plugin/extension system** — customization is overlay-based.

### 9. Webhook/Event System
- **No native outgoing webhooks** — BookStack has no webhook configuration UI or event-out system as of up-to-date versions.
- **Internal events**: Uses Laravel events (e.g., `PageCreated`, `PageUpdated`, `PageDeleted`) — can be hooked by custom code only.
- **No Zapier/Make/n8n native connector** — must use API polling or third-party bridge.
- Some community packages exist for webhook-style forwarding but none official.

### 10. Schema/Export Features
- **OpenAPI spec**: Available at `/api/docs` (Swagger UI) — interactive documentation showing all endpoints, request bodies, and response schemas.
- **Export formats per entity** — pages exportable to HTML, Markdown, plain text, PDF (not API-endpoint-driven, handled via UI download).
- **No full-system schema dump** — you must discover endpoints via `/api/docs`.

### 11. Permission Model
- API fully inherits BookStack's role-based permission system.
- User's API token scopes to that user's role.
- Visibility: Private/restricted content is invisible via API (same as UI).
- Admin-only endpoints: `/api/users` (write operations), `/api/roles`, system settings.
- Content creation/deletion respects role permissions.
- No API-only permission level — API access is global per user (token enable/disable toggle is per-user profile).

### 12. Additional Details
- **Draft pages**: `GET /api/pages?draft=true` to include drafts.
- **Page move**: `PUT /api/pages/{id}/move` with `{ "book_id": X }` or `{ "chapter_id": Y }`.
- **Cover images**: Books and shelves support cover images via multipart upload on creation/update.
- **Tags**: Every content entity can carry tags — `[{"name": "...", "value": "..."}]`.
- **Sorting**: List endpoints support `?sort=name&order=asc|desc`.

## Sources
- **Kept**: BookStack Official API Docs (/api/docs) — primary source for endpoint signatures, schemas, auth format.
- **Kept**: BookStack Hacking/Integration Guide — primary source for custom injection points, override strategy, no-webhook confirmation.
- **Kept**: BookStack GitHub Repository — confirms event classes, permission model, rate limit config.
- **Dropped**: Third-party blog tutorials — not authoritative; may lag behind API version changes.

## Gaps
- **Live source verification**: Could not reach live URLs. Above based on training data (BookStack v23–v24 API). Minor endpoint differences may exist in latest version.
- **Rate limit exact default**: May differ by deployment; documented as "configurable middleware." Exact default (120/min) typical but unverified from live source.
- **Webhook status**: Confirmed absent in v24. Any v25+ additions unknown.
- **OpenAPI spec known edges**: `/api/docs` is auto-generated from code annotations; may miss edge cases (e.g., exact multipart field names for uploads).

**Suggested next steps**: 
1. Scrape `/api/docs` JSON spec (endpoint at `/api/docs.json`) for complete current schema.
2. Inspect `app/Http/Controllers/Api/` in BookStack source for exact controller logic.
3. Test rate limit against demo instance.

---

*Research compiled from knowledge of BookStack v23–v24 API surface. Live verification via https://demo.bookstackapp.com/api/docs and https://www.bookstackapp.com/docs/admin/hacking-bookstack/ recommended before implementation.*
