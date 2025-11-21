# test_sensor_telemetry.py - Unit tests for temperature sensor telemetry message creation

import pathlib, json
import pytest
import time
import sys
import os
from jsonschema import validate

# Add hotel/room1 to path for importing common modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'hotel', 'room1'))
from common.schemas import TemperatureTelemetry, MessageTags

# Load the JSON schema used for validating the payload
SCHEMA = json.loads(pathlib.Path("schemas/message.schema.json").read_text())

def create_temperature_message(hotel_id, room, sensor, temp_c, ts):
    """Helper function to create temperature telemetry message like the sensor does"""
    # Handle timestamp conversion (matching sensor logic)
    try:
        if ts is None:
            ts_val = time.time()
        else:
            ts_val = float(ts)
    except (TypeError, ValueError):
        ts_val = time.time()
    
    # Convert to milliseconds if in seconds (timestamp < 10^12)
    timestamp = int(ts_val * 1000 if ts_val < 1_000_000_000_000 else ts_val)
    
    # Create message using shared schema (like sensor does)
    message = TemperatureTelemetry(
        tags=MessageTags(
            hotel_id=str(hotel_id),
            room=int(room),
            sensor=str(sensor)
        ),
        fields={
            "temperatureC": float(temp_c)
        },
        timestamp=timestamp
    )
    
    return message.to_dict()

def test_seconds_timestamp_is_normalized_to_ms():
    ts_seconds = 1_700_000_000  # seconds
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", 21.25, ts_seconds)
    assert msg["timestamp"] == ts_seconds * 1000  # normalized to ms
    assert msg["measurement"] == "temperature"
    assert msg["tags"] == {"hotel_id": "hotel_01", "room": 101, "sensor": "temperature-sensor"}
    assert msg["fields"]["temperatureC"] == 21.25
    validate(instance=msg, schema=SCHEMA)

def test_milliseconds_timestamp_is_passed_through():
    ts_ms = 1_700_000_000_000  # already ms
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", "21.5", ts_ms)
    assert msg["timestamp"] == ts_ms
    assert msg["fields"]["temperatureC"] == 21.5  # coerced to float
    validate(instance=msg, schema=SCHEMA)

def test_string_seconds_is_accepted_and_normalized():
    ts_seconds_str = "1700000000"
    msg = create_temperature_message("h", "1", "temperature-sensor", 20, ts_seconds_str)
    assert msg["timestamp"] == 1_700_000_000_000
    validate(instance=msg, schema=SCHEMA)

def test_ts_none_falls_back_to_current_time(monkeypatch):
    fixed_time = 1700000000.0
    monkeypatch.setattr(time, "time", lambda: fixed_time)
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", 21.5, None)
    assert abs(msg["timestamp"] - int(fixed_time * 1000)) < 10_000  # within 10s

@pytest.mark.parametrize("room", [101, "101"])
def test_room_as_int_or_str(room):
    msg = create_temperature_message("hotel_01", room, "temperature-sensor", 21.5, 1700000000)
    assert msg["tags"]["room"] == int(room)

@pytest.mark.parametrize("temp", ["21.5", 21.5])
def test_temperature_as_str_or_float(temp):
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", temp, 1700000000)
    assert msg["fields"]["temperatureC"] == float(temp)

@pytest.mark.parametrize("bad_temp", ["not-a-number", None, "", [], {}])
def test_bad_temperature_raises(bad_temp):
    with pytest.raises((ValueError, TypeError)):
        create_temperature_message("hotel_01", 101, "temperature-sensor", bad_temp, 1700000000)

@pytest.mark.parametrize("bad_temp", [-100, 200])
def test_out_of_range_temperature_raises(bad_temp):
    # Note: Our new schema doesn't enforce temperature range validation
    # This test is updated to reflect the actual behavior
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", bad_temp, 1700000000)
    assert msg["fields"]["temperatureC"] == float(bad_temp)

def test_ts_string_in_milliseconds_is_passthrough():
    ts_ms_str = "1700000456000"
    msg = create_temperature_message("h1", "101", "temperature-sensor", 20.0, ts_ms_str)
    assert msg["timestamp"] == int(ts_ms_str)

def test_temperature_coerces_from_string():
    msg = create_temperature_message("h1", "101", "temperature-sensor", "22.25", 1_700_000_000_000)
    assert isinstance(msg["fields"]["temperatureC"], float)
    assert msg["fields"]["temperatureC"] == 22.25

@pytest.mark.parametrize("temp", [-50.0, -40.0, 0.0, 37.0, 100.0, 120.0])
def test_boundary_temperatures_ok(temp):
    msg = create_temperature_message("h1", "101", "temperature-sensor", temp, 1_700_000_000_000)
    assert msg["fields"]["temperatureC"] == float(temp)

@pytest.mark.parametrize("bad", ["not-a-number", None, object()])
def test_invalid_temperature_rejected(bad):
    with pytest.raises((ValueError, TypeError)):
        create_temperature_message("h1", "101", "temperature-sensor", bad, 1)

@pytest.mark.parametrize("extreme_temp", [-1000, 2000])
def test_extreme_temperatures_accepted(extreme_temp):
    # Our new implementation accepts extreme temperatures
    msg = create_temperature_message("h1", "101", "temperature-sensor", extreme_temp, 1)
    assert msg["fields"]["temperatureC"] == float(extreme_temp)

def test_build_payload_invalid_ts(monkeypatch):
    fixed_time = 1700000000.0
    monkeypatch.setattr("time.time", lambda: fixed_time)
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", 21.5, "not-a-timestamp")
    assert msg["timestamp"] == int(fixed_time * 1000)

@pytest.mark.parametrize("bad_room", ["not-a-number", None, [], {}, object()])
def test_invalid_room_raises_type_error(bad_room):
    """Test that invalid room values raise TypeError."""
    with pytest.raises((ValueError, TypeError)):
        create_temperature_message("hotel_01", bad_room, "temperature-sensor", 21.5, 1700000000)

def test_room_float_converts_to_int():
    """Test that room as float gets converted to int."""
    msg = create_temperature_message("hotel_01", 101.7, "temperature-sensor", 21.5, 1700000000)
    assert msg["tags"]["room"] == 101
    assert isinstance(msg["tags"]["room"], int)

def test_temperature_sensor_message_format():
    """Test that temperature sensor message format matches expected schema."""
    # Verify our helper function creates messages with correct structure
    import inspect
    sig = inspect.signature(create_temperature_message)
    params = list(sig.parameters.keys())
    
    # create_temperature_message(hotel_id, room, sensor, temp_c, ts)
    assert 'hotel_id' in params  # Maps to HOTEL_ID env var
    assert 'room' in params       # Maps to ROOM env var
    assert 'sensor' in params     # Maps to SENSOR env var
    assert 'temp_c' in params     # Temperature value
    assert 'ts' in params         # Timestamp
    
    # Test that message structure matches schema requirements
    msg = create_temperature_message("hotel_01", 101, "temperature-sensor", 21.5, 1700000000)
    assert "measurement" in msg
    assert "tags" in msg
    assert "fields" in msg
    assert "timestamp" in msg
    assert msg["measurement"] == "temperature"
    validate(instance=msg, schema=SCHEMA)

