# Agent Protocol

## TDD: Red / Green / Refactor

All development follows strict red/green TDD cycle.

### Cycle

1. **Red** — Write a failing test first. Run it. It must fail.
2. **Green** — Write minimal production code to pass the test.
3. **Refactor** — Clean up both test and production code.

### Rules

- No production code without a failing test for the specific change.
- Run full test suite before marking any task complete.
- If stuck in red, ask user for guidance — do not skip to green.
- Commit after each green phase (if git history matters).

### Running Tests

```bash
uv run pytest -v           # full suite (130+ tests)
uv run pytest -q           # quick summary
uv run pytest -x           # stop on first failure
uv run pytest -k "test_"   # filter by name
uv run pytest --cov        # coverage report
uv run pytest --tb=short   # shorter tracebacks
```

### Test Structure

| File | Coverage |
|---|---|
| `tests/test_client.py` | Auth header, retry, error mapping, CRUD, pagination, context manager |
| `tests/test_config.py` | Env var loading, TOML loading, config cascade, save/escape |
| `tests/test_models.py` | Pydantic parsing (all entities), UserRef coercion, page update partials |
| `tests/test_resources.py` | Every CRUD operation for all 10 resource modules |
| `tests/test_main.py` | All CLI commands via CliRunner with mocked HTTP |

### Test Style

- One assert per test preferred.
- Descriptive test names: `test_<unit>_<scenario>_<expected>`.
- Fixtures in `tests/conftest.py` for shared mock data and sample API responses.
- Mock HTTP via `pytest-httpx` (httpx_mock fixture).
- Mock env vars via `monkeypatch`.
- Mock config file path via `monkeypatch.setattr`.
- No network calls in test suite — all HTTP is mocked.

### Client Testability

- `BookStackClient` accepts explicit `base_url`, `token_id`, `token_secret` to bypass config loading.
- Context manager supports both sync (`with`) and async (`async with`) usage.

### Common Fixtures

| Fixture | Purpose |
|---|---|
| `client` | BookStackClient with test creds |
| `_setup_env` | Sets BOOKSTACK_URL / TOKEN_ID / TOKEN_SECRET env vars |
| `sample_book_dict` etc. | Sample API response dicts for model tests |

### Key Gotchas

- BookStack API returns `per_page: null` on list endpoints — paginator uses `len(items)` fallback.
- BookStack API returns `created_by`/`updated_by` as plain int IDs on list endpoints — `UserRef` BeforeValidator handles coercion.
- BookStack API returns `uploaded_to` instead of `page_id` on attachment responses — Field alias handles this.
- CLI `--markdown` flag can't handle newlines — use `--markdown-file` or pipe stdin for multi-line content.
- BookStack serves `/attachments/{id}` as raw image files to web session users, but returns 401 for API token requests on the same URL.
