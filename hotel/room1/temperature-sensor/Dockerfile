FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and shared libraries
COPY . /app

# Set environment variables with defaults
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=temperature-sensor \
    MQTT_BROKER=mosquitto MQTT_PORT=1883 QOS=1 KEEPALIVE=60 \
    TARGET_TEMP=21.0 INTERVAL=1.0 SPEED=1.0 START_TEMP=21.0

# Use new modular entry point
CMD ["python", "app/main.py"]
