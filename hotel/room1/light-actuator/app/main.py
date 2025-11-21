"""
Light actuator entry point - smart lighting control service.
Completes the light control loop with the light sensor.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from actuator import LightActuator
from config import LightControllerConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start light actuator"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("light-actuator")
    mqtt_config = MQTTConfig.from_env()
    light_controller_config = LightControllerConfig.from_env()
    
    # Initialize and start actuator
    actuator = LightActuator(device_config, mqtt_config, light_controller_config)
    actuator.start()

if __name__ == "__main__":
    main()
