import time

def build_telemetry(measurement: str, tags: dict, fields: dict, timestamp: int | None = None) -> dict:
    """Build telemetry payload.

    The simulator historically emitted timestamps in seconds. Telegraf's
    configuration in this project expects unix_ms (milliseconds). To avoid
    timestamp parsing issues, emit milliseconds here.
    """
    ts = (timestamp if timestamp is not None else time.time())
    # Ensure milliseconds
    ts_ms = int(ts * 1000)
    return {
        "measurement": measurement,
        "tags": tags,
        "fields": fields,
        "timestamp": ts_ms,
    }

def build_ack(correlation_id: str | None, status: str, message: str) -> dict:
    return {
        "header": {
            "type": "ack",
            "correlationId": correlation_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "body": {"status": status, "message": message}
    }
