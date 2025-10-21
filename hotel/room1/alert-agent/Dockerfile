FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PYTHONUNBUFFERED=1 \
	MQTT_BROKER=mosquitto \
	MQTT_PORT=1883 \
	MQTT_SUB=sensors/# \
	MQTT_PUB=sensors \
	HOTEL_ID=hotel_01 \
	ROOM=101 \
	TEMP_HIGH_C=30 \
	OFFLINE_TIMEOUT_S=120 \
	DEDUP_WINDOW_S=60
CMD ["python", "-m", "app.main"]
