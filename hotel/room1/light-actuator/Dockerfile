FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and shared libraries
COPY . /app

# Set environment variables with defaults
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=light-actuator \
    MQTT_BROKER=mosquitto MQTT_PORT=1883 QOS=1 KEEPALIVE=60 \
    DEFAULT_BRIGHTNESS=75.0 CONTROL_INTERVAL=5.0

CMD ["python", "app/main.py"]
