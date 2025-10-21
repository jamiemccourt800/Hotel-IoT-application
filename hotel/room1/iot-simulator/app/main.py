#!/usr/bin/env python3
import argparse
import os
import sys
import time
import threading

from mqtt.mqtt_io import MqttIO
from core.messages import build_telemetry
from core.state import SimulatorState
from sources.csv_source import csv_rows
from services.sensor_monitor import monitor_loop

def random_source(state: SimulatorState, interval_s: float):
    """Very small random walk around targetTemp."""
    import random
    while True:
        state.temperatureC += (state.targetTemp - state.temperatureC) * 0.1
        state.temperatureC += random.uniform(-0.2, 0.2)
        state.temperatureC = round(state.temperatureC, 2)
        yield int(time.time()), state.temperatureC
        time.sleep(interval_s)

def main():
    p = argparse.ArgumentParser("Hotel IoT Simulator (modular)")
    p.add_argument("--mode", choices=["random", "csv"], default="random")
    p.add_argument("--csv", help="CSV path for mode=csv (timestamp,temperatureC)")
    p.add_argument("--interval", type=float, default=1.0, help="Random mode: seconds between points")
    p.add_argument("--offline-after", type=int, default=10, help="Seconds of silence => sensor_offline alert")
    # IDs / broker
    import os

    p.add_argument("--mqtt-topic", default=os.getenv("MQTT_TOPIC", "sensors"))
    p.add_argument("--hotel-id", default=os.getenv("HOTEL_ID", "hotel_01"))
    p.add_argument("--room", default=int(os.getenv("ROOM", "101")))
    p.add_argument("--sensor", default=os.getenv("SENSOR", "sensor-1"))
    p.add_argument("--broker", default=os.getenv("BROKER", "localhost"))
    p.add_argument("--port", type=int, default=int(os.getenv("BROKER_PORT", "1883")))
    # MQTT config
    p.add_argument("--qos", type=int, default=int(os.getenv("QOS", "0")), help="MQTT QoS (0/1/2)")
    p.add_argument("--retain", action="store_true" if os.getenv("RETAIN","false").lower()=="true" else "store_false")
    p.add_argument("--keepalive", type=int, default=int(os.getenv("KEEPALIVE", "60")), help="MQTT keepalive seconds")
    # CSV pacing
    p.add_argument("--pace-real", action="store_true", help="Replay CSV using timestamp deltas (real time)")
    p.add_argument("--speed", type=float, default=float(os.getenv("SPEED","1.0")), help="Pace multiplier (2.0 = 2x faster)")
    args = p.parse_args()

    tags = {"hotel_id": args.hotel_id, "room": args.room, "sensor": args.sensor}

    # shared state
    state = SimulatorState(temperatureC=21.0, targetTemp=21.5, lightOn=False, pause_until=0.0)
    io = MqttIO(
        broker=args.broker,
        port=args.port,
        hotel_id=args.hotel_id,
        room=args.room,
        sensor=args.sensor,
        qos=args.qos,
        retain=args.retain,
        keepalive=args.keepalive,
        state=state
    )
    io.connect()

    # Choose source
    if args.mode == "csv":
        if not args.csv:
            print("Error: --csv required for mode=csv", file=sys.stderr)
            sys.exit(2)
        source = csv_rows(args.csv)
    else:
        source = random_source(state, args.interval)

    # Sensor monitor thread
    last_sent_ref = {"ts": 0}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(io, tags, last_sent_ref, args.offline_after, stop_event),
        daemon=True
    )
    monitor_thread.start()

    try:
        prev_ts = None
        for ts, tempC in source:
            # CSV pacing: sleep according to timestamp deltas (before publish)
            if args.mode == "csv" and args.pace_real and prev_ts is not None:
                delta = max(0.0, (ts - prev_ts) / max(0.001, args.speed))
                time.sleep(delta)
            prev_ts = ts

            # Respect simulateDrop pause window
            if state.pause_until and time.time() < state.pause_until:
                continue

            state.temperatureC = tempC
            payload = build_telemetry(
                measurement="temperature",
                tags=tags,
                fields={"temperatureC": state.temperatureC, "lightOn": state.lightOn},
                timestamp=ts
            )
            io.publish_telemetry(payload)
            last_sent_ref["ts"] = ts
    except KeyboardInterrupt:
        pass
    finally:
        # graceful shutdown
        stop_event.set()
        monitor_thread.join(timeout=2.0)
        io.flush_buffer()
        io.close()

if __name__ == "__main__":
    main()
