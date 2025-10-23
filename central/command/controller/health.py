import os

from fastapi import FastAPI
from aiokafka import AIOKafkaProducer
import asyncio
from config import config
import httpx

VICTORIA_BASE_URL = os.getenv("VICTORIA_URL", "http://victoria-metrics:8428").rstrip("/")
REQUEST_TIMEOUT_SEC = os.getenv("REQUEST_TIMEOUT_SEC", 30)

async def health_check():
    """Check if Kafka is reachable."""
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP,
            client_id=config.CLIENT_ID,
        )
        victoria_task = asyncio.create_task(victoria_health())
        await producer.start()
        # fetch metadata to ensure connectivity
        await producer.client.fetch_all_metadata()
        await producer.stop()
        victoria_status = await victoria_task
        if not victoria_status.get("ok"):
            return {"status": "fail", "victoria": victoria_status, "kafka": "connected"}
        else:
            return {"status": "ok", "victoria": victoria_status, "kafka": "connected"}
    except Exception as e:
        return {"status": "fail", "kafka": str(e)}


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
