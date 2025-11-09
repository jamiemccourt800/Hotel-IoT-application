# tests/integration/test_mqtt_kafka_error_branch.py
import pytest
from kafka.errors import NoBrokersAvailable

def test_bridge_skips_on_nobrokers(monkeypatch, integration_settings):
    """
    Force the bridge test to take the 'skip because Kafka is down' path.
    This way we cover both success and failure branches.
    """
    import tests.integration.test_mqtt_to_kafka_bridge as bridge_mod

    class FakeKafka:
        def __init__(self, *a, **k):
            raise NoBrokersAvailable()

    # patch KafkaConsumer to raise in the kafka module
    monkeypatch.setattr("kafka.KafkaConsumer", FakeKafka)

    with pytest.raises(pytest.skip.Exception):
        bridge_mod.test_mqtt_message_is_forwarded_to_kafka(integration_settings)
