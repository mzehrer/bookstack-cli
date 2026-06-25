# bookstack-cli

[![Python](https://img.shields.io/badge/python-≥3.14-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()

CLI for coding agents to interact with a [BookStack](https://www.bookstackapp.com/) wiki via its REST API. All output is JSON — built for LLM pipelines, not humans.

```bash
bookstack books list | jq '. | length'
bookstack pages get 42 | jq '.html[:200]'
bookstack search query "api docs" | jq '.[] | {name, type, score}'
bookstack test
```

## Install

```bash
# One-liner (no clone needed)
uv tool install git+https://git.optimal-systems.org/michael/bookstack-cli.git

# Or clone for development
cd bookstack-cli
make init          # or: uv sync
```

## Setup

```bash
bookstack auth           # interactive — prompts for URL, token, secret

# If public web URL differs from API (e.g. behind OAuth proxy):
bookstack auth --resolve-url https://wiki.public.example.com
```

### Config File

Saved to `~/.config/bookstack-cli/config.toml`:

```toml
[connection]
url = "http://10.0.0.1:8080"                    # API endpoint (internal)
resolve_url = "https://wiki.public.example.com"  # public web URL (optional)
token_id = "ltA4dR2k6QhGxY1z"
token_secret = "AbCdeFgHiJkLmNoPqRsTuVwXyZ0123456789"
```

`resolve_url` is optional — defaults to `url` if not set.

### Env Vars (override file)

```bash
export BOOKSTACK_URL=http://10.0.0.1:8080
export BOOKSTACK_RESOLVE_URL=https://wiki.example.com
export BOOKSTACK_TOKEN_ID=ltA4dR2k6QhGxY1z
export BOOKSTACK_TOKEN_SECRET=AbCdeFgHiJkLmNoPqRsTuVwXyZ0123456789
```

Precedence: env vars > config file > error.

[See auth docs →](docs/authentication.md)

## Usage

```
$ bookstack --help

╭─ Commands ───────────────────────────────────────╮
│ auth         Save connection credentials.         │
│ config       Manage connection config.            │
│ test         Test connection to BookStack.        │
│ shelves      Manage bookshelves.                  │
│ books        Manage books.                        │
│ chapters     Manage chapters.                     │
│ pages        Manage pages.                        │
│ attachments  Manage attachments.                  │
│ users        Manage users (admin).                │
│ roles        Manage roles (admin).                │
│ search       Search content.                      │
╰───────────────────────────────────────────────────╯
```

### Common Workflows

```bash
# Test connection
bookstack test

# List all books
bookstack books list

# Get a specific page
bookstack pages get 42

# Create a page from file
bookstack pages create "My Page" --book-id 1 --markdown-file content.md

# Pipe multi-line content
cat content.md | bookstack pages create "Piped Page" --book-id 1

# Append text to existing page
bookstack pages update 42 --append "New section at the end"

# Resolve web URL to page
bookstack pages resolve-url "https://wiki/books/my-book/page/my-page"

# Import markdown with images
bookstack pages import --file article.md --book-id 1 --name "Article"

# Search across all content
bookstack search query "installation guide"

# List attachments on a page
bookstack attachments list --page-id 10

# Upload a file attachment
bookstack attachments upload --name "Report" --page-id 42 --file report.pdf

# Create a shelf and assign books
bookstack shelves create "Dev Docs"
bookstack shelves update 1 "Dev Docs" --books "10,20,30"

# Update entity
bookstack books update 1 "New Title"
```

## Features

| Feature | Status |
|---|---|
| Shelves CRUD (+ book assignment) | ✅ |
| Books CRUD | ✅ |
| Chapters CRUD | ✅ |
| Pages CRUD (partial update, append, move) | ✅ |
| Markdown import with image handling | ✅ |
| Web URL → API ID resolution | ✅ |
| Attachments (link + file upload) | ✅ |
| Search across content | ✅ |
| Users/Roles (admin) | ✅ |
| Async HTTP with retry/backoff | ✅ |
| Auto-pagination (client-side filtering) | ✅ |
| Config test / connection check | ✅ |
| JSON-only output | ✅ |

## Project Layout

```
bookstack-cli/
├── bookstack_cli/
│   ├── client.py        # HTTP client, auth, rate-limit, pagination
│   ├── config.py        # Env vars → ~/.config/bookstack-cli/config.toml
│   ├── exceptions.py    # Typed error hierarchy
│   ├── models.py        # Pydantic models for all entities
│   ├── main.py          # Typer CLI entry point
│   └── resources/       # One module per entity
│       ├── books.py
│       ├── chapters.py
│       ├── pages.py
│       ├── shelves.py
│       ├── attachments.py
│       ├── search.py
│       ├── users.py
│       ├── roles.py
│       ├── revisions.py
│       └── tags.py
├── tests/               # 130+ tests
├── docs/                # Detailed docs
├── skill/               # Pi agent skill
├── Makefile             # init/test/lint/format/run
└── pyproject.toml
```

## Documentation

| File | What |
|---|---|
| [docs/overview.md](docs/overview.md) | Architecture, goals, scope |
| [docs/authentication.md](docs/authentication.md) | Token setup, env config, security |
| [docs/api-reference.md](docs/api-reference.md) | All endpoints, schemas, pagination |
| [docs/integration-guide.md](docs/integration-guide.md) | Hacking BookStack, injections, webhooks |
| [docs/research.md](docs/research.md) | Raw API research findings |
| [skill/SKILL.md](skill/SKILL.md) | Agent skill for pi/coding agents |
| [AGENT.md](AGENT.md) | TDD protocol for this project |

## Design

- **Async from day one** — `httpx.AsyncClient` with retry + exponential backoff on 429s
- **Pydantic v2** — typed models for every entity, validated responses
- **Agent-friendly output** — everything is JSON via stdout, no interactive prompts
- **Resource-per-file** — one module per entity, consistent `list/get/create/update/delete` signatures
- **Config cascade** — env vars > `~/.config/bookstack-cli/config.toml` > error
- **TDD** — 130 tests, red/green/refactor cycle (see [AGENT.md](AGENT.md))

## License

MIT
