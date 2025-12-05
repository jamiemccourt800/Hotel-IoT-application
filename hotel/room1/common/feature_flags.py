"""Feature flag integration with GitLab Unleash for controlled feature releases.
Allows runtime control of simulator features without redeployment.

Usage:
------
from common import FeatureFlags

# Initialize with device config (for logging context)
flags = FeatureFlags(device_config)

# Check if a feature is enabled (defaults to True if Unleash unavailable)
if flags.is_enabled('external_control'):
    process_external_command()

if flags.is_enabled('ack_publishing', default=False):
    send_acknowledgment()

# Always cleanup in finally block
try:
    # ... service logic ...
finally:
    flags.shutdown()

Environment Variables Required:
-------------------------------
UNLEASH_URL:         GitLab Unleash API endpoint
UNLEASH_INSTANCE_ID: Authentication instance ID (from GitLab)
UNLEASH_APP_NAME:    Application identifier (e.g., 'actuator')

Exported:
---------
- FeatureFlags: Main class for feature flag evaluation
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
        
        # Read Unleash configuration from environment (matching lab pattern)
        unleash_url = os.getenv('UNLEASH_URL')
        unleash_instance_id = os.getenv('UNLEASH_INSTANCE_ID')
        unleash_app_name = os.getenv('UNLEASH_APP_NAME', 'room-simulator')
        
        # Only initialize if both URL and instance_id are provided
        if unleash_url and unleash_instance_id:
            try:
                self.client = UnleashClient(
                    url=unleash_url,
                    app_name=unleash_app_name,
                    instance_id=unleash_instance_id
                )
                self.client.initialize_client()
                self.logger.info('unleash-initialized', 'feature flags enabled',
                               url=unleash_url, app_name=unleash_app_name)
            except Exception as e:
                self.logger.error('unleash-init-failed', f'failed to initialize: {e}',
                                error=str(e))
                self.client = None
        else:
            self.logger.info('unleash-disabled', 'no UNLEASH_URL/INSTANCE_ID - feature flags disabled')
    
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
