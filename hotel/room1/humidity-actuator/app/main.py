"""
Humidity actuator entry point - humidifier/dehumidifier control service.
Completes the humidity control loop with the humidity sensor.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from actuator import HumidityActuator
from config import HumidifierConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start humidity actuator"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("humidity-actuator")
    mqtt_config = MQTTConfig.from_env()
    humidifier_config = HumidifierConfig.from_env()
    
    # Initialize and start actuator
    actuator = HumidityActuator(device_config, mqtt_config, humidifier_config)
    actuator.start()

if __name__ == "__main__":
    main()
