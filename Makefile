UV := uv
PYTEST := $(UV) run pytest
RUFF := $(UV) run ruff
PYTHON := $(UV) run python

SKILL_DIR := $(PWD)/skill
PI_SKILLS := $(HOME)/.pi/agent/skills
CLAUDE_SKILLS := $(HOME)/.claude/skills

.PHONY: init install test test-watch lint format clean run

init:
	@echo "==> Installing dependencies via uv"
	$(UV) sync

install: init
	@echo "==> Installing CLI via uv tool install"
	$(UV) tool install --force .
	@echo "==> Linking skill to pi global skills"
	mkdir -p $(PI_SKILLS)
	ln -sfn $(SKILL_DIR) $(PI_SKILLS)/bookstack-cli
	@echo "==> Linking skill to Claude Code global skills (non-standard)"
	mkdir -p $(CLAUDE_SKILLS)
	ln -sfn $(PI_SKILLS)/bookstack-cli $(CLAUDE_SKILLS)/bookstack-cli
	@echo "==> Done. bookstack-cli installed globally."

test:
	@echo "==> Running tests"
	$(PYTEST) -v

test-watch:
	@echo "==> Running tests in watch mode (Ctrl+C to stop)"
	@while true; do \
		clear; \
		$(PYTEST) -v 2>&1; \
		echo; \
		echo "--- Watching for changes (polling every 2s) ---"; \
		sleep 2; \
	done

lint:
	@echo "==> Linting with ruff"
	$(RUFF) check .

format:
	@echo "==> Formatting with ruff"
	$(RUFF) format .

clean:
	@echo "==> Cleaning cache and build artifacts"
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.py[co]' -delete 2>/dev/null || true

run:
	@echo "==> Running bookstack CLI"
	$(UV) run bookstack $(ARGS)
