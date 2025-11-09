# test_alert_agent_rules.py - Unit tests for alert_agent.evaluate (from rules module)

import pytest
from tests.conftest import load_module_from_path

ALERT_AGENT = load_module_from_path(
    "alert_agent",
    "hotel/room1/alert-agent/app/main.py",
)

def test_high_temperature_triggers_alert():
    """Test that high temperature triggers an alert using the evaluate function."""
    msg = {
        "measurement": "temperature",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"},
        "fields": {"temperatureC": 40.0}
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is not None
    assert result["measurement"] == "alert"
    assert result["fields"]["alert_type"] == "temp_high"

def test_normal_temperature_no_alert():
    """Test that normal temperature does not trigger an alert."""
    msg = {
        "measurement": "temperature",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"},
        "fields": {"temperatureC": 22.0}
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is None

def test_low_temperature_no_alert():
    """Test that low temperature does not trigger an alert."""
    msg = {
        "measurement": "temperature",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"},
        "fields": {"temperatureC": 10.0}
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is None

def test_invalid_temperature_returns_none():
    """Test that invalid temperature returns None instead of raising."""
    msg = {
        "measurement": "temperature",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"},
        "fields": {"temperatureC": "not-a-number"}
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is None

def test_evaluate_with_non_dict_returns_none():
    """Test that non-dict input returns None."""
    result = ALERT_AGENT.evaluate("not a dict")
    assert result is None

def test_evaluate_with_non_temperature_measurement():
    """Test that non-temperature measurement returns None."""
    msg = {
        "measurement": "humidity",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "hum-001"},
        "fields": {"humidity": 50.0}
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is None

def test_evaluate_with_missing_fields():
    """Test that message with missing fields returns None."""
    msg = {
        "measurement": "temperature",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"}
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is None

def test_evaluate_with_none_fields():
    """Test that message with None fields returns None."""
    msg = {
        "measurement": "temperature",
        "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"},
        "fields": None
    }
    result = ALERT_AGENT.evaluate(msg)
    assert result is None

def test_check_temperature_alert_alias():
    """Test that check_temperature_alert is an alias for evaluate."""
    assert ALERT_AGENT.check_temperature_alert == ALERT_AGENT.evaluate

def test_handle_alias():
    """Test that handle is an alias for evaluate."""
    assert ALERT_AGENT.handle == ALERT_AGENT.evaluate
