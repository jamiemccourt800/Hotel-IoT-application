import os
import logging
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx

# Basic logging
logging.basicConfig(level=logging.INFO, format='[automation-api] %(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger("vm-api")

VICTORIA_BASE_URL = os.getenv("VICTORIA_BASE_URL", "http://victoria-metrics:8428")
REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "5"))

app = FastAPI()

async def victoria_health():
    details = {"ok": False}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as http:
            r = await http.get(f"{VICTORIA_BASE_URL}/health")
            details["status_code"] = r.status_code
            details["ok"] = 200 <= r.status_code < 300
    except Exception as e:
        details["ok"] = False
        details["error"] = str(e)
    return details


@app.get("/health")
async def health():
    victoria_res = await asyncio.gather(asyncio.create_task(victoria_health()))
    overall_ok = bool(victoria_res.get("ok"))
    status = 200 if overall_ok else 503
    return JSONResponse(
        status_code=status,
        content={"status": "ok"},
    )

@app.get("/temperature-status/<hotel>/<int:room>?timeframe={timeframe}")
async def temperature_status(hotel: str, room: int, timeframe: str = "5m"):
    query = f'''
    vm_series(
        metric="room_temperature",
        filter={{"hotel": "{hotel}", "room": "{room}"}},
        time_range="{timeframe}"
    )
    '''
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as http:
            r = await http.get(f"{VICTORIA_BASE_URL}/api/v1/query", params={"query": query})
            r.raise_for_status()
            data = r.json()
            if "data" in data and "result" in data["data"] and data["data"]["result"]:
                latest_value = data["data"]["result"][0]["value"][1]
                temperature = float(latest_value)
                status = "normal"
                if temperature > 25:
                    status = "high"
                elif temperature < 18:
                    status = "low"
                return JSONResponse(
                    status_code=200,
                    content={"hotel": hotel, "room": room, "temperature": temperature, "status": status},
                )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"error": "No temperature data found for the specified room."},
                )
    except Exception as e:
        log.error(f"Error fetching temperature data: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error."},
        )


@app.get("/light-status")
async def light_status(hotel: str, room: int, timeframe: str = "5m"):
    query = f'''
    vm_series(
        metric="room_light_status",
        filter={{"hotel": "{hotel}", "room": "{room}"}},
        time_range="{timeframe}"
    )
    '''
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as http:
            r = await http.get(f"{VICTORIA_BASE_URL}/api/v1/query", params={"query": query})
            r.raise_for_status()
            data = r.json()
            if "data" in data and "result" in data["data"] and data["data"]["result"]:
                latest_value = data["data"]["result"][0]["value"][1]
                light_stats = "on" if latest_value == "1" else "off"
                return JSONResponse(
                    status_code=200,
                    content={"hotel": hotel, "room": room, "light_status": light_stats},
                )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"error": "No light status data found for the specified room."},
                )
    except Exception as e:
        log.error(f"Error fetching light status data: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error."},
        )
