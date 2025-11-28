import time
import json
import pathlib
import pytest
from jsonschema import validate
import importlib

SCHEMA_PATH = pathlib.Path("tests/contracts/message_schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

class DummyClient:
    def __init__(self):
        self.published = []
        self.subscribed = []
    def publish(self, topic, payload, *a, **k):
        self.published.append((topic, payload))
        return True
    def subscribe(self, topic, *a, **k):
        self.subscribed.append(topic)
        return True

def _mk_mqtt_message(topic, payload_dict):
    class Msg:
        pass
    m = Msg()
    m.topic = topic
    m.payload = json.dumps(payload_dict).encode()
    return m

def test_on_connect_subscribes_without_crashing():
    client = DummyClient()
    ALERT_MAIN = importlib.import_module('hotel.room1.alert-agent.app.main')
    ALERT_MAIN.on_connect(client, None, None, 0)
    assert client.subscribed

def test_on_message_temperature_above_threshold_emits_alert():
    client = DummyClient()
    ALERT_MAIN = importlib.import_module('hotel.room1.alert-agent.app.main')
    msg = _mk_mqtt_message("sensors/hotel_01/101/temperature-sensor", {
        "measurement": "temperature",
        "timestamp": 1730514475000,
        "fields": {"temperatureC": 32.5},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"}
    })
    ALERT_MAIN.on_message(client, None, msg)
    assert client.published
    payload = json.loads(client.published[-1][1])
    validate(instance=payload, schema=SCHEMA)
    assert payload["measurement"] == "alert"

def test_on_message_light_state_is_understood():
    client = DummyClient()
    ALERT_MAIN = importlib.import_module('hotel.room1.alert-agent.app.main')
    msg = _mk_mqtt_message("sensors/hotel_01/101/light-actuator", {
        "measurement": "light_state",
        "timestamp": 1730514475000,
        "fields": {"on": True, "brightness": 80},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "light-actuator"}
    })
    ALERT_MAIN.on_message(client, None, msg)
    # Just ensure no crash

def test_on_message_bad_json_is_ignored_gracefully():
    client = DummyClient()
    ALERT_MAIN = importlib.import_module('hotel.room1.alert-agent.app.main')
    class Msg:
        topic = "sensors/hotel_01/101/temperature-sensor"
        payload = b"not-json"
    ALERT_MAIN.on_message(client, None, Msg())
    # Should not raise
    msg = type('msg', (), {'payload': b'{bad json'})
    ALERT_MAIN.on_message(client, None, msg)
    # Should not raise, should not publish
    assert not client.published

# NOTE: Removed test_rules_evaluate_* tests - rules.py module was deleted
# Alert agent now uses consolidated threshold logic in agent.py
# See tests/unit/hotel/alert_agent/test_threshold_rules.py for new tests

