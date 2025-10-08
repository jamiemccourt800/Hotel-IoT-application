import json
import time
import threading
from typing import List, Tuple

import paho.mqtt.client as mqtt

from core.messages import build_ack
from core.state import SimulatorState

class MqttIO:
    """
    Robust MQTT wrapper with:
    - LWT (Last Will & Testament) → sensor_offline alert on unexpected death
    - Auto reconnect with exponential backoff
    - Small publish buffer to survive brief outages
    - Configurable QoS/retain/keepalive
    """
    def __init__(self, broker, port, hotel_id, room, sensor, qos, retain, keepalive, state: SimulatorState):
        self.broker = broker
        self.port = port
        self.qos = qos
        self.retain = bool(retain)
        self.keepalive = keepalive
        self.state = state

        base = f"{hotel_id}/{room}/{sensor}"
        self.t_telemetry = f"telemetry/{base}"
        self.t_alerts   = f"alerts/{base}"
        self.t_acks     = f"acks/{base}"
        self.t_cmds     = f"commands/{base}"

        self.client = mqtt.Client(
            client_id="iot-sim",
            protocol=mqtt.MQTTv311,
            transport="tcp",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self.client.enable_logger()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # LWT payload (sensor_offline due to unexpected disconnect)
        lwt_payload = json.dumps({
            "measurement": "alert",
            "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
            "fields": {"severity": "HIGH", "kind": "sensor_offline", "detail_reason": "LWT"},
            "timestamp": int(time.time())
        })
        self.client.will_set(self.t_alerts, lwt_payload, qos=self.qos, retain=self.retain)

        # connection state
        self._connected = False
        self._stopping = False

        # simple bounded buffer for unsent publishes
        self._buffer: List[Tuple[str, str, int, bool]] = []  # (topic, payload_json, qos, retain)
        self._buffer_max = 200
        self._buf_lock = threading.Lock()

        # reconnect control
        self._reconnect_thread = None

    def connect(self):
        print(f"[MQTT] connecting to {self.broker}:{self.port} keepalive={self.keepalive}", flush=True)
        self.client.connect(self.broker, self.port, keepalive=self.keepalive)
        self.client.subscribe(self.t_cmds, qos=self.qos)
        self.client.loop_start()

    def close(self):
        """Stop loops and disconnect cleanly."""
        self._stopping = True
        # try flush before disconnect; if disconnected, nothing to flush
        if self._connected:
            self.flush_buffer()
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    # ---------- Callbacks ----------
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self._connected = True
        # On (re)connect, resubscribe and flush buffer
        self.client.subscribe(self.t_cmds, qos=self.qos)
        print(f"[MQTT] on_connect reason_code={reason_code}", flush=True)
        self.flush_buffer()

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"[MQTT] on_disconnect reason_code={reason_code}", flush=True)
        self._connected = False
        if self._stopping:
            return
        # Fire a reconnect thread with exponential backoff
        if self._reconnect_thread is None or not self._reconnect_thread.is_alive():
            self._reconnect_thread = threading.Thread(target=self._reconnect_with_backoff, daemon=True)
            self._reconnect_thread.start()

    def _reconnect_with_backoff(self):
        backoff = 1.0
        max_backoff = 60.0
        while not self._stopping and not self._connected:
            try:
                self.client.reconnect()
                time.sleep(0.2)
            except Exception:
                time.sleep(backoff)
                backoff = min(max_backoff, backoff * 2)
            else:
                backoff = 1.0

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            self.publish_alert({}, "LOW", "cmd_malformed", {"raw": str(msg.payload[:200])})
            return

        action = payload.get("action")
        correlation_id = payload.get("correlationId")

        if action == "setTargetTemp":
            val = payload.get("value")
            ok = isinstance(val, (int, float))
            if ok:
                self.state.targetTemp = float(val)
            self._ack(correlation_id, ok, f"targetTemp={self.state.targetTemp}")

        elif action == "toggleLight":
            self.state.lightOn = not self.state.lightOn
            self._ack(correlation_id, True, f"lightOn={self.state.lightOn}")

        elif action == "reset":
            self.state.pause_until = 0
            self._ack(correlation_id, True, "reset OK")

        elif action == "simulateDrop":
            dur = payload.get("duration", 10)
            try:
                d = int(dur)
                self.state.pause_until = time.time() + d
                self._ack(correlation_id, True, f"simulateDrop {d}s")
                self.publish_alert({}, "MEDIUM", "simulated_drop", {"duration": d})
            except Exception:
                self._ack(correlation_id, False, "invalid duration")

        else:
            self._ack(correlation_id, False, f"unknown action: {action}")

    # ---------- Publish helpers ----------
    def _publish_or_buffer(self, topic: str, payload_json: str, qos: int = None, retain: bool = None):
        qos = self.qos if qos is None else qos
        retain = self.retain if retain is None else retain
        if self._connected:
            self.client.publish(topic, payload_json, qos=qos, retain=retain)
        else:
            with self._buf_lock:
                if len(self._buffer) >= self._buffer_max:
                    self._buffer.pop(0)  # drop oldest
                self._buffer.append((topic, payload_json, qos, retain))

    def flush_buffer(self):
        if not self._connected:
            return
        with self._buf_lock:
            while self._buffer:
                topic, payload_json, qos, retain = self._buffer.pop(0)
                self.client.publish(topic, payload_json, qos=qos, retain=retain)

    def publish_telemetry(self, payload: dict):
        self._publish_or_buffer(self.t_telemetry, json.dumps(payload))

    def publish_alert(self, tags: dict, severity: str, kind: str, details: dict):
        data = {
            "measurement": "alert",
            "tags": tags,
            "fields": {"severity": severity, "kind": kind, **{f"detail_{k}": v for k, v in details.items()}},
            "timestamp": int(time.time())
        }
        self._publish_or_buffer(self.t_alerts, json.dumps(data))

    def _ack(self, correlation_id, ok: bool, message: str):
        ack = build_ack(correlation_id, "OK" if ok else "ERROR", message)
        self._publish_or_buffer(self.t_acks, json.dumps(ack))
