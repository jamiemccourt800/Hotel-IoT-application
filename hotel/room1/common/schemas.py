"""
Centralized message schemas for type safety and consistency.
Ensures all services use identical message formats for MQTT communication.
"""
import time
from dataclasses import dataclass
from typing import Dict, Any, Union

@dataclass
class MessageTags:
    """Standard tags for all messages"""
    hotel_id: str
    room: int  
    sensor: str

@dataclass
class BaseMessage:
    """Base class for all MQTT messages"""
    tags: MessageTags
    measurement: str = ""
    timestamp: int = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = int(time.time() * 1000)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MQTT-ready dictionary"""
        return {
            "measurement": self.measurement,
            "tags": {
                "hotel_id": self.tags.hotel_id,
                "room": self.tags.room,
                "sensor": self.tags.sensor
            },
            "fields": getattr(self, 'fields', {}),
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create message from dictionary"""
        tags = MessageTags(**data.get('tags', {}))
        instance = cls(
            measurement=data.get('measurement', ''),
            tags=tags,
            timestamp=data.get('timestamp')
        )
        if 'fields' in data:
            instance.fields = data['fields']
        return instance

@dataclass
class TemperatureTelemetry(BaseMessage):
    """Temperature sensor telemetry message"""
    measurement: str = "temperature"
    fields: Dict[str, Union[float, int]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.fields is None:
            self.fields = {}

@dataclass
class LightTelemetry(BaseMessage):
    """Light sensor/actuator telemetry message"""
    measurement: str = "light-state"
    fields: Dict[str, Union[float, bool, int, str]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.fields is None:
            self.fields = {}

@dataclass
class HumidityTelemetry(BaseMessage):
    """Humidity sensor telemetry message"""
    measurement: str = "humidity"
    fields: Dict[str, Union[float, int]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.fields is None:
            self.fields = {}

@dataclass
class AlertMessage(BaseMessage):
    """Alert/status message"""
    measurement: str = "alert"
    fields: Dict[str, str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.fields is None:
            self.fields = {}

@dataclass
class CommandMessage(BaseMessage):
    """Command message for actuators"""
    measurement: str = "command"
    fields: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.fields is None:
            self.fields = {}

@dataclass
class AckMessage(BaseMessage):
    """Acknowledgment message"""
    measurement: str = "ack"
    fields: Dict[str, str] = None
    correlation_id: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.fields is None:
            self.fields = {}
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.correlation_id:
            result["correlationId"] = self.correlation_id
        return result