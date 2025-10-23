import os, time, json, random, argparse
import paho.mqtt.client as mqtt

# --- Logging ---
def log(level, event, msg, **fields):
    ts = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + f'.{int(time.time()*1000)%1000:03d}Z'
    service = 'sensor'
    hotel = fields.pop('hotel_id', None)
    room = fields.pop('room', None)
    sensor = fields.pop('sensor', None)
    device = f'{hotel}/{room}/{sensor}' if hotel and room and sensor else ''
    base = [ts, f'{level.upper():<5}', service, f'{device:<28}', f'event={event}', f'msg="{msg}"']
    for k, v in fields.items():
        if isinstance(v, bool):
            v = str(v).lower()
        base.append(f'{k}={v}')
    print(' | '.join(base), flush=True)

def build_payload(hotel_id, room, sensor, temp_c, ts):
    """
    Build telemetry payload.

    The simulator historically emitted timestamps in seconds. Telegraf's
    configuration in this project expects unix_ms (milliseconds). To avoid
    timestamp parsing issues, emit milliseconds here.

    Return: dict
    """
    # Normalize timestamp to unix_ms
    try:
        ts_val = int(float(ts))
    except (TypeError, ValueError):
        # fall back to current time in milliseconds
        ts_val = int(time.time() * 1000)
    ts = ts_val * 1000 if ts_val < 1_000_000_000_000 else ts_val

    # Coerce and validate room id (must be integer)
    try:
        room_id = int(room)
    except Exception:
        raise TypeError("room must be an integer")

    # Coerce and validate temperature
    try:
        temp_f = float(temp_c)
    except Exception:
        # Non-numeric temperature
        raise TypeError("temperature must be a number")

    # Acceptable physical range for our sensors
    if not (-50.0 <= temp_f <= 120.0):
        raise ValueError("temperature out of allowed range")

    # Returns a dict like:
    return {
        "measurement": "temperature",
        "tags": {
            "hotel_id": str(hotel_id),
            "room": room_id,
            "sensor": str(sensor)
        },
        "fields": {"temperatureC": temp_f},
        "timestamp": int(ts)
    }

def main():
    """
     Simple temperature sensor simulator.
     
     Publishes telemetry to MQTT broker.
     Supports two modes:
     - random: generates a random walk around a target temperature
     - csv: reads from a CSV file with lines: timestamp,temperatureC
     """
    
    # Parse command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["random", "csv"], default=os.getenv("MODE", "random"))
    parser.add_argument("--interval", type=float, default=float(os.getenv("INTERVAL", "1.0")))
    parser.add_argument("--csv", default=os.getenv("CSV_PATH", ".data/telemetry.csv"))
    parser.add_argument("--speed", type=float, default=float(os.getenv("SPEED", "1.0")))
    args = parser.parse_args()

    # Config from env
    hotel_id = os.getenv("HOTEL_ID", "hotel1")
    room = os.getenv("ROOM", "1")
    sensor = os.getenv("SENSOR", "temperature-sensor")
    broker = (
        os.getenv("MQTT_HOST")
        or os.getenv("MQTT_BROKER")
        or os.getenv("BROKER")
        or "mosquitto"
    )
    port = int(os.getenv("MQTT_PORT") or os.getenv("BROKER_PORT") or "1883")
    qos = int(os.getenv("MQTT_QOS") or os.getenv("QOS") or "1")
    log('INFO', 'startup', 'started', hotel_id=hotel_id, room=room, sensor=sensor, mode=args.mode, interval_s=args.interval, qos=qos, broker=f'{broker}:{port}')

    # MQTT config
    broker = (
        os.getenv("MQTT_HOST")
        or os.getenv("MQTT_BROKER")
        or os.getenv("BROKER")
        or "mosquitto"
    )
    port = int(os.getenv("MQTT_PORT") or os.getenv("BROKER_PORT") or "1883")
    qos = int(os.getenv("MQTT_QOS") or os.getenv("QOS") or "1")
    keepalive = int(os.getenv("MQTT_KEEPALIVE") or os.getenv("KEEPALIVE") or "60")

    # MQTT topics (overridable via env)
    base_topic = os.getenv("MQTT_BASE_TOPIC", f"{hotel_id}/{room}/{sensor}")
    topic_telemetry = os.getenv("MQTT_TOPIC_TELEMETRY", f"{base_topic}/telemetry")
    topic_status = os.getenv("MQTT_TOPIC_STATUS", f"{base_topic}/status")

    # MQTT client setup
    lwt = json.dumps({
        "measurement": "alert",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"kind": "sensor_offline", "severity": "HIGH"},
            "timestamp": int(time.time() * 1000)
    })

    # Create MQTT client
    client = mqtt.Client(client_id=f"{sensor}")
    client.will_set(topic_status, payload=lwt, qos=1, retain=False)

    # Robust connect with retries
    attempts, max_attempts, delay = 0, int(os.getenv("MQTT_MAX_ATTEMPTS", "30")), float(os.getenv("MQTT_RETRY_DELAY", "2"))
    while True:
        try:
            attempts += 1
            log('INFO', 'connect-attempt', f'connecting to {broker}:{port}', hotel_id=hotel_id, room=room, sensor=sensor, attempt=attempts, max_attempts=max_attempts)
            client.connect(broker, port, keepalive)
            client.loop_start()
            log('INFO', 'connect', 'mqtt connected', hotel_id=hotel_id, room=room, sensor=sensor)
            break
        except Exception as e:
            if attempts >= max_attempts:
                log('ERROR', 'mqtt-connect-exhausted', f'failed to connect after {max_attempts} attempts', hotel_id=hotel_id, room=room, sensor=sensor, error=str(e))
                raise
            log('WARNING', 'mqtt-connect-retry', f'connect failed: {e}; retrying in {delay}s', hotel_id=hotel_id, room=room, sensor=sensor, error=str(e))
            time.sleep(delay)

    # On start, publish sensor_online alert
    client.publish(topic_status, json.dumps({
        "measurement": "alert",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"kind": "sensor_online", "severity": "INFO"},
            "timestamp": int(time.time() * 1000)
    }), qos=1)


    def csv_source():
        """
        Generator reading from CSV file.
        If file not found, switches to random source.
        """
        try:
            with open(args.csv, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    ts, temp = line.split(",")
                    yield int(ts), float(temp)
        except FileNotFoundError:
            print(f"CSV not found at {args.csv}, switching to random mode.")
            yield from random_source()

    def random_source():

        """
        Generator producing random walk temperature readings.
        """

        # Start around START_TEMP, walk towards TARGET_TEMP
        temp = float(os.getenv("START_TEMP", "21.0"))
        target = float(os.getenv("TARGET_TEMP", "21.0"))
        while True:
            temp += (target - temp) * 0.1
            temp += random.uniform(-0.2, 0.2)
            temp = round(temp, 2)
            yield int(time.time() * 1000), temp
            time.sleep(max(args.interval / max(args.speed, 0.01), 0.01))

    # Choose source
    source = csv_source() if args.mode == "csv" else random_source()

    # Main loop: publish telemetry
    log('INFO', 'publishing', f'publishing telemetry to {topic_telemetry}', hotel_id=hotel_id, room=room, sensor=sensor, topic_out=topic_telemetry)
    published_count = 0
    try:
        for ts, temp_c in source:
            payload = build_payload(hotel_id, room, sensor, temp_c, ts)
            client.publish(topic_telemetry, json.dumps(payload), qos=qos)
            published_count += 1
            # No per-message telemetry logs (per requirements)
    except KeyboardInterrupt:
        log('INFO', 'shutdown', 'stopping sensor', hotel_id=hotel_id, room=room, sensor=sensor)
    finally:
        client.loop_stop()
        client.disconnect()
        log('INFO', 'shutdown', 'sensor disconnected cleanly', hotel_id=hotel_id, room=room, sensor=sensor, published_count=published_count)

if __name__ == "__main__":
    main()
