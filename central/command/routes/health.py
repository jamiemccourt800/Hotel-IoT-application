from fastapi import FastAPI
from aiokafka import AIOKafkaProducer
import asyncio
from config import config

async def health_check():
    """Check if Kafka is reachable."""
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP,
            client_id=config.CLIENT_ID,
        )
        await producer.start()
        # fetch metadata to ensure connectivity
        await producer.client.fetch_all_metadata()
        await producer.stop()
        return {"status": "ok", "kafka": "connected"}
    except Exception as e:
        return {"status": "fail", "kafka": str(e)}
