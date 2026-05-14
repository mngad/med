.PHONY: run lint format clean build

# ── Development ──────────────────────────────────────────────────────────────

run:
	python -m markdown_editor

# ── Linting & formatting ─────────────────────────────────────────────────────

lint:
	ruff check src/

format:
	ruff format src/
	ruff check --fix src/

# ── Packaging ────────────────────────────────────────────────────────────────

build:
	pyinstaller markdown-editor.spec

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
