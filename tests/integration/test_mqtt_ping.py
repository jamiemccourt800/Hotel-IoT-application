import pytest

def test_can_publish_to_mqtt_only(integration_settings):
    """Covers MQTT side even if Kafka is down."""
    import paho.mqtt.client as mqtt

    host = integration_settings["mqtt_host"]
    port = integration_settings["mqtt_port"]

    client = mqtt.Client()
    client.connect(host, port, 60)
    rc, _ = client.publish("tests/ping", "ping", qos=0)
    client.disconnect()

    assert rc == 0, "MQTT publish failed"
