"""
Temperature simulation algorithms extracted from existing main.py.
Implements random walk temperature simulation around target.
"""
import time
import random
from typing import Iterator, Tuple

class TemperatureSimulation:
    """Temperature simulation using random walk algorithm"""
    
    def __init__(self, config):
        self.config = config
        self.target_temperature = config.target_temp
        self.current_temp = config.start_temp
        
    def set_target_temperature(self, target: float):
        """Update target temperature for simulation (from thermostat commands)"""
        self.target_temperature = target
        
    def generate_readings(self) -> Iterator[Tuple[int, float]]:
        """Generate temperature readings using random walk (extracted from existing logic)"""
        while True:
            # Move towards target with some randomness (exact same algorithm as original)
            target = self.target_temperature
            self.current_temp += (target - self.current_temp) * 0.1
            self.current_temp += random.uniform(-0.2, 0.2)
            self.current_temp = round(self.current_temp, 2)
            
            timestamp = int(time.time() * 1000)
            yield timestamp, self.current_temp
            
            # Sleep with speed control (matching original behavior)
            time.sleep(max(self.config.interval / max(self.config.speed, 0.01), 0.01))