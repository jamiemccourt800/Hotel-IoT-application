FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir paho-mqtt
COPY . /app

# Set environment variables with defaults
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=temperature-sensor \
    BROKER=mqtt-broker BROKER_PORT=1883 QOS=0 KEEPALIVE=60 \
    MODE=random INTERVAL=1.0 SPEED=1.0 \
    START_TEMP=21.0 TARGET_TEMP=21.0 \
    CSV_PATH=.data/telemetry.csv
    
CMD ["python", "logic/main.py"]
