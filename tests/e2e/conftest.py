"""
E2E test configuration and fixtures.

These tests verify the complete data flow:
1. Sensor → MQTT → Kafka → Telegraf → VictoriaMetrics
2. FastAPI → Kafka → MQTT → Actuator
"""
import os
import pytest

# Environment variables for E2E tests
# These should be set in docker-compose.test.e2e.yml or overridden locally
MQTT_BROKER = os.getenv("E2E_MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("E2E_MQTT_PORT", "18831"))

KAFKA_BOOTSTRAP = os.getenv("E2E_KAFKA_BOOTSTRAP", "localhost:9092")

VICTORIA_METRICS_URL = os.getenv("E2E_VICTORIA_METRICS_URL", "http://localhost:8428")

FASTAPI_URL = os.getenv("E2E_FASTAPI_URL", "http://localhost:5000")

# Hotel configuration
HOTEL_ID = os.getenv("E2E_HOTEL_ID", "hotel_01")
ROOM_NUMBER = int(os.getenv("E2E_ROOM_NUMBER", "101"))


@pytest.fixture(scope="module")
def e2e_config():
    """E2E test configuration."""
    return {
        "mqtt_broker": MQTT_BROKER,
        "mqtt_port": MQTT_PORT,
        "kafka_bootstrap": KAFKA_BOOTSTRAP,
        "victoria_metrics_url": VICTORIA_METRICS_URL,
        "fastapi_url": FASTAPI_URL,
        "hotel_id": HOTEL_ID,
        "room_number": ROOM_NUMBER,
    }


# Register e2e marker
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end (deselect with '-m \"not e2e\"')"
    )
