"""
Humidifier/dehumidifier actuator configuration.
"""
import os
from dataclasses import dataclass

@dataclass
class HumidifierConfig:
    """Humidifier control configuration"""
    default_target: float = 50.0
    control_interval: float = 5.0  # Control loop frequency in seconds
    deadband: float = 2.0  # Humidity deadband for control
    max_humidifying: float = 100.0  # Max humidifying output %
    max_dehumidifying: float = 100.0  # Max dehumidifying output %
    
    @classmethod
    def from_env(cls) -> 'HumidifierConfig':
        """Create humidifier config from environment variables"""
        return cls(
            default_target=float(os.getenv("DEFAULT_TARGET", "50.0")),
            control_interval=float(os.getenv("CONTROL_INTERVAL", "5.0")),
            deadband=float(os.getenv("DEADBAND", "2.0")),
            max_humidifying=float(os.getenv("MAX_HUMIDIFYING", "100.0")),
            max_dehumidifying=float(os.getenv("MAX_DEHUMIDIFYING", "100.0"))
        )
