import json
import pathlib
import pytest
from jsonschema import validate, ValidationError
from conftest import load_module

SCHEMA_PATH = pathlib.Path("tests/contracts/message_schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

SENSOR = load_module("sensor_logic", pathlib.Path("hotel/room1/temperature-sensor/logic/main.py"))
ACTUATOR = load_module("light_logic", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
ALERT = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))

def test_temperature_sensor_message_contract():
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", 22.5, 1730514475000)
    validate(instance=msg, schema=SCHEMA)

def test_light_actuator_message_contract():
    msg = ACTUATOR.build_state("hotel_01", 101, "light-actuator", True, 60)
    validate(instance=msg, schema=SCHEMA)

def test_alert_agent_message_contract():
    msg = {
        "measurement": "alert",
        "timestamp": 1730514475000,
        "fields": {"type": "temperature_high", "value": 28.5},
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "alert-agent"}
    }
    validate(instance=msg, schema=SCHEMA)

def test_invalid_message_rejected():
    bad_msg = {"measurement": "temperature"}  # missing keys
    with pytest.raises(ValidationError):
        validate(instance=bad_msg, schema=SCHEMA)
