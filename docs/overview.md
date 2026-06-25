# Overview

bookstack-cli enables LLM-based coding agents to read, write, search, and manage
content in a [BookStack](https://www.bookstackapp.com/) wiki instance.

## Goals

- Agent-friendly CLI: stdin/stdout JSON pipelines, no interactive prompts
- Full CRUD coverage over all BookStack API entities
- Secure token management via env/config file
- Pagination iteration helpers
- Search integration for RAG-style context retrieval

## Scope

| Feature | Status |
|---|---|
| Shelves CRUD | planned |
| Books CRUD | planned |
| Chapters CRUD | planned |
| Pages CRUD (incl. drafts, move) | planned |
| Attachments (file + link) | planned |
| Search across content | planned |
| User/Role management | planned |
| Tag filtering | planned |
| Rate-limit aware retry | planned |

## Architecture

```
┌──────────────┐     stdin/args      ┌──────────────────┐
│  Coding Agent │ ──────────────────→ │  bookstack-cli    │
│  (Claude, etc) │ ←──────────────── │  (Python CLI)     │
└──────────────┘     JSON stdout     └────────┬─────────┘
                                              │ HTTP (JSON)
                                              ↓
                                      ┌──────────────────┐
                                      │  BookStack API    │
                                      │  /api/*           │
                                      └──────────────────┘
```

All communication with BookStack is via its REST API. Responses are printed
as structured JSON for easy consumption by agents.

## Project Layout

```
bookstack-cli/
├── main.py              # Entry point
├── pyproject.toml       # Project config, deps
├── docs/                # Documentation
├── research.md          # API research notes
├── bookstack_cli/       # Package source
│   ├── __init__.py
│   ├── client.py        # HTTP client, auth, rate-limit
│   ├── models.py        # Pydantic models for entities
│   └── commands/        # Subcommand modules
│       ├── shelves.py
│       ├── books.py
│       ├── chapters.py
│       ├── pages.py
│       ├── attachments.py
│       ├── search.py
│       ├── users.py
│       └── roles.py
└── tests/               # Test suite
    ├── test_client.py
    ├── test_*.py
    └── fixtures/
```
