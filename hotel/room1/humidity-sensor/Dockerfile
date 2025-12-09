FROM python:3.12-slim
WORKDIR /app

# Install build dependencies for mmhash3
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY humidity-sensor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared common library
COPY common /app/common

# Copy application code
COPY humidity-sensor /app

# Set environment variables with defaults
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=humidity-sensor \
    MQTT_BROKER=mosquitto MQTT_PORT=1883 QOS=1 KEEPALIVE=60 \
    TARGET_HUMIDITY=50.0 INTERVAL=1.0 SPEED=1.0

CMD ["python", "app/main.py"]
