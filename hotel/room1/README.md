# IoT Simulator

Complete hotel room IoT simulation system with sensors, actuators, and intelligent alert monitoring. This simulator represents a fully functional smart hotel room (Room 101) with environmental monitoring and control capabilities.

## Components

### Sensors (3)
- **Temperature Sensor**: Simulates room temperature readings (18-30°C)
- **Humidity Sensor**: Simulates humidity levels (30-70%)
- **Light Sensor**: Simulates ambient light brightness (0-1000 lux)

### Actuators (3)
- **Temperature Actuator**: Controls HVAC/thermostat with PID feedback control
- **Humidity Actuator**: Controls humidifier with deadband control
- **Light Actuator**: Controls room lighting with adaptive brightness

### Alert Agent (1)
- Monitors sensor telemetry for threshold violations
- Detects offline sensors (heartbeat monitoring)
- Publishes alerts to `alerts` topic
- Deduplication with configurable time windows

## Message Flow

### Sensor → Central System
```
Sensor → MQTT (hotel_01/101/{sensor}/telemetry) → 
MQTT-to-Kafka Bridge → Kafka (mqtt_messages) → 
Telegraf → VictoriaMetrics
```

### Central System → Actuator
```
FastAPI → Kafka (actuators.hotel_01.101.{actuator}.cmd) → 
Kafka-to-MQTT Bridge → MQTT (hotel_01/101/{actuator}/cmd) → 
Actuator → ACK (hotel_01/101/{actuator}/ack)
```

### Local Feedback Loop
```
Sensor → MQTT → Actuator → Control Logic → MQTT → Physical Output
```

## MQTT Topic Structure

### Sensor Telemetry
- Temperature: `hotel_01/101/temperature-sensor/telemetry`
- Humidity: `hotel_01/101/humidity-sensor/telemetry`
- Light: `hotel_01/101/light-sensor/telemetry`

### Actuator Commands
- Temperature: `hotel_01/101/temperature-actuator/cmd`
- Humidity: `hotel_01/101/humidity-actuator/cmd`
- Light: `hotel_01/101/light-actuator/cmd`

### Actuator Acknowledgments
- Temperature: `hotel_01/101/temperature-actuator/ack`
- Humidity: `hotel_01/101/humidity-actuator/ack`
- Light: `hotel_01/101/light-actuator/ack`

### Alerts
- All alerts: `alerts`

## Message Format

All messages follow the InfluxDB line protocol format in JSON:

```json
{
  "measurement": "temperature",
  "tags": {
    "hotel_id": "hotel_01",
    "room": 101,
    "sensor": "temperature-sensor"
  },
  "fields": {
    "temperatureC": 23.5
  },
  "timestamp": 1732809600000,
  "correlationId": "uuid-optional"
}
```

## Docker Images

All components are available on Docker Hub under `dkitdevops`:

- `dkitdevops/hotel-temperature-sensor:latest`
- `dkitdevops/hotel-temperature-actuator:latest`
- `dkitdevops/hotel-humidity-sensor:latest`
- `dkitdevops/hotel-humidity-actuator:latest`
- `dkitdevops/hotel-light-sensor:latest`
- `dkitdevops/hotel-light-actuator:latest`
- `dkitdevops/hotel-alert-agent:latest`
- `dkitdevops/hotel-mqtt-to-kafka:latest`
- `dkitdevops/hotel-kafka-to-mqtt:latest`

## Running the Simulator

### Option 1: Build Locally
```bash
# From project root
docker-compose -f hotel/docker-compose.hotel1.yml up -d
```

### Option 2: Use Docker Hub Images
```bash
# From project root
docker-compose -f hotel/docker-compose.hotel1.dockerhub.yml up -d
```

## Configuration

### Environment Variables (Common)
| Variable | Default | Description |
|----------|---------|-------------|
| HOTEL_ID | hotel_01 | Hotel identifier |
| ROOM | 101 | Room number |
| MQTT_BROKER | mosquitto | MQTT broker hostname |
| MQTT_PORT | 1883 | MQTT broker port |
| MQTT_QOS | 1 | Quality of Service level |

### Sensor-Specific Variables
| Variable | Default | Description |
|----------|---------|-------------|
| INTERVAL | 1.0 | Publish interval (seconds) |
| SPEED | 1.0 | Simulation speed multiplier |
| TARGET_TEMP | 23.5 | Target temperature for simulation |

### Actuator-Specific Variables
| Variable | Default | Description |
|----------|---------|-------------|
| DEFAULT_TARGET | 22.0 | Default setpoint |
| CONTROL_INTERVAL | 5.0 | Control loop interval (seconds) |

### Alert Agent Variables
| Variable | Default | Description |
|----------|---------|-------------|
| TEMP_HIGH_C | 30 | High temperature threshold |
| OFFLINE_TIMEOUT_S | 45 | Offline detection timeout |
| DEDUP_WINDOW_S | 30 | Alert deduplication window |

## Architecture Details

### Sensor Operation
1. Sensors run continuous simulation loops
2. Generate realistic environmental data
3. Publish to MQTT on configurable intervals
4. Support replay speed adjustment for testing

### Actuator Operation
1. Subscribe to both local sensors and external commands
2. Run feedback control loops (PID/deadband)
3. Publish acknowledgments for external commands
4. Support dual-mode operation (local/external control)

### Alert Agent Operation
1. Subscribe to all sensor telemetry (`hotel_01/#`)
2. Maintain last-seen timestamps for offline detection
3. Evaluate threshold rules on each message
4. Deduplicate alerts within time windows
5. Publish structured alerts with severity levels

## Development

### Common Module
Shared utilities across all components:
- `config.py`: Configuration dataclasses with environment variable loading
- `logging.py`: Structured JSON logging
- `mqtt_client.py`: MQTT client wrapper with retry logic
- `schemas.py`: Message validation and telemetry builders
- `utils.py`: Timestamp and utility functions

### Adding New Sensors
1. Copy sensor template from `temperature-sensor/`
2. Implement simulation logic in `simulation.py`
3. Update sensor.py with measurement-specific logic
4. Add Dockerfile and requirements.txt
5. Add to docker-compose files

### Adding New Actuators
1. Copy actuator template from `temperature-actuator/`
2. Implement control logic (PID/deadband/custom)
3. Update message handlers for device-specific commands
4. Add Dockerfile and requirements.txt
5. Add to docker-compose files

## Performance Characteristics

- **Sensor Publish Rate**: 1 msg/second (configurable)
- **Actuator Control Loop**: 5 seconds (configurable)
- **Alert Evaluation**: Real-time on message receipt
- **MQTT QoS**: Level 1 (at least once delivery)
- **Message Size**: ~200-300 bytes average