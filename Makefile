# Makefile for running tests

# Python interpreter
PYTHON ?= python

# Unit tests
unit:
	$(PYTHON) -m pytest -q tests/unit --cov=. --junitxml=reports/unit.xml