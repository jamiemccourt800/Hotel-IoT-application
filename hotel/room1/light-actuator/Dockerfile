FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir paho-mqtt
COPY . /app

# Environment variables
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=light-actuator \
    BROKER=mqtt-broker BROKER_PORT=1883 QOS=1 KEEPALIVE=60 \
    INITIAL_ON=true INITIAL_BRIGHTNESS=100

CMD ["python", "logic/main.py"]
