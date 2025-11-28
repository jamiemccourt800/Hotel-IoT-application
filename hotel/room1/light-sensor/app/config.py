"""
Light sensor specific configuration.
Extracts light-related settings from environment.
"""
import os
import argparse
from dataclasses import dataclass

@dataclass
class LightConfig:
    """Light sensor configuration"""
    interval: float = 1.0
    speed: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'LightConfig':
        """Create light config from environment variables and command line"""
        # Parse command line arguments (matching existing behavior)
        parser = argparse.ArgumentParser()
        parser.add_argument("--interval", type=float, default=float(os.getenv("INTERVAL", "1.0")))
        parser.add_argument("--speed", type=float, default=float(os.getenv("SPEED", "1.0")))
        
        # Parse known args to avoid conflicts with other modules
        args, _ = parser.parse_known_args()
        
        return cls(
            interval=args.interval,
            speed=args.speed
        )
