"""
Alert agent business logic for monitoring sensor/actuator health and telemetry.
Handles offline detection, command acknowledgment tracking, and rule-based alerts.
"""
import json
import time
import threading
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, get_logger, now_ms
import paho.mqtt.client as mqtt
import ulid

class AlertAgent:
    """Alert agent for monitoring room sensors and actuators"""
    
    def __init__(self, device_config, mqtt_config, alert_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config
        self.alert_config = alert_config
        self.logger = get_logger("alert-agent", device_config)
        
        # State tracking
        self.last_value = {}  # key -> last value tuple(s) for change detection
        self.last_seen = {}  # key -> last unix seconds seen
        self.dedupe = {}  # dedup_key -> last unix seconds emitted
        self.pending_commands = {}  # key -> (timestamp, command details)
        self.lock = threading.Lock()
        
        # Subscribe and publish topics
        self.sub_topic = os.getenv("MQTT_SUB", f"{device_config.hotel_id}/#")
        self.pub_prefix = os.getenv("MQTT_PUB", "alerts")
        
    def start(self):
        """Start alert agent operations"""
        self.logger.info('startup', 'started',
                        subscribe=self.sub_topic,
                        temp_high_c=self.alert_config.temp_high_c,
                        offline_timeout_s=self.alert_config.offline_timeout_s,
                        dedup_window_s=self.alert_config.dedup_window_s)
        
        # Create MQTT client
        client = mqtt.Client()
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        
        # Connect to MQTT
        client.connect(self.mqtt_config.broker, self.mqtt_config.port)
        
        self.client = client
        
        # Start offline watchdog thread
        watchdog = threading.Thread(target=self._offline_loop, daemon=True)
        watchdog.start()
        
        # Keep running
        try:
            client.loop_forever()
        except KeyboardInterrupt:
            self.logger.info('shutdown', 'stopping agent')
        finally:
            client.loop_stop()
            client.disconnect()
            
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        client.subscribe(self.sub_topic, qos=self.mqtt_config.qos)
        self.logger.info('connect', f'subscribed to {self.sub_topic}')
        
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        
        # Ignore our own alerts to avoid loops
        if payload.get("measurement") == "alert":
            return
        
        meas = payload.get("measurement")
        tags = payload.get("tags", {})
        key = self._device_key(tags)
        
        # Track commands sent to actuators
        if meas == "light-command":
            with self.lock:
                self.pending_commands[key] = (time.time(), payload)
            self.logger.info('command-tracked', f'Command tracked for {key}',
                           hotel_id=tags.get('hotel_id'),
                           room=tags.get('room'),
                           sensor=tags.get('sensor'),
                           command=payload.get('fields'))
            return
        
        # Heartbeat touch (for all other measurements)
        with self.lock:
            self.last_seen[key] = time.time()
        
        # If state/ack received, clear pending command
        if meas == "light-state":
            with self.lock:
                if key in self.pending_commands:
                    del self.pending_commands[key]
                    self.logger.info('command-ack', f'State/ack received for {key}, clearing pending command',
                                   hotel_id=tags.get('hotel_id'),
                                   room=tags.get('room'),
                                   sensor=tags.get('sensor'))
            self._handle_light_state(payload)
        elif meas == "temperature":
            self._handle_temperature(payload)
        elif meas == "humidity":
            self._handle_humidity(payload)
            
    def _handle_light_state(self, payload: dict):
        """Handle light state threshold violations only"""
        tags = payload.get("tags", {})
        fields = payload.get("fields", {})
        key = self._device_key(tags)
        
        # Brightness threshold checks
        b = fields.get("brightness")
        if isinstance(b, (int, float)):
            # Check for out of valid range
            if b < 0 or b > 100:
                dedup_key = f"brightness-oor:{key}:{b}"
                if self._should_emit(dedup_key):
                    self._publish_alert(
                        payload,
                        alert_type="brightness_out_of_range",
                        severity="warning",
                        message=f"Brightness out of range: {b}",
                        value=b
                    )
            # Check for high brightness
            elif b >= self.alert_config.light_high_pct:
                dedup_key = f"brightness-high:{key}:{int(b)}"
                if self._should_emit(dedup_key):
                    self._publish_alert(
                        payload,
                        alert_type="brightness_high",
                        severity="warning",
                        message=f"High brightness {b}%",
                        value=b
                    )
            # Check for low brightness
            elif b <= self.alert_config.light_low_pct:
                dedup_key = f"brightness-low:{key}:{int(b)}"
                if self._should_emit(dedup_key):
                    self._publish_alert(
                        payload,
                        alert_type="brightness_low",
                        severity="warning",
                        message=f"Low brightness {b}%",
                        value=b
                    )
                
    def _handle_temperature(self, payload: dict):
        """Handle temperature alerts"""
        tags = payload.get("tags", {})
        fields = payload.get("fields", {})
        key = self._device_key(tags)
        
        c = fields.get("temperatureC")
        if not isinstance(c, (int, float)):
            return
        
        # Check for high temperature
        if c >= self.alert_config.temp_high_c:
            dedup_key = f"temp-high:{key}:{int(c)}"
            if self._should_emit(dedup_key):
                self._publish_alert(
                    payload,
                    alert_type="temp_high",
                    severity="warning",
                    message=f"High temperature {c}°C",
                    value=c
                )
        
        # Check for low temperature
        if c <= self.alert_config.temp_low_c:
            dedup_key = f"temp-low:{key}:{int(c)}"
            if self._should_emit(dedup_key):
                self._publish_alert(
                    payload,
                    alert_type="temp_low",
                    severity="warning",
                    message=f"Low temperature {c}°C",
                    value=c
                )
                
    def _handle_humidity(self, payload: dict):
        """Handle humidity alerts"""
        tags = payload.get("tags", {})
        fields = payload.get("fields", {})
        key = self._device_key(tags)
        
        h = fields.get("humidityPercent")
        if not isinstance(h, (int, float)):
            return
            
        # Check for high humidity
        if h >= self.alert_config.humidity_high_pct:
            dedup_key = f"humidity-high:{key}:{int(h)}"
            if self._should_emit(dedup_key):
                self._publish_alert(
                    payload,
                    alert_type="humidity_high",
                    severity="warning",
                    message=f"High humidity {h}%",
                    value=h
                )
        # Check for low humidity
        elif h <= self.alert_config.humidity_low_pct:
            dedup_key = f"humidity-low:{key}:{int(h)}"
            if self._should_emit(dedup_key):
                self._publish_alert(
                    payload,
                    alert_type="humidity_low",
                    severity="warning",
                    message=f"Low humidity {h}%",
                    value=h
                )
                
    def _offline_loop(self, interval_s: int = 10):
        """Background thread to check for offline sensors and missed acks"""
        while True:
            time.sleep(interval_s)
            t = time.time()
            
            # Check for missed actuator acks (pending commands)
            with self.lock:
                expired_cmds = []
                for key, (cmd_time, cmd_payload) in list(self.pending_commands.items()):
                    age = t - cmd_time
                    if age >= self.alert_config.offline_timeout_s:
                        expired_cmds.append((key, age, cmd_payload, cmd_time))
                        
                for key, age, cmd_payload, cmd_time in expired_cmds:
                    hotel, room, sensor = key.split(":", 2)
                    dedup_key = f"missed-ack:{key}:{int(cmd_time)}"
                    if self._should_emit(dedup_key):
                        self._publish_alert(
                            cmd_payload,
                            alert_type="actuator_no_ack",
                            severity="critical",
                            message=f"No state/ack after command for {self.alert_config.offline_timeout_s}s (actuator offline)",
                            value=age
                        )
                        self.logger.warning('actuator-no-ack',
                                          f'No state/ack after command for {self.alert_config.offline_timeout_s}s',
                                          hotel_id=hotel, room=room, sensor=sensor, value=age)
                    del self.pending_commands[key]
                    
            # Check for regular sensor offline (no events at all)
            to_alert = []
            with self.lock:
                for key, last in list(self.last_seen.items()):
                    age = t - last
                    if age >= self.alert_config.offline_timeout_s:
                        to_alert.append((key, int(age)))
                        
            for key, age in to_alert:
                hotel, room, sensor = key.split(":", 2)
                fake_src = {
                    "measurement": "heartbeat",
                    "tags": {"hotel_id": hotel, "room": room, "sensor": sensor},
                    "fields": {"age_s": age},
                    "timestamp": now_ms()
                }
                dedup_key = f"offline:{key}:{self.alert_config.offline_timeout_s}"
                if self._should_emit(dedup_key):
                    self._publish_alert(
                        fake_src,
                        alert_type="sensor_offline",
                        severity="critical",
                        message=f"No events for {self.alert_config.offline_timeout_s}s (sensor offline)",
                        value=age
                    )
                    self.logger.warning('sensor-offline',
                                      f'sensor offline for {self.alert_config.offline_timeout_s}s',
                                      hotel_id=hotel, room=room, sensor=sensor, value=age)
                    
    def _device_key(self, tags: dict) -> str:
        """Generate device key from tags"""
        return f"{tags.get('hotel_id')}:{tags.get('room')}:{tags.get('sensor')}"
    
    def _should_emit(self, dedup_key: str) -> bool:
        """Check if alert should be emitted based on deduplication window"""
        t = time.time()
        last = self.dedupe.get(dedup_key)
        if last and (t - last) < self.alert_config.dedup_window_s:
            return False
        self.dedupe[dedup_key] = t
        return True
    
    def _publish_alert(self, src: dict, alert_type: str, severity: str, message: str, value=None):
        """Publish alert to MQTT"""
        tags = src.get("tags", {})
        out = {
            "measurement": "alert",
            "tags": {
                "hotel_id": tags.get("hotel_id", self.device_config.hotel_id),
                "room": tags.get("room", self.device_config.room),
                "sensor": tags.get("sensor", "unknown"),
                "alert_id": str(ulid.new())
            },
            "fields": {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "original_measurement": src.get("measurement"),
                "value": value,
                "origin": "room-alert-agent"
            },
            "timestamp": now_ms()
        }
        
        topic = f"{self.pub_prefix}/{out['tags']['hotel_id']}/{out['tags']['room']}/{out['tags']['sensor']}"
        self.client.publish(topic, json.dumps(out), qos=1, retain=False)
        
        # Log with appropriate level
        if severity.lower() in ('warning', 'critical'):
            self.logger.warning(alert_type, 'alert published',
                              hotel_id=out['tags']['hotel_id'],
                              room=out['tags']['room'],
                              sensor=out['tags']['sensor'],
                              value=value,
                              alert_id=out['tags']['alert_id'],
                              topic_out=topic)
        else:
            self.logger.info(alert_type, 'alert published',
                           hotel_id=out['tags']['hotel_id'],
                           room=out['tags']['room'],
                           sensor=out['tags']['sensor'],
                           value=value,
                           alert_id=out['tags']['alert_id'],
                           topic_out=topic)
