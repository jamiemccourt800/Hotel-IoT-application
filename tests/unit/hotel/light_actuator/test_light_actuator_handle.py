# test_light_actuator_handle.py - Unit tests for light_actuator command handling

import pytest
import sys
import os

# Add hotel/room1 to path for importing common modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'hotel', 'room1'))

# Import the actuator class
from common import DeviceConfig, MQTTConfig
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'hotel', 'room1', 'light-actuator', 'app'))
from actuator import LightActuator

@pytest.fixture
def light_actuator():
    """Create a light actuator instance for testing"""
    device_config = DeviceConfig(hotel_id="test_hotel", room=101, sensor="light-actuator")
    mqtt_config = MQTTConfig(broker="localhost", port=1883, qos=1, keepalive=60)
    return LightActuator(device_config, mqtt_config)

def test_turn_on_light(light_actuator):
    """Test turning on the light using process_command_action."""
    # Reset state
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    result = light_actuator.process_command_action("on", {})
    assert result["ack"] is True
    assert light_actuator.light_on is True
    assert light_actuator.brightness == 100  # Default brightness when turning on from 0

def test_turn_off_light(light_actuator):
    """Test turning off the light using process_command_action."""
    # Set initial state
    light_actuator.light_on = True
    light_actuator.brightness = 50
    
    result = light_actuator.process_command_action("off", {})
    assert result["ack"] is True
    assert light_actuator.light_on is False
    assert light_actuator.brightness == 0

def test_toggle_light(light_actuator):
    """Test toggling the light using process_command_action."""
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    result = light_actuator.process_command_action("toggle", {})
    assert result["ack"] is True
    assert light_actuator.light_on is True

def test_turn_on_with_brightness(light_actuator):
    """Test turning on light with specified brightness."""
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    result = light_actuator.process_command_action("on", {"brightness": 75})
    assert result["ack"] is True
    assert light_actuator.light_on is True
    assert light_actuator.brightness == 75

def test_turn_on_with_value_field(light_actuator):
    """Test turning on light with 'value' field instead of 'brightness'."""
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    result = light_actuator.process_command_action("on", {"value": 60})
    assert result["ack"] is True
    assert light_actuator.light_on is True
    assert light_actuator.brightness == 60

def test_turn_on_brightness_invalid_type(light_actuator):
    """Test that turning on with invalid brightness type raises TypeError."""
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    with pytest.raises(TypeError, match="brightness must be an integer"):
        light_actuator.process_command_action("on", {"brightness": "not-a-number"})

def test_turn_on_without_brightness_when_already_set(light_actuator):
    """Test turning on when brightness is already > 0."""
    light_actuator.light_on = False
    light_actuator.brightness = 50
    
    result = light_actuator.process_command_action("on", {})
    assert result["ack"] is True
    assert light_actuator.light_on is True
    assert light_actuator.brightness == 50  # Should maintain current brightness

def test_set_brightness(light_actuator):
    """Test setting brightness."""
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    result = light_actuator.process_command_action("set_brightness", {"value": 50})
    assert result["ack"] is True
    assert light_actuator.brightness == 50
    assert light_actuator.light_on is True  # Should turn on when brightness > 0

def test_set_brightness_to_zero(light_actuator):
    """Test setting brightness to 0."""
    light_actuator.light_on = True
    light_actuator.brightness = 100
    
    result = light_actuator.process_command_action("set_brightness", {"value": 0})
    assert result["ack"] is True
    assert light_actuator.brightness == 0
    assert light_actuator.light_on is False  # Should turn off when brightness is 0

def test_set_brightness_with_brightness_field(light_actuator):
    """Test setting brightness using 'brightness' field instead of 'value'."""
    result = light_actuator.process_command_action("set_brightness", {"brightness": 45})
    assert result["ack"] is True
    assert light_actuator.brightness == 45

def test_toggle_light_off_to_on(light_actuator):
    """Test toggling light from off to on."""
    light_actuator.light_on = False
    light_actuator.brightness = 50
    
    result = light_actuator.process_command_action("toggle", {})
    assert result["ack"] is True
    assert light_actuator.light_on is True
    assert light_actuator.brightness == 50

def test_toggle_light_on_to_off(light_actuator):
    """Test toggling light from on to off."""
    light_actuator.light_on = True
    light_actuator.brightness = 50
    
    result = light_actuator.process_command_action("toggle", {})
    assert result["ack"] is True
    assert light_actuator.light_on is False

def test_set_brightness_clamping_high(light_actuator):
    """Test that brightness is clamped to 100."""
    result = light_actuator.process_command_action("set_brightness", {"value": 150})
    assert result["ack"] is True
    assert light_actuator.brightness == 100

def test_set_brightness_clamping_low(light_actuator):
    """Test that brightness is clamped to 0."""
    result = light_actuator.process_command_action("set_brightness", {"value": -10})
    assert result["ack"] is True
    assert light_actuator.brightness == 0

def test_set_brightness_invalid_type(light_actuator):
    """Test that invalid brightness type raises TypeError."""
    with pytest.raises(TypeError):
        light_actuator.process_command_action("set_brightness", {"value": "not-a-number"})

def test_invalid_action(light_actuator):
    """Test that invalid action raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        light_actuator.process_command_action("invalid_action", {})

def test_handle_function(light_actuator):
    """Test the handle wrapper function."""
    light_actuator.light_on = False
    light_actuator.brightness = 0
    
    cmd = {"cmd": "light.set", "payload": {"on": True}}
    result = light_actuator.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["on"] is True

def test_handle_with_brightness(light_actuator):
    """Test handle function with brightness."""
    cmd = {"cmd": "light.set", "payload": {"brightness": 60}}
    result = light_actuator.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["brightness"] == 60

def test_handle_with_on_field(light_actuator):
    """Test handle function with 'on' field in payload."""
    cmd = {"cmd": "light.set", "payload": {"on": True}}
    result = light_actuator.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["on"] is True

def test_handle_with_brightness_field(light_actuator):
    """Test handle function with direct brightness field."""
    cmd = {"cmd": "light.set", "payload": {"brightness": 80}}
    result = light_actuator.handle(cmd)
    assert result["ack"] is True
    assert result["state"]["brightness"] == 80

def test_handle_missing_fields(light_actuator):
    """Test handle function with missing required fields."""
    with pytest.raises(KeyError):
        light_actuator.handle({"cmd": "light.set", "payload": {}})
