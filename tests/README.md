# Testing Infrastructure

This directory contains the comprehensive test suite for the DevOps Group Project, covering unit, integration, contract, and end-to-end (E2E) tests across all system components.

## Table of Contents

- [Test Structure](#test-structure)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [GitLab CI Integration](#gitlab-ci-integration)
- [Coverage Reports](#coverage-reports)
- [Troubleshooting](#troubleshooting)

## Test Structure

```
tests/
├── contract/          # Contract tests for message schemas and API contracts
├── e2e/              # End-to-end integration tests
├── integration/      # Integration tests for inter-service communication
├── unit/             # Unit tests for individual components
│   ├── central/      # Central system components
│   ├── hotel/        # Hotel service components
│   └── contracts/    # Contract testing utilities
├── conftest.py       # Global pytest fixtures and configuration
├── docker-compose.test.central.yml
├── docker-compose.test.e2e.yml
└── docker-compose.test.hotel.yml
```

## Prerequisites

### 1. Install Python Dependencies

```bash
# Install testing dependencies
pip install -r requirements-test.txt

# Install project dependencies
pip install -r requirements.txt
```

### 2. Docker and Docker Compose

Ensure Docker and Docker Compose are installed and running:

```bash
docker --version
docker-compose --version
```

### 3. Environment Setup

Some tests require services to be running. The test suites use isolated Docker Compose configurations.

## Running Tests

### Using Make (Recommended)

The project includes a Makefile with convenient test targets:

```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Run only unit tests
make test-integration   # Run only integration tests
make test-contract      # Run only contract tests
make test-e2e          # Run only end-to-end tests

# Run tests with coverage
make test-coverage      # Run all tests with coverage report
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=xml

# Run specific test file
pytest tests/unit/hotel/alert_agent/test_alert_agent_log.py

# Run tests matching a pattern
pytest -k "test_alert" -v
```

## Test Categories

### Unit Tests (`tests/unit/`)

Tests individual functions and classes in isolation without external dependencies.

**Components tested:**
- **Central Services:**
  - Automation app
  - Command service (config, controller, Kafka producer, routes)
- **Hotel Services:**
  - Alert agent (logging, rules)
  - Light actuator (handler, logging)
  - Temperature sensor (payload building, logging)

**Run unit tests:**
```bash
pytest tests/unit/ -v
```

### Integration Tests (`tests/integration/`)

Tests interaction between multiple components and services.

**Components tested:**
- MQTT to Kafka message bridge
- VictoriaMetrics data ingestion
- Service-to-service communication
- Message serialization/deserialization

**Prerequisites:**
- Start required services using Docker Compose

**Run integration tests:**
```bash
# Start test services
docker-compose -f docker-compose.test.central.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.central.yml down
```

### Contract Tests (`tests/contract/`)

Tests message schemas and API contracts to ensure compatibility between services.

**Components tested:**
- Message schema validation
- Alert agent contract compliance
- Light actuator contract compliance
- Cross-service message formats

**Run contract tests:**
```bash
pytest tests/contract/ -v
```

### End-to-End Tests (`tests/e2e/`)

Tests complete workflows from sensor input to data storage and actuation.

**Scenarios tested:**
- Sensor → MQTT → Kafka → VictoriaMetrics pipeline
- FastAPI → Light Actuator command flow
- Complete alert generation and handling

**Prerequisites:**
- Start E2E test environment

**Run E2E tests:**
```bash
# Start E2E test services
docker-compose -f docker-compose.test.e2e.yml up -d

# Run E2E tests
pytest tests/e2e/ -v

# Cleanup
docker-compose -f docker-compose.test.e2e.yml down
```

## GitLab CI Integration

### Recommended `.gitlab-ci.yml` Configuration

Add the following to your `.gitlab-ci.yml` file:

```yaml
stages:
  - test
  - coverage
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .pytest_cache/

before_script:
  - python -m pip install --upgrade pip
  - pip install -r requirements.txt
  - pip install -r requirements-test.txt

# Unit Tests Job
test:unit:
  stage: test
  image: python:3.11
  script:
    - pytest tests/unit/ -v --junitxml=reports/unit.xml
  artifacts:
    when: always
    reports:
      junit: reports/unit.xml
    paths:
      - reports/unit.xml
    expire_in: 30 days

# Contract Tests Job
test:contract:
  stage: test
  image: python:3.11
  script:
    - pytest tests/contract/ -v --junitxml=reports/contract.xml
  artifacts:
    when: always
    reports:
      junit: reports/contract.xml
    paths:
      - reports/contract.xml
    expire_in: 30 days

# Integration Tests Job
test:integration:
  stage: test
  image: python:3.11
  services:
    - name: eclipse-mosquitto:2
      alias: mosquitto
    - name: confluentinc/cp-kafka:latest
      alias: kafka
  script:
    - pytest tests/integration/ -v --junitxml=reports/integration.xml
  artifacts:
    when: always
    reports:
      junit: reports/integration.xml
    paths:
      - reports/integration.xml
    expire_in: 30 days

# E2E Tests Job
test:e2e:
  stage: test
  image: python:3.11
  services:
    - docker:dind
  before_script:
    - apk add --no-cache docker-compose
    - pip install -r requirements.txt
    - pip install -r requirements-test.txt
  script:
    - docker-compose -f docker-compose.test.e2e.yml up -d
    - sleep 10  # Wait for services to be ready
    - pytest tests/e2e/ -v --junitxml=reports/e2e.xml
    - docker-compose -f docker-compose.test.e2e.yml down
  artifacts:
    when: always
    reports:
      junit: reports/e2e.xml
    paths:
      - reports/e2e.xml
    expire_in: 30 days

# Coverage Job
test:coverage:
  stage: coverage
  image: python:3.11
  script:
    - pytest --cov=. --cov-report=xml --cov-report=html --cov-report=term --junitxml=reports/all.xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    when: always
    reports:
      junit: reports/all.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - reports/
      - htmlcov/
      - coverage.xml
    expire_in: 30 days

# Generate coverage badge (optional)
pages:
  stage: deploy
  dependencies:
    - test:coverage
  script:
    - mv htmlcov/ public/
  artifacts:
    paths:
      - public
    expire_in: 30 days
  only:
    - main
```

### Simplified CI Configuration (Minimal)

If you want a simpler setup:

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r requirements.txt -r requirements-test.txt
  script:
    - make test-unit
    - make test-contract
  artifacts:
    when: always
    reports:
      junit: reports/*.xml
```

## Coverage Reports

### Generate Coverage Report

```bash
# HTML report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser

# Terminal report
pytest --cov=. --cov-report=term

# XML report (for CI)
pytest --cov=. --cov-report=xml
```

### Coverage Configuration

Coverage settings are defined in `pytest.ini`:

```ini
[pytest]
addopts = 
    --cov-config=.coveragerc
    --cov-report=term-missing
    --cov-fail-under=80
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError` when running tests

**Solution:**
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest with proper path discovery
pytest --import-mode=importlib
```

#### 2. Docker Services Not Ready

**Problem:** Integration/E2E tests fail because services aren't ready

**Solution:**
```bash
# Add wait time after docker-compose up
docker-compose -f docker-compose.test.e2e.yml up -d
sleep 15  # Wait for services to initialize
pytest tests/e2e/
```

#### 3. Port Conflicts

**Problem:** Docker services fail to start due to port conflicts

**Solution:**
```bash
# Stop existing services
docker-compose down

# Or modify port mappings in test docker-compose files
```

#### 4. Permission Errors

**Problem:** Cannot write to reports directory

**Solution:**
```bash
# Create reports directory with proper permissions
mkdir -p reports
chmod 755 reports
```

### Debugging Tests

```bash
# Run with extra verbose output
pytest -vv

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests only
pytest --lf

# Run specific test with debugging
pytest tests/unit/hotel/alert_agent/test_alert_agent_log.py::test_log_info -vv -s
```