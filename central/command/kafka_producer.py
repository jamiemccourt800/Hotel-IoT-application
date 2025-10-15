import asyncio
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from config import config

logger = logging.getLogger("kafka_producer")
logger.setLevel(logging.INFO)

producer: AIOKafkaProducer = None

async def start_producer():
    """Initialize and start the Kafka producer with retries."""
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP,
            client_id=config.CLIENT_ID,
            acks=config.ACKS,
            linger_ms=config.LINGER_MS,
        )
        attempts, max_attempts, delay = 0, getattr(config, 'RETRIES', 10), 2
        while True:
            try:
                attempts += 1
                logger.info(f"Starting Kafka producer (attempt {attempts}/{max_attempts}) to {config.KAFKA_BOOTSTRAP}")
                await producer.start()
                logger.info("Kafka producer started")
                break
            except Exception as e:
                if attempts >= max_attempts:
                    logger.error(f"Failed to start Kafka producer after {attempts} attempts: {e}")
                    raise
                logger.warning(f"Kafka not ready: {e}; retrying in {delay}s...")
                await asyncio.sleep(delay)

async def stop_producer():
    """Flush and stop the Kafka producer."""
    global producer
    if producer:
        await producer.stop()
        logger.info("Kafka producer stopped")

async def send_message(topic: str, message: bytes, key: bytes = None):
    """Send a message asynchronously to Kafka."""
    if producer is None:
        raise RuntimeError("Producer not started")
    try:
        fut = await producer.send_and_wait(topic, message, key=key)
        logger.info(f"Message sent to topic {fut.topic} partition {fut.partition} offset {fut.offset}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise
