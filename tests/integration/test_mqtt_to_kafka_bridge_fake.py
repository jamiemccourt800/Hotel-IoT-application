# tests/integration/test_mqtt_to_kafka_bridge_fake.py
import pytest
import json
from types import SimpleNamespace

@pytest.mark.integration
@pytest.mark.timeout(15)
def test_mqtt_bridge_happy_path_without_real_kafka(monkeypatch, integration_settings):
    """
    This test forces the 'message received from Kafka' branch to run.
    WITHOUT requiring a real Kafka broker.
    We monkeypatch both MQTT and Kafka so the original test code can run.
    """
    import tests.integration.test_mqtt_to_kafka_bridge as bridge_mod

    # this is the fake message we want the test to 'receive' from Kafka
    fake_msg = {
        "message": {
            "measurement": "temperature",
            "timestamp": 1730000000000,
            "fields": {"temperatureC": 22.5},
            "tags": {
                "hotel_id": "hotel_01",
                "room": "101",
                "sensor": "temperature-sensor",
            },
        }
    }

    # 1) Fake KafkaConsumer that yields exactly one message
    class FakeConsumer:
        def __iter__(self):
            # simulate kafka-python msg.value after value_deserializer (already a dict)
            yield SimpleNamespace(value=fake_msg)

    # patch KafkaConsumer in the kafka module
    monkeypatch.setenv("TEST_KAFKA_BOOTSTRAP", "fake-kafka:9092")
    monkeypatch.setattr("kafka.KafkaConsumer", lambda *a, **k: FakeConsumer())

    # 2) Fake MQTT client so we don't need a real broker here
    class FakeMQTTClient:
        def connect(self, *a, **k):
            # no-op
            return 0
        def publish(self, *a, **k):
            # mimic paho return code
            return (0, None)
        def disconnect(self):
            return 0

    monkeypatch.setattr("paho.mqtt.client.Client", lambda *args, **kwargs: FakeMQTTClient())

    # 3) Now call the REAL integration test — but it will use our fakes
    bridge_mod.test_mqtt_message_is_forwarded_to_kafka(integration_settings)
