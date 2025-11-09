import pathlib
import json
import pytest
from jsonschema import validate
from tests.conftest import load_module

SCHEMA_PATH = pathlib.Path("tests/contracts/message_schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

class DummyClient:
    def __init__(self):
        self.published = []
    def publish(self, topic, payload, *a, **k):
        self.published.append((topic, payload))
        return True

def _msg(topic, payload_dict):
    class Msg:
        pass
    m = Msg()
    m.topic = topic
    m.payload = json.dumps(payload_dict).encode()
    return m

def test_on_message_unsupported_command_publishes_error(load_module):
    actuator_mod = load_module("hotel.room1.light-actuator.logic.main")
    client = DummyClient()
    msg = _msg("actuators/hotel_01/101/light-actuator", {
        "cmd": "not-a-real-cmd",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "light-actuator"}
    })
    actuator_mod.on_message(client, None, msg)
    assert client.published
    for topic, payload in client.published:
        validate(instance=json.loads(payload), schema=SCHEMA)

def test_on_message_with_unsupported_command(load_module):
    mod = load_module("hotel.room1.light-actuator.logic.main")
    class DummyClient:
        def __init__(self):
            self.published = []
        def publish(self, topic, payload, *a, **k):
            self.published.append((topic, payload))
            return True
    msg = type('msg', (), {'topic': "actuators/hotel_01/101/light-actuator", 'payload': b'{"cmd": "not-a-real-cmd"}'})
    client = DummyClient()
    mod.on_message(client, None, msg)
    assert client.published

def test_on_message_brightness_out_of_range_is_clamped_or_rejected(load_module):
    actuator_mod = load_module("hotel.room1.light-actuator.logic.main")
    client = DummyClient()
    msg = _msg("actuators/hotel_01/101/light-actuator", {
        "cmd": "brightness",
        "value": 999,
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "light-actuator"}
    })
    actuator_mod.on_message(client, None, msg)
    assert client.published
    for topic, payload in client.published:
        validate(instance=json.loads(payload), schema=SCHEMA)

def test_on_message_with_missing_cmd(load_module):
    mod = load_module("hotel.room1.light-actuator.logic.main")
    class DummyClient:
        def __init__(self):
            self.published = []
        def publish(self, topic, payload, *a, **k):
            self.published.append((topic, payload))
            return True
    msg = type('msg', (), {'topic': "actuators/hotel_01/101/light-actuator", 'payload': b'{}'})
    client = DummyClient()
    mod.on_message(client, None, msg)
    # Should not raise
