import pytest
import importlib.util
import pathlib

# Test actuator route logic

import os
import sys
ACTUATOR_PATH = "central/command/routes/actuator.py"
COMMAND_DIR = str(pathlib.Path("central/command").resolve())
if not os.path.exists(ACTUATOR_PATH):
    import pytest; pytest.skip("Actuator module not found: {}".format(ACTUATOR_PATH), allow_module_level=True)

# Ensure local imports inside central/command resolve (eg. kafka_producer)
if COMMAND_DIR not in sys.path:
    sys.path.insert(0, COMMAND_DIR)

spec = importlib.util.spec_from_file_location("actuator", ACTUATOR_PATH)
actuator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actuator)

def test_set_light_action_functions_exist():
    """Test that the set_light_action function exists."""
    assert hasattr(actuator, "set_light_action")
    assert callable(actuator.set_light_action)

def test_set_temperature_function_exists():
    """Test that the set_temperature function exists."""
    assert hasattr(actuator, "set_temperature")
    assert callable(actuator.set_temperature)

