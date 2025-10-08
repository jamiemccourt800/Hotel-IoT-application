import csv
import time
from datetime import datetime

def _to_unix(ts_str: str) -> int:
    try:
        return int(ts_str)
    except ValueError:
        pass
    try:
        return int(datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp())
    except Exception:
        return int(time.time())

def csv_rows(path: str):
    """Yield (unix_ts, temperatureC) from CSV with headers: timestamp,temperatureC"""
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            yield _to_unix(row["timestamp"]), float(row["temperatureC"])
