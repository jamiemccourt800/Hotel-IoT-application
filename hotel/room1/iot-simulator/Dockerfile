FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONPATH=/app
# Defaults (override at runtime)
ENV HOTEL_ID=hotel_01 ROOM=101 SENSOR=sensor-1 BROKER=mosquitto BROKER_PORT=1883 QOS=0 RETAIN=false KEEPALIVE=60 SPEED=1.0
CMD ["python", "app/main.py", "--mode", "random", "--interval", "1.0", "--offline-after", "10"]
