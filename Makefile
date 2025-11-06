.PHONY: install api api-migrations api-tests webui

install:
	uv sync --all-groups --all-packages

api:
	cd packages/api && uv run uvicorn src.api.main:app --log-config log-config.json --reload

api-migrations:
	cd packages/api && uv run alembic upgrade head

api-tests:
	cd packages/api && uv run pytest

webui:
	cd packages/webui && uv run streamlit run src/webui/main.py
