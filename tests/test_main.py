"""Tests for CLI commands via CliRunner with mocked HTTP and config."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from bookstack_cli.main import app

runner = CliRunner()


# ------------------------------------------------------------------
# Config commands
# ------------------------------------------------------------------


class TestConfigShow:
    def test_shows_config(self, monkeypatch):
        monkeypatch.setenv("BOOKSTACK_URL", "http://test.local")
        monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "tid")
        monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "ts")

        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["url"] == "http://test.local"
        assert data["token_id"] == "tid"

    def test_error_when_no_config(self, monkeypatch):
        monkeypatch.delenv("BOOKSTACK_URL", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_ID", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_SECRET", raising=False)
        from pathlib import Path
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE",
                            Path("/nonexistent/bookstack/config.toml"))

        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert "error" in data

    def test_auth_saves_config(self, monkeypatch):
        """auth command saves to config file."""
        saved = {}

        def fake_save(url, token_id, token_secret, resolve_url=None):
            saved["url"] = url
            saved["token_id"] = token_id
            saved["token_secret"] = token_secret
            saved["resolve_url"] = resolve_url
            from pathlib import Path
            return Path("/tmp/fake")

        monkeypatch.setattr("bookstack_cli.main.save_config", fake_save)

        result = runner.invoke(
            app,
            ["auth", "--url", "http://saved.local", "--token-id", "tid_s", "--token-secret", "ts_s"],
        )
        assert result.exit_code == 0, result.stdout
        assert saved["url"] == "http://saved.local"
        assert saved["token_id"] == "tid_s"
        assert saved["resolve_url"] is None

    def test_auth_with_resolve_url(self, monkeypatch):
        """auth accepts --resolve-url."""
        saved = {}

        def fake_save(url, token_id, token_secret, resolve_url=None):
            saved.update(locals())
            from pathlib import Path
            return Path("/tmp/fake")

        monkeypatch.setattr("bookstack_cli.main.save_config", fake_save)

        result = runner.invoke(
            app,
            [
                "auth",
                "--url", "http://10.0.0.1:8080",
                "--token-id", "tid",
                "--token-secret", "ts",
                "--resolve-url", "https://wiki.public.example.com",
            ],
        )
        assert result.exit_code == 0, result.stdout
        assert saved["url"] == "http://10.0.0.1:8080"
        assert saved["resolve_url"] == "https://wiki.public.example.com"


# ------------------------------------------------------------------
# Books commands
# ------------------------------------------------------------------


class TestBooksList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_books(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=100&page=1",
            method="GET",
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "Dev Handbook",
                        "description": "",
                        "tags": [],
                        "created_at": None,
                        "updated_at": None,
                        "created_by": None,
                        "updated_by": None,
                    }
                ],
                "total": 1,
                "per_page": 100,
                "current_page": 1,
                "last_page": 1,
            },
        )

        result = runner.invoke(app, ["books", "list"])
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["name"] == "Dev Handbook"

    @pytest.mark.usefixtures("_setup_env")
    def test_list_empty(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["books", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == []


class TestBooksGet:
    @pytest.mark.usefixtures("_setup_env")
    def test_get_book(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="GET",
            json={
                "id": 1,
                "name": "Dev Handbook",
                "description": "",
                "tags": [],
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )

        result = runner.invoke(app, ["books", "get", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "Dev Handbook"


class TestBooksCreate:
    @pytest.mark.usefixtures("_setup_env")
    def test_create_book(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books",
            method="POST",
            json={
                "id": 2,
                "name": "New Book",
                "description": "A new book",
                "tags": [],
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )

        result = runner.invoke(app, ["books", "create", "New Book", "--description", "A new book"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == 2
        assert data["name"] == "New Book"


class TestBooksDelete:
    @pytest.mark.usefixtures("_setup_env")
    def test_delete_book(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="DELETE",
            status_code=204,
        )

        result = runner.invoke(app, ["books", "delete", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["id"] == 1


# ------------------------------------------------------------------
# Pages commands
# ------------------------------------------------------------------


class TestPagesList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_pages(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages?count=100&page=1",
            method="GET",
            json={
                "data": [
                    {
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
                        "created_at": None,
                        "updated_at": None,
                        "created_by": None,
                        "updated_by": None,
                    }
                ],
                "total": 1,
                "per_page": 100,
                "current_page": 1,
                "last_page": 1,
            },
        )

        result = runner.invoke(app, ["pages", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["name"] == "Getting Started"


class TestPagesCreate:
    @pytest.mark.usefixtures("_setup_env")
    def test_create_page(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages",
            method="POST",
            json={
                "id": 42,
                "book_id": 1,
                "chapter_id": None,
                "name": "My Page",
                "slug": "my-page",
                "html": "",
                "markdown": "# Hello",
                "draft": False,
                "tags": [],
                "priority": 1,
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )

        result = runner.invoke(
            app,
            ["pages", "create", "My Page", "--book-id", "1", "--markdown", "# Hello"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "My Page"
        assert data["markdown"] == "# Hello"


class TestPagesDelete:
    @pytest.mark.usefixtures("_setup_env")
    def test_delete_page(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/42",
            method="DELETE",
            status_code=204,
        )

        result = runner.invoke(app, ["pages", "delete", "42"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True


# ------------------------------------------------------------------
# Shelves commands
# ------------------------------------------------------------------


class TestShelvesList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_shelves(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["shelves", "list"])
        assert result.exit_code == 0
        assert json.loads(result.stdout) == []


# ------------------------------------------------------------------
# Chapters commands
# ------------------------------------------------------------------


class TestChaptersList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_chapters(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/chapters?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["chapters", "list"])
        assert result.exit_code == 0
        assert json.loads(result.stdout) == []


# ------------------------------------------------------------------
# Search commands
# ------------------------------------------------------------------


class TestAttachmentsCreateLink:
    @pytest.mark.usefixtures("_setup_env")
    def test_create_link(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments",
            method="POST",
            json={
                "id": 1,
                "name": "Reference",
                "page_id": 42,
                "link": "https://example.com/doc",
                "file_path": None,
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )
        result = runner.invoke(
            app,
            [
                "attachments", "create-link",
                "--name", "Reference",
                "--page-id", "42",
                "--link", "https://example.com/doc",
            ],
        )
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert data["id"] == 1
        assert data["link"] == "https://example.com/doc"


class TestAttachmentsDelete:
    @pytest.mark.usefixtures("_setup_env")
    def test_delete_attachment(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments/1",
            method="DELETE",
            status_code=204,
        )
        result = runner.invoke(app, ["attachments", "delete", "1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True


class TestSearch:
    @pytest.mark.usefixtures("_setup_env")
    def test_search(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/search?count=100&page=1&query=hello",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["search", "query", "hello"])
        assert result.exit_code == 0
        assert json.loads(result.stdout) == []


# ------------------------------------------------------------------
# Other list commands
# ------------------------------------------------------------------


class TestUsersList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_users(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/users?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["users", "list"])
        assert result.exit_code == 0
        assert json.loads(result.stdout) == []


class TestRolesList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_roles(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/roles?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["roles", "list"])
        assert result.exit_code == 0
        assert json.loads(result.stdout) == []


class TestAttachmentsList:
    @pytest.mark.usefixtures("_setup_env")
    def test_list_attachments(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/attachments?count=100&page=1",
            method="GET",
            json={"data": [], "total": 0, "per_page": 100, "current_page": 1, "last_page": 1},
        )

        result = runner.invoke(app, ["attachments", "list"])
        assert result.exit_code == 0
        assert json.loads(result.stdout) == []


# ------------------------------------------------------------------
# Config test
# ------------------------------------------------------------------


class TestConfigTest:
    @pytest.mark.usefixtures("_setup_env")
    def test_test_connection_ok(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books?count=1",
            method="GET",
            json={"data": [], "total": 42, "per_page": 1},
        )
        result = runner.invoke(app, ["test"])
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["total_books"] == 42

    def test_test_connection_fails_no_config(self, monkeypatch):
        monkeypatch.delenv("BOOKSTACK_URL", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_ID", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_SECRET", raising=False)
        from pathlib import Path
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", Path("/nonexistent/otherx/config.toml"))

        result = runner.invoke(app, ["test"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["ok"] is False


# ------------------------------------------------------------------
# Update commands
# ------------------------------------------------------------------


class TestBooksUpdate:
    @pytest.mark.usefixtures("_setup_env")
    def test_update_book(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/books/1",
            method="PUT",
            json={
                "id": 1,
                "name": "Renamed Book",
                "description": "Updated desc",
                "tags": [],
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )
        result = runner.invoke(app, ["books", "update", "1", "Renamed Book", "--description", "Updated desc"])
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert data["name"] == "Renamed Book"
        assert data["description"] == "Updated desc"


class TestShelvesUpdate:
    @pytest.mark.usefixtures("_setup_env")
    def test_update_shelf(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves/1",
            method="PUT",
            json={
                "id": 1,
                "name": "Renamed Shelf",
                "description": "",
                "tags": [],
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )
        result = runner.invoke(app, ["shelves", "update", "1", "Renamed Shelf"])
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert data["name"] == "Renamed Shelf"


class TestChaptersUpdate:
    @pytest.mark.usefixtures("_setup_env")
    def test_update_chapter(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/chapters/1",
            method="PUT",
            json={
                "id": 1,
                "book_id": 5,
                "name": "Renamed Chapter",
                "description": "",
                "tags": [],
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )
        result = runner.invoke(
            app,
            ["chapters", "update", "1", "Renamed Chapter", "--book-id", "5"],
        )
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert data["name"] == "Renamed Chapter"


class TestShelvesUpdateBooks:
    @pytest.mark.usefixtures("_setup_env")
    def test_update_shelf_with_books(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/shelves/1",
            method="PUT",
            json={
                "id": 1,
                "name": "Shelf",
                "description": "",
                "tags": [],
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )
        result = runner.invoke(
            app,
            ["shelves", "update", "1", "Shelf", "--books", "10,20,30"],
        )
        assert result.exit_code == 0, result.stdout


class TestPagesUpdate:
    @pytest.mark.usefixtures("_setup_env")
    def test_update_page_name(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/1",
            method="PUT",
            json={
                "id": 1,
                "book_id": 1,
                "chapter_id": None,
                "name": "Renamed Page",
                "slug": "renamed-page",
                "html": "",
                "markdown": "",
                "draft": False,
                "tags": [],
                "priority": 0,
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
            },
        )
        result = runner.invoke(app, ["pages", "update", "1", "--name", "Renamed Page"])
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert data["name"] == "Renamed Page"

    @pytest.mark.usefixtures("_setup_env")
    def test_update_page_append(self, httpx_mock):
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/1",
            method="GET",
            json={
                "id": 1, "book_id": 1, "name": "Test", "slug": "test",
                "markdown": "Existing content",
                "html": "", "draft": False, "tags": [], "priority": 0,
                "created_at": None, "updated_at": None,
                "created_by": None, "updated_by": None,
            },
        )
        httpx_mock.add_response(
            url="http://test.bookstack.local/api/pages/1",
            method="PUT",
            json={
                "id": 1, "book_id": 1, "name": "Test", "slug": "test",
                "markdown": "Existing content\n\nAppended text",
                "html": "", "draft": False, "tags": [], "priority": 0,
                "created_at": None, "updated_at": None,
                "created_by": None, "updated_by": None,
            },
        )
        result = runner.invoke(app, ["pages", "update", "1", "--append", "Appended text"])
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert "Appended text" in data["markdown"]

    @pytest.mark.usefixtures("_setup_env")
    def test_update_page_no_fields_errors(self, httpx_mock):
        result = runner.invoke(app, ["pages", "update", "1"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert "error" in data


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def _setup_env(monkeypatch):
    """Set env vars so CLI can create a BookStackClient."""
    monkeypatch.setenv("BOOKSTACK_URL", "http://test.bookstack.local")
    monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "cli-test-token-id")
    monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "cli-test-token-secret")
