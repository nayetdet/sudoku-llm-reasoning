.PHONY: sync db-dump db-view tests

sync:
	uv sync --all-groups

db-dump:
	PYTHONPATH=. uv run scripts/sudoku_db_generator.py

db-view:
	PYTHONPATH=. uv run scripts/sudoku_db_reader.py

tests:
	uv run pytest
