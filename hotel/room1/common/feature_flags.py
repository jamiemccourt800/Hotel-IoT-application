"""
Feature flag integration with GitLab Unleash for controlled feature releases.
Allows runtime control of simulator features without redeployment.
"""
import os
from typing import Optional
from UnleashClient import UnleashClient
from .logging import get_logger

class FeatureFlags:
    """
    Feature flag manager using GitLab Unleash.
    Enables controlled rollout and A/B testing of simulator features.
    """
    
    def __init__(self, device_config=None):
        self.logger = get_logger("feature-flags", device_config)
        self.client: Optional[UnleashClient] = None
        
        # Read Unleash configuration from environment
        unleash_url = os.getenv('UNLEASH_URL')
        unleash_app_name = os.getenv('UNLEASH_APP_NAME', 'room-simulator')
        unleash_environment = os.getenv('UNLEASH_ENVIRONMENT', 'development')
        unleash_client_key = os.getenv('UNLEASH_CLIENT_KEY', '*:default.secret')
        
        # Only initialize if Unleash URL is provided
        if unleash_url:
            try:
                self.client = UnleashClient(
                    url=unleash_url,
                    app_name=unleash_app_name,
                    environment=unleash_environment,
                    custom_headers={'Authorization': unleash_client_key}
                )
                self.client.initialize_client()
                self.logger.info('unleash-initialized', 'feature flags enabled',
                               url=unleash_url, app_name=unleash_app_name,
                               environment=unleash_environment)
            except Exception as e:
                self.logger.error('unleash-init-failed', f'failed to initialize: {e}',
                                error=str(e))
                self.client = None
        else:
            self.logger.info('unleash-disabled', 'no UNLEASH_URL - feature flags disabled')
    
    def is_enabled(self, flag_name: str, default: bool = True) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag in GitLab
            default: Default value if Unleash is not configured
            
        Returns:
            True if feature is enabled, False otherwise
        """
        if self.client is None:
            # If Unleash not configured, return default (typically True for existing features)
            return default
        
        try:
            enabled = self.client.is_enabled(flag_name)
            self.logger.debug('flag-checked', f'{flag_name}: {enabled}',
                            flag=flag_name, enabled=enabled)
            return enabled
        except Exception as e:
            self.logger.error('flag-check-error', f'error checking {flag_name}: {e}',
                            flag=flag_name, error=str(e))
            return default
    
    def shutdown(self):
        """Cleanup Unleash client"""
        if self.client:
            try:
                self.client.destroy()
            except Exception:
                pass
