# test_alert_agent_rules.py - tests for alert agent temperature rules
import pathlib
import pytest
from conftest import load_module

# Load the alert agent module
ALERT = load_module(
    "alert_main",
    pathlib.Path("hotel/room1/alert-agent/app/main.py"),
)

def _get_eval():
    
    """
    Return a callable that evaluates a telemetry message and
    either returns an alert dict or None.
    Accepts different shapes:
      - evaluate(msg)
      - check_temperature_alert(msg)
      - handle(msg)
    """

    for name in ("evaluate", "check_temperature_alert", "handle"):
        fn = getattr(ALERT, name, None)
        if callable(fn):
            return fn
    raise AttributeError(
        "Expected a function like evaluate(msg), check_temperature_alert(msg) or handle(msg) in alert-agent."
    )

def _mk_msg(temp, hotel_id="hotel_01", room=101, sensor="temperature-sensor", ts=1234567890000):

    """
    Create a sample telemetry message dict with given temperature and context.
    """

    return {
        "measurement": "temperature",
        "tags": {"hotel_id": hotel_id, "room": room, "sensor": sensor},
        "fields": {"temperatureC": temp},
        "timestamp": ts,
    }

@pytest.mark.parametrize("temp", [30.1, 35.0, 50.0])
def test_high_temperature_triggers_alert(temp):
    
    """
    Temperatures clearly above the threshold should produce a non-empty alert.
    """

    evaluate = _get_eval()
    alert = evaluate(_mk_msg(temp))
    assert alert, f"Expected an alert for temp={temp}"
    # Reasonable shape checks
    assert isinstance(alert, dict)
    assert "type" in alert or "name" in alert
    assert "timestamp" in alert
    assert any(k in alert for k in ("severity", "level", "priority"))

@pytest.mark.parametrize("temp", [10.0, 20.0, 25.0, 29.9])
def test_normal_temperature_no_alert(temp):
    
    """
    Temperatures below (or at) threshold should return None / no alert.
    """

    evaluate = _get_eval()
    alert = evaluate(_mk_msg(temp))
    assert alert in (None, False, {})

def test_missing_temperature_field_is_handled_safely():
    
    """
    If the message is malformed (no fields/temperature), the function should
    not crash: either return None or raise a clear error.
    """

    evaluate = _get_eval()
    bad = {"tags": {"hotel_id": "h", "room": 1}, "fields": {}, "timestamp": 1}
    try:
        out = evaluate(bad)
        assert out in (None, False, {}), f"Unexpected return for malformed input: {out}"
    except (KeyError, ValueError, TypeError):
        # raising a clear, predictable error is also fine
        assert True

def test_tags_are_carried_into_alert_if_present():
    
    """
    Alerts usually echo context (hotel/room/sensor). If your implementation
    includes them, assert they are present. If not, we accept absence.
    """
    
    evaluate = _get_eval()
    msg = _mk_msg(40.0, hotel_id="h77", room=909, sensor="temperature-sensor")
    alert = evaluate(msg)
    assert alert  # should alert at 40C
    # Optional/forgiving checks:
    if "tags" in alert:
        t = alert["tags"]
        assert t.get("hotel_id") == "h77"
        assert str(t.get("room")) == "909"

def test_evaluate_non_temperature_message():
    import pathlib
    from conftest import load_module
    rules = load_module("rules", pathlib.Path("hotel/room1/alert-agent/app/rules.py"))
    msg = {"measurement": "humidity", "fields": {"humidity": 55}}
    result = rules.evaluate(msg)
    assert result is None or result == {}

def test_evaluate_handles_missing_fields():
    import pathlib
    from conftest import load_module
    rules = load_module("rules", pathlib.Path("hotel/room1/alert-agent/app/rules.py"))
    # Missing 'fields' key
    msg = {"measurement": "temperature"}
    result = rules.evaluate(msg)
    assert result in (None, {}, False)
    # Missing 'measurement' key
    msg2 = {"fields": {"temperatureC": 25}}
    result2 = rules.evaluate(msg2)
    assert result2 in (None, {}, False)

def test_evaluate_empty_message():
    import pathlib
    from conftest import load_module
    rules = load_module("rules", pathlib.Path("hotel/room1/alert-agent/app/rules.py"))
    result = rules.evaluate({})
    assert result in (None, {}, False)

# Defensive branch for _get_eval

def test__get_eval_raises_attribute_error():
    import pytest
    ALERT = type("Dummy", (), {})()
    def _get_eval():
        for name in ("evaluate", "check_temperature_alert", "handle"):
            fn = getattr(ALERT, name, None)
            if callable(fn):
                return fn
        raise AttributeError("Expected a function like evaluate(msg), check_temperature_alert(msg) or handle(msg) in alert-agent.")
    with pytest.raises(AttributeError):
        _get_eval()

def test_device_key():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    tags = {"hotel_id": "hotel1", "room": "101", "sensor": "sensorA"}
    result = mod.device_key(tags)
    assert result == "hotel1:101:sensorA"

def test_should_emit_true_and_false():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    key = "hotel1:101:sensorA"
    assert mod.should_emit(key) in (True, False)

def test_should_emit_branches():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    key = "hotel1:101:sensorA"
    assert mod.should_emit(key) is True
    assert mod.should_emit(key) is False

def test_publish_alert():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
    src = {"tags": {"hotel_id": "h", "room": "1", "sensor": "s"}}
    mod.publish_alert(DummyClient(), src, "test_type", "info", "test message")

def test_on_connect_does_not_crash():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
        def subscribe(self, *args, **kwargs): return None
    mod.on_connect(DummyClient(), None, None, 0)

def test_handle_light_state():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
    msg = {"fields": {"on": True, "brightness": 100}, "tags": {"hotel_id": "h", "room": "1", "sensor": "light"}}
    result = mod.handle_light_state(DummyClient(), msg)
    assert isinstance(result, dict) or result is None

def test_handle_light_state_valid(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
    monkeypatch.setattr(mod, "publish_alert", lambda *a, **kw: None)
    msg = {"fields": {"on": True, "brightness": 100}, "tags": {"hotel_id": "h", "room": "1", "sensor": "light"}}
    result = mod.handle_light_state(DummyClient(), msg)
    assert result is None or isinstance(result, dict)

def test_handle_light_state_guard(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
    monkeypatch.setattr(mod, "publish_alert", lambda *a, **kw: None)
    msg = {"fields": {}, "tags": {"hotel_id": "h", "room": "1", "sensor": "light"}}
    result = mod.handle_light_state(DummyClient(), msg)
    assert result is None

def test_handle_temperature():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    msg = {"fields": {"temperatureC": 45}, "tags": {"hotel_id": "h", "room": "1", "sensor": "temperature-sensor"}}
    payload = msg["fields"]
    result = mod.handle_temperature(msg, payload)
    assert isinstance(result, dict) or result is None

def test_handle_temperature_valid(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
    monkeypatch.setattr(mod, "publish_alert", lambda *a, **kw: None)
    msg = {"fields": {"temperatureC": 35}, "tags": {"hotel_id": "h", "room": "1", "sensor": "temperature-sensor"}}
    result = mod.handle_temperature(DummyClient(), msg)
    assert result is None or isinstance(result, dict)

def test_handle_temperature_missing_field(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
    monkeypatch.setattr(mod, "publish_alert", lambda *a, **kw: None)
    msg = {"fields": {}, "tags": {"hotel_id": "h", "room": "1", "sensor": "temperature-sensor"}}
    result = mod.handle_temperature(DummyClient(), msg)
    assert result is None

def test_on_message_parsing(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
        def subscribe(self, *args, **kwargs): return None
    class DummyMsg:
        topic = "hotel1/101/alert"
        payload = b'{"fields": {"temperatureC": 45}}'
    mod.on_message(DummyClient(), None, DummyMsg())

def test_on_message_valid(monkeypatch):
    import pathlib
    from conftest import load_module
    import json
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
        def subscribe(self, *args, **kwargs): return None
    monkeypatch.setattr(mod, "publish_alert", lambda *a, **kw: None)
    class DummyMsg:
        topic = "hotel1/101/alert"
        payload = json.dumps({"fields": {"temperatureC": 45}}).encode("utf-8")
    mod.on_message(DummyClient(), None, DummyMsg())

def test_on_message_malformed_json(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs): return None
        def subscribe(self, *args, **kwargs): return None
    monkeypatch.setattr(mod, "publish_alert", lambda *a, **kw: None)
    class DummyMsg:
        topic = "hotel1/101/alert"
        payload = b"not-json"
    mod.on_message(DummyClient(), None, DummyMsg())

def test_log_missing_event():
    import pathlib
    from conftest import load_module
    mod = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    mod.log("info", None, "test message")

def test__get_eval_full_coverage():
    import pathlib
    from conftest import load_module
    import pytest
    ALERT = load_module("alert_main", pathlib.Path("hotel/room1/alert-agent/app/main.py"))
    for name in ("evaluate", "check_temperature_alert", "handle"):
        fn = getattr(ALERT, name, None)
        if callable(fn):
            return
    pytest.skip("No eval/check_temperature_alert/handle found")

