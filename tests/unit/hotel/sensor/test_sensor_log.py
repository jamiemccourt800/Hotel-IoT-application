# test_sensor_log.py - tests for the logging function in sensor main.py
import pathlib
from tests.conftest import load_module_from_path

# Load the sensor_main module
SENSOR = load_module_from_path(
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

def test_log_without_device_info(capsys):
    """Test log function when device info is not provided."""
    SENSOR.log("warn", "test-event", "test without device info", some_field="value")
    out = capsys.readouterr().out.strip()
    
    assert "WARN " in out
    assert "test-event" in out
    assert 'msg="test without device info"' in out
    assert "some_field=value" in out

def test_log_with_false_boolean(capsys):
    """Test log function with False boolean value."""
    SENSOR.log("info", "test", "testing false boolean", hotel_id="h1", room="1", sensor="s1", enabled=False)
    out = capsys.readouterr().out.strip()
    
    assert "enabled=false" in out  # Boolean False should be lowercase

