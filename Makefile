# Makefile for running tests

# Prefer a local venv Python if present (Windows .venv), otherwise fall back to
# whatever `python` on PATH resolves to. This avoids Windows Store/python-on-PATH
# surprises while keeping the Makefile portable.
ifeq ($(shell if exist .venv\Scripts\python.exe (echo yes)),yes)
PYTHON := .venv\Scripts\python.exe
else
PYTHON ?= python
endif

# Unit tests
unit:
	.venv\Scripts\python.exe -m pytest -q tests/unit \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=xml:reports/coverage.xml \
		--cov-report=html:reports/htmlcov \
		--junitxml=reports/unit.xml

coverage-html: unit
	@echo Opening coverage report (using Python webbrowser)...
	@$(PYTHON) -c "import webbrowser,os; webbrowser.open(os.path.abspath('reports/htmlcov/index.html'))" || \
		echo "Could not open browser automatically. See reports/htmlcov/index.html"

.PHONY: init
init:
	python -m venv .venv
	.venv\Scripts\python.exe -m pip install --upgrade pip
	.venv\Scripts\python.exe -m pip install -r requirements-test.txt

# Contract tests
contract:
	.venv\Scripts\python.exe -m pytest -q tests/contract --cov=. --junitxml=reports/contract.xml