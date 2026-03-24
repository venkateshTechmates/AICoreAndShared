.PHONY: install install-dev lint fmt typecheck test test-fast test-cov clean build

# ── Install ──────────────────────────────────────────────────────────────────
install:
	pip install -e ".[core]"

install-dev:
	pip install -e ".[all]"
	pip install pytest pytest-asyncio pytest-cov ruff mypy

# ── Code Quality ─────────────────────────────────────────────────────────────
lint:
	ruff check . --fix

fmt:
	ruff format .

typecheck:
	mypy ai_core ai_shared --ignore-missing-imports

check: lint typecheck  ## Run lint + typecheck together

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-fast:
	pytest tests/ -x -q

test-cov:
	pytest tests/ --cov=ai_core --cov=ai_shared --cov-report=term-missing --cov-report=html

# ── Examples ─────────────────────────────────────────────────────────────────
example-rag:
	python examples/01_basic_rag.py

example-agents:
	python examples/02_agent_system.py

example-compliance:
	python examples/03_compliance_governance.py

example-cost:
	python examples/04_cost_optimization.py

example-cache:
	python examples/05_caching_resilience.py

example-full:
	python examples/06_full_enterprise_pipeline.py

# ── Build / Package ──────────────────────────────────────────────────────────
build:
	python -m build

# ── Cleanup ──────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  install         Install core package"
	@echo "  install-dev     Install all extras + dev tools"
	@echo "  lint            Run ruff with auto-fix"
	@echo "  fmt             Run ruff formatter"
	@echo "  typecheck       Run mypy strict"
	@echo "  check           lint + typecheck"
	@echo "  test            Run full test suite"
	@echo "  test-fast       Stop on first failure"
	@echo "  test-cov        Run with coverage report"
	@echo "  example-rag     Run RAG pipeline example"
	@echo "  example-agents  Run agent system example"
	@echo "  example-full    Run full enterprise pipeline"
	@echo "  build           Build distribution packages"
	@echo "  clean           Remove all build artifacts"
	@echo ""
