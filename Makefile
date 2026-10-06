.PHONY: test format check

test:
	uv run python -m pytest -q

format:
	uv run isort src tests
	uv run black src tests

check: format test

run:
	uv run python -m streamlit run src/app.py