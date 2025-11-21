"""
Humidity sensor specific configuration.
Extracts humidity-related settings from environment.
"""
import os
import argparse
from dataclasses import dataclass

@dataclass
class HumidityConfig:
    """Humidity sensor configuration"""
    target_humidity: float = 50.0
    interval: float = 1.0
    speed: float = 1.0
    start_humidity: float = 50.0
    
    @classmethod
    def from_env(cls) -> 'HumidityConfig':
        """Create humidity config from environment variables and command line"""
        # Parse command line arguments (matching existing behavior)
        parser = argparse.ArgumentParser()
        parser.add_argument("--interval", type=float, default=float(os.getenv("INTERVAL", "1.0")))
        parser.add_argument("--speed", type=float, default=float(os.getenv("SPEED", "1.0")))
        
        # Parse known args to avoid conflicts with other modules
        args, _ = parser.parse_known_args()
        
        return cls(
            target_humidity=float(os.getenv("TARGET_HUMIDITY", "50.0")),
            interval=args.interval,
            speed=args.speed,
            start_humidity=float(os.getenv("START_HUMIDITY", "50.0"))
        )
