import os
import logging
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
from pymongo import MongoClient

# Basic logging
logging.basicConfig(level=logging.INFO, format='[automation-api] %(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger("automation-api")

# Environment configuration (align with other services)
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb") or "mongodb"
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "bookings")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")

COMMAND_BASE_URL = os.getenv("COMMAND_BASE_URL", "http://command:5000")
# VictoriaMetrics base URL; defaults to the service name on Docker network
VICTORIA_BASE_URL = os.getenv("VICTORIA_BASE_URL", "http://victoria-metrics:8428")

REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "5"))
AUTOMATION_PORT = int(os.getenv("PORT", os.getenv("AUTOMATION_PORT", "5102")))

if MONGO_USER and MONGO_PASS:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

app = FastAPI()

# Start background tasks
try:
    from lights import light_controller_loop, LIGHTS_ENABLED, LIGHT_HOTEL_ID, LIGHT_ROOMS, evaluate_room
except Exception:
    # lights module is optional at import time; runtime errors will surface in logs
    light_controller_loop = None
    LIGHTS_ENABLED = False
    LIGHT_HOTEL_ID = None
    LIGHT_ROOMS = []
    evaluate_room = None

@app.on_event("startup")
async def _startup():
    if LIGHTS_ENABLED and callable(light_controller_loop):
        asyncio.create_task(light_controller_loop())

@app.get("/")
async def root():
    return {"service": "automation", "ok": True}


@app.get("/lights/scan")
async def lights_scan():
    if evaluate_room is None or LIGHT_HOTEL_ID is None:
        return JSONResponse(status_code=503, content={"ok": False, "error": "lights module not available"})
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as http:
            tasks = [asyncio.create_task(evaluate_room(http, LIGHT_HOTEL_ID, room)) for room in LIGHT_ROOMS]
            results = await asyncio.gather(*tasks)
        return JSONResponse(content={"ok": True, "results": results}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


async def mongo_health():
    details = {"ok": False}
    try:
        # run blocking Mongo calls off the event loop
        await asyncio.to_thread(client.admin.command, 'ping')
        await asyncio.to_thread(db.list_collection_names)
        details["ok"] = True
    except Exception as e:
        details["ok"] = False
        details["error"] = str(e)
    return details


async def command_health():
    details = {"ok": False}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as http:
            r = await http.get(f"{COMMAND_BASE_URL}/health")
            details["status_code"] = r.status_code
            details["ok"] = 200 <= r.status_code < 300
    except Exception as e:
        details["ok"] = False
        details["error"] = str(e)
    return details


# VictoriaMetrics health check
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
    mongo_task = asyncio.create_task(mongo_health())
    command_task = asyncio.create_task(command_health())
    victoria_task = asyncio.create_task(victoria_health())
    mongo_res, command_res, victoria_res = await asyncio.gather(mongo_task, command_task, victoria_task)
    overall_ok = bool(mongo_res.get("ok") and command_res.get("ok") and victoria_res.get("ok"))
    status = 200 if overall_ok else 503
    return JSONResponse(
        content={
            "ok": overall_ok,
            "service": "automation",
            "details": {"mongo": mongo_res, "command": command_res, "victoria": victoria_res},
        },
        status_code=status,
    )
