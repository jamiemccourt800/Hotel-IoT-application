"""
Temperature actuator entry point - HVAC/thermostat control service.
Completes the temperature control loop with the temperature sensor.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from actuator import TemperatureActuator
from config import ThermostatConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start temperature actuator"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("temperature-actuator")
    mqtt_config = MQTTConfig.from_env()
    thermostat_config = ThermostatConfig.from_env()
    
    # Initialize and start actuator
    actuator = TemperatureActuator(device_config, mqtt_config, thermostat_config)
    actuator.start()

if __name__ == "__main__":
    main()