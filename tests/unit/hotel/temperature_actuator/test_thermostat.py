"""
Unit tests for thermostat controller.
Tests PID control logic, deadband control, and HVAC mode management.
"""
import pytest
from unittest.mock import Mock

# Import from temperature-actuator/app
import sys
sys.path.insert(0, 'hotel/room1/temperature-actuator/app')
from thermostat import ThermostatController, HVACMode, ControlOutput


@pytest.fixture
def thermostat_config():
    config = Mock()
    config.default_target = 22.0
    config.deadband = 0.5
    config.max_heating = 100.0
    config.max_cooling = 100.0
    config.control_interval = 5.0
    return config


class TestThermostatController:
    
    def test_initialization(self, thermostat_config):
        """Test thermostat initializes with config"""
        controller = ThermostatController(thermostat_config)
        assert controller.target_temperature == 22.0
        assert controller.mode == HVACMode.AUTO
        assert controller.current_temperature is None
        
    def test_set_target_temperature(self, thermostat_config):
        """Test updating target temperature"""
        controller = ThermostatController(thermostat_config)
        controller.set_target_temperature(25.0)
        assert controller.target_temperature == 25.0
        
    def test_set_mode_valid(self, thermostat_config):
        """Test setting valid HVAC mode"""
        controller = ThermostatController(thermostat_config)
        controller.set_mode("heating")
        assert controller.mode == HVACMode.HEATING
        
    def test_set_mode_invalid_defaults_to_auto(self, thermostat_config):
        """Test invalid mode defaults to AUTO"""
        controller = ThermostatController(thermostat_config)
        controller.set_mode("invalid_mode")
        assert controller.mode == HVACMode.AUTO
        
    def test_update_current_temperature(self, thermostat_config):
        """Test updating current temperature reading"""
        controller = ThermostatController(thermostat_config)
        controller.update_current_temperature(21.5)
        assert controller.current_temperature == 21.5
        
    def test_control_output_no_temperature_reading(self, thermostat_config):
        """Test control output when no temperature reading available"""
        controller = ThermostatController(thermostat_config)
        output = controller.calculate_control_output()
        
        assert output.mode == HVACMode.OFF
        assert output.power_level == 0.0
        
    def test_control_output_within_deadband(self, thermostat_config):
        """Test HVAC turns off when within deadband"""
        controller = ThermostatController(thermostat_config)
        controller.set_target_temperature(22.0)
        controller.update_current_temperature(22.2)  # Within 0.5°C deadband
        
        output = controller.calculate_control_output()
        assert output.mode == HVACMode.OFF
        assert output.power_level == 0.0
        
    def test_control_output_needs_heating(self, thermostat_config):
        """Test heating activates when too cold"""
        controller = ThermostatController(thermostat_config)
        controller.set_target_temperature(22.0)
        controller.update_current_temperature(20.0)  # 2°C below target
        
        output = controller.calculate_control_output()
        assert output.mode == HVACMode.HEATING
        assert output.power_level > 0.0
        
    def test_control_output_needs_cooling(self, thermostat_config):
        """Test cooling activates when too hot"""
        controller = ThermostatController(thermostat_config)
        controller.set_target_temperature(22.0)
        controller.update_current_temperature(24.0)  # 2°C above target
        
        output = controller.calculate_control_output()
        assert output.mode == HVACMode.COOLING
        assert output.power_level > 0.0
        
    def test_control_output_power_increases_with_error(self, thermostat_config):
        """Test power level increases with larger temperature error"""
        controller = ThermostatController(thermostat_config)
        controller.set_target_temperature(22.0)
        
        # Small error
        controller.update_current_temperature(21.0)
        output_small = controller.calculate_control_output()
        
        # Large error
        controller.update_current_temperature(18.0)
        output_large = controller.calculate_control_output()
        
        assert output_large.power_level > output_small.power_level
        
    def test_control_output_respects_max_limits(self, thermostat_config):
        """Test power level doesn't exceed configured maximum"""
        controller = ThermostatController(thermostat_config)
        controller.set_target_temperature(22.0)
        controller.update_current_temperature(10.0)  # Very cold
        
        output = controller.calculate_control_output()
        assert output.power_level <= thermostat_config.max_heating
