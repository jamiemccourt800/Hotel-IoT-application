# test_alert_agent_rules.py - tests for alert agent temperature rules
import pathlib
import pytest
from conftest import load_module

# Load the alert agent module
ALERT = load_module(
    "alert_main",
    pathlib.Path("hotel/room1/alert-agent/app/main.py"),
)

def _get_eval():
    
    """
    Return a callable that evaluates a telemetry message and
    either returns an alert dict or None.
    Accepts different shapes:
      - evaluate(msg)
      - check_temperature_alert(msg)
      - handle(msg)
    """

    for name in ("evaluate", "check_temperature_alert", "handle"):
        fn = getattr(ALERT, name, None)
        if callable(fn):
            return fn
    raise AttributeError(
        "Expected a function like evaluate(msg), check_temperature_alert(msg) or handle(msg) in alert-agent."
    )

def _mk_msg(temp, hotel_id="hotel_01", room=101, sensor="temperature-sensor", ts=1234567890000):

    """
    Create a sample telemetry message dict with given temperature and context.
    """

    return {
        "measurement": "temperature",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"temperatureC": temp},
        "timestamp": ts,
    }

@pytest.mark.parametrize("temp", [30.1, 35.0, 50.0])
def test_high_temperature_triggers_alert(temp):
    
    """
    Temperatures clearly above the threshold should produce a non-empty alert.
    """

    evaluate = _get_eval()
    alert = evaluate(_mk_msg(temp))
    assert alert, f"Expected an alert for temp={temp}"
    # Reasonable shape checks
    assert isinstance(alert, dict)
    assert "type" in alert or "name" in alert
    assert "timestamp" in alert
    assert any(k in alert for k in ("severity", "level", "priority"))

@pytest.mark.parametrize("temp", [10.0, 20.0, 25.0, 29.9])
def test_normal_temperature_no_alert(temp):
    
    """
    Temperatures below (or at) threshold should return None / no alert.
    """

    evaluate = _get_eval()
    alert = evaluate(_mk_msg(temp))
    assert alert in (None, False, {})

def test_missing_temperature_field_is_handled_safely():
    
    """
    If the message is malformed (no fields/temperature), the function should
    not crash: either return None or raise a clear error.
    """

    evaluate = _get_eval()
    bad = {"tags": {"hotel_id": "h", "room": 1}, "fields": {}, "timestamp": 1}
    try:
        out = evaluate(bad)
        assert out in (None, False, {}), f"Unexpected return for malformed input: {out}"
    except (KeyError, ValueError, TypeError):
        # raising a clear, predictable error is also fine
        assert True

def test_tags_are_carried_into_alert_if_present():
    
    """
    Alerts usually echo context (hotel/room/sensor). If your implementation
    includes them, assert they are present. If not, we accept absence.
    """
    
    evaluate = _get_eval()
    msg = _mk_msg(40.0, hotel_id="h77", room=909, sensor="temperature-sensor")
    alert = evaluate(msg)
    assert alert  # should alert at 40C
    # Optional/forgiving checks:
    if "tags" in alert:
        t = alert["tags"]
        assert t.get("hotel_id") == "h77"
        assert str(t.get("room")) == "909"
