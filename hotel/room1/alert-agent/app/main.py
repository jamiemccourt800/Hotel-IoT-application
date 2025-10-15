import json, os, time, threading
from collections import defaultdict
import paho.mqtt.client as mqtt
import ulid

# --- Logging ---
def log(level, event, msg, **fields):
    ts = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + f'.{int(time.time()*1000)%1000:03d}Z'
    service = 'alert-agent'
    base = [ts, f'{level.upper():<5}', service]
    hotel = fields.pop('hotel_id', HOTEL)
    room = fields.pop('room', ROOM)
    sensor = fields.pop('sensor', None)
    device = f'{hotel}/{room}/{sensor}' if sensor else f'{hotel}/{room}'
    base.append(f'{device:<28}')
    base.append(f'event={event}')
    base.append(f'msg="{msg}"')
    for k, v in fields.items():
        if isinstance(v, bool):
            v = str(v).lower()
        base.append(f'{k}={v}')
    print(' | '.join(base), flush=True)

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
PENDING_COMMANDS = {}           # key -> (timestamp, command details)
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
    log(
        'WARNING' if severity.lower() in ('warning','critical') else 'INFO',
        alert_type,
        'alert published',
        hotel_id=out['tags']['hotel_id'],
        room=out['tags']['room'],
        sensor=out['tags']['sensor'],
        value=value,
        alert_id=out['tags']['alert_id'],
        topic_out=topic
    )

# --- Handlers ---

def on_connect(c: mqtt.Client, _u, _f, _rc):
    c.subscribe(SUB, qos=1)
    log('INFO', 'connect', f'subscribed to {SUB}', hotel_id=HOTEL, room=ROOM)


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
    key = device_key(tags)

    # Track commands sent to actuators (e.g., light-actuator)
    if meas == "light-command":
        # Record the time and command details
        with LOCK:
            PENDING_COMMANDS[key] = (now_s(), payload)
        log('INFO', 'command-tracked', f'Command tracked for {key}', hotel_id=tags.get('hotel_id'), room=tags.get('room'), sensor=tags.get('sensor'), command=payload.get('fields'))
        return

    # heartbeat touch (for all other measurements)
    with LOCK:
        LAST_SEEN[key] = now_s()

    # If a state/ack is received, clear any pending command for this actuator
    if meas == "light-state":
        with LOCK:
            if key in PENDING_COMMANDS:
                del PENDING_COMMANDS[key]
                log('INFO', 'command-ack', f'State/ack received for {key}, clearing pending command', hotel_id=tags.get('hotel_id'), room=tags.get('room'), sensor=tags.get('sensor'))
        handle_light_state(client, payload)
    elif meas == "temperature":
        handle_temperature(client, payload)


# --- Offline & Command watchdog ---

def offline_loop(client: mqtt.Client, interval_s: int = 10):
    while True:
        time.sleep(interval_s)
        t = now_s()
        to_alert = []
        # Check for missed actuator acks (pending commands)
        with LOCK:
            expired_cmds = []
            for key, (cmd_time, cmd_payload) in list(PENDING_COMMANDS.items()):
                age = t - cmd_time
                if age >= OFFLINE_TIMEOUT_S:
                    expired_cmds.append((key, age, cmd_payload))
            for key, age, cmd_payload in expired_cmds:
                hotel, room, sensor = key.split(":", 2)
                dedup_key = f"missed-ack:{key}:{int(cmd_time)}"
                if should_emit(dedup_key):
                    publish_alert(
                        client, cmd_payload,
                        alert_type="actuator_no_ack",
                        severity="critical",
                        message=f"No state/ack after command for {OFFLINE_TIMEOUT_S}s (actuator offline)",
                        value=age
                    )
                    log('WARNING', 'actuator-no-ack', f'No state/ack after command for {OFFLINE_TIMEOUT_S}s', hotel_id=hotel, room=room, sensor=sensor, value=age)
                del PENDING_COMMANDS[key]
        # Check for regular sensor offline (no events at all)
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
                log('WARNING', 'sensor-offline', f'sensor offline for {OFFLINE_TIMEOUT_S}s', hotel_id=hotel, room=room, sensor=sensor, value=age)


# --- Main ---

def main():
    log('INFO', 'startup', 'started', hotel_id=HOTEL, room=ROOM, sensor=None, subscribe=SUB, temp_high_c=TEMP_HIGH_C, offline_timeout_s=OFFLINE_TIMEOUT_S, dedup_window_s=DEDUP_WINDOW_S)
    client = mqtt.Client()
    # client.enable_logger()  # disable paho default logging
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)

    # start offline watchdog thread
    th = threading.Thread(target=offline_loop, args=(client,), daemon=True)
    th.start()

    client.loop_forever()

if __name__ == "__main__":
    main()