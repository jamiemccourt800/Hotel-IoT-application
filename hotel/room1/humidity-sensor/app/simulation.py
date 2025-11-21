"""
Humidity simulation algorithms extracted from existing main.py.
Implements random walk humidity simulation around target.
"""
import time
import random
from typing import Iterator, Tuple

class HumiditySimulation:
    """Humidity simulation using random walk algorithm"""
    
    def __init__(self, config):
        self.config = config
        self.target_humidity = config.target_humidity
        self.current_humidity = config.start_humidity
        
    def set_target_humidity(self, target: float):
        """Update target humidity for simulation (from humidifier/dehumidifier commands)"""
        self.target_humidity = target
        
    def generate_readings(self) -> Iterator[Tuple[int, float]]:
        """Generate humidity readings using random walk (exact same algorithm as temperature)"""
        while True:
            # Move towards target with some randomness (exact same algorithm as original)
            target = self.target_humidity
            self.current_humidity += (target - self.current_humidity) * 0.1
            self.current_humidity += random.uniform(-0.5, 0.5)
            self.current_humidity = max(0.0, min(100.0, round(self.current_humidity, 2)))
            
            timestamp = int(time.time() * 1000)
            yield timestamp, self.current_humidity
            
            # Sleep with speed control (matching original behavior)
            time.sleep(max(self.config.interval / max(self.config.speed, 0.01), 0.01))
