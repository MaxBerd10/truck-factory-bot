.PHONY: help lint format type test test-cov check clean

help:
	@echo "Mavjud buyruqlar:"
	@echo "  make lint       - Ruff bilan tekshirish"
	@echo "  make format     - Ruff bilan formatlash"
	@echo "  make type       - mypy bilan tekshirish"
	@echo "  make test       - Testlarni ishga tushirish"
	@echo "  make test-cov   - Coverage bilan"
	@echo "  make check      - Hammasi"
	@echo "  make clean      - Cache tozalash"

lint:
	ruff check src/

format:
	ruff format src/
	ruff check --fix src/

type:
	mypy src/

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

check: lint type test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
