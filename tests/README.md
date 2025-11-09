# Testing Infrastructure

This directory contains the comprehensive test suite for the DevOps Group Project, covering unit, integration, contract, and end-to-end (E2E) tests across all system components.

## Table of Contents

- [Test Structure](#test-structure)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Coverage Reports](#coverage-reports)
- [Troubleshooting](#troubleshooting)

## Test Structure

```
tests/
├── contract/                   # Contract tests (6 test files)
├── contracts/                  # Shared schemas
├── e2e/                        # End-to-end tests (2 test files + fixtures)
├── integration/                # Integration tests (9 test files)
├── unit/                       # Unit tests (11 test files)
│   ├── central/
│   │   ├── app/          # FastAPI application tests
│   │   └── command/
│   ├── contracts/
│   └── hotel/
│       ├── alert_agent/
│       ├── light_actuator/
│       └── sensor/
├── conftest.py                 # Global pytest fixtures
├── docker-compose.test.central.yml    # For integration tests
├── docker-compose.test.e2e.yml        # For E2E tests
├── docker-compose.test.hotel.yml      # For hotel service tests
└── README.md                   # This file
```

**Test Count Summary:**
- **Unit Tests:** 11 files (~100+ test cases)
- **Contract Tests:** 6 files (~30+ test cases)  
- **Integration Tests:** 9 files (~25+ test cases)
- **E2E Tests:** 2 files (~10+ test cases)

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

### 3. Environment Setup

Some tests require services to be running. The test suites use isolated Docker Compose configurations.

## Running Tests

### Using Make (Recommended)

The project includes a Makefile with convenient test targets:

```bash
# Run specific test categories
make unit               # Run only unit tests
make contract           # Run only contract tests
make integration        # Run only integration tests
make e2e               # Run only end-to-end tests

# Run frontend tests (requires Node.js and npm)
make frontend-test              # Run frontend tests
make frontend-test-coverage     # Run frontend tests with coverage

# Run all Python tests
make all-tests                  # Run unit, contract, and integration tests

# Run all tests with HTML coverage report
make all-tests-coverage-html    # Run all Python tests and open coverage report

# Run all tests including frontend
make all-tests-with-frontend    # Run Python and frontend tests

# Setup environment
make init                       # Create virtual environment and install dependencies
```

## Test Categories

### Unit Tests (`tests/unit/`)

Tests individual functions and classes in isolation without external dependencies (no Docker or external services required).

**Structure:**
```
unit/
├── central/
│   ├── app/           # FastAPI application tests (health endpoints)
│   └── command/       # Command service components
│       ├── test_config.py          # Configuration loading and validation
│       ├── test_controller.py      # Business logic controllers
│       ├── test_kafka_producer.py  # Kafka message production
│       └── test_routes.py          # API route handlers
├── contracts/
│   └── test_unit_conftest_import.py  # Test fixture imports
└── hotel/
    ├── alert_agent/
    │   ├── test_alert_agent_log.py    # Alert logging functionality
    │   └── test_alert_agent_rules.py  # Alert rule evaluation
    ├── light_actuator/
    │   ├── test_light_actuator_handle.py  # Command handling logic
    │   └── test_light_actuator_log.py     # Logging, state/alert builders, env helpers
    └── sensor/
        ├── test_sensor_build_payload.py  # Payload construction, validation
        └── test_sensor_log.py            # Sensor logging functionality
```

**What's tested:**
- **Central/Command Service:**
  - FastAPI health endpoint behavior
  - Configuration parsing and defaults
  - Controller business logic
  - Kafka producer message formatting
  - API route request/response handling
  
- **Hotel/Alert Agent:**
  - Structured logging with proper field formatting
  - Alert rule threshold evaluation (temperature, humidity)
  - Alert severity determination

- **Hotel/Light Actuator:**
  - Command handling (on, off, toggle, set_brightness)
  - State message construction with/without temperature
  - Alert and acknowledgment message builders
  - Environment variable parsing (bool, int)
  - Value clamping (0-100 brightness range)

- **Hotel/Temperature Sensor:**
  - Telemetry payload construction
  - Timestamp normalization (seconds → milliseconds)
  - Temperature validation (range: -50°C to 100°C)
  - Data type coercion and error handling
  - Room number validation

### Integration Tests (`tests/integration/`)

Tests interaction between multiple components and services. Requires external dependencies (MQTT, Kafka) to be running.

**Test files:**
- `test_mqtt_to_kafka_bridge.py` - MQTT → Kafka message forwarding (happy path)
- `test_mqtt_to_kafka_bridge_fake.py` - Bridge testing with fake/mock services
- `test_mqtt_kafka_down.py` - Behavior when Kafka is unavailable
- `test_mqtt_kafka_error_branch.py` - Error handling branches
- `test_mqtt_ping.py` - MQTT connectivity tests
- `test_victoriametrics_integration.py` - VictoriaMetrics data ingestion
- `test_conftest_loader.py` - Module loading utilities
- `test_integration_envs.py` - Environment configuration validation

**What's tested:**
- **MQTT to Kafka Bridge:**
  - Messages published to MQTT are forwarded to Kafka
  - Topic mapping and transformation
  - Message serialization/deserialization
  - Connection resilience when services are down
  - Error handling and recovery
  
- **VictoriaMetrics Integration:**
  - Metric data ingestion and storage
  - Query API functionality
  - Time-series data retrieval
  
- **Service Communication:**
  - MQTT broker connectivity
  - Kafka producer/consumer behavior
  - Message format preservation across services

**Prerequisites:**
Start required services using Docker Compose:
```bash
# For MQTT and Kafka tests
docker-compose -f tests/docker-compose.test.central.yml up -d

# Verify services are running
docker-compose -f tests/docker-compose.test.central.yml ps
```

**Cleanup:**
```bash
docker-compose -f tests/docker-compose.test.central.yml down
```

**Note:** Some tests will skip if services are unavailable rather than fail, allowing CI to proceed.

### Contract Tests (`tests/contract/`)

Tests message schemas and API contracts to ensure compatibility between services. Validates that all components produce and consume messages according to the shared schema.

**Test files:**
- `test_message_contract.py` - Message schema validation
- `test_alert_agent_contract.py` - Alert agent message compliance
- `test_alert_agent_edges.py` - Alert agent edge cases and error handling
- `test_light_actuator_contract.py` - Light actuator message compliance
- `test_light_actuator_edges.py` - Light actuator edge cases
- `test_conftest_import.py` - Fixture imports and dependencies

**Shared schema:**
- `contracts/message_schema.json` - Universal message format using JSON Schema

**What's tested:**
- **Message Schema Compliance:**
  - All messages conform to JSON Schema structure
  - Required fields are present (measurement, timestamp, fields, tags)
  - Field types are correct (timestamps as int, etc.)
  
- **Alert Agent Contracts:**
  - Temperature sensor messages trigger appropriate alerts
  - Alert messages have correct structure (severity, kind)
  - Subscription behavior on connection
  
- **Light Actuator Contracts:**
  - Command messages are processed correctly
  - State messages include all required fields
  - Acknowledgment messages follow schema
  
- **Edge Cases:**
  - Invalid message formats are rejected
  - Missing required fields trigger errors
  - Type mismatches are handled properly

### End-to-End Tests (`tests/e2e/`)

Tests complete workflows from sensor input through the entire system to data storage and actuation. Validates the full data pipeline in a realistic environment.

**Test files:**
- `test_sensor_to_victoriametrics.py` - Complete telemetry pipeline test
- `test_fastapi_light_actuator.py` - FastAPI command to actuator flow
- `conftest.py` - E2E test fixtures and configuration

**Test scenarios:**

**1. Sensor → VictoriaMetrics Pipeline** (`test_sensor_to_victoriametrics.py`)
Complete data flow testing:
```
Temperature Sensor → MQTT Broker → Kafka Topic → Telegraf → VictoriaMetrics
```
- Publishes temperature telemetry to MQTT topic
- Verifies MQTT-to-Kafka bridge forwards the message
- Confirms Telegraf consumes from Kafka
- Validates data is stored in VictoriaMetrics
- Queries VictoriaMetrics API to retrieve and verify the data

**2. FastAPI → Light Actuator Flow** (`test_fastapi_light_actuator.py`)
Command execution testing:
```
FastAPI Endpoint → Kafka Topic → Light Actuator → State Update
```
- Sends light control commands via FastAPI
- Verifies commands are published to Kafka
- Confirms light actuator processes commands
- Validates state changes are published back
- Tests acknowledgment message flow

**What's tested:**
- End-to-end message routing across all components
- Data persistence in time-series database
- Real-time command and control flow
- System integration with actual MQTT, Kafka, Telegraf, VictoriaMetrics
- Complete request/response cycles
- Timing and latency considerations

**Prerequisites:**
Start complete E2E test environment:
```bash
# Start all required services
docker-compose -f tests/docker-compose.test.e2e.yml up -d

# Wait for services to initialize (important!)
sleep 15

# Verify all services are healthy
docker-compose -f tests/docker-compose.test.e2e.yml ps
```

**Cleanup:**
```bash
docker-compose -f tests/docker-compose.test.e2e.yml down

# Clean up volumes if needed
docker-compose -f tests/docker-compose.test.e2e.yml down -v
```

**Troubleshooting E2E Tests:**
- **Services not ready:** Increase wait time after `docker-compose up`
- **Connection refused:** Check `docker-compose ps` to ensure all services are running
- **Data not found in VictoriaMetrics:** Verify Telegraf configuration and Kafka topic
- **Port conflicts:** Ensure ports 1883, 9092, 8428 are available

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

## Quick Reference

### Common Test Commands

```bash
# Quick test runs
make unit                    # Fastest - no external dependencies
make contract                # Fast - schema validation only
make integration             # Requires MQTT + Kafka (Docker)
make e2e                     # Slowest - full stack (Docker)

# Coverage and reporting
make all-tests-coverage-html # Generate and open HTML coverage report
make all-tests               # All Python tests (unit + contract + integration)

# Frontend (requires Node.js/npm)
make frontend-test           # React component tests
```

### Docker Commands for Tests

```bash
# Start integration test environment
docker-compose -f tests/docker-compose.test.central.yml up -d

# Start E2E test environment
docker-compose -f tests/docker-compose.test.e2e.yml up -d

# View logs
docker-compose -f tests/docker-compose.test.e2e.yml logs -f

# Stop and remove containers
docker-compose -f tests/docker-compose.test.e2e.yml down

# Stop and remove with volumes
docker-compose -f tests/docker-compose.test.e2e.yml down -v
```

### Output and Reporting

```bash
# Generate XML report (for CI)
pytest --junitxml=reports/junit.xml

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# Generate all report types
pytest --cov=. --cov-report=html --cov-report=xml --cov-report=term --junitxml=reports/all.xml

# Open HTML coverage report (generated in htmlcov/)
# Windows
start reports/htmlcov/index.html
# Linux/Mac
open reports/htmlcov/index.html
```

### Environment Variables for Testing

```bash
# Set custom MQTT/Kafka hosts for integration tests
export MQTT_HOST=localhost
export MQTT_PORT=1883
export KAFKA_BOOTSTRAP=localhost:9092

# Run integration tests with custom config
pytest tests/integration/

# Disable test output capture (see print statements)
pytest -s

# Set pytest verbosity
pytest -v    # Verbose
pytest -vv   # Very verbose
pytest -q    # Quiet
```