# test_light_actuator_log.py - tests for the logging function in light actuator main.py
import pathlib
import pytest
from conftest import load_module

# Load the actuator module from a path that contains a hyphen
ACT = load_module(
    "actuator_main",
    pathlib.Path("hotel/room1/light-actuator/logic/main.py"),
)

@pytest.mark.skipif(not hasattr(ACT, "log"), reason="actuator module has no log()")
def test_log_includes_expected_fields(capsys):
    """
    If the actuator exposes a log(level, event, message, **fields),
    verify the log line contains stable parts (level/service/device/custom fields).
    """
    ACT.log(
        "info",
        "command",
        "applied",
        hotel_id="hotel_01",
        room=101,
        sensor="light-actuator",
        on=True,
        brightness=75,
    )
    out = capsys.readouterr().out.strip()

    assert "INFO " in out                  # level uppercased/padded
    assert "actuator" in out or "light" in out  # service name
    assert "hotel_01/101/light-actuator" in out
    assert "event=command" in out
    assert 'msg="applied"' in out
    assert "on=true" in out
    assert "brightness=75" in out
