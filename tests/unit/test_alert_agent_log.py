# test_alert_agent_log.py - tests for alert-agent logging
import pathlib
import pytest
from conftest import load_module

# Load the alert agent module
ALERT = load_module(
    "alert_main",
    pathlib.Path("hotel/room1/alert-agent/app/main.py"),
)

@pytest.mark.skipif(not hasattr(ALERT, "log"), reason="alert-agent module has no log()")
def test_log_outputs_expected_fields(capsys):
    
    """
    If alert-agent exposes log(level, event, message, **fields),
    verify the log line contains stable parts.
    """
    
    ALERT.log(
        "info",
        "rule_eval",
        "high temp alert",
        hotel_id="hotel_01",
        room=101,
        sensor="alert-agent",
        threshold=30,
        temperatureC=35.5,
    )
    out = capsys.readouterr().out.strip()

    # Assertions similar to your other log tests
    assert "INFO " in out
    assert "alert" in out or "agent" in out
    assert "hotel_01/101/alert-agent" in out
    assert "event=rule_eval" in out
    assert 'msg="high temp alert"' in out
    assert "threshold=30" in out
    assert "temperatureC=35.5" in out
