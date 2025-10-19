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
REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "5"))
AUTOMATION_PORT = int(os.getenv("PORT", os.getenv("AUTOMATION_PORT", "5102")))

if MONGO_USER and MONGO_PASS:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

app = FastAPI()

@app.get("/")
async def root():
    return {"service": "automation", "ok": True}


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


@app.get("/health")
async def health():
    mongo_task = asyncio.create_task(mongo_health())
    command_task = asyncio.create_task(command_health())
    mongo_res, command_res = await asyncio.gather(mongo_task, command_task)
    overall_ok = bool(mongo_res.get("ok") and command_res.get("ok"))
    status = 200 if overall_ok else 503
    return JSONResponse(
        content={"ok": overall_ok, "service": "automation", "details": {"mongo": mongo_res, "command": command_res}},
        status_code=status,
    )

# Run with: uvicorn app:app --host 0.0.0.0 --port 5102
