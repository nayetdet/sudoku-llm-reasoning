.PHONY: install api api-migrations api-view api-tests webui

install:
	uv sync --all-groups --all-packages

api:
	uv run --package api uvicorn packages.api.src.api.main:app --log-config packages/api/log-config.json --reload

api-migrations:
	uv run --package api alembic upgrade head

api-view:
	uv run --package api packages/api/scripts/sudoku_db_reader.py

api-tests:
	uv run --package api pytest

webui:
	cd packages/webui && uv run streamlit run src/webui/main.py
