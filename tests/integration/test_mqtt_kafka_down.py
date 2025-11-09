import pytest
import os
from importlib import reload
import tests.integration.test_mqtt_to_kafka_bridge as bridge_test

def test_integration_skips_cleanly_when_kafka_is_down(monkeypatch, integration_settings):
    """
    Cover the branch where kafka is unreachable by pointing to a fake host.
    """
    monkeypatch.setenv("TEST_KAFKA_BOOTSTRAP", "does-not-exist:9999")
    reload(bridge_test)

    with pytest.raises(pytest.skip.Exception):
        bridge_test.test_mqtt_message_is_forwarded_to_kafka(integration_settings)
