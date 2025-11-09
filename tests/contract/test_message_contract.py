import json
import pathlib
import pytest
from jsonschema import validate, ValidationError

SCHEMA_PATH = pathlib.Path("tests/contracts/message_schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

@pytest.fixture
def sensor_module(load_module):
    return load_module("hotel.room1.temperature-sensor.logic.main")

@pytest.fixture
def actuator_module(load_module):
    return load_module("hotel.room1.light-actuator.logic.main")

@pytest.fixture
def alert_module(load_module):
    return load_module("hotel.room1.alert-agent.app.main")

def test_sensor_message_with_room_as_int_is_valid(sensor_module):
    msg = sensor_module.build_payload("hotel_01", 101, "temperature-sensor", 21.5, 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_sensor_message_with_room_as_string_is_valid(sensor_module):
    msg = sensor_module.build_payload("hotel_01", "101", "temperature-sensor", 21.5, 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_sensor_message_with_different_timestamp_is_valid(sensor_module):
    msg = sensor_module.build_payload("hotel_01", 101, "temperature-sensor", 21.5, 1_700_000_000)
    validate(instance=msg, schema=SCHEMA)

def test_sensor_message_matches_contract(sensor_module):
    msg = sensor_module.build_payload("hotel_01", 101, "temperature-sensor", 22.5, 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_actuator_state_matches_contract(actuator_module):
    msg = actuator_module.build_state("hotel_01", 101, "light-actuator", True, 75)
    msg["measurement"] = "light_state"
    validate(instance=msg, schema=SCHEMA)

def test_actuator_ack_matches_contract(actuator_module):
    # build_ack signature: correlation_id, hotel_id, room, sensor, status, error=""
    msg = actuator_module.build_ack("corr-123", "hotel_01", 101, "light-actuator", "ok")
    msg["measurement"] = "light_ack"
    msg.pop("correlationId", None)
    validate(instance=msg, schema=SCHEMA)

def test_alert_message_matches_contract():
    msg = {
        "measurement": "alert",
        "timestamp": 1730514475000,
        "fields": {"type": "temperature_high", "value": 29.4},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "alert-agent"}
    }
    validate(instance=msg, schema=SCHEMA)

@pytest.mark.parametrize("bad_msg", [
    # missing timestamp
    {
        "measurement": "temperature",
        "fields": {"temperatureC": 21.1},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"}
    },
    # missing fields
    {
        "measurement": "temperature",
        "timestamp": 1730514475000,
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"}
    },
    # missing tags
    {
        "measurement": "temperature",
        "timestamp": 1730514475000,
        "fields": {"temperatureC": 21.1}
    },
    # wrong type for timestamp
    {
        "measurement": "temperature",
        "timestamp": "1730514475000",
        "fields": {"temperatureC": 21.1},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"}
    },
    # extra top-level property
    {
        "measurement": "temperature",
        "timestamp": 1730514475000,
        "fields": {"temperatureC": 21.1},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"},
        "extra": "should-not-be-here"
    },
])
def test_invalid_messages_are_rejected(bad_msg):
    with pytest.raises(ValidationError):
        validate(instance=bad_msg, schema=SCHEMA)

def test_sensor_build_payload_with_room_as_int_is_valid(sensor_module):
    msg = sensor_module.build_payload("hotel_01", 101, "temperature-sensor", 21.5, 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_sensor_build_payload_with_room_as_string_is_valid(sensor_module):
    msg = sensor_module.build_payload("hotel_01", "101", "temperature-sensor", 21.5, 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_sensor_build_payload_with_string_temperature_is_valid(sensor_module):
    msg = sensor_module.build_payload("hotel_01", 101, "temperature-sensor", "21.5", 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_build_payload_with_missing_tags(sensor_module):
    mod = sensor_module
    import pytest
    with pytest.raises(TypeError, match="room must be an integer"):
        mod.build_payload(None, None, None, 21.5, 1730514475000)

def test_build_payload_with_invalid_temperature_type(sensor_module):
    mod = sensor_module
    import pytest
    with pytest.raises(TypeError, match="temperature must be a number"):
        mod.build_payload("hotel_01", 101, "temperature-sensor", "not-a-number", 1730514475000)
