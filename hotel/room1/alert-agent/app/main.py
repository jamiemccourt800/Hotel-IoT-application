import json, os, time, threading
from collections import defaultdict
import paho.mqtt.client as mqtt
import ulid

# --- Env config ---
BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT   = int(os.getenv("MQTT_PORT", "1883"))
SUB    = os.getenv("MQTT_SUB",  "sensors/#")      # subscribe alongside devices
PUB    = os.getenv("MQTT_PUB",  "sensors")        # publish alerts into same path
HOTEL  = os.getenv("HOTEL_ID",  "hotel_01")
ROOM   = os.getenv("ROOM",      "101")
TEMP_HIGH_C = float(os.getenv("TEMP_HIGH_C", "28"))
OFFLINE_TIMEOUT_S = int(os.getenv("OFFLINE_TIMEOUT_S", "120"))
DEDUP_WINDOW_S = int(os.getenv("DEDUP_WINDOW_S", "60"))

# --- State ---
LAST_VALUE = {}                 # key -> last value tuple(s) for change detection
LAST_SEEN  = {}                 # key -> last unix seconds seen
DEDUPE     = {}                 # dedup_key -> last unix seconds emitted
LOCK = threading.Lock()

# --- Utils ---
now_ms = lambda: int(time.time() * 1000)
now_s  = lambda: time.time()

def device_key(tags: dict) -> str:
    return f"{tags.get('hotel_id')}:{tags.get('room')}:{tags.get('sensor')}"

def should_emit(dedup_key: str) -> bool:
    t = now_s()
    last = DEDUPE.get(dedup_key)
    if last and (t - last) < DEDUP_WINDOW_S:
        return False
    DEDUPE[dedup_key] = t
    return True

def publish_alert(client: mqtt.Client, src: dict, alert_type: str, severity: str, message: str, value=None):
    tags = src.get("tags", {})
    out = {
        "measurement": "alert",
        "tags": {
            "hotel_id": tags.get("hotel_id", HOTEL),
            "room":     tags.get("room", ROOM),
            "sensor":   tags.get("sensor", "unknown"),
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
    topic = f"{PUB}/{out['tags']['hotel_id']}/{out['tags']['room']}/{out['tags']['sensor']}"
    client.publish(topic, json.dumps(out), qos=1, retain=False)

# --- Handlers ---

def on_connect(c: mqtt.Client, _u, _f, _rc):
    c.subscribe(SUB, qos=1)


def handle_light_state(client: mqtt.Client, payload: dict):
    tags = payload.get("tags", {})
    fields = payload.get("fields", {})
    key = device_key(tags)

    # change detection on (state, brightness)
    state_tuple = (fields.get("state"), fields.get("brightness"))
    last = LAST_VALUE.get((key, "light-state"))
    if last != state_tuple:
        LAST_VALUE[(key, "light-state")] = state_tuple
        dedup_key = f"light-change:{key}:{state_tuple}"
        if should_emit(dedup_key):
            publish_alert(
                client, payload,
                alert_type="actuator_state_changed",
                severity="info",
                message=f"Light → {state_tuple[0]} (brightness={state_tuple[1]})",
                value=state_tuple[1]
            )

    # brightness range
    b = fields.get("brightness")
    if isinstance(b, (int, float)) and (b < 0 or b > 100):
        dedup_key = f"brightness-oor:{key}:{b}"
        if should_emit(dedup_key):
            publish_alert(
                client, payload,
                alert_type="brightness_out_of_range",
                severity="warning",
                message=f"Brightness out of range: {b}",
                value=b
            )


def handle_temperature(client: mqtt.Client, payload: dict):
    tags = payload.get("tags", {})
    fields = payload.get("fields", {})
    key = device_key(tags)

    c = fields.get("temperatureC")
    if isinstance(c, (int, float)) and c >= TEMP_HIGH_C:
        dedup_key = f"temp-high:{key}:{int(c)}"
        if should_emit(dedup_key):
            publish_alert(
                client, payload,
                alert_type="temp_high",
                severity="warning",
                message=f"High temperature {c}°C",
                value=c
            )


def on_message(client: mqtt.Client, _u, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        return

    # ignore our own alerts to avoid loops
    if payload.get("measurement") == "alert":
        return

    meas = payload.get("measurement")
    tags = payload.get("tags", {})

    # heartbeat touch
    key = device_key(tags)
    with LOCK:
        LAST_SEEN[key] = now_s()

    # route by measurement
    if meas == "light-state":
        handle_light_state(client, payload)
    elif meas == "temperature":
        handle_temperature(client, payload)


# --- Offline watchdog ---

def offline_loop(client: mqtt.Client, interval_s: int = 10):
    while True:
        time.sleep(interval_s)
        t = now_s()
        to_alert = []
        with LOCK:
            for key, last in list(LAST_SEEN.items()):
                age = t - last
                if age >= OFFLINE_TIMEOUT_S:
                    to_alert.append((key, int(age)))
        for key, age in to_alert:
            hotel, room, sensor = key.split(":", 2)
            fake_src = {
                "measurement": "heartbeat",
                "tags": {"hotel_id": hotel, "room": room, "sensor": sensor},
                "fields": {"age_s": age},
                "timestamp": now_ms()
            }
            dedup_key = f"offline:{key}:{OFFLINE_TIMEOUT_S}"
            if should_emit(dedup_key):
                publish_alert(
                    client, fake_src,
                    alert_type="sensor_offline",
                    severity="critical",
                    message=f"No events for {OFFLINE_TIMEOUT_S}s (sensor offline)",
                    value=age
                )


# --- Main ---

def main():
    client = mqtt.Client()
    client.enable_logger()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)

    # start offline watchdog thread
    th = threading.Thread(target=offline_loop, args=(client,), daemon=True)
    th.start()

    client.loop_forever()

if __name__ == "__main__":
    main()