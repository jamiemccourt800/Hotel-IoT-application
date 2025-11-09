import os
import pytest

DEFAULT_MQTT_HOST = os.getenv("TEST_MQTT_HOST", "mosquitto")
DEFAULT_MQTT_PORT = int(os.getenv("TEST_MQTT_PORT", "1883"))
DEFAULT_KAFKA_BOOTSTRAP = os.getenv("TEST_KAFKA_BOOTSTRAP", "kafka:9092")
DEFAULT_VICTORIA_METRICS_URL = os.getenv("TEST_VICTORIA_METRICS_URL", "http://victoria-metrics:8428")

@pytest.fixture
def integration_settings():
    """Common settings every integration test can reuse."""
    return {
        "mqtt_host": DEFAULT_MQTT_HOST,
        "mqtt_port": DEFAULT_MQTT_PORT,
        "kafka_bootstrap": DEFAULT_KAFKA_BOOTSTRAP,
        "victoria_metrics_url": DEFAULT_VICTORIA_METRICS_URL,
        "topic": "mqtt_messages",
    }

def test_conftest_sanity(integration_settings):
    """Tiny test just so conftest code is covered in integration run."""
    assert integration_settings["mqtt_host"]
    assert integration_settings["mqtt_port"] > 0
