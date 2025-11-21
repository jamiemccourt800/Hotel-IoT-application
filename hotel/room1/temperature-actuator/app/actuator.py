"""
Temperature actuator business logic for HVAC control.
Completes the temperature control loop by managing thermostat setpoints.
"""
import asyncio
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, TemperatureTelemetry, MessageTags, get_logger, now_ms
from thermostat import ThermostatController, ControlOutput

class TemperatureActuator:
    """Temperature actuator for HVAC/thermostat control"""
    
    def __init__(self, device_config, mqtt_config, thermostat_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config
        self.thermostat_config = thermostat_config
        self.logger = get_logger("temperature-actuator", device_config)
        
        # Initialize components
        self.mqtt_client = HotelMQTTClient(mqtt_config, "temperature-actuator", device_config)
        self.thermostat = ThermostatController(thermostat_config)
        
    def start(self):
        """Start temperature actuator operations"""
        self.logger.info('startup', 'started',
                        default_target=self.thermostat_config.default_target,
                        control_interval=self.thermostat_config.control_interval)
        
        # Connect to MQTT
        client = self.mqtt_client.connect_with_retries()
        
        # Set up MQTT topics
        base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
        
        # Subscribe to thermostat commands from central system
        cmd_topic = f"commands/temperature/{base_room}/{self.device_config.sensor}"
        client.subscribe(cmd_topic, qos=self.mqtt_config.qos)
        
        # Subscribe to temperature sensor readings for feedback control
        sensor_topic = f"{base_room}/temperature-sensor/telemetry"
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
        
        # Keep running
        try:
            client.loop_forever()
        except KeyboardInterrupt:
            self.logger.info('shutdown', 'stopping actuator')
        finally:
            client.loop_stop()
            client.disconnect()
            
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            data = json.loads(msg.payload.decode())
            
            if "/commands/temperature/" in msg.topic:
                # Handle thermostat commands
                self._process_command(data, msg.topic)
            elif "/temperature-sensor/telemetry" in msg.topic:
                # Handle temperature sensor readings
                self._process_temperature_reading(data, msg.topic)
                
        except Exception as e:
            self.logger.error('message-error', f'error processing message: {e}',
                            error=str(e), topic=msg.topic)
            
    def _process_command(self, command: dict, topic: str):
        """Process thermostat command (set target temperature, mode)"""
        fields = command.get("fields", {})
        correlation_id = command.get("correlationId")
        
        try:
            if "target_temperature" in fields:
                target = float(fields["target_temperature"])
                self.thermostat.set_target_temperature(target)
                self.logger.info('command-processed', f'set target temperature to {target}°C',
                               target_temp=target, correlation_id=correlation_id)
                               
            if "mode" in fields:
                mode = fields["mode"]
                self.thermostat.set_mode(mode)
                self.logger.info('command-processed', f'set mode to {mode}',
                               mode=mode, correlation_id=correlation_id)
                               
            # Send acknowledgment
            self._send_ack("ok", "", correlation_id)
            
        except Exception as e:
            self.logger.error('command-error', f'error processing command: {e}',
                            error=str(e), correlation_id=correlation_id)
            self._send_ack("failed", str(e), correlation_id)
            
    def _process_temperature_reading(self, telemetry: dict, topic: str):
        """Update thermostat with current temperature for feedback control"""
        try:
            fields = telemetry.get("fields", {})
            if "temperatureC" in fields:
                temp = float(fields["temperatureC"])
                self.thermostat.update_current_temperature(temp)
                # Note: No per-message logging to avoid spam
        except Exception as e:
            self.logger.error('sensor-reading', f'error processing temperature reading: {e}',
                            error=str(e), topic=topic)
            
    def _control_loop(self, client):
        """Continuous HVAC control based on temperature feedback"""
        base_room = f"{self.device_config.hotel_id}/{self.device_config.room}"
        setpoint_topic = f"{base_room}/thermostat"
        hvac_topic = f"{base_room}/hvac-status"
        
        while True:
            try:
                # Calculate control output
                control = self.thermostat.calculate_control_output()
                
                # Publish setpoint update for temperature sensor
                setpoint_msg = {
                    "target_temperature": control.target_temperature,
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(setpoint_topic, setpoint_msg)
                
                # Publish HVAC status
                hvac_msg = {
                    "measurement": "hvac-status",
                    "tags": {
                        "hotel_id": self.device_config.hotel_id,
                        "room": self.device_config.room,
                        "sensor": self.device_config.sensor
                    },
                    "fields": {
                        "mode": control.mode.value,
                        "power_level": control.power_level,
                        "target_temperature": control.target_temperature,
                        "current_temperature": control.current_temperature
                    },
                    "timestamp": now_ms()
                }
                self.mqtt_client.publish_telemetry(hvac_topic, hvac_msg)
                
                # Log control action if HVAC is active
                if control.power_level > 0:
                    self.logger.info('control-output', 
                                   f'{control.mode.value} at {control.power_level:.1f}%',
                                   mode=control.mode.value,
                                   power_level=control.power_level,
                                   target_temp=control.target_temperature,
                                   current_temp=control.current_temperature)
                
                time.sleep(self.thermostat_config.control_interval)
                
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