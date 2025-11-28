"""
Humidifier control algorithms for humidity management.
Implements simple bang-bang control with deadband.
"""
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

class HumidifierMode(Enum):
    """Humidifier operating modes"""
    OFF = "off"
    HUMIDIFYING = "humidifying" 
    DEHUMIDIFYING = "dehumidifying"
    AUTO = "auto"

@dataclass
class ControlOutput:
    """Humidifier control output"""
    mode: HumidifierMode
    power_level: float  # 0-100%
    target_humidity: float
    current_humidity: float = None

class HumidifierController:
    """Simple humidifier controller with deadband control"""
    
    def __init__(self, config):
        self.config = config
        self.target_humidity = config.default_target
        self.current_humidity = None
        self.mode = HumidifierMode.AUTO
        
    def set_target_humidity(self, target: float):
        """Update target humidity setpoint"""
        self.target_humidity = target
        
    def set_mode(self, mode: str):
        """Set humidifier operating mode"""
        try:
            self.mode = HumidifierMode(mode.lower())
        except ValueError:
            self.mode = HumidifierMode.AUTO
            
    def update_current_humidity(self, humidity: float):
        """Update current humidity reading from sensor"""
        self.current_humidity = humidity
        
    def calculate_control_output(self) -> ControlOutput:
        """Calculate humidifier control output based on humidity error"""
        if self.current_humidity is None:
            # No humidity reading yet
            return ControlOutput(
                mode=HumidifierMode.OFF,
                power_level=0.0,
                target_humidity=self.target_humidity
            )
            
        # Calculate humidity error
        error = self.target_humidity - self.current_humidity
        
        # Apply deadband control to prevent oscillation
        if abs(error) < self.config.deadband:
            # Within deadband - turn off humidifier
            mode = HumidifierMode.OFF
            power_level = 0.0
        elif error > self.config.deadband:
            # Too dry - humidifying required
            mode = HumidifierMode.HUMIDIFYING if self.mode == HumidifierMode.AUTO else self.mode
            power_level = min(abs(error) * 10, self.config.max_humidifying)  # Simple proportional
        else:
            # Too humid - dehumidifying required  
            mode = HumidifierMode.DEHUMIDIFYING if self.mode == HumidifierMode.AUTO else self.mode
            power_level = min(abs(error) * 10, self.config.max_dehumidifying)  # Simple proportional
            
        return ControlOutput(
            mode=mode,
            power_level=power_level,
            target_humidity=self.target_humidity,
            current_humidity=self.current_humidity
        )
