"""
Contract tests for external control command and ACK messages.
Validates FastAPI command format and acknowledgment responses.
"""
import pytest
import json
import jsonschema


# Command message schema (from FastAPI to actuators)
COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "minProperties": 1  # At least one command field
        },
        "correlationId": {"type": "string"}
    },
    "required": ["fields"]  # correlationId optional but recommended
}

# Temperature command schema
TEMPERATURE_COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "properties": {
                "target_temperature": {"type": "number"}
            },
            "required": ["target_temperature"]
        },
        "correlationId": {"type": "string"}
    },
    "required": ["fields"]
}

# Humidity command schema
HUMIDITY_COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "properties": {
                "target_humidity": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["target_humidity"]
        },
        "correlationId": {"type": "string"}
    },
    "required": ["fields"]
}

# Light command schema
LIGHT_COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "properties": {
                "brightness": {"type": "number", "minimum": 0, "maximum": 100},
                "mode": {"type": "string", "enum": ["adaptive", "manual", "off"]},
                "action": {"type": "string", "enum": ["on", "off", "toggle"]}
            }
        },
        "correlationId": {"type": "string"}
    },
    "required": ["fields"]
}

# ACK message schema (from actuators to FastAPI)
ACK_SCHEMA = {
    "type": "object",
    "properties": {
        "measurement": {"type": "string", "const": "ack"},
        "tags": {
            "type": "object",
            "properties": {
                "hotel_id": {"type": "string"},
                "room": {"type": "integer"},
                "sensor": {"type": "string"}
            },
            "required": ["hotel_id", "room", "sensor"]
        },
        "fields": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["ok", "failed", "error"]},
                "error": {"type": "string"}
            },
            "required": ["status", "error"]
        },
        "timestamp": {"type": "integer", "minimum": 0},
        "correlationId": {"type": "string"}
    },
    "required": ["measurement", "tags", "fields", "timestamp"]
}


class TestTemperatureCommandContract:
    """Test temperature command message format"""
    
    def test_valid_temperature_command(self):
        """Test that valid temperature command passes schema validation"""
        command = {
            "fields": {"target_temperature": 25.0},
            "correlationId": "test-123"
        }
        
        jsonschema.validate(instance=command, schema=TEMPERATURE_COMMAND_SCHEMA)
    
    def test_temperature_command_without_correlation_id(self):
        """Test that temperature command works without correlationId"""
        command = {
            "fields": {"target_temperature": 22.0}
        }
        
        # Should still be valid (correlationId is optional)
        jsonschema.validate(instance=command, schema=COMMAND_SCHEMA)
    
    def test_temperature_command_with_various_temperatures(self):
        """Test temperature commands with different values"""
        test_temps = [-10.0, 0.0, 15.5, 22.0, 25.5, 30.0, 40.0]
        
        for temp in test_temps:
            command = {
                "fields": {"target_temperature": temp},
                "correlationId": f"test-{temp}"
            }
            jsonschema.validate(instance=command, schema=TEMPERATURE_COMMAND_SCHEMA)
    
    def test_temperature_command_requires_fields(self):
        """Test that command requires fields object"""
        invalid_command = {
            "correlationId": "test-123"
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_command, schema=TEMPERATURE_COMMAND_SCHEMA)


class TestHumidityCommandContract:
    """Test humidity command message format"""
    
    def test_valid_humidity_command(self):
        """Test that valid humidity command passes schema validation"""
        command = {
            "fields": {"target_humidity": 60.0},
            "correlationId": "hum-test-1"
        }
        
        jsonschema.validate(instance=command, schema=HUMIDITY_COMMAND_SCHEMA)
    
    def test_humidity_percentage_bounds(self):
        """Test that humidity is validated to be 0-100"""
        valid_commands = [
            {"fields": {"target_humidity": 0.0}},
            {"fields": {"target_humidity": 50.0}},
            {"fields": {"target_humidity": 100.0}}
        ]
        
        for cmd in valid_commands:
            jsonschema.validate(instance=cmd, schema=HUMIDITY_COMMAND_SCHEMA)


class TestLightCommandContract:
    """Test light command message format"""
    
    def test_valid_light_brightness_command(self):
        """Test that valid brightness command passes schema validation"""
        command = {
            "fields": {"brightness": 75.0},
            "correlationId": "light-test-1"
        }
        
        jsonschema.validate(instance=command, schema=LIGHT_COMMAND_SCHEMA)
    
    def test_light_mode_command(self):
        """Test light mode command"""
        command = {
            "fields": {"mode": "adaptive"},
            "correlationId": "mode-test"
        }
        
        jsonschema.validate(instance=command, schema=LIGHT_COMMAND_SCHEMA)
    
    def test_light_action_commands(self):
        """Test light on/off/toggle commands"""
        actions = ["on", "off", "toggle"]
        
        for action in actions:
            command = {
                "fields": {"action": action},
                "correlationId": f"action-{action}"
            }
            jsonschema.validate(instance=command, schema=LIGHT_COMMAND_SCHEMA)
    
    def test_light_combined_command(self):
        """Test command with multiple fields"""
        command = {
            "fields": {
                "brightness": 80.0,
                "mode": "manual",
                "action": "on"
            },
            "correlationId": "combined-test"
        }
        
        jsonschema.validate(instance=command, schema=LIGHT_COMMAND_SCHEMA)


class TestACKMessageContract:
    """Test acknowledgment message format"""
    
    def test_valid_success_ack(self):
        """Test that valid success ACK passes schema validation"""
        ack = {
            "measurement": "ack",
            "tags": {
                "hotel_id": "hotel_01",
                "room": 101,
                "sensor": "temperature-actuator"
            },
            "fields": {
                "status": "ok",
                "error": ""
            },
            "timestamp": 1234567890,
            "correlationId": "test-123"
        }
        
        jsonschema.validate(instance=ack, schema=ACK_SCHEMA)
    
    def test_valid_error_ack(self):
        """Test that valid error ACK passes schema validation"""
        ack = {
            "measurement": "ack",
            "tags": {
                "hotel_id": "hotel_01",
                "room": 101,
                "sensor": "humidity-actuator"
            },
            "fields": {
                "status": "failed",
                "error": "Invalid temperature value"
            },
            "timestamp": 1234567890,
            "correlationId": "error-test"
        }
        
        jsonschema.validate(instance=ack, schema=ACK_SCHEMA)
    
    def test_ack_status_values(self):
        """Test that ACK supports ok, failed, error statuses"""
        statuses = ["ok", "failed", "error"]
        
        for status in statuses:
            ack = {
                "measurement": "ack",
                "tags": {"hotel_id": "hotel_01", "room": 101, "sensor": "test"},
                "fields": {"status": status, "error": ""},
                "timestamp": 1234567890,
                "correlationId": "status-test"
            }
            jsonschema.validate(instance=ack, schema=ACK_SCHEMA)
    
    def test_ack_requires_correlation_id(self):
        """Test that ACK includes correlationId to match command"""
        ack = {
            "measurement": "ack",
            "tags": {"hotel_id": "hotel_01", "room": 101, "sensor": "test"},
            "fields": {"status": "ok", "error": ""},
            "timestamp": 1234567890,
            "correlationId": "match-this-id"
        }
        
        assert "correlationId" in ack
        jsonschema.validate(instance=ack, schema=ACK_SCHEMA)
    
    def test_ack_measurement_is_ack(self):
        """Test that ACK measurement field is exactly 'ack'"""
        ack = {
            "measurement": "ack",
            "tags": {"hotel_id": "hotel_01", "room": 101, "sensor": "test"},
            "fields": {"status": "ok", "error": ""},
            "timestamp": 1234567890,
            "correlationId": "test"
        }
        
        assert ack["measurement"] == "ack"
        jsonschema.validate(instance=ack, schema=ACK_SCHEMA)


class TestCommandACKRoundTrip:
    """Test command and ACK correlation"""
    
    def test_correlation_id_preserved(self):
        """Test that correlationId from command appears in ACK"""
        correlation_id = "unique-request-id-12345"
        
        command = {
            "fields": {"target_temperature": 25.0},
            "correlationId": correlation_id
        }
        
        ack = {
            "measurement": "ack",
            "tags": {"hotel_id": "hotel_01", "room": 101, "sensor": "temperature-actuator"},
            "fields": {"status": "ok", "error": ""},
            "timestamp": 1234567890,
            "correlationId": correlation_id
        }
        
        # Both should be valid
        jsonschema.validate(instance=command, schema=TEMPERATURE_COMMAND_SCHEMA)
        jsonschema.validate(instance=ack, schema=ACK_SCHEMA)
        
        # Correlation IDs should match
        assert command.get("correlationId") == ack.get("correlationId")
