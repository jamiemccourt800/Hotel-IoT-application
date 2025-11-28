import os
import pytest


def pytest_configure(config):
    """Register custom markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: integration tests requiring external services (MQTT, Kafka, etc.)"
    )


@pytest.fixture
def integration_settings():
    """Common settings every integration test can reuse.

    IMPORTANT: Read environment variables at fixture runtime so tests that
    monkeypatch.setenv(...) inside a test will be picked up by this fixture.
    Previously these were read into module-level constants at import time,
    which made them insensitive to later monkeypatch.setenv calls.
    """
    mqtt_host = os.getenv("TEST_MQTT_HOST", "mosquitto")
    mqtt_port = int(os.getenv("TEST_MQTT_PORT", "1883"))
    kafka_bootstrap = os.getenv("TEST_KAFKA_BOOTSTRAP", "kafka:9092")
    victoria_metrics_url = os.getenv("TEST_VICTORIA_METRICS_URL", "http://victoria-metrics:8428")

    return {
        "mqtt_host": mqtt_host,
        "mqtt_port": mqtt_port,
        "kafka_bootstrap": kafka_bootstrap,
        "victoria_metrics_url": victoria_metrics_url,
        "topic": "mqtt_messages",
    }

def test_conftest_sanity(integration_settings):
    """Tiny test just so conftest code is covered in integration run."""
    assert integration_settings["mqtt_host"]
    assert integration_settings["mqtt_port"] > 0
