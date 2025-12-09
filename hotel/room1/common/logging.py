"""Unified structured logging system.
Replaces duplicate log() functions across all services with consistent formatting.

Usage:
------
from common import get_logger

# Create logger with device context
logger = get_logger('temperature-actuator', device_config)

# Structured logging with consistent format
logger.info('startup', 'actuator initialized', target_temp=21.0)
logger.warning('threshold-exceeded', 'temperature above limit', temp=32.5)
logger.error('mqtt-publish-failed', 'failed to send telemetry', error=str(e))

# Logs appear as:
# 2025-12-05T10:30:45.123Z | INFO  | temperature-actuator | hotel_01/101/temp-act | event=startup | msg="actuator initialized" | target_temp=21.0

Exported:
---------
- HotelLogger:  Main logger class with structured output
- get_logger(): Factory function (recommended for consistent device context)
"""
import time
from typing import Dict, Any, Optional

class HotelLogger:
    """Structured logger for hotel services"""
    
    def __init__(self, service_name: str, hotel_id: str = "unknown", room: str = "unknown", sensor: str = "unknown"):
        self.service_name = service_name
        self.hotel_id = hotel_id
        self.room = str(room)  # Convert room to string for logging display
        self.sensor = sensor
        
    def log(self, level: str, event: str, msg: str, **fields):
        """Structured logging with consistent format across all services"""
        # Generate timestamp in same format as existing services
        ts = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + f'.{int(time.time()*1000)%1000:03d}Z'
        
        # Extract device info from fields or use instance defaults
        hotel = fields.pop('hotel_id', self.hotel_id)
        room = fields.pop('room', self.room)
        sensor = fields.pop('sensor', self.sensor)
        device = f'{hotel}/{room}/{sensor}'
        
        # Build log entry matching existing format
        base = [ts, f'{level.upper():<5}', self.service_name, f'{device:<28}', f'event={event}', f'msg="{msg}"']
        
        # Add additional fields
        for k, v in fields.items():
            if isinstance(v, bool):
                v = str(v).lower()
            base.append(f'{k}={v}')
            
        print(' | '.join(base), flush=True)
        
    def debug(self, event: str, msg: str, **fields):
        """Log debug level message"""
        self.log('DEBUG', event, msg, **fields)
        
    def info(self, event: str, msg: str, **fields):
        """Log info level message"""
        self.log('INFO', event, msg, **fields)
        
    def warning(self, event: str, msg: str, **fields):
        """Log warning level message"""
        self.log('WARNING', event, msg, **fields)
        
    def error(self, event: str, msg: str, **fields):
        """Log error level message"""
        self.log('ERROR', event, msg, **fields)

def get_logger(service_name: str, device_config=None) -> HotelLogger:
    """Factory function to create loggers with device configuration"""
    if device_config:
        return HotelLogger(
            service_name, 
            device_config.hotel_id, 
            device_config.room, 
            device_config.sensor
        )
    return HotelLogger(service_name)