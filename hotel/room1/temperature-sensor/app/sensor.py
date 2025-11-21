"""
Temperature sensor business logic extracted from existing main.py.
Handles MQTT communication, telemetry publishing, and target updates.
"""
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, TemperatureTelemetry, MessageTags, get_logger
from simulation import TemperatureSimulation

class TemperatureSensor:
    """Temperature sensor with MQTT communication and simulation"""
    
    def __init__(self, device_config, mqtt_config, temp_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config  
        self.temp_config = temp_config
        self.logger = get_logger("temperature-sensor", device_config)
        
        # Initialize components
        self.mqtt_client = HotelMQTTClient(mqtt_config, "temperature-sensor", device_config)
        self.simulation = TemperatureSimulation(temp_config)
        
    def start(self):
        """Main sensor operation loop"""
        self.logger.info('startup', 'started', 
                        hotel_id=self.device_config.hotel_id,
                        room=self.device_config.room,
                        sensor=self.device_config.sensor,
                        interval_s=self.temp_config.interval,
                        speed=self.temp_config.speed,
                        target_temp=self.temp_config.target_temp)
        
        # Connect to MQTT with retries (using shared client)
        client = self.mqtt_client.connect_with_retries()
        
        # Set up MQTT topics (matching existing structure)
        base_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/{self.device_config.sensor}"
        telemetry_topic = f"{base_topic}/telemetry"
        status_topic = f"{base_topic}/status"
        target_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/thermostat"
        
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
        
        # Subscribe to target temperature updates
        client.subscribe(target_topic, qos=self.mqtt_config.qos)
        client.on_message = self._on_target_update
        
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
        """Publish temperature readings at configured interval"""
        self.logger.info('publishing', f'publishing telemetry to {telemetry_topic}', 
                        topic_out=telemetry_topic)
        
        published_count = 0
        try:
            for timestamp, temperature in self.simulation.generate_readings():
                # Build message using shared schema
                message = TemperatureTelemetry(
                    tags=MessageTags(
                        hotel_id=self.device_config.hotel_id,
                        room=self.device_config.room,
                        sensor=self.device_config.sensor
                    ),
                    fields={
                        "temperatureC": temperature
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
            
    def _on_target_update(self, client, userdata, msg):
        """Handle target temperature updates from thermostat"""
        try:
            data = json.loads(msg.payload.decode())
            if "target_temperature" in data:
                target = float(data["target_temperature"])
                self.simulation.set_target_temperature(target)
                self.logger.info('target-update', f'updated target temperature to {target}°C',
                               target_temp=target, topic_in=msg.topic)
        except Exception as e:
            self.logger.error('target-update', f'failed to process target update: {e}',
                            error=str(e), topic_in=msg.topic)