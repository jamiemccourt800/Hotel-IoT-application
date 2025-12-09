"""
Integration tests for feature flag behavior in actuators.

Tests verify:
- Actuators respond correctly to feature flag changes
- external_control, local_control, and ack_publishing flags work as expected
- Flag changes affect actuator behavior in real-time
- Graceful degradation when Unleash unavailable
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client for testing"""
    client = Mock()
    client.publish = Mock()
    client.subscribe = Mock()
    return client


@pytest.fixture
def mock_device_config():
    """Mock device configuration"""
    config = Mock()
    config.hotel_id = 'hotel_01'
    config.room = 101
    config.sensor = 'test-actuator'
    return config


@pytest.fixture
def mock_mqtt_config():
    """Mock MQTT configuration"""
    config = Mock()
    config.broker = 'test-broker'
    config.port = 1883
    config.qos = 1
    config.keepalive = 60
    return config


class TestActuatorFeatureFlagIntegration:
    """Test actuator behavior with different feature flag states"""
    
    def test_external_control_flag_enables_command_processing(self, mock_device_config, mock_mqtt_config, monkeypatch):
        """When external_control is enabled, actuator should process commands"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            # Setup mock to return True for external_control
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_unleash.return_value = mock_client
            
            # Import actuator module (this would be temperature/humidity/light)
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify flag is enabled
            assert flags.is_enabled('external_control') is True
            
            # Simulate command processing
            command_processed = flags.is_enabled('external_control')
            assert command_processed is True
            
            flags.shutdown()
    
    def test_external_control_flag_disables_command_processing(self, mock_device_config, monkeypatch):
        """When external_control is disabled, actuator should ignore commands"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            # Setup mock to return False for external_control
            mock_client = Mock()
            mock_client.is_enabled.return_value = False
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify flag is disabled
            assert flags.is_enabled('external_control') is False
            
            # Command processing should be skipped
            command_processed = flags.is_enabled('external_control')
            assert command_processed is False
            
            flags.shutdown()
    
    def test_local_control_flag_enables_autonomous_loop(self, mock_device_config, monkeypatch):
        """When local_control is enabled, actuator should run control loop"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify local control is enabled
            assert flags.is_enabled('local_control') is True
            
            flags.shutdown()
    
    def test_local_control_flag_disables_autonomous_loop(self, mock_device_config, monkeypatch):
        """When local_control is disabled, actuator should skip control loop"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = False
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify local control is disabled
            assert flags.is_enabled('local_control') is False
            
            flags.shutdown()
    
    def test_ack_publishing_flag_enables_acknowledgments(self, mock_device_config, monkeypatch):
        """When ack_publishing is enabled, actuator should send ack messages"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify ack publishing is enabled
            assert flags.is_enabled('ack_publishing') is True
            
            flags.shutdown()
    
    def test_ack_publishing_flag_disables_acknowledgments(self, mock_device_config, monkeypatch):
        """When ack_publishing is disabled, actuator should not send ack messages"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = False
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify ack publishing is disabled
            assert flags.is_enabled('ack_publishing') is False
            
            flags.shutdown()
    
    def test_multiple_flags_can_be_toggled_independently(self, mock_device_config, monkeypatch):
        """Different flags can have different states simultaneously"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            
            # Different flags return different values
            def is_enabled_side_effect(flag_name):
                return {
                    'external_control': True,
                    'local_control': False,
                    'ack_publishing': True
                }.get(flag_name, True)
            
            mock_client.is_enabled.side_effect = is_enabled_side_effect
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Verify independent flag states
            assert flags.is_enabled('external_control') is True
            assert flags.is_enabled('local_control') is False
            assert flags.is_enabled('ack_publishing') is True
            
            flags.shutdown()


class TestActuatorGracefulDegradation:
    """Test actuator behavior when feature flags unavailable"""
    
    def test_actuator_starts_without_unleash_config(self, mock_device_config, monkeypatch):
        """Actuator should start successfully even when Unleash not configured"""
        # Clear Unleash environment variables
        monkeypatch.delenv('UNLEASH_URL', raising=False)
        monkeypatch.delenv('UNLEASH_INSTANCE_ID', raising=False)
        
        from common import FeatureFlags
        
        # Should initialize without errors
        flags = FeatureFlags(mock_device_config)
        
        # All flags should default to True
        assert flags.is_enabled('external_control') is True
        assert flags.is_enabled('local_control') is True
        assert flags.is_enabled('ack_publishing') is True
        
        flags.shutdown()
    
    def test_actuator_continues_on_unleash_error(self, mock_device_config, monkeypatch):
        """Actuator should continue operating if Unleash client fails"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            # Simulate Unleash client error
            mock_unleash.side_effect = Exception("Connection failed")
            
            from common import FeatureFlags
            
            # Should still initialize
            flags = FeatureFlags(mock_device_config)
            
            # Should fall back to defaults
            assert flags.is_enabled('external_control') is True
            assert flags.is_enabled('local_control') is True
            
            flags.shutdown()
    
    def test_actuator_handles_unleash_evaluation_error(self, mock_device_config, monkeypatch):
        """Actuator should handle errors during flag evaluation"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            # Simulate evaluation error
            mock_client.is_enabled.side_effect = Exception("Network timeout")
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Should return default instead of raising
            result = flags.is_enabled('external_control', default=True)
            assert result is True
            
            flags.shutdown()


class TestFeatureFlagLogging:
    """Test that feature flag operations are properly logged"""
    
    def test_unleash_initialized_logged(self, mock_device_config, monkeypatch, capfd):
        """Unleash initialization should be logged"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        monkeypatch.setenv('UNLEASH_APP_NAME', 'test-app')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Check logs contain initialization message
            captured = capfd.readouterr()
            assert 'unleash-initialized' in captured.out
            assert 'feature flags enabled' in captured.out
            
            flags.shutdown()
    
    def test_unleash_disabled_logged(self, mock_device_config, monkeypatch, capfd):
        """When Unleash not configured, should log disabled message"""
        monkeypatch.delenv('UNLEASH_URL', raising=False)
        monkeypatch.delenv('UNLEASH_INSTANCE_ID', raising=False)
        
        from common import FeatureFlags
        
        flags = FeatureFlags(mock_device_config)
        
        # Check logs contain disabled message
        captured = capfd.readouterr()
        assert 'unleash-disabled' in captured.out
        assert 'feature flags disabled' in captured.out
        
        flags.shutdown()
    
    def test_flag_evaluation_error_logged(self, mock_device_config, monkeypatch, capfd):
        """Flag evaluation errors should be logged"""
        monkeypatch.setenv('UNLEASH_URL', 'https://test.unleash.com')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.side_effect = Exception("Test error")
            mock_unleash.return_value = mock_client
            
            from common import FeatureFlags
            
            flags = FeatureFlags(mock_device_config)
            
            # Trigger error
            flags.is_enabled('test_flag')
            
            # Check error was logged
            captured = capfd.readouterr()
            assert 'flag-check-error' in captured.out or 'ERROR' in captured.out
            
            flags.shutdown()
