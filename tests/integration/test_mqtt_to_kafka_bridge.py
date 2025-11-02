
import os
import json
import pytest
from kafka.errors import NoBrokersAvailable

def _make_test_payload():
    return {
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

def test_mqtt_message_is_forwarded_to_kafka(integration_settings):
    """
    Happy-path integration test.
    Will SKIP if Kafka can't be reached (we still want the code to run).
    """
    import paho.mqtt.client as mqtt
    from kafka import KafkaConsumer

    mqtt_host = integration_settings["mqtt_host"]
    mqtt_port = integration_settings["mqtt_port"]
    kafka_bootstrap = integration_settings["kafka_bootstrap"]

    print(f"� connecting to MQTT at {mqtt_host}:{mqtt_port} ...")
    client = mqtt.Client()
    client.connect(mqtt_host, mqtt_port, 60)

    payload = _make_test_payload()
    client.publish("sensors/hotel_01/101/temperature", json.dumps(payload), qos=0)
    client.disconnect()
    print("📤 published test message to MQTT")

    print(f"🧭 connecting to Kafka at {kafka_bootstrap} ...")
    try:
        consumer = KafkaConsumer(
            "mqtt_messages",
            bootstrap_servers=kafka_bootstrap,
            group_id=None,
            auto_offset_reset="latest",
            consumer_timeout_ms=4000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
    except NoBrokersAvailable as e:
        pytest.skip(f"⚠️ Kafka not available: {e}")

    print("⏳ waiting for message on topic mqtt_messages ...")
    for msg in consumer:
        data = msg.value
        if data.get("message", {}).get("measurement") == "temperature":
            print("✅ got message from Kafka")
            break
    else:
        pytest.fail("message never arrived from bridge")
