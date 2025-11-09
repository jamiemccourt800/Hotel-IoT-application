import pytest
import importlib.util
import pathlib

# Dynamically load kafka_producer.py

import os
import sys
KAFKA_PRODUCER_PATH = "central/command/kafka_producer.py"
COMMAND_DIR = str(pathlib.Path("central/command").resolve())
if not os.path.exists(KAFKA_PRODUCER_PATH):
    import pytest; pytest.skip("Kafka producer module not found: {}".format(KAFKA_PRODUCER_PATH), allow_module_level=True)

# Ensure local package imports inside central/command resolve (e.g., `import config`)
if COMMAND_DIR not in sys.path:
    sys.path.insert(0, COMMAND_DIR)

spec = importlib.util.spec_from_file_location("kafka_producer", KAFKA_PRODUCER_PATH)
kafka_producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kafka_producer)

def test_start_producer_function_exists():
    assert hasattr(kafka_producer, "start_producer")
    assert callable(kafka_producer.start_producer)

def test_stop_producer_function_exists():
    assert hasattr(kafka_producer, "stop_producer")
    assert callable(kafka_producer.stop_producer)

def test_send_message_function_exists():
    assert hasattr(kafka_producer, "send_message")
    assert callable(kafka_producer.send_message)
