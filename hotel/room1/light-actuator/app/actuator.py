"""
Light actuator business logic for smart lighting control.
Completes the light control loop by managing brightness and on/off states.
"""
import asyncio
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, LightTelemetry, MessageTags, get_logger, now_ms
from light_controller import LightController, ControlOutput

class LightActuator:
    """Light actuator for brightness/on-off control"""
    
    def __init__(self, device_config, mqtt_config, light_controller_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config
        self.light_controller_config = light_controller_config
        self.logger = get_logger("light-actuator", device_config)
        
        # Initialize components
        self.mqtt_client = HotelMQTTClient(mqtt_config, "light-actuator", device_config)
        self.light_controller = LightController(light_controller_config)
        
        # External control flag - disables local adaptive control when FastAPI commands are used
        self.external_control_mode = False
        
    def start(self):
        """Start light actuator operations"""
        self.logger.info('startup', 'started',
                        default_brightness=self.light_controller_config.default_brightness,
                        control_interval=self.light_controller_config.control_interval)
        
        # Connect to MQTT
        client = self.mqtt_client.connect_with_retries()
        
        # Set up MQTT topics
        base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
        
        # Subscribe to light commands from Kafka-to-MQTT bridge
        # Bridge converts: actuators.hotel_01.101.light-actuator.cmd -> hotel_01/101/light-actuator/cmd
        cmd_topic = f"{base_room}/light-actuator/cmd"
        client.subscribe(cmd_topic, qos=self.mqtt_config.qos)
        
        # Subscribe to light sensor readings for feedback control
        sensor_topic = f"{base_room}/light-sensor/telemetry"
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
            
            if "/light-actuator/cmd" in msg.topic:
                # Handle light commands from FastAPI
                self._process_command(data, msg.topic)
            elif "/light-sensor/telemetry" in msg.topic:
                # Handle light sensor readings
                self._process_brightness_reading(data, msg.topic)
                
        except Exception as e:
            self.logger.error('message-error', f'error processing message: {e}',
                            error=str(e), topic=msg.topic)
            
    def _process_command(self, command: dict, topic: str):
        """Process light command from FastAPI (external control)"""
        fields = command.get("fields", {})
        correlation_id = command.get("correlationId")
        
        try:
            # Enable external control mode when command received
            if not self.external_control_mode:
                self.external_control_mode = True
                self.logger.info('control-mode', 'switched to external control mode (FastAPI)',
                               correlation_id=correlation_id)
            
            if "brightness" in fields:
                brightness = float(fields["brightness"])
                self.light_controller.set_brightness(brightness)
                self.logger.info('command-processed', f'set brightness to {brightness}%',
                               brightness=brightness, correlation_id=correlation_id)
                
                # Directly publish setpoint to sensor (bypass adaptive control)
                base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
                light_control_topic = f"{base_room}/light-control"
                control_msg = {
                    "target_brightness": brightness,
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(light_control_topic, control_msg)
                               
            if "mode" in fields:
                mode = fields["mode"]
                self.light_controller.set_mode(mode)
                self.logger.info('command-processed', f'set mode to {mode}',
                               mode=mode, correlation_id=correlation_id)
                               
            if "action" in fields:
                action = fields["action"]
                if action == "on":
                    self.light_controller.turn_on()
                    self.logger.info('command-processed', 'turned light on',
                                   correlation_id=correlation_id)
                elif action == "off":
                    self.light_controller.turn_off()
                    self.logger.info('command-processed', 'turned light off',
                                   correlation_id=correlation_id)
                elif action == "toggle":
                    self.light_controller.toggle()
                    self.logger.info('command-processed', 'toggled light',
                                   correlation_id=correlation_id)
            
            # Send acknowledgment
            self._send_ack("ok", "", correlation_id)
            
        except Exception as e:
            self.logger.error('command-error', f'error processing command: {e}',
                            error=str(e), correlation_id=correlation_id)
            self._send_ack("failed", str(e), correlation_id)
            
    def _process_brightness_reading(self, telemetry: dict, topic: str):
        """Update light controller with current brightness for feedback control"""
        try:
            fields = telemetry.get("fields", {})
            if "brightness" in fields:
                brightness = float(fields["brightness"])
                self.light_controller.update_current_brightness(brightness)
                # Note: No per-message logging to avoid spam
        except Exception as e:
            self.logger.error('sensor-reading', f'error processing brightness reading: {e}',
                            error=str(e), topic=topic)
            
    def _control_loop(self, client):
        """Continuous light control based on brightness feedback (local mode only)"""
        base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
        light_status_topic = f"{base_room}/light-status"
        light_control_topic = f"{base_room}/light-control"
        
        while True:
            try:
                # Skip local control if external commands are being used
                if self.external_control_mode:
                    time.sleep(self.light_controller_config.control_interval)
                    continue
                
                # Calculate control output (local adaptive control)
                control = self.light_controller.calculate_control_output()
                
                # Publish target brightness for sensor feedback (matching temp/humidity pattern)
                target_msg = {
                    "target_brightness": control.brightness_level,
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(light_control_topic, target_msg)
                
                # Publish light status
                light_msg = {
                    "measurement": "light-status",
                    "tags": {
                        "hotel_id": self.device_config.hotel_id,
                        "room": self.device_config.room,
                        "sensor": self.device_config.sensor
                    },
                    "fields": {
                        "mode": control.mode.value,
                        "brightness_level": control.brightness_level,
                        "current_brightness": control.current_brightness
                    },
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(light_status_topic, light_msg)
                
                # Log control action if light is on
                if control.brightness_level > 0:
                    self.logger.info('control-output', 
                                   f'{control.mode.value} at {control.brightness_level:.1f}%',
                                   mode=control.mode.value,
                                   brightness_level=control.brightness_level,
                                   current_brightness=control.current_brightness)
                
                time.sleep(self.light_controller_config.control_interval)
                
            except Exception as e:
                self.logger.error('control-loop', f'error in control loop: {e}', error=str(e))
                time.sleep(5)  # Recovery delay
                
    def _send_ack(self, status: str, error: str, correlation_id: str):
        """Send acknowledgment message"""
        # Publish to actuator-specific ACK topic
        ack_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/light-actuator/ack"
        ack_msg = {
            "measurement": "ack",
            "tags": {
                "hotel_id": self.device_config.hotel_id,
                "room": self.device_config.room,
                "actuator": "light-actuator"
            },
            "fields": {"status": status, "error": error},
            "timestamp": now_ms(),
            "correlationId": correlation_id
        }
        self.mqtt_client.publish_telemetry(ack_topic, ack_msg)
        self.logger.info('ack-sent', f'sent acknowledgment: {status}',
                        status=status, correlation_id=correlation_id, topic=ack_topic)
