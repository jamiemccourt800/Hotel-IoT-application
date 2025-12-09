"""
Unit tests for FeatureFlags wrapper module.

Tests cover:
- Initialization with/without environment variables
- Flag evaluation with different defaults
- Graceful error handling when Unleash unavailable
- Cleanup and resource management
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from common.feature_flags import FeatureFlags


class TestFeatureFlagsInitialization:
    """Test FeatureFlags initialization scenarios"""
    
    def test_init_with_valid_unleash_config(self, monkeypatch):
        """FeatureFlags should initialize UnleashClient when env vars are set"""
        # Setup environment
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api/v4/feature_flags/unleash/123')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'test-instance-id')
        monkeypatch.setenv('UNLEASH_APP_NAME', 'test-actuator')
        
        # Mock UnleashClient
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client_instance = Mock()
            mock_unleash.return_value = mock_client_instance
            
            # Create FeatureFlags instance
            flags = FeatureFlags()
            
            # Verify UnleashClient was initialized with correct params
            mock_unleash.assert_called_once_with(
                url='https://gitlab.example.com/api/v4/feature_flags/unleash/123',
                app_name='test-actuator',
                instance_id='test-instance-id'
            )
            mock_client_instance.initialize_client.assert_called_once()
            
            # Cleanup
            flags.shutdown()
    
    def test_init_without_unleash_url(self, monkeypatch):
        """FeatureFlags should not initialize client when UNLEASH_URL is missing"""
        # Clear environment
        monkeypatch.delenv('UNLEASH_URL', raising=False)
        monkeypatch.delenv('UNLEASH_INSTANCE_ID', raising=False)
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            flags = FeatureFlags()
            
            # UnleashClient should NOT be instantiated
            mock_unleash.assert_not_called()
            assert flags.client is None
            
            flags.shutdown()
    
    def test_init_without_instance_id(self, monkeypatch):
        """FeatureFlags should not initialize client when UNLEASH_INSTANCE_ID is missing"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.delenv('UNLEASH_INSTANCE_ID', raising=False)
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            flags = FeatureFlags()
            
            mock_unleash.assert_not_called()
            assert flags.client is None
            
            flags.shutdown()
    
    def test_init_with_default_app_name(self, monkeypatch):
        """FeatureFlags should use default app_name if not provided"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        monkeypatch.delenv('UNLEASH_APP_NAME', raising=False)
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            flags = FeatureFlags()
            
            # Should use default 'room-simulator'
            mock_unleash.assert_called_once()
            call_kwargs = mock_unleash.call_args.kwargs
            assert call_kwargs['app_name'] == 'room-simulator'
            
            flags.shutdown()
    
    def test_init_handles_unleash_client_error(self, monkeypatch):
        """FeatureFlags should handle UnleashClient initialization errors gracefully"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            # Simulate initialization error
            mock_unleash.side_effect = Exception("Connection failed")
            
            # Should not raise, should set client to None
            flags = FeatureFlags()
            assert flags.client is None
            
            flags.shutdown()


class TestFeatureFlagsEvaluation:
    """Test flag evaluation with is_enabled()"""
    
    def test_is_enabled_returns_true_when_flag_enabled(self, monkeypatch):
        """is_enabled() should return True when flag is enabled in Unleash"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_unleash.return_value = mock_client
            
            flags = FeatureFlags()
            result = flags.is_enabled('external_control')
            
            assert result is True
            mock_client.is_enabled.assert_called_once_with('external_control')
            
            flags.shutdown()
    
    def test_is_enabled_returns_false_when_flag_disabled(self, monkeypatch):
        """is_enabled() should return False when flag is disabled in Unleash"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = False
            mock_unleash.return_value = mock_client
            
            flags = FeatureFlags()
            result = flags.is_enabled('external_control')
            
            assert result is False
            
            flags.shutdown()
    
    def test_is_enabled_returns_default_when_client_none(self, monkeypatch):
        """is_enabled() should return default value when Unleash client not initialized"""
        monkeypatch.delenv('UNLEASH_URL', raising=False)
        
        flags = FeatureFlags()
        
        # Should return default True
        assert flags.is_enabled('external_control') is True
        assert flags.is_enabled('external_control', default=True) is True
        
        # Should return default False
        assert flags.is_enabled('some_flag', default=False) is False
        
        flags.shutdown()
    
    def test_is_enabled_handles_client_error(self, monkeypatch):
        """is_enabled() should return default when client raises exception"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.side_effect = Exception("Network error")
            mock_unleash.return_value = mock_client
            
            flags = FeatureFlags()
            
            # Should return default instead of raising
            result = flags.is_enabled('external_control', default=True)
            assert result is True
            
            result = flags.is_enabled('other_flag', default=False)
            assert result is False
            
            flags.shutdown()
    
    def test_is_enabled_with_various_flag_names(self, monkeypatch):
        """is_enabled() should work with different flag names"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_unleash.return_value = mock_client
            
            flags = FeatureFlags()
            
            # Test various flag names
            flags.is_enabled('external_control')
            flags.is_enabled('local_control')
            flags.is_enabled('ack_publishing')
            flags.is_enabled('adaptive_control')
            
            # Verify all were checked
            assert mock_client.is_enabled.call_count == 4
            
            flags.shutdown()


class TestFeatureFlagsShutdown:
    """Test cleanup and resource management"""
    
    def test_shutdown_destroys_client(self, monkeypatch):
        """shutdown() should call destroy() on UnleashClient"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_unleash.return_value = mock_client
            
            flags = FeatureFlags()
            flags.shutdown()
            
            mock_client.destroy.assert_called_once()
    
    def test_shutdown_handles_none_client(self):
        """shutdown() should handle None client gracefully"""
        flags = FeatureFlags()
        assert flags.client is None
        
        # Should not raise
        flags.shutdown()
    
    def test_shutdown_handles_destroy_error(self, monkeypatch):
        """shutdown() should handle destroy() errors gracefully"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        with patch('common.feature_flags.UnleashClient') as mock_unleash:
            mock_client = Mock()
            mock_client.destroy.side_effect = Exception("Cleanup error")
            mock_unleash.return_value = mock_client
            
            flags = FeatureFlags()
            
            # Should not raise exception
            flags.shutdown()


class TestFeatureFlagsWithDeviceConfig:
    """Test FeatureFlags integration with device config for logging"""
    
    def test_init_with_device_config(self, monkeypatch):
        """FeatureFlags should accept device_config for logger context"""
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.setenv('UNLEASH_INSTANCE_ID', 'instance-123')
        
        # Create mock device config
        mock_device_config = Mock()
        mock_device_config.hotel_id = 'hotel_01'
        mock_device_config.room = 101
        mock_device_config.sensor = 'temperature-actuator'
        
        with patch('common.feature_flags.UnleashClient'):
            flags = FeatureFlags(mock_device_config)
            
            # Logger should have device context
            assert flags.logger is not None
            
            flags.shutdown()


class TestFeatureFlagsGracefulDegradation:
    """Test graceful degradation scenarios"""
    
    def test_all_flags_default_true_when_unleash_unavailable(self):
        """All flags should default to True for backward compatibility"""
        flags = FeatureFlags()
        
        # Core flags should all default to True
        assert flags.is_enabled('external_control') is True
        assert flags.is_enabled('local_control') is True
        assert flags.is_enabled('ack_publishing') is True
        assert flags.is_enabled('adaptive_control') is True
        
        flags.shutdown()
    
    def test_custom_defaults_respected(self):
        """Custom defaults should be respected when Unleash unavailable"""
        flags = FeatureFlags()
        
        # Custom default False should be respected
        assert flags.is_enabled('experimental_feature', default=False) is False
        assert flags.is_enabled('beta_mode', default=False) is False
        
        flags.shutdown()
    
    def test_partial_environment_variables(self, monkeypatch):
        """Should handle partial environment variable configuration"""
        # Only URL, no instance_id
        monkeypatch.setenv('UNLEASH_URL', 'https://gitlab.example.com/api')
        monkeypatch.delenv('UNLEASH_INSTANCE_ID', raising=False)
        
        flags = FeatureFlags()
        
        # Should fall back to defaults
        assert flags.client is None
        assert flags.is_enabled('external_control') is True
        
        flags.shutdown()
