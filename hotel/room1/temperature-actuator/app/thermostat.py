"""
Thermostat control algorithms for HVAC management.
Implements simple bang-bang control with deadband.
"""
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

class HVACMode(Enum):
    """HVAC operating modes"""
    OFF = "off"
    HEATING = "heating" 
    COOLING = "cooling"
    AUTO = "auto"

@dataclass
class ControlOutput:
    """HVAC control output"""
    mode: HVACMode
    power_level: float  # 0-100%
    target_temperature: float
    current_temperature: float = None

class ThermostatController:
    """Simple thermostat controller with deadband control"""
    
    def __init__(self, config):
        self.config = config
        self.target_temperature = config.default_target
        self.current_temperature = None
        self.mode = HVACMode.AUTO
        
    def set_target_temperature(self, target: float):
        """Update target temperature setpoint"""
        self.target_temperature = target
        
    def set_mode(self, mode: str):
        """Set HVAC operating mode"""
        try:
            self.mode = HVACMode(mode.lower())
        except ValueError:
            self.mode = HVACMode.AUTO
            
    def update_current_temperature(self, temperature: float):
        """Update current temperature reading from sensor"""
        self.current_temperature = temperature
        
    def calculate_control_output(self) -> ControlOutput:
        """Calculate HVAC control output based on temperature error"""
        if self.current_temperature is None:
            # No temperature reading yet
            return ControlOutput(
                mode=HVACMode.OFF,
                power_level=0.0,
                target_temperature=self.target_temperature
            )
            
        # Calculate temperature error
        error = self.target_temperature - self.current_temperature
        
        # Apply deadband control to prevent oscillation
        if abs(error) < self.config.deadband:
            # Within deadband - turn off HVAC
            mode = HVACMode.OFF
            power_level = 0.0
        elif error > self.config.deadband:
            # Too cold - heating required
            mode = HVACMode.HEATING if self.mode == HVACMode.AUTO else self.mode
            power_level = min(abs(error) * 20, self.config.max_heating)  # Simple proportional
        else:
            # Too hot - cooling required  
            mode = HVACMode.COOLING if self.mode == HVACMode.AUTO else self.mode
            power_level = min(abs(error) * 20, self.config.max_cooling)  # Simple proportional
            
        return ControlOutput(
            mode=mode,
            power_level=power_level,
            target_temperature=self.target_temperature,
            current_temperature=self.current_temperature
        )