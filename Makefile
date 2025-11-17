.PHONY: install api api-migrations api-view api-image-view api-tests webui

install:
	uv sync --all-groups --all-packages

api:
	cd packages/api && uv run uvicorn src.api.main:app --log-config log-config.json --reload

api-migrations:
	cd packages/api && uv run alembic upgrade head

api-view:
	cd packages/api && uv run scripts/sudoku_viewer.py

api-image-view:
	cd packages/api && uv run scripts/sudoku_image_viewer.py

api-tests:
	cd packages/api && uv run pytest

webui:
	cd packages/webui && uv run streamlit run src/webui/main.py
