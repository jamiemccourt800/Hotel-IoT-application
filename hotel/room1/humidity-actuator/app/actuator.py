"""
Humidity actuator business logic for humidifier/dehumidifier control.
Completes the humidity control loop by managing humidity setpoints.
"""
import asyncio
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, HumidityTelemetry, MessageTags, get_logger, now_ms
from humidifier import HumidifierController, ControlOutput

class HumidityActuator:
    """Humidity actuator for humidifier/dehumidifier control"""
    
    def __init__(self, device_config, mqtt_config, humidifier_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config
        self.humidifier_config = humidifier_config
        self.logger = get_logger("humidity-actuator", device_config)
        
        # Initialize components
        self.mqtt_client = HotelMQTTClient(mqtt_config, "humidity-actuator", device_config)
        self.humidifier = HumidifierController(humidifier_config)
        
        # External control flag - disables local deadband control when FastAPI commands are used
        self.external_control_mode = False
        
    def start(self):
        """Start humidity actuator operations"""
        self.logger.info('startup', 'started',
                        default_target=self.humidifier_config.default_target,
                        control_interval=self.humidifier_config.control_interval)
        
        # Connect to MQTT
        client = self.mqtt_client.connect_with_retries()
        
        # Set up MQTT topics
        base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
        
        # Subscribe to humidifier commands from central system
        cmd_topic = f"commands/humidity/{base_room}/{self.device_config.sensor}"
        client.subscribe(cmd_topic, qos=self.mqtt_config.qos)
        
        # Subscribe to humidity sensor readings for feedback control
        sensor_topic = f"{base_room}/humidity-sensor/telemetry"
        client.subscribe(sensor_topic, qos=self.mqtt_config.qos)
        
        # Set message callback
        client.on_message = self._on_message
        
        self.logger.info('subscribed', 'subscribed to topics',
                        cmd_topic=cmd_topic, sensor_topic=sensor_topic)
        
        # Start control loop in separate thread
        import threading
        control_thread = threading.Thread(target=self._control_loop, args=(client,))
        control_thread.daemon = True
        control_thread.start()
        
        # Start network loop in background
        client.loop_start()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info('shutdown', 'stopping actuator')
        finally:
            client.loop_stop()
            client.disconnect()
            
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            data = json.loads(msg.payload.decode())
            
            if "commands/humidity/" in msg.topic:
                # Handle humidifier commands
                self._process_command(data, msg.topic)
            elif "/humidity-sensor/telemetry" in msg.topic:
                # Handle humidity sensor readings
                self._process_humidity_reading(data, msg.topic)
                
        except Exception as e:
            self.logger.error('message-error', f'error processing message: {e}',
                            error=str(e), topic=msg.topic)
            
    def _process_command(self, command: dict, topic: str):
        """Process humidifier command from FastAPI (external control)"""
        fields = command.get("fields", {})
        correlation_id = command.get("correlationId")
        
        try:
            # Enable external control mode when command received
            if not self.external_control_mode:
                self.external_control_mode = True
                self.logger.info('control-mode', 'switched to external control mode (FastAPI)',
                               correlation_id=correlation_id)
            
            if "target_humidity" in fields:
                target = float(fields["target_humidity"])
                self.humidifier.set_target_humidity(target)
                self.logger.info('command-processed', f'set target humidity to {target}%',
                               target_humidity=target, correlation_id=correlation_id)
                
                # Directly publish setpoint to sensor (bypass deadband control)
                base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
                setpoint_topic = f"{base_room}/humidifier"
                setpoint_msg = {
                    "target_humidity": target,
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(setpoint_topic, setpoint_msg)
                               
            if "mode" in fields:
                mode = fields["mode"]
                self.humidifier.set_mode(mode)
                self.logger.info('command-processed', f'set mode to {mode}',
                               mode=mode, correlation_id=correlation_id)
                               
            # Send acknowledgment
            self._send_ack("ok", "", correlation_id)
            
        except Exception as e:
            self.logger.error('command-error', f'error processing command: {e}',
                            error=str(e), correlation_id=correlation_id)
            self._send_ack("failed", str(e), correlation_id)
            
    def _process_humidity_reading(self, telemetry: dict, topic: str):
        """Update humidifier with current humidity for feedback control"""
        try:
            fields = telemetry.get("fields", {})
            if "humidityPercent" in fields:
                humidity = float(fields["humidityPercent"])
                self.humidifier.update_current_humidity(humidity)
                # Note: No per-message logging to avoid spam
        except Exception as e:
            self.logger.error('sensor-reading', f'error processing humidity reading: {e}',
                            error=str(e), topic=topic)
            
    def _control_loop(self, client):
        """Continuous humidifier control based on humidity feedback (local mode only)"""
        base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
        setpoint_topic = f"{base_room}/humidifier"
        humidifier_topic = f"{base_room}/humidifier-status"
        
        while True:
            try:
                # Skip local control if external commands are being used
                if self.external_control_mode:
                    time.sleep(self.humidifier_config.control_interval)
                    continue
                
                # Calculate control output (local deadband control)
                control = self.humidifier.calculate_control_output()
                
                # Publish setpoint update for humidity sensor
                setpoint_msg = {
                    "target_humidity": control.target_humidity,
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(setpoint_topic, setpoint_msg)
                
                # Publish humidifier status
                humidifier_msg = {
                    "measurement": "humidifier-status",
                    "tags": {
                        "hotel_id": self.device_config.hotel_id,
                        "room": self.device_config.room,
                        "sensor": self.device_config.sensor
                    },
                    "fields": {
                        "mode": control.mode.value,
                        "power_level": control.power_level,
                        "target_humidity": control.target_humidity,
                        "current_humidity": control.current_humidity
                    },
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(humidifier_topic, humidifier_msg)
                
                # Log control action if humidifier is active
                if control.power_level > 0:
                    self.logger.info('control-output', 
                                   f'{control.mode.value} at {control.power_level:.1f}%',
                                   mode=control.mode.value,
                                   power_level=control.power_level,
                                   target_humidity=control.target_humidity,
                                   current_humidity=control.current_humidity)
                
                time.sleep(self.humidifier_config.control_interval)
                
            except Exception as e:
                self.logger.error('control-loop', f'error in control loop: {e}', error=str(e))
                time.sleep(5)  # Recovery delay
                
    def _send_ack(self, status: str, error: str, correlation_id: str):
        """Send acknowledgment message"""
        ack_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/{self.device_config.sensor}/ack"
        ack_msg = {
            "measurement": "ack",
            "tags": {
                "hotel_id": self.device_config.hotel_id,
                "room": self.device_config.room,
                "sensor": self.device_config.sensor
            },
            "fields": {"status": status, "error": error},
            "timestamp": now_ms(),
            "correlationId": correlation_id
        }
        self.mqtt_client.publish_telemetry(ack_topic, ack_msg)
