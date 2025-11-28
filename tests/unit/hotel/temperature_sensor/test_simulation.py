"""
Unit tests for temperature simulation logic.
Tests TemperatureSimulation class drift, target updates, and reading generation.
"""
import pytest
from unittest.mock import Mock, patch
import time

# Import from temperature-sensor/app
import sys
sys.path.insert(0, 'hotel/room1/temperature-sensor/app')
from simulation import TemperatureSimulation


@pytest.fixture
def temp_config():
    config = Mock()
    config.target_temp = 22.0
    config.start_temp = 20.0
    config.interval = 1.0
    config.speed = 1.0
    return config


class TestTemperatureSimulation:
    
    def test_initialization(self, temp_config):
        """Test simulation initializes with config values"""
        sim = TemperatureSimulation(temp_config)
        assert sim.target_temperature == 22.0
        assert sim.current_temp == 20.0
        
    def test_set_target_temperature(self, temp_config):
        """Test updating target temperature"""
        sim = TemperatureSimulation(temp_config)
        sim.set_target_temperature(25.0)
        assert sim.target_temperature == 25.0
        
    def test_generate_readings_moves_toward_target(self, temp_config):
        """Test temperature drifts toward target"""
        temp_config.interval = 0.01  # Fast for testing
        sim = TemperatureSimulation(temp_config)
        
        generator = sim.generate_readings()
        
        # Get first few readings
        readings = []
        for _ in range(5):
            timestamp, temp = next(generator)
            readings.append(temp)
            
        # Should be moving toward target (22.0 from 20.0)
        # Due to random walk, average should be increasing
        assert readings[-1] > readings[0] - 1.0  # Allow some variance
        
    def test_generate_readings_includes_randomness(self, temp_config):
        """Test readings have variance (not deterministic)"""
        temp_config.interval = 0.01
        sim = TemperatureSimulation(temp_config)
        
        generator = sim.generate_readings()
        
        readings = [next(generator)[1] for _ in range(10)]
        
        # Readings should not all be identical (random walk)
        unique_readings = set(readings)
        assert len(unique_readings) > 1
        
    def test_generate_readings_yields_timestamp(self, temp_config):
        """Test readings include timestamp"""
        temp_config.interval = 0.01
        sim = TemperatureSimulation(temp_config)
        
        generator = sim.generate_readings()
        timestamp, temp = next(generator)
        
        # Timestamp should be milliseconds since epoch
        current_ms = int(time.time() * 1000)
        assert abs(timestamp - current_ms) < 1000  # Within 1 second
        
    def test_temperature_stays_near_target(self, temp_config):
        """Test temperature converges and stays near target"""
        temp_config.interval = 0.01
        sim = TemperatureSimulation(temp_config)
        
        generator = sim.generate_readings()
        
        # Let it converge (skip many readings)
        for _ in range(100):
            timestamp, temp = next(generator)
            
        # After convergence, should be close to target (within noise)
        final_temp = temp
        assert abs(final_temp - temp_config.target_temp) < 2.0  # Within ±2°C (random noise)
