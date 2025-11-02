import pathlib
import json
import pytest
from jsonschema import validate
from conftest import load_module

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

def _msg(topic, payload_dict):
    class Msg:
        pass
    m = Msg()
    m.topic = topic
    m.payload = json.dumps(payload_dict).encode()
    return m

def test_on_message_unknown_measurement_is_ignored(load_module):
    alert_mod = load_module("hotel.room1.alert-agent.app.main")
    client = DummyClient()
    msg = _msg("sensors/hotel_01/101/unknown", {
        "measurement": "something-else",
        "timestamp": 1730514475000,
        "fields": {},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "unknown"}
    })
    alert_mod.on_message(client, None, msg)
    assert not client.published

def test_handle_temperature_missing_fields_does_not_crash(load_module):
    alert_mod = load_module("hotel.room1.alert-agent.app.main")
    client = DummyClient()
    msg = _msg("sensors/hotel_01/101/temperature-sensor", {
        "measurement": "temperature",
        "timestamp": 1730514475000,
        "fields": {},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"}
    })
    alert_mod.on_message(client, None, msg)
    # Should not raise

def test_handle_light_state_low_brightness_does_not_crash(load_module):
    alert_mod = load_module("hotel.room1.alert-agent.app.main")
    client = DummyClient()
    msg = _msg("sensors/hotel_01/101/light-actuator", {
        "measurement": "light_state",
        "timestamp": 1730514475000,
        "fields": {"on": True, "brightness": 1},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "light-actuator"}
    })
    alert_mod.on_message(client, None, msg)
    # Should not raise

def test_should_emit_true_and_false_branches(load_module):
    alert_mod = load_module("hotel.room1.alert-agent.app.main")
    key = "test-dedup-key"
    assert alert_mod.should_emit(key)
    assert not alert_mod.should_emit(key)

def test_should_emit_with_different_keys(load_module):
    mod = load_module("hotel.room1.alert-agent.app.main")
    assert mod.should_emit("key1")
    assert not mod.should_emit("key1")
    assert mod.should_emit("key2")

def test_device_key_with_missing_tags(load_module):
    mod = load_module("hotel.room1.alert-agent.app.main")
    tags = {}
    key = mod.device_key(tags)
    assert isinstance(key, str)

def test_on_message_with_missing_payload_fields(load_module):
    mod = load_module("hotel.room1.alert-agent.app.main")
    class DummyClient:
        def __init__(self):
            self.published = []
        def publish(self, topic, payload, *a, **k):
            self.published.append((topic, payload))
            return True
    msg = type('msg', (), {'topic': "sensors/hotel_01/101/temperature-sensor", 'payload': b'{}'})
    client = DummyClient()
    mod.on_message(client, None, msg)
    # Should not raise

def test_on_message_with_non_bytes_payload(load_module):
    mod = load_module("hotel.room1.alert-agent.app.main")
    class DummyClient:
        def __init__(self):
            self.published = []
        def publish(self, topic, payload, *a, **k):
            self.published.append((topic, payload))
            return True
    msg = type('msg', (), {'topic': "sensors/hotel_01/101/temperature-sensor", 'payload': "not-bytes"})
    client = DummyClient()
    mod.on_message(client, None, msg)
    # Should not raise
