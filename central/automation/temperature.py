import os
import time
import logging
from typing import Dict, Tuple

import requests

# Logger
log = logging.getLogger("automation-temperature")

# Environment
COMMAND_BASE_URL = os.getenv("COMMAND_BASE_URL", "http://command:5000")
REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "5"))
DEDUP_WINDOW_SEC = int(os.getenv("DEDUP_WINDOW_SEC", "600"))  # 10 minutes

# Dedup memory: key -> last command info
_last_applied: Dict[Tuple[str, str], Dict[str, float]] = {}


def to_int_room_number(room_number) -> int | None:
    try:
        return int(str(room_number).strip())
    except Exception:
        return None


def should_send(hotel_id: str, room_number_str: str, target_temp: int) -> bool:
    """Prevent spamming the command service for the same room and temp."""
    now = time.time()
    key = (hotel_id, room_number_str)
    info = _last_applied.get(key)
    if not info:
        _last_applied[key] = {"temp": target_temp, "ts": now}
        return True
    if info.get("temp") != target_temp or (now - info.get("ts", 0)) > DEDUP_WINDOW_SEC:
        _last_applied[key] = {"temp": target_temp, "ts": now}
        return True
    return False


essential_headers = {"Content-Type": "application/json"}

def post_temperature(hotel_id: str, room_number_str: str, value: int) -> tuple[bool, str | None]:
    """Send a temperature command to the Command service.

    Returns (ok, error_message_or_none).
    """
    room_number_int = to_int_room_number(room_number_str)
    if room_number_int is None:
        log.warning(
            f"Skip room with non-numeric room_number: hotel={hotel_id} room_number={room_number_str}"
        )
        return False, "non_numeric_room"

    url = f"{COMMAND_BASE_URL}/send_command/{hotel_id}/{room_number_int}/temperature/{value}"
    try:
        r = requests.post(url, timeout=REQUEST_TIMEOUT_SEC, headers=essential_headers)
        if 200 <= r.status_code < 300:
            log.info(f"Set temperature {value} OK -> hotel={hotel_id} room={room_number_int}")
            return True, None
        else:
            log.warning(f"Command failed ({r.status_code}) -> {url} body={r.text}")
            return False, f"status_{r.status_code}"
    except Exception as e:
        log.error(f"HTTP error posting to command service: {e}")
        return False, str(e)
