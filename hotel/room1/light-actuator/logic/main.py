# Import necessary libraries
import os, json, time
import paho.mqtt.client as mqtt

# -------------- Helper functions  --------------- #
def env_bool(name: str, default: bool) -> bool:
    """
    Read a boolean environment variable.
    Accepts: 1, true, yes, on (case insensitive) as True.
    Anything else (including unset) is False.

    Args:
        name (str): environment variable name
        default (bool): default value if unset
    Returns:
        bool: boolean value or default
    """
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def env_int(name: str, default: int) -> int:
    """
    Read an integer environment variable.
    Returns default if unset or malformed.

    Args:
        name (str): environment variable name
        default (int): default value if unset or malformed
    Returns:
        int: integer value or default
    """
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default

def clamp_0_100(v: int) -> int:
    """
    Clamp integer to 0-100 range.
    Values <0 become 0, >100 become 100.
    Used for brightness percentage.

    Args:
        v (int): input integer
    Returns:
        int: clamped integer
    """
    return 0 if v < 0 else 100 if v > 100 else v

def now_ms() -> int:
    """
    Current timestamp in milliseconds since epoch.
    Used for MQTT message timestamps.

    Returns an integer.
    """
    return int(time.time() * 1000)

def build_alert(hotel_id, room, sensor, kind: str, severity: str = "INFO"):
    """
    Build an alert/status message in the universal schema.

    Args:
        hotel_id (str): Hotel identifier
        room (str): Room identifier
        sensor (str): Device identifier (kept as 'sensor' for schema parity)
        kind (str): e.g., 'actuator_online' | 'actuator_offline'
        severity (str): e.g., 'INFO' | 'HIGH'

    Returns:
        dict: payload with measurement/tags/fields/timestamp
    """
    return {
        "measurement": "alert",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"kind": kind, "severity": severity},
        "timestamp": now_ms(),
    }

def build_ack(correlation_id, hotel_id, room, sensor, status, error=""):
    """
    Build an acknowledgment message.
    status: "ok", "failed", "rejected"
    error: error code or empty string
    correlation_id: echoes back the messageId from the command, if any
    hotel_id, room, sensor: identifiers for tags

    Returns a dict suitable for JSON serialization and MQTT publishing.
    """
    return {
        "measurement": "ack",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"status": status, "error": error},
        "timestamp": now_ms(),
        "correlationId": correlation_id,
    }

def build_state(hotel_id, room, sensor, on: bool, brightness: int):

    """
    Build a state message.
    on: boolean, light is on or off
    brightness: integer 0-100
    hotel_id, room, sensor: identifiers for tags
    
    Returns a dict suitable for JSON serialization and MQTT publishing.
    """
    return {
        "measurement": "state",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"on": on, "brightness": brightness},
        "timestamp": now_ms(),
    }

# -------------- Main logic  --------------- #

# Configuration from environment variables
HOTEL_ID = os.environ.get("HOTEL_ID", "hotel_01")
ROOM = str(os.environ.get("ROOM", "101"))
SENSOR = os.environ.get("SENSOR", "light-actuator")
BROKER = os.environ.get("BROKER", "mqtt-broker")
BROKER_PORT = int(os.environ.get("BROKER_PORT", 1883))
QOS = int(os.environ.get("QOS", 1))
KEEPALIVE = int(os.environ.get("KEEPALIVE", 60))
INITIAL_ON = env_bool("INITIAL_ON", True)
INITIAL_BRIGHTNESS = clamp_0_100(env_int("INITIAL_BRIGHTNESS", 100))

# MQTT topics
BASE = f"{HOTEL_ID}/{ROOM}/{SENSOR}"
TOPIC_CMD = f"{BASE}/cmd"
TOPIC_ACK = f"{BASE}/ack"
TOPIC_STATE = f"{BASE}/state"
TOPIC_STATUS = f"{BASE}/status"

# Global state
light_on = INITIAL_ON
brightness = INITIAL_BRIGHTNESS

# MQTT client setup
client = mqtt.Client(protocol=mqtt.MQTTv311, clean_session=True, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.will_set(
    TOPIC_STATUS,
    payload=json.dumps(build_alert(HOTEL_ID, ROOM, SENSOR, kind="actuator_offline", severity="HIGH")),
    qos=1,
    retain=False,
)

def on_connect(client, userdata, flags, reason_code, properties):
    """
    MQTT on_connect callback.
    Publishes initial status and state, subscribes to command topic.
    """
    print(f"Connected to MQTT with reason_code={reason_code}")
    online_msg = build_alert(HOTEL_ID, ROOM, SENSOR, kind="actuator_online", severity="INFO")
    client.publish(TOPIC_STATUS, json.dumps(online_msg), qos=1, retain=False)
    boot = build_state(HOTEL_ID, ROOM, SENSOR, light_on, brightness)
    client.publish(TOPIC_STATE, json.dumps(boot), qos=QOS, retain=True)
    client.subscribe(TOPIC_CMD, qos=QOS)
    print(f"Connected. Subscribed to {TOPIC_CMD}")

def on_message(client, userdata, msg):
    """
    MQTT on_message callback.
    Processes incoming messages on the command topic.
    Expects JSON payload with "fields" containing "action" and optional "value".
    Valid actions: "on", "off", "toggle", "set_brightness"
    Publishes acknowledgment and updated state.

    Args:
        client: MQTT client instance
        userdata: user data (not used)
        msg: MQTT message instance with topic and payload
    
    Returns: None
    """
    # MQTT message processing
    global light_on, brightness
    
    # Only process messages on the command topic
    try:
        data = json.loads(msg.payload.decode("utf-8")) if msg.payload else {}
    except Exception:
        # Debug log to help identify malformed publishers
        try:
            raw = msg.payload.decode("utf-8", errors="replace") if msg.payload else "<empty>"
        except Exception:
            raw = str(msg.payload)
        print(f"Malformed JSON on topic={msg.topic}: payload={raw}")
        ack = build_ack(None, HOTEL_ID, ROOM, SENSOR, status="failed", error="malformed_json")
        client.publish(TOPIC_ACK, json.dumps(ack), qos=QOS, retain=False)
        return

    # Extract action and correlation ID
    fields = data.get("fields") or {}
    action = (fields.get("action") or "").lower()
    corr = data.get("messageId")

    # Validate action
    if action not in ("on", "off", "toggle", "set_brightness"):
        ack = build_ack(corr, HOTEL_ID, ROOM, SENSOR, status="rejected", error=f"unsupported_action:{action}")
        client.publish(TOPIC_ACK, json.dumps(ack), qos=QOS, retain=False)
        return

    # Execute action
    before_on, before_bri = light_on, brightness

    # Change state based on action
    if action == "on":
        light_on = True
        if brightness == 0:
            brightness = 100
    elif action == "off":
        light_on = False
    elif action == "toggle":
        light_on = not light_on
        if light_on and brightness == 0:
            brightness = 100
    else:
        try:
            value = int(fields.get("value"))
        except Exception:
            value = None
        if value is None:
            ack = build_ack(corr, HOTEL_ID, ROOM, SENSOR, status="failed", error="missing_value")
            client.publish(TOPIC_ACK, json.dumps(ack), qos=QOS, retain=False)
            return
        brightness = clamp_0_100(value)
        light_on = brightness > 0

    # Publish acknowledgment and new state
    ack = build_ack(corr, HOTEL_ID, ROOM, SENSOR, status="ok", error="")
    client.publish(TOPIC_ACK, json.dumps(ack), qos=QOS, retain=False)

    # Publish updated state
    state = build_state(HOTEL_ID, ROOM, SENSOR, light_on, brightness)
    client.publish(TOPIC_STATE, json.dumps(state), qos=QOS, retain=True)

    # Log state change
    print(f"cmd={action} before_on={before_on} before_bri={before_bri} after_on={light_on} after_bri={brightness} → ack+state emitted")

def main():
    """
    Main entry point.
    Sets up MQTT client and starts the network loop.

    Returns: None
    """
    client.on_connect = on_connect
    client.on_message = on_message

    # Robust MQTT connect with retries
    attempts, max_attempts, delay = 0, int(os.environ.get("MQTT_MAX_ATTEMPTS", "30")), float(os.environ.get("MQTT_RETRY_DELAY", "2"))
    while True:
        try:
            attempts += 1
            print(f"[mqtt] connecting to {BROKER}:{BROKER_PORT} (attempt {attempts}/{max_attempts})")
            client.connect(BROKER, BROKER_PORT, KEEPALIVE)
            print("[mqtt] connected")
            break
        except Exception as e:
            if attempts >= max_attempts:
                raise
            print(f"[mqtt] connect failed: {e}; retrying in {delay}s...")
            time.sleep(delay)

    client.loop_forever()

if __name__ == "__main__":
    main()
