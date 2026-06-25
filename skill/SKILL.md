---
name: bookstack-cli
description: CLI for coding agents to read, write, search, and manage content in a BookStack wiki via its REST API. Covers shelves, books, chapters, pages, attachments, search, users, and roles.
---

# bookstack-cli

Command-line interface to interact with a [BookStack](https://www.bookstackapp.com/) wiki instance. All output is JSON for easy consumption by coding agents.

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
cd /home/michael/Projekte/itop/bookstack-cli
uv sync
```

### Configuration

Interactive setup (recommended):

```bash
bookstack auth
```

Prompts for URL, token ID, and secret. If the public web URL differs from the
API URL (e.g. behind an OAuth reverse proxy), provide `--resolve-url`:

```bash
bookstack auth --resolve-url https://wiki.public.example.com
```

Saves to `~/.config/bookstack-cli/config.toml`:

```toml
[connection]
url = "http://10.0.0.1:8080"              # API endpoint (internal)
resolve_url = "https://wiki.public.example.com"  # public web URL
```

Or set env vars (override config file):

```bash
export BOOKSTACK_URL=http://10.0.0.1:8080
export BOOKSTACK_RESOLVE_URL=https://wiki.example.com
export BOOKSTACK_TOKEN_ID=<token-id>
export BOOKSTACK_TOKEN_SECRET=<token-secret>
```

## Commands

### Config

| Command | Description |
|---------|-------------|
| `bookstack auth` | Save credentials to `~/.config/bookstack-cli/config.toml` |
| `bookstack config show` | Show current connection config |
| `bookstack test` | Test connection to configured instance |

### Contents

| Command | Description |
|---------|-------------|
| `bookstack shelves list` | List all shelves |
| `bookstack shelves get <id>` | Get shelf by ID |
| `bookstack shelves create <name>` | Create shelf (`--tags`, `--books`) |
| `bookstack shelves update <id> <name>` | Update shelf (`--tags`, `--books`) |
| `bookstack shelves upload-cover <id> --file <path>` | Upload cover image |
| `bookstack shelves delete <id>` | Delete shelf |
| `bookstack books list` | List all books |
| `bookstack books get <id>` | Get book by ID |
| `bookstack books create <name>` | Create book (`--tags`) |
| `bookstack books update <id> <name>` | Update book (`--tags`) |
| `bookstack books upload-cover <id> --file <path>` | Upload cover image |
| `bookstack books delete <id>` | Delete book |
| `bookstack chapters list` | List chapters |
| `bookstack chapters get <id>` | Get chapter by ID |
| `bookstack chapters create <name>` | Create chapter (`--book-id`, `--tags`) |
| `bookstack chapters update <id> <name>` | Update chapter (`--book-id`, `--tags`) |
| `bookstack chapters delete <id>` | Delete chapter |
| `bookstack pages list` | List pages (`--drafts`, `--book-id`) |
| `bookstack pages get <id>` | Get page by ID |
| `bookstack pages update <id>` | Update page (partial: `--name`, `--markdown`, `--html`, `--tags`, `--markdown-file`, `--append`, `--append-file`, pipe stdin) |
| `bookstack pages resolve-url <url>` | Resolve web URL to page |
| `bookstack pages create <name>` | Create page (`--book-id`, `--markdown`, `--markdown-file`, or pipe stdin) |
| `bookstack pages delete <id>` | Delete page |
| `bookstack pages import` | Import markdown file with image handling (`--file`, `--book-id`, `--page-id`) |
| `bookstack attachments list` | List attachments (`--page-id`) |
| `bookstack attachments get <id>` | Get attachment by ID |
| `bookstack attachments create-link` | Create link attachment (`--name`, `--page-id`, `--link`) |
| `bookstack attachments upload` | Upload file attachment (`--name`, `--page-id`, `--file`) |
| `bookstack attachments delete <id>` | Delete attachment |
| `bookstack users list` | List users (admin) |
| `bookstack users get <id>` | Get user by ID |
| `bookstack roles list` | List roles (admin) |
| `bookstack search query <term>` | Search across all content |
| `bookstack test` | Test connection to configured BookStack instance |

### Common Options

- `--help` on any command shows usage
- `--sort` and `--order` on `books list` (e.g. `--sort name --order asc`)

### Output Format

All responses are JSON printed to stdout. Single entities are JSON objects, lists are JSON arrays. Errors include `{"error": {"code": <status>, "message": "..."}}`.

## Examples for Coding Agents

```bash
# Read a page by web URL (resolves slug → ID)
bookstack pages resolve-url "https://csiwiki.optimal-systems.org/books/test-perm/page/test-perm"

# Read a specific page by ID
bookstack pages get 42

# Create a new page in book 1
bookstack pages create "API Overview" --book-id 1 --markdown "# API Overview\n\nThis page covers..."

# Search for relevant content
bookstack search query "authentication tokens"

# List books for context
bookstack books list | jq '[.[] | {id, name}]'

# Get book contents
bookstack books get 1 | jq '{name, description, tags}'

# Create a shelf with books
bookstack shelves create "Technical Docs" --description "Engineering documentation"

# List all pages in a book
bookstack pages list --book-id 1 | jq '.[] | {id, name, draft}'
```

### Import Markdown with Images

Scenario: Import a markdown file containing local image references into BookStack.
The tool uploads images as attachments and replaces local paths with attachment URLs.

```bash
# Import a markdown file (creates new page)
bookstack pages import --file docs/sauna-article.md --book-id 2072 --name "Sauna Article"

# Import and update an existing page
bookstack pages import --file docs/updated-content.md --page-id 2144

# Import with explicit name (default: filename without extension)
bookstack pages import --file readme.md --book-id 1 --name "Project README"
```

The import command:
1. Scans markdown for `![](local-path)` references
2. Uploads each local file as a page attachment
3. Replaces local paths with attachment URLs (`/attachments/{id}`)
4. BookStack serves attachment files as raw images to authenticated web sessions,
   so images render inline in the page viewer
5. Creates or updates the page

**Note:** Attachment URLs work inline for web UI users (session auth).
API tokens get 401 on the same endpoint — that's expected.

### Appending Content

```bash
# Append text to an existing page
bookstack pages update 42 --append "\n\n## New Section\n\nContent here."

# Append from file
bookstack pages update 42 --append-file new-section.md
```

### Connection Test

```bash
bookstack test
# → {"ok": true, "url": "...", "token_id": "...", "total_books": 42}
```

### End-to-End: Finnish Sauna Article

Scenario: Insert a long Finnish-language text about sauna operation into an existing page
at a known web URL. Uses `--markdown-file` for multi-line content.

```bash
# 1. Save content to a file (avoids shell escaping issues)
cat > /tmp/sauna.md << 'EOF'
# Saunan toiminta

## Johdanto

Sauna on suomalainen perinne, joka ulottuu tuhansien vuosien taakse.
Suomessa on noin 3,3 miljoonaa saunaa.

## L\u00f6yly

L\u00f6yly on saunan sielu. Heit\u00e4 vett\u00e4 kiukaan kiville annoksissa.

> *"Jos et saunassa k\u00e4y, et ole kunnon ihminen."*
EOF

# 2. Resolve the web URL to a page ID
bookstack pages resolve-url "https://wiki/books/test-perm/page/test"

# 3. Update the page with file content
bookstack pages create "Test" --book-id 2072 --markdown-file /tmp/sauna.md

# 4. Verify
bookstack pages resolve-url "https://wiki/books/test-perm/page/test" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['name']); print(d['markdown'][:200])"
```

Multi-line content can also be piped:

```bash
cat /tmp/sauna.md | bookstack pages create "Piped Content" --book-id 1
```

## Architecture

The CLI wraps BookStack's REST API (`/api/*`). Key behaviors:

- **Auth**: Token-based (`Authorization: Token <id>:<secret>`)
- **Pagination**: Auto-iterates all pages, returns complete list
- **Rate limits**: Automatic retry with exponential backoff (up to 5 retries on 429)
- **Errors**: Typed exceptions map to HTTP status codes (401→Auth, 404→NotFound, 429→RateLimit, 5xx→Server)

### Web URLs vs API URLs

BookStack web URLs differ from API resource identifiers. The web URL uses human-readable slugs while the API uses numeric IDs:

| Entity | Web URL | API URL |
|--------|---------|---------|
| Page | `/books/{book-slug}/page/{page-slug}` | `GET /api/pages/{id}` |
| Book | `/books/{book-slug}` | `GET /api/books/{id}` |
| Shelf | `/shelves/{shelf-slug}` | `GET /api/shelves/{id}` |
| Chapter | `/books/{book-slug}/chapter/{chapter-slug}` | `GET /api/chapters/{id}` |

Use **`pages resolve-url <web-url>`** to convert a web URL to an API-addressable page. The tool reads the configured BookStack URL from `~/.config/bookstack-cli/config.toml` to parse the path and extract the page slug. Works even when the public domain differs from the internal API URL.

## Reference

Detailed docs at `docs/`:

| File | Content |
|------|---------|
| [docs/overview.md](docs/overview.md) | Architecture and scope |
| [docs/authentication.md](docs/authentication.md) | Token setup and security |
| [docs/api-reference.md](docs/api-reference.md) | All endpoints and schemas |
| [docs/integration-guide.md](docs/integration-guide.md) | BookStack hacking guide |
