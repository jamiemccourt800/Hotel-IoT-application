FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY humidity-actuator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared common library
COPY common /app/common

# Copy application code
COPY humidity-actuator /app

# Set environment variables with defaults
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=humidity-actuator \
    MQTT_BROKER=mosquitto MQTT_PORT=1883 QOS=1 KEEPALIVE=60 \
    DEFAULT_TARGET=50.0 CONTROL_INTERVAL=5.0 DEADBAND=2.0

CMD ["python", "app/main.py"]
