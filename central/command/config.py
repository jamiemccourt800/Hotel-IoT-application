import os

class Config:
    KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "test-topic")
    CLIENT_ID = os.getenv("CLIENT_ID", "fastapi-producer")
    ACKS = os.getenv("ACKS", "all")
    RETRIES = int(os.getenv("RETRIES", 3))
    LINGER_MS = int(os.getenv("LINGER_MS", 5))

config = Config()