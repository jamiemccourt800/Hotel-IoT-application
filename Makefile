# Makefile for running tests

# Cross-platform Python detection
# Detects OS and sets appropriate paths for Windows vs Linux/Mac
ifeq ($(OS),Windows_NT)
	# Windows paths
	PYTHON := .venv\Scripts\python.exe
	PIP := .venv\Scripts\pip.exe
	VENV_CREATE := python -m venv .venv
	VENV_ACTIVATE := .venv\Scripts\activate
	FRONTEND_DIR := central\frontend
else
	# Linux/Mac paths
	PYTHON := .venv/bin/python
	PIP := .venv/bin/pip
	VENV_CREATE := python3 -m venv .venv
	VENV_ACTIVATE := source .venv/bin/activate
	FRONTEND_DIR := central/frontend
endif

# Fallback if venv doesn't exist
ifeq (,$(wildcard $(PYTHON)))
	PYTHON := python
endif

# Unit tests
unit:
	$(PYTHON) -m pytest -q tests/unit --cov=. --cov-report=term-missing --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov --junitxml=reports/unit.xml

# Contract tests
contract:
	$(PYTHON) -m pytest -q tests/contract --cov=. --junitxml=reports/contract.xml

# Frontend tests (React/Jest)
frontend-test:
	@echo "NOTE: This requires Node.js and npm to be installed and in your PATH"
	@echo "If you see 'npm not found' error, please install Node.js or run manually:"
	@echo "  cd $(FRONTEND_DIR) && npx react-scripts test --watchAll=false"
	@where npm >nul 2>&1 || (echo ERROR: npm not found in PATH. Please install Node.js. && exit 1)
	cd $(FRONTEND_DIR) && npx react-scripts test --watchAll=false

# Frontend tests with coverage
frontend-test-coverage:
	@echo "NOTE: This requires Node.js and npm to be installed and in your PATH"
	@where npm >nul 2>&1 || (echo ERROR: npm not found in PATH. Please install Node.js. && exit 1)
	cd $(FRONTEND_DIR) && npx react-scripts test --watchAll=false --coverage --coverageReporters=text --coverageReporters=lcov

# Integration tests
integration:
	$(PYTHON) -m pytest -s tests/integration --cov=. --junitxml=reports/integration.xml

# E2E tests
e2e:
	$(PYTHON) -m pytest -s tests/e2e --cov=. --junitxml=reports/e2e.xml

# Run all test types together (unit, contract, integration)
all-tests:
	$(PYTHON) -m pytest -q tests/unit tests/contract tests/integration --cov=. --cov-report=term-missing --cov-report=xml:reports/coverage.xml --junitxml=reports/all.xml

# Run all test types together and generate HTML coverage report
all-tests-coverage-html:
	$(PYTHON) -m pytest -q tests/unit tests/contract tests/integration --cov=. --cov-report=term-missing --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov --junitxml=reports/all.xml
	@echo Opening coverage report (using Python webbrowser)...
	@$(PYTHON) -c "import webbrowser,os; webbrowser.open(os.path.abspath('reports/htmlcov/index.html'))" || \
		echo "Could not open browser automatically. See reports/htmlcov/index.html"

# Run all tests including frontend
all-tests-with-frontend:
	@echo "Running Python tests..."
	$(PYTHON) -m pytest -q tests/unit tests/contract tests/integration --cov=. --cov-report=term-missing --cov-report=xml:reports/coverage.xml --junitxml=reports/all.xml
	@echo "Running Frontend tests..."
	cd $(FRONTEND_DIR) && npx react-scripts test --watchAll=false

.PHONY: init unit contract integration e2e frontend-test frontend-test-coverage all-tests all-tests-coverage-html all-tests-with-frontend

# Environment setup
init:
	$(VENV_CREATE)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-test.txt