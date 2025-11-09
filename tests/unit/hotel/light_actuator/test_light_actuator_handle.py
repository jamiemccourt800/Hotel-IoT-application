# test_light_actuator_handle.py - Unit tests for light_actuator command handling

import pytest
from tests.conftest import load_module_from_path

LIGHT_ACTUATOR = load_module_from_path(
    "light_actuator",
    "hotel/room1/light-actuator/logic/main.py",
)

def test_turn_on_light():
    """Test turning on the light using process_command_action."""
    # Reset state
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    result = LIGHT_ACTUATOR.process_command_action("on", {})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is True
    assert LIGHT_ACTUATOR.brightness == 100  # Default brightness when turning on from 0

def test_turn_off_light():
    """Test turning off the light using process_command_action."""
    # Set initial state
    LIGHT_ACTUATOR.light_on = True
    LIGHT_ACTUATOR.brightness = 50
    
    result = LIGHT_ACTUATOR.process_command_action("off", {})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is False
    assert LIGHT_ACTUATOR.brightness == 0

def test_toggle_light():
    """Test toggling the light using process_command_action."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    result = LIGHT_ACTUATOR.process_command_action("toggle", {})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is True

def test_turn_on_with_brightness():
    """Test turning on light with specified brightness."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    result = LIGHT_ACTUATOR.process_command_action("on", {"brightness": 75})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is True
    assert LIGHT_ACTUATOR.brightness == 75

def test_turn_on_with_value_field():
    """Test turning on light with 'value' field instead of 'brightness'."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    result = LIGHT_ACTUATOR.process_command_action("on", {"value": 60})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is True
    assert LIGHT_ACTUATOR.brightness == 60

def test_turn_on_brightness_invalid_type():
    """Test that turning on with invalid brightness type raises TypeError."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    with pytest.raises(TypeError, match="brightness must be an integer"):
        LIGHT_ACTUATOR.process_command_action("on", {"brightness": "not-a-number"})

def test_turn_on_without_brightness_when_already_set():
    """Test turning on when brightness is already > 0."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 50
    
    result = LIGHT_ACTUATOR.process_command_action("on", {})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is True
    assert LIGHT_ACTUATOR.brightness == 50  # Should maintain current brightness

def test_set_brightness():
    """Test setting brightness."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    result = LIGHT_ACTUATOR.process_command_action("set_brightness", {"value": 50})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.brightness == 50
    assert LIGHT_ACTUATOR.light_on is True  # Should turn on when brightness > 0

def test_set_brightness_to_zero():
    """Test setting brightness to 0."""
    LIGHT_ACTUATOR.light_on = True
    LIGHT_ACTUATOR.brightness = 100
    
    result = LIGHT_ACTUATOR.process_command_action("set_brightness", {"value": 0})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.brightness == 0
    assert LIGHT_ACTUATOR.light_on is False  # Should turn off when brightness is 0

def test_set_brightness_with_brightness_field():
    """Test setting brightness using 'brightness' field instead of 'value'."""
    result = LIGHT_ACTUATOR.process_command_action("set_brightness", {"brightness": 45})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.brightness == 45

def test_toggle_light_off_to_on():
    """Test toggling light from off to on."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 50
    
    result = LIGHT_ACTUATOR.process_command_action("toggle", {})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is True
    assert LIGHT_ACTUATOR.brightness == 50

def test_toggle_light_on_to_off():
    """Test toggling light from on to off."""
    LIGHT_ACTUATOR.light_on = True
    LIGHT_ACTUATOR.brightness = 50
    
    result = LIGHT_ACTUATOR.process_command_action("toggle", {})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.light_on is False

def test_set_brightness_clamping_high():
    """Test that brightness is clamped to 100."""
    result = LIGHT_ACTUATOR.process_command_action("set_brightness", {"value": 150})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.brightness == 100

def test_set_brightness_clamping_low():
    """Test that brightness is clamped to 0."""
    result = LIGHT_ACTUATOR.process_command_action("set_brightness", {"value": -10})
    assert result["ack"] is True
    assert LIGHT_ACTUATOR.brightness == 0

def test_set_brightness_invalid_type():
    """Test that invalid brightness type raises TypeError."""
    with pytest.raises(TypeError):
        LIGHT_ACTUATOR.process_command_action("set_brightness", {"value": "not-a-number"})

def test_invalid_action():
    """Test that invalid action raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        LIGHT_ACTUATOR.process_command_action("invalid_action", {})

def test_handle_function():
    """Test the handle wrapper function."""
    LIGHT_ACTUATOR.light_on = False
    LIGHT_ACTUATOR.brightness = 0
    
    cmd = {"cmd": "light.set", "payload": {"on": True}}
    result = LIGHT_ACTUATOR.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["on"] is True

def test_handle_with_brightness():
    """Test handle function with brightness."""
    cmd = {"cmd": "light.set", "payload": {"brightness": 60}}
    result = LIGHT_ACTUATOR.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["brightness"] == 60

def test_handle_with_on_field():
    """Test handle function with 'on' field in payload."""
    cmd = {"cmd": "light.set", "payload": {"on": True}}
    result = LIGHT_ACTUATOR.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["on"] is True

def test_handle_with_brightness_field():
    """Test handle function with direct brightness field."""
    cmd = {"cmd": "light.set", "payload": {"brightness": 80}}
    result = LIGHT_ACTUATOR.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["brightness"] == 80

def test_handle_missing_fields():
    """Test handle function with missing required fields."""
    with pytest.raises(KeyError):
        LIGHT_ACTUATOR.handle({"cmd": "light.set", "payload": {}})
