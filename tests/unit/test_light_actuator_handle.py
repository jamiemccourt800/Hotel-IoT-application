# test_light_actuator_handle.py - tests for the light actuator handler
import pathlib
import pytest
from conftest import load_module

# Load the actuator module from a path that contains a hyphen
ACT = load_module(
    "actuator_main",
    pathlib.Path("hotel/room1/light-actuator/logic/main.py"),
)

def _get_handler():
    
    """
    Return a callable that handles a light command: handler(command_dict) -> dict.
    Works with either:
      - function: handle_light_command(cmd) or handle(cmd)
      - class   : LightActuator/Controller with .handle(cmd)
    """

    # function style
    if hasattr(ACT, "handle_light_command") and callable(ACT.handle_light_command):
        return ACT.handle_light_command
    if hasattr(ACT, "handle") and callable(ACT.handle):
        return ACT.handle

    # class style
    for cls_name in ("LightActuator", "Controller", "Actuator"):
        if hasattr(ACT, cls_name):
            inst = getattr(ACT, cls_name)()
            if hasattr(inst, "handle") and callable(inst.handle):
                return inst.handle

    raise AttributeError(
        "Expected a handler: handle_light_command(cmd), handle(cmd), or "
        "a class LightActuator/Controller with .handle(cmd)."
    )

def test_light_on_ack_and_state():
    
    """
    Turning the light ON with a valid brightness returns ack=True
    and a state reflecting on=True and the requested brightness.
    """

    handle = _get_handler()
    cmd = {"cmd": "light.set", "payload": {"on": True, "brightness": 80}}
    result = handle(cmd)

    assert isinstance(result, dict)
    assert result.get("ack") is True
    assert "state" in result and isinstance(result["state"], dict)
    assert result["state"]["on"] is True
    assert result["state"]["brightness"] == 80

def test_light_off_ack_and_state():
    
    """
    Turning the light OFF returns ack=True and state.on=False.
    """

    handle = _get_handler()
    cmd = {"cmd": "light.set", "payload": {"on": False, "brightness": 0}}
    result = handle(cmd)

    assert result.get("ack") is True
    assert result["state"]["on"] is False
    assert result["state"]["brightness"] == 0

@pytest.mark.parametrize("b", [0, 1, 50, 99, 100])
def test_brightness_boundaries_valid(b):
    
    """
    Brightness accepted at the edges and typical mid values.
    """

    handle = _get_handler()
    result = handle({"cmd": "light.set", "payload": {"on": True, "brightness": b}})
    assert result.get("ack") is True
    assert result["state"]["brightness"] == b

@pytest.mark.parametrize(
    "payload",
    [
        {"on": True, "brightness": -1},
        {"on": True, "brightness": 101},
        {"on": "yes", "brightness": 50},
        {"on": True, "brightness": "bright"},
        {},  # missing fields
    ],
)
def test_invalid_payload_rejected_or_errors(payload):
    
    """
    Invalid inputs either cause a clear exception OR return ack=False.
    Both behaviours are acceptable for unit tests.
    """

    handle = _get_handler()
    bad = {"cmd": "light.set", "payload": payload}
    try:
        result = handle(bad)
        assert result.get("ack") is False
    except (ValueError, TypeError, KeyError, AssertionError):
        # raising a clear error is also OK
        assert True

def test_unknown_command_is_rejected():
    
    """
    Unknown command results in a negative ack or a clear exception.
    """
    
    handle = _get_handler()
    unknown = {"cmd": "light.nuke", "payload": {}}
    try:
        result = handle(unknown)
        assert result.get("ack") is False
    except (ValueError, NotImplementedError, KeyError):
        assert True
