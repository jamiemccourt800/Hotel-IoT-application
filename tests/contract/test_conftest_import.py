import pathlib

def test_load_module_imports_alert_agent(load_module):
    mod = load_module("hotel.room1.alert-agent.app.main")
    assert hasattr(mod, "on_message")

def test_load_module_with_invalid_name(load_module):
    import pytest
    with pytest.raises(ImportError):
        load_module("not.a.real.module")

def test_load_module_with_non_string_argument(load_module):
    import pytest
    with pytest.raises(Exception):
        load_module(12345)
