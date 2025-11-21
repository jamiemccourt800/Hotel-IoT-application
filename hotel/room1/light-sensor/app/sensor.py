"""
Light sensor business logic extracted from existing main.py.
Handles MQTT communication, telemetry publishing, and ambient light simulation.
"""
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, LightTelemetry, MessageTags, get_logger
from simulation import LightSimulation

class LightSensor:
    """Light sensor with MQTT communication and simulation"""
    
    def __init__(self, device_config, mqtt_config, light_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config  
        self.light_config = light_config
        self.logger = get_logger("light-sensor", device_config)
        
        # Initialize components
        self.mqtt_client = HotelMQTTClient(mqtt_config, "light-sensor", device_config)
        self.simulation = LightSimulation(light_config)
        
    def start(self):
        """Main sensor operation loop"""
        self.logger.info('startup', 'started', 
                        hotel_id=self.device_config.hotel_id,
                        room=self.device_config.room,
                        sensor=self.device_config.sensor,
                        interval_s=self.light_config.interval,
                        speed=self.light_config.speed)
        
        # Connect to MQTT with retries (using shared client)
        client = self.mqtt_client.connect_with_retries()
        
        # Set up MQTT topics (matching existing structure)
        base_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/{self.device_config.sensor}"
        telemetry_topic = f"{base_topic}/telemetry"
        status_topic = f"{base_topic}/status"
        
        # Set up Last Will Testament for offline detection
        lwt_payload = {
            "measurement": "alert",
            "tags": {
                "hotel_id": self.device_config.hotel_id,
                "room": self.device_config.room,
                "sensor": self.device_config.sensor
            },
            "fields": {"kind": "sensor_offline", "severity": "HIGH"},
            "timestamp": int(time.time() * 1000)
        }
        self.mqtt_client.setup_last_will(status_topic, lwt_payload)
        
        # Publish sensor online status
        online_payload = {
            "measurement": "alert",
            "tags": {
                "hotel_id": self.device_config.hotel_id,
                "room": self.device_config.room,
                "sensor": self.device_config.sensor
            },
            "fields": {"kind": "sensor_online", "severity": "INFO"},
            "timestamp": int(time.time() * 1000)
        }
        self.mqtt_client.publish_telemetry(status_topic, online_payload)
        
        # Start telemetry publishing loop
        self._telemetry_loop(client, telemetry_topic)
        
    def _telemetry_loop(self, client, telemetry_topic):
        """Publish light readings at configured interval"""
        self.logger.info('publishing', f'publishing telemetry to {telemetry_topic}', 
                        topic_out=telemetry_topic)
        
        published_count = 0
        try:
            for timestamp, brightness in self.simulation.generate_readings():
                # Build message using shared schema
                message = LightTelemetry(
                    tags=MessageTags(
                        hotel_id=self.device_config.hotel_id,
                        room=self.device_config.room,
                        sensor=self.device_config.sensor
                    ),
                    fields={
                        "brightness": brightness
                    },
                    timestamp=timestamp
                )
                
                # Publish via standardized client  
                self.mqtt_client.publish_telemetry(telemetry_topic, message.to_dict())
                published_count += 1
                
        except KeyboardInterrupt:
            self.logger.info('shutdown', 'stopping sensor')
        finally:
            client.loop_stop()
            client.disconnect()
            self.logger.info('shutdown', 'sensor disconnected cleanly', 
                           published_count=published_count)
