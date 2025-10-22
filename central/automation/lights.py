import os
import time
import logging
from typing import Dict, Tuple, List

import asyncio
import httpx

# Logger
log = logging.getLogger("automation-lights")

# Environment / Config
COMMAND_BASE_URL = os.getenv("COMMAND_BASE_URL", "http://command:5000")
VICTORIA_BASE_URL = os.getenv("VICTORIA_BASE_URL", "http://victoria-metrics:8428")
REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "5"))
POLL_INTERVAL_SEC = float(os.getenv("LIGHTS_POLL_INTERVAL_SEC", os.getenv("POLL_INTERVAL_SEC", "10")))
DEDUP_WINDOW_SEC = int(os.getenv("DEDUP_WINDOW_SEC", "600"))  # 10 minutes

# Light control specifics
LIGHTS_ENABLED = os.getenv("LIGHTS_ENABLED", "true").lower() in ("1", "true", "yes", "on")
LIGHT_METRIC = os.getenv("LIGHT_METRIC", "light_status")  # default aligns with simulator output
LIGHT_WINDOW = os.getenv("LIGHT_WINDOW", "5m")  # range window for last_over_time
LIGHT_DAY_THRESHOLD = float(os.getenv("LIGHT_DAY_THRESHOLD", "0.5"))  # default: 1=on, so >0.5 means on

# Targets to monitor
LIGHT_HOTEL_ID = os.getenv("LIGHT_HOTEL_ID", os.getenv("HOTEL_ID", "DUB-Grand"))
LIGHT_ROOMS = [r.strip() for r in os.getenv("LIGHT_ROOMS", os.getenv("ROOMS", "621")).split(",") if r.strip()]

# Dedup memory: (hotel_id, room) -> {"action": str, "ts": float}
_last_action: Dict[Tuple[str, str], Dict[str, float]] = {}


def _to_int_room(room: str) -> int | None:
    try:
        return int(str(room).strip())
    except Exception:
        return None


async def _query_light_level(http: httpx.AsyncClient, hotel_id: str, room: str) -> float | None:
    """Query VictoriaMetrics for the latest ambient light level for given room.

    Uses PromQL: last_over_time(METRIC{hotel_id="...",room="..."}[LIGHT_WINDOW])
    Returns the numeric value or None if not found.
    """
    # Build PromQL
    promql = f'last_over_time({LIGHT_METRIC}{{hotel_id="{hotel_id}",room="{room}"}}[{LIGHT_WINDOW}])'
    try:
        r = await http.get(
            f"{VICTORIA_BASE_URL}/api/v1/query",
            params={"query": promql},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            log.warning(f"VM query not success: {data}")
            return None
        result = data.get("data", {}).get("result") or []
        if not result:
            return None
        # Take first series' value
        value = result[0].get("value")
        if isinstance(value, list) and len(value) >= 2:
            try:
                return float(value[1])
            except Exception:
                return None
        return None
    except Exception as e:
        log.error(f"Error querying VictoriaMetrics: {e}")
        return None


async def _post_light_off(http: httpx.AsyncClient, hotel_id: str, room: str) -> tuple[bool, str | None]:
    room_int = _to_int_room(room)
    if room_int is None:
        return False, "non_numeric_room"
    url = f"{COMMAND_BASE_URL}/actuator/light/{hotel_id}/{room_int}/off"
    try:
        r = await http.post(url, timeout=REQUEST_TIMEOUT_SEC)
        if 200 <= r.status_code < 300:
            log.info(f"Light OFF command sent -> hotel={hotel_id} room={room_int}")
            return True, None
        log.warning(f"Light OFF failed ({r.status_code}) -> {url} body={r.text}")
        return False, f"status_{r.status_code}"
    except Exception as e:
        log.error(f"HTTP error posting light OFF: {e}")
        return False, str(e)


def _should_send_off(hotel_id: str, room: str) -> bool:
    now = time.time()
    key = (hotel_id, room)
    info = _last_action.get(key)
    if not info:
        _last_action[key] = {"action": "off", "ts": now}
        return True
    if info.get("action") != "off" or (now - info.get("ts", 0)) > DEDUP_WINDOW_SEC:
        _last_action[key] = {"action": "off", "ts": now}
        return True
    return False


async def evaluate_room(http: httpx.AsyncClient, hotel_id: str, room: str) -> dict:
    """Evaluate a single room and turn off lights if bright daylight detected.

    Returns details for diagnostics.
    """
    level = await _query_light_level(http, hotel_id, room)
    decision = {"hotel_id": hotel_id, "room": room, "metric": LIGHT_METRIC, "threshold": LIGHT_DAY_THRESHOLD}
    if level is None:
        decision.update({"ok": False, "reason": "no_data"})
        return decision

    decision["level"] = level
    if level >= LIGHT_DAY_THRESHOLD:
        if _should_send_off(hotel_id, room):
            ok, err = await _post_light_off(http, hotel_id, room)
            decision.update({"ok": ok, "action": "off", "error": err})
        else:
            decision.update({"ok": True, "action": "ignored_dedup"})
    else:
        decision.update({"ok": True, "action": "none"})
    return decision


async def light_controller_loop():
    """Background loop for automated light control.

    Periodically checks ambient light for configured rooms and switches lights off
    when above the daylight threshold.
    """
    if not LIGHTS_ENABLED:
        log.info("Lights controller disabled via LIGHTS_ENABLED")
        return

    log.info(
        "Starting lights controller: hotel=%s rooms=%s metric=%s threshold=%s window=%s interval=%ss",
        LIGHT_HOTEL_ID,
        ",".join(LIGHT_ROOMS),
        LIGHT_METRIC,
        LIGHT_DAY_THRESHOLD,
        LIGHT_WINDOW,
        POLL_INTERVAL_SEC,
    )
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as http:
        while True:
            try:
                tasks: List[asyncio.Task] = [
                    asyncio.create_task(evaluate_room(http, LIGHT_HOTEL_ID, room)) for room in LIGHT_ROOMS
                ]
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for res in results:
                        if isinstance(res, Exception):
                            log.error(f"lights controller error: {res}")
                        else:
                            # Optional: log verbose only on action or failure
                            if res.get("action") in ("off", "ignored_dedup") or not res.get("ok", True):
                                log.info(f"lights eval: {res}")
                await asyncio.sleep(POLL_INTERVAL_SEC)
            except Exception as e:
                log.error(f"lights loop error: {e}")
                await asyncio.sleep(POLL_INTERVAL_SEC)
