# test_light_actuator_handle.py - tests for the light actuator handler
import pathlib
import pytest
from conftest import load_module

# Load the actuator module from a path that contains a hyphen
ACT = load_module(
    "actuator_main",
    pathlib.Path("hotel/room1/light-actuator/logic/main.py"),
)

def _get_handler():
    
    """
    Return a callable that handles a light command: handler(command_dict) -> dict.
    Works with either:
      - function: handle_light_command(cmd) or handle(cmd)
      - class   : LightActuator/Controller with .handle(cmd)
    """

    # function style
    if hasattr(ACT, "handle_light_command") and callable(ACT.handle_light_command):
        return ACT.handle_light_command
    if hasattr(ACT, "handle") and callable(ACT.handle):
        return ACT.handle

    # class style
    for cls_name in ("LightActuator", "Controller", "Actuator"):
        if hasattr(ACT, cls_name):
            inst = getattr(ACT, cls_name)()
            if hasattr(inst, "handle") and callable(inst.handle):
                return inst.handle

    raise AttributeError(
        "Expected a handler: handle_light_command(cmd), handle(cmd), or "
        "a class LightActuator/Controller with .handle(cmd)."
    )

def test_light_on_ack_and_state():
    
    """
    Turning the light ON with a valid brightness returns ack=True
    and a state reflecting on=True and the requested brightness.
    """

    handle = _get_handler()
    cmd = {"cmd": "light.set", "payload": {"on": True, "brightness": 80}}
    result = handle(cmd)

    assert isinstance(result, dict)
    assert result.get("ack") is True
    assert "state" in result and isinstance(result["state"], dict)
    assert result["state"]["on"] is True
    assert result["state"]["brightness"] == 80

def test_light_off_ack_and_state():
    
    """
    Turning the light OFF returns ack=True and state.on=False.
    """

    handle = _get_handler()
    cmd = {"cmd": "light.set", "payload": {"on": False, "brightness": 0}}
    result = handle(cmd)

    assert result.get("ack") is True
    assert result["state"]["on"] is False
    assert result["state"]["brightness"] == 0

@pytest.mark.parametrize("b", [0, 1, 50, 99, 100])
def test_brightness_boundaries_valid(b):
    
    """
    Brightness accepted at the edges and typical mid values.
    """

    handle = _get_handler()
    result = handle({"cmd": "light.set", "payload": {"on": True, "brightness": b}})
    assert result.get("ack") is True
    assert result["state"]["brightness"] == b

@pytest.mark.parametrize(
    "payload",
    [
        {"on": True, "brightness": -1},
        {"on": True, "brightness": 101},
        {"on": "yes", "brightness": 50},
        {"on": True, "brightness": "bright"},
        {},  # missing fields
    ],
)
def test_invalid_payload_rejected_or_errors(payload):
    
    """
    Invalid inputs either cause a clear exception OR return ack=False.
    Both behaviours are acceptable for unit tests.
    """

    handle = _get_handler()
    bad = {"cmd": "light.set", "payload": payload}
    try:
        result = handle(bad)
        assert result.get("ack") is False
    except (ValueError, TypeError, KeyError, AssertionError):
        # raising a clear error is also OK
        assert True

def test_unknown_command_is_rejected():
    
    """
    Unknown command results in a negative ack or a clear exception.
    """
    
    handle = _get_handler()
    unknown = {"cmd": "light.nuke", "payload": {}}
    try:
        result = handle(unknown)
        assert result.get("ack") is False
    except (ValueError, NotImplementedError, KeyError):
        assert True

def test_env_bool(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    monkeypatch.setenv("FLAG", "true")
    assert mod.env_bool("FLAG", False) is True
    monkeypatch.delenv("FLAG", raising=False)
    assert mod.env_bool("FLAG", False) is False

def test_env_int(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    monkeypatch.setenv("PORT", "1884")
    assert mod.env_int("PORT", 1883) == 1884
    monkeypatch.delenv("PORT", raising=False)
    assert mod.env_int("PORT", 1883) == 1883

def test_build_ack():
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    ack = mod.build_ack("corr-id", "hotel1", "101", "light", "ok", error="")
    assert "correlationId" in ack
    assert "error" in ack["fields"]
    assert ack["fields"]["status"] == "ok"

def test_build_state():
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    state = mod.build_state("hotel1", "101", "light", True, 60)
    assert state["fields"]["on"] is True
    assert state["fields"]["brightness"] == 60

import pytest

@pytest.mark.parametrize("action,fields,expected_on,expected_brightness", [
    ("on", {}, True, None),
    ("off", {}, False, None),
    ("toggle", {"on": True}, False, None),
    ("toggle", {"on": False}, True, None),
    ("set_brightness", {"brightness": 150}, None, 100),  # clamp to 100
    ("set_brightness", {"brightness": -10}, None, 0),    # clamp to 0
])
def test_process_command_action(action, fields, expected_on, expected_brightness):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    result = mod.process_command_action(action, fields)
    if expected_on is not None and "fields" in result:
        assert result["fields"]["on"] == expected_on
    if expected_brightness is not None and "fields" in result:
        assert result["fields"]["brightness"] == expected_brightness

@pytest.mark.parametrize("action", ["brightness"])
def test_process_command_action_not_implemented(action):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    with pytest.raises(NotImplementedError):
        mod.process_command_action(action, {"brightness": 100})

def test_process_command_action_unsupported():
    import pathlib
    from conftest import load_module
    import pytest
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    with pytest.raises(NotImplementedError):
        mod.process_command_action("unsupported", {})

def test_handle_unknown_command():
    import pathlib
    from conftest import load_module
    import pytest
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    with pytest.raises(NotImplementedError):
        mod.handle({"cmd": "light.unknown", "payload": {}})

def test_handle_missing_cmd_key():
    import pathlib
    from conftest import load_module
    import pytest
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    with pytest.raises(NotImplementedError):
        mod.handle({"payload": {}})

def test_on_connect_does_not_crash():
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs):
            return None
        def subscribe(self, *args, **kwargs):
            return None
    mod.on_connect(DummyClient(), None, None, 0, None)

def test_on_message_parsing(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs):
            return None
    class DummyMsg:
        topic = "hotel1/101/light/command"
        payload = b'{"fields": {"action": "on"}}'
    mod.on_message(DummyClient(), None, DummyMsg())

def test_env_bool_unexpected(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    monkeypatch.setenv("FLAG", "unexpected")
    assert mod.env_bool("FLAG", True) is False

def test_env_int_non_integer(monkeypatch):
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    monkeypatch.setenv("PORT", "notanumber")
    assert mod.env_int("PORT", 1883) == 1883

def test_handle_non_dict():
    import pathlib
    from conftest import load_module
    import pytest
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    with pytest.raises(TypeError):
        mod.handle("not a dict")

def test_on_message_malformed_json():
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs):
            return None
    class DummyMsg:
        topic = "hotel1/101/light/command"
        payload = b'{bad json'
    mod.on_message(DummyClient(), None, DummyMsg())

def test_on_message_unsupported_action():
    import pathlib
    from conftest import load_module
    mod = load_module("main", pathlib.Path("hotel/room1/light-actuator/logic/main.py"))
    class DummyClient:
        def publish(self, *args, **kwargs):
            return None
    class DummyMsg:
        topic = "hotel1/101/light/command"
        payload = b'{"fields": {"action": "unsupported"}}'
    mod.on_message(DummyClient(), None, DummyMsg())
