import os
import time
import ulid

# Configuration local to rules; defaults mirror main.py
TEMP_HIGH_C = float(os.getenv("TEMP_HIGH_C", "30"))
HOTEL = os.getenv("HOTEL_ID", "hotel_01")
ROOM = os.getenv("ROOM", "101")

def now_ms():
    return int(time.time() * 1000)


def evaluate(msg: dict):
    """
    Pure function: given a telemetry message dict, return an alert dict
    (the same shape as would be published) or None.

    This deliberately has no side-effects and reads only minimal env
    defaults so it can be used in unit tests and other tooling.
    """
    if not isinstance(msg, dict):
        return None

    if msg.get("measurement") != "temperature":
        return None

    tags = msg.get("tags", {}) or {}
    fields = msg.get("fields", {}) or {}
    c = fields.get("temperatureC")
    if not isinstance(c, (int, float)):
        return None

    if c >= TEMP_HIGH_C:
        out = {
            "measurement": "alert",
            "type": "temp_high",
            "name": "temp_high",
            # top-level severity/level for test expectations
            "severity": "warning",
            "level": "warning",
            "tags": {
                "hotel_id": tags.get("hotel_id", HOTEL),
                "room": tags.get("room", ROOM),
                "sensor": tags.get("sensor", "unknown"),
                "alert_id": str(ulid.new()),
            },
            "fields": {
                "alert_type": "temp_high",
                "severity": "warning",
                "message": f"High temperature {c}°C",
                "value": c,
                "origin": "room-alert-agent",
            },
            "timestamp": now_ms(),
        }
        return out

    return None


# backwards-compatible alias
check_temperature_alert = evaluate
handle = evaluate
