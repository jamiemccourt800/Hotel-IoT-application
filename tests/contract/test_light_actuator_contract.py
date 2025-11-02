import json
import pathlib
import pytest
from jsonschema import validate
import json
import pathlib
import pytest
from jsonschema import validate

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

def _mk_msg(topic, payload_dict):
    class Msg:
        pass
    m = Msg()
    m.topic = topic
    m.payload = json.dumps(payload_dict).encode()
    return m

@pytest.fixture
def light_module(load_module):
    return load_module("hotel.room1.light-actuator.logic.main")

def test_on_connect_registers_topics(light_module):
    client = DummyClient()
    light_module.on_connect(client, None, None, 0, {})
    assert client.subscribed

def test_on_message_turn_on_command_produces_state(light_module):
    client = DummyClient()
    msg = _mk_msg("actuators/light/hotel_01/101", {
        "cmd": "on",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "controller"}
    })
    light_module.on_message(client, None, msg)
    assert client.published
    for topic, payload in client.published:
        payload_dict = json.loads(payload)
        validate(instance=payload_dict, schema=SCHEMA)

def test_on_message_brightness_command_is_validated(light_module):
    client = DummyClient()
    msg = _mk_msg("actuators/light/hotel_01/101", {
        "cmd": "brightness",
        "value": 55,
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "controller"}
    })
    light_module.on_message(client, None, msg)
    assert client.published
    for topic, payload in client.published:
        payload_dict = json.loads(payload)
        validate(instance=payload_dict, schema=SCHEMA)

def test_on_message_bad_json_does_not_crash(light_module):
    client = DummyClient()
    class Msg:
        topic = "actuators/light/hotel_01/101"
        payload = b"not-json"
    light_module.on_message(client, None, Msg())
    # Should not raise
