"""
Contract tests for MQTT message schemas.
Validates that all telemetry messages conform to expected schema.
"""
import pytest
import json
import jsonschema

from common.schemas import TemperatureTelemetry, HumidityTelemetry, LightTelemetry, MessageTags
from common.utils import now_ms


# Schema definitions
TEMPERATURE_SCHEMA = {
    "type": "object",
    "properties": {
        "measurement": {"type": "string", "const": "temperature"},
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
                "temperatureC": {"type": "number"}
            },
            "required": ["temperatureC"]
        },
        "timestamp": {"type": "integer", "minimum": 0}
    },
    "required": ["measurement", "tags", "fields", "timestamp"]
}

HUMIDITY_SCHEMA = {
    "type": "object",
    "properties": {
        "measurement": {"type": "string", "const": "humidity"},
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
                "humidityPercent": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["humidityPercent"]
        },
        "timestamp": {"type": "integer", "minimum": 0}
    },
    "required": ["measurement", "tags", "fields", "timestamp"]
}

LIGHT_SCHEMA = {
    "type": "object",
    "properties": {
        "measurement": {"type": "string", "const": "light-state"},
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
                "brightness": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["brightness"]
        },
        "timestamp": {"type": "integer", "minimum": 0}
    },
    "required": ["measurement", "tags", "fields", "timestamp"]
}


class TestTemperatureTelemetrySchema:
    """Test that temperature telemetry conforms to schema"""
    
    def test_valid_temperature_telemetry(self):
        """Test that valid temperature telemetry passes schema validation"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="temperature-sensor")
        telemetry = TemperatureTelemetry(tags, 22.5, now_ms())
        
        telemetry_dict = telemetry.to_dict()
        
        # Should not raise exception
        jsonschema.validate(instance=telemetry_dict, schema=TEMPERATURE_SCHEMA)
    
    def test_temperature_measurement_field(self):
        """Test that measurement field is exactly 'temperature'"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="temp-sensor")
        telemetry = TemperatureTelemetry(tags, 20.0, now_ms())
        
        assert telemetry.to_dict()["measurement"] == "temperature"
    
    def test_temperature_has_required_fields(self):
        """Test that all required fields are present"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="temp-sensor")
        telemetry = TemperatureTelemetry(tags, 25.0, now_ms())
        telemetry_dict = telemetry.to_dict()
        
        assert "measurement" in telemetry_dict
        assert "tags" in telemetry_dict
        assert "fields" in telemetry_dict
        assert "timestamp" in telemetry_dict
        assert "temperatureC" in telemetry_dict["fields"]


class TestHumidityTelemetrySchema:
    """Test that humidity telemetry conforms to schema"""
    
    def test_valid_humidity_telemetry(self):
        """Test that valid humidity telemetry passes schema validation"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="humidity-sensor")
        telemetry = HumidityTelemetry(tags, 55.5, now_ms())
        
        telemetry_dict = telemetry.to_dict()
        
        # Should not raise exception
        jsonschema.validate(instance=telemetry_dict, schema=HUMIDITY_SCHEMA)
    
    def test_humidity_measurement_field(self):
        """Test that measurement field is exactly 'humidity'"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="humidity-sensor")
        telemetry = HumidityTelemetry(tags, 50.0, now_ms())
        
        assert telemetry.to_dict()["measurement"] == "humidity"
    
    def test_humidity_percentage_bounds(self):
        """Test that humidity percentage is between 0-100"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="humidity-sensor")
        
        # Valid values
        telemetry_min = HumidityTelemetry(tags, 0.0, now_ms())
        telemetry_max = HumidityTelemetry(tags, 100.0, now_ms())
        
        jsonschema.validate(instance=telemetry_min.to_dict(), schema=HUMIDITY_SCHEMA)
        jsonschema.validate(instance=telemetry_max.to_dict(), schema=HUMIDITY_SCHEMA)


class TestLightTelemetrySchema:
    """Test that light telemetry conforms to schema"""
    
    def test_valid_light_telemetry(self):
        """Test that valid light telemetry passes schema validation"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="light-sensor")
        telemetry = LightTelemetry(tags, 75.0, now_ms())
        
        telemetry_dict = telemetry.to_dict()
        
        # Should not raise exception
        jsonschema.validate(instance=telemetry_dict, schema=LIGHT_SCHEMA)
    
    def test_light_measurement_field(self):
        """Test that measurement field is exactly 'light-state'"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="light-sensor")
        telemetry = LightTelemetry(tags, 80.0, now_ms())
        
        assert telemetry.to_dict()["measurement"] == "light-state"
    
    def test_brightness_percentage_bounds(self):
        """Test that brightness is between 0-100"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="light-sensor")
        
        # Valid values
        telemetry_off = LightTelemetry(tags, 0.0, now_ms())
        telemetry_full = LightTelemetry(tags, 100.0, now_ms())
        
        jsonschema.validate(instance=telemetry_off.to_dict(), schema=LIGHT_SCHEMA)
        jsonschema.validate(instance=telemetry_full.to_dict(), schema=LIGHT_SCHEMA)


class TestMessageTagsSchema:
    """Test that message tags conform to expected structure"""
    
    def test_tags_structure(self):
        """Test that tags have hotel_id, room, and sensor"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="test-sensor")
        tags_dict = tags.to_dict()
        
        assert "hotel_id" in tags_dict
        assert "room" in tags_dict
        assert "sensor" in tags_dict
        
        assert isinstance(tags_dict["hotel_id"], str)
        assert isinstance(tags_dict["room"], int)
        assert isinstance(tags_dict["sensor"], str)
    
    def test_tags_hotel_id_format(self):
        """Test that hotel_id follows expected format"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="sensor")
        
        assert tags.hotel_id.startswith("hotel_")
    
    def test_tags_room_is_positive_integer(self):
        """Test that room number is a positive integer"""
        tags = MessageTags(hotel_id="hotel_01", room=101, sensor="sensor")
        
        assert isinstance(tags.room, int)
        assert tags.room > 0
