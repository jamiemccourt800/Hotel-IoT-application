FROM python:3.12-slim
WORKDIR /app

# Install build dependencies for mmhash3
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY alert-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared common library
COPY common /app/common

# Copy application code
COPY alert-agent /app

# Set environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    HOTEL_ID=hotel_01 \
    ROOM=101 \
    SENSOR=alert-agent \
    MQTT_BROKER=mosquitto \
    MQTT_PORT=1883 \
    QOS=1 \
    KEEPALIVE=60 \
    MQTT_SUB=hotel_01/# \
    MQTT_PUB=alerts \
    TEMP_HIGH_C=30 \
    OFFLINE_TIMEOUT_S=120 \
    DEDUP_WINDOW_S=60

CMD ["python", "app/main.py"]
