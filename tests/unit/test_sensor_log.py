# test_sensor_log.py - tests for the logging function in sensor main.py
import pathlib
from conftest import load_module

# Load the sensor_main module
SENSOR = load_module(
    "sensor_main",
    pathlib.Path("hotel/room1/temperature-sensor/logic/main.py"),
)

def test_log_includes_expected_fields(capsys):

    """
    Test that the log function outputs a log line with expected fields and formatting.
    """
    
    SENSOR.log(
        "info",
        "startup",
        "started",
        hotel_id="hotel_01",
        room="101",
        sensor="temperature-sensor",
        active=True,
        qos=1,
    )
    out = capsys.readouterr().out.strip()

    # Don’t assert on the timestamp; assert on stable parts:
    assert "INFO " in out                      # level uppercased + padded
    assert "sensor" in out                     # service name
    assert "hotel_01/101/temperature-sensor" in out  # device triple
    assert "event=startup" in out
    assert 'msg="started"' in out
    assert "active=true" in out                # booleans lowercased
    assert "qos=1" in out
