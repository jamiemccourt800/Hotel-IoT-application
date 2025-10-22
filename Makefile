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
	$(PYTHON) -m pytest -q tests/unit --cov=. --junitxml=reports/unit.xml

.PHONY: init
init:
	python -m venv .venv
	.venv\Scripts\python.exe -m pip install --upgrade pip
	.venv\Scripts\python.exe -m pip install -r requirements-test.txt