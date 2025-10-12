import time

def monitor_loop(io, tags: dict, last_sent_ref: dict, offline_after_s: int, stop_event):
    """Background monitor thread.
    - If no telemetry for offline_after_s: publish HIGH sensor_offline
    - When telemetry resumes: publish INFO sensor_online
    """
    was_offline = False
    while not stop_event.is_set():
        now = int(time.time())
        last = int(last_sent_ref.get("ts", 0))
        gap = now - last if last else now
        is_offline = gap > offline_after_s

        if is_offline and not was_offline:
            io.publish_alert(tags, severity="HIGH", kind="sensor_offline", details={"gapSeconds": gap})
            was_offline = True

        if not is_offline and was_offline:
            io.publish_alert(tags, severity="INFO", kind="sensor_online", details={"gapSeconds": gap})
            was_offline = False

        stop_event.wait(1.0)
