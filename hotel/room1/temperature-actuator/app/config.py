"""
Thermostat/HVAC actuator configuration.
"""
import os
from dataclasses import dataclass

@dataclass
class ThermostatConfig:
    """Thermostat control configuration"""
    default_target: float = 22.0
    control_interval: float = 5.0  # Control loop frequency in seconds
    deadband: float = 0.5  # Temperature deadband for control
    max_heating: float = 100.0  # Max heating output %
    max_cooling: float = 100.0  # Max cooling output %
    
    @classmethod
    def from_env(cls) -> 'ThermostatConfig':
        """Create thermostat config from environment variables"""
        return cls(
            default_target=float(os.getenv("DEFAULT_TARGET", "22.0")),
            control_interval=float(os.getenv("CONTROL_INTERVAL", "5.0")),
            deadband=float(os.getenv("DEADBAND", "0.5")),
            max_heating=float(os.getenv("MAX_HEATING", "100.0")),
            max_cooling=float(os.getenv("MAX_COOLING", "100.0"))
        )