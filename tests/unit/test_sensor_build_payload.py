# test_sensor_build_payload.py - Unit tests for sensor_main.build_payload()

import pathlib, json
import pytest
import time
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
    ts_seconds = 1_700_000_000  # seconds
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", 21.25, ts_seconds)
    assert msg["timestamp"] == ts_seconds * 1000  # normalized to ms
    assert msg["measurement"] == "temperature"
    assert msg["tags"] == {"hotel_id": "hotel_01", "room": 101, "sensor": "temperature-sensor"}
    assert msg["fields"]["temperatureC"] == 21.25
    validate(instance=msg, schema=SCHEMA)

def test_milliseconds_timestamp_is_passed_through():
    ts_ms = 1_700_000_000_000  # already ms
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", "21.5", ts_ms)
    assert msg["timestamp"] == ts_ms
    assert msg["fields"]["temperatureC"] == 21.5  # coerced to float
    validate(instance=msg, schema=SCHEMA)

def test_string_seconds_is_accepted_and_normalized():
    ts_seconds_str = "1700000000"
    msg = SENSOR.build_payload("h", "1", "temperature-sensor", 20, ts_seconds_str)
    assert msg["timestamp"] == 1_700_000_000_000
    validate(instance=msg, schema=SCHEMA)

def test_ts_none_falls_back_to_current_time(monkeypatch):
    fixed_time = 1700000000.0
    monkeypatch.setattr(time, "time", lambda: fixed_time)
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", 21.5, None)
    assert abs(msg["timestamp"] - int(fixed_time * 1000)) < 10_000  # within 10s

@pytest.mark.parametrize("room", [101, "101"])
def test_room_as_int_or_str(room):
    msg = SENSOR.build_payload("hotel_01", room, "temperature-sensor", 21.5, 1700000000)
    assert msg["tags"]["room"] == int(room)

@pytest.mark.parametrize("temp", ["21.5", 21.5])
def test_temperature_as_str_or_float(temp):
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", temp, 1700000000)
    assert msg["fields"]["temperatureC"] == float(temp)

@pytest.mark.parametrize("bad_temp", ["not-a-number", None, "", [], {}])
def test_bad_temperature_raises(bad_temp):
    with pytest.raises(TypeError):
        SENSOR.build_payload("hotel_01", 101, "temperature-sensor", bad_temp, 1700000000)

@pytest.mark.parametrize("bad_temp", [-100, 200])
def test_out_of_range_temperature_raises(bad_temp):
    with pytest.raises(ValueError):
        SENSOR.build_payload("hotel_01", 101, "temperature-sensor", bad_temp, 1700000000)

def test_ts_string_in_milliseconds_is_passthrough():
    ts_ms_str = "1700000456000"
    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", 20.0, ts_ms_str)
    assert msg["timestamp"] == int(ts_ms_str)

def test_temperature_coerces_from_string():
    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", "22.25", 1_700_000_000_000)
    assert isinstance(msg["fields"]["temperatureC"], float)
    assert msg["fields"]["temperatureC"] == 22.25

@pytest.mark.parametrize("temp", [-50.0, -40.0, 0.0, 37.0, 100.0, 120.0])
def test_boundary_temperatures_ok(temp):
    msg = SENSOR.build_payload("h1", "101", "temperature-sensor", temp, 1_700_000_000_000)
    assert msg["fields"]["temperatureC"] == float(temp)

@pytest.mark.parametrize("bad", [-1000, 2000, "not-a-number", None, object()])
def test_invalid_temperature_rejected(bad):
    with pytest.raises((ValueError, TypeError)):
        SENSOR.build_payload("h1", "101", "temperature-sensor", bad, 1)

def test_build_payload_invalid_ts(monkeypatch):
    import pathlib
    from conftest import load_module
    SENSOR = load_module("sensor_main", pathlib.Path("hotel/room1/temperature-sensor/logic/main.py"))
    fixed_time = 1700000000.0
    monkeypatch.setattr("time.time", lambda: fixed_time)
    msg = SENSOR.build_payload("hotel_01", 101, "temperature-sensor", 21.5, "not-a-timestamp")
    assert msg["timestamp"] == int(fixed_time * 1000)
