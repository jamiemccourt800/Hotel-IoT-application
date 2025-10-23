# test_sensor_build_payload.py - Unit tests for sensor_main.build_payload()

import pathlib, json
import pytest
from jsonschema import validate
from conftest import load_module

# Load the sensor_main module and the JSON schema for validation
SENSOR = load_module(
    "sensor_main",
    pathlib.Path("hotel/room1/temperature-sensor/logic/main.py"),
)

# Load the JSON schema used for validating the payload
SCHEMA = json.loads(pathlib.Path("schemas/message.schema.json").read_text())

def test_seconds_timestamp_is_normalized_to_ms():
   
    """
    Test that a timestamp given in seconds is correctly normalized to milliseconds
    and that the payload structure matches the expected schema.
    """

    ts_seconds = 1_700_000_000  # seconds
    # room is an integer identifier in this project (not a string)
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", 21.25, ts_seconds)
    assert msg["timestamp"] == ts_seconds * 1000  # normalized to ms
    assert msg["measurement"] == "temperature"
    assert msg["tags"] == {"hotel_id": "hotel_01", "room": 101, "sensor": "temperature-sensor"}
    assert msg["fields"]["temperatureC"] == 21.25
    validate(instance=msg, schema=SCHEMA)

def test_milliseconds_timestamp_is_passed_through():
    
    """
    Test that a timestamp given in milliseconds is passed through unchanged
    and that the payload structure matches the expected schema.
    """

    ts_ms = 1_700_000_000_000  # already ms
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", "21.5", ts_ms)
    assert msg["timestamp"] == ts_ms
    assert msg["fields"]["temperatureC"] == 21.5  # coerced to float
    validate(instance=msg, schema=SCHEMA)

def test_string_seconds_is_accepted_and_normalized():
    
    """
    Test that a timestamp given as a string in seconds is accepted,
    normalized to milliseconds, and that the payload structure matches the expected schema.
    """

    ts_seconds_str = "1700000000"
    msg = SENSOR.build_payload("h", "1", "temperature-sensor", 20, ts_seconds_str)
    assert msg["timestamp"] == 1_700_000_000_000
    validate(instance=msg, schema=SCHEMA)

def test_invalid_ts_falls_back_to_current_time_ms(monkeypatch):
    """
    Test that an invalid timestamp causes the function to fall back to the current time in ms,
    and that the payload structure matches the expected schema.
    """

    def fake_time():

        """
        Fake time function returning a fixed timestamp in seconds.
        """

        return 1_700_000_000.0  # seconds -> *1000 = 1_700_000_000_000 ms (> 1e12)
    
    monkeypatch.setattr(SENSOR.time, "time", fake_time)
    msg = SENSOR.build_payload("h", "1", "temperature-sensor", 19.0, "not-a-number")
    assert msg["timestamp"] == 1_700_000_000_000
    validate(instance=msg, schema=SCHEMA)

@pytest.mark.parametrize("room", [101, "101"])
def test_accepts_room_as_int_or_str(room):
   
    """
    Room can be provided as int or str; tags should keep what we pass.
    """

    msg = SENSOR.build_payload("h1", room, "temperature-sensor", 21.0, 1_700_000_000_000)
    # build_payload now coerces room to int
    assert msg["tags"]["room"] == int(room)

def test_uses_current_time_when_ts_is_none(monkeypatch):
    
    """
    If ts is None, build_payload should use int(time.time()*1000).
    """
    
    def fake_time():
        return 1_700_000_123.456
    monkeypatch.setattr(SENSOR.time, "time", fake_time)

    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", 19.75, ts=None)
    assert msg["timestamp"] == 1_700_000_123_456
    assert msg["fields"]["temperatureC"] == 19.75

def test_ts_string_in_milliseconds_is_passthrough():
    
    """
    If ts is a numeric string already in ms (>= 1e12), use as-is.
    """


    ts_ms_str = "1700000456000"
    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", 20.0, ts_ms_str)
    assert msg["timestamp"] == int(ts_ms_str)

def test_temperature_coerces_from_string():
    
    """
    Temperature strings should be coerced to float.
    """

    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", "22.25", 1_700_000_000_000)
    assert isinstance(msg["fields"]["temperatureC"], float)
    assert msg["fields"]["temperatureC"] == 22.25

@pytest.mark.parametrize("temp", [-50.0, -40.0, 0.0, 37.0, 100.0, 120.0])
def test_boundary_temperatures_ok(temp):
    
    """
    Typical/edge values within allowed bounds should work.
    """

    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", temp, 1_700_000_000_000)
    assert msg["fields"]["temperatureC"] == float(temp)

@pytest.mark.parametrize("bad", [-1000, 2000, "not-a-number", None, object()])
def test_invalid_temperature_rejected(bad):
    
    """
    Out-of-range or bad-type temps should either raise or fail clearly.
    """

    with pytest.raises((ValueError, TypeError)):
        SENSOR.build_payload("h1", "101", "temperature-sensor", bad, 1)