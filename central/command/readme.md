# FastAPI Kafka Prototype

A minimal, prototype FastAPI application to asynchronously publish messages to Kafka, mimicking an actuator route for setting room temperatures.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Components](#components)
- [Setup](#setup)
- [Running the App](#running-the-app)
- [API Endpoints](#api-endpoints)
- [Development Notes](#development-notes)
- [Future Enhancements](#future-enhancements)

---

## Project Structure

app/\
├── app.py # FastAPI application entrypoint\
├── config.py # Environment-based configuration\
├── kafka_producer.py # Async Kafka producer setup and send wrapper\
├── routes/\
│ ├── actuator.py # /set_temperature route\
│ └── health.py # /health endpoint to check Kafka connectivity\
├── schemas.py # Pydantic models\
└── README.md # This file

---

## Components

### `app.py`
- FastAPI app instance.
- Includes startup/shutdown events:
  - `startup` → initializes Kafka producer.
  - `shutdown` → flushes and stops Kafka producer.
- Registers routers for actuator and health endpoints.

### `config.py`
- Loads configuration from environment variables:
  - `KAFKA_BOOTSTRAP` (default: `localhost:9092`)
  - `KAFKA_TOPIC` (default: `test-topic`)
  - `CLIENT_ID` (default: `fastapi-producer`)
  - `ACKS`, `RETRIES`, `LINGER_MS`
- Single source of truth for container settings.

### `kafka_producer.py`
- Global singleton Kafka producer.
- Functions:
  - `start_producer()` → initializes and starts async producer.
  - `stop_producer()` → flushes and closes producer.
  - `send_message(topic, message, key=None)` → asynchronously sends messages and logs results.

### `routes/actuator.py`
- `/set_temperature` route to mimic a room thermostat actuator.
- Accepts JSON:
  - `hotel_id` (str)
  - `room_number` (int)
  - `temperature` (float)
- Publishes enriched message to Kafka topic asynchronously.
- Returns:
  - `{"status": "success", "target_temperature": ...}` on enqueue.
  - `{"status": "error", "error": ...}` on failure.
- Logging includes hotel, room, temperature, and message ID.

### `routes/health.py`
- `/health` route.
- Checks Kafka connectivity.
- Returns JSON:
  - `{"status": "ok", "kafka": "connected"}` if producer can connect.
  - `{"status": "fail", "kafka": <error message>}` on failure.

---

## Setup

1. Clone the repository.
2. Create a `.env` file or set environment variables:

```dotenv
KAFKA_BOOTSTRAP=localhost:9092
KAFKA_TOPIC=test-topic
CLIENT_ID=fastapi-producer
ACKS=all
RETRIES=3
LINGER_MS=5
