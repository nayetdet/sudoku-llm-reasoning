.PHONY: db-dump db-view tests

db-dump:
	PYTHONPATH=. uv run scripts/sudoku_db_generator.py

db-view:
	PYTHONPATH=. uv run scripts/sudoku_db_reader.py

tests:
	uv run pytest
