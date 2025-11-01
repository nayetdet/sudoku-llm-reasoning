.PHONY: sync dump view tests

sync:
	uv sync --all-groups

dump:
	PYTHONPATH=. uv run scripts/sudoku_db_generator.py

view:
	PYTHONPATH=. uv run scripts/sudoku_db_reader.py

tests:
	uv run pytest
