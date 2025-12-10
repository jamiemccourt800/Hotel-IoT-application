from UnleashClient import UnleashClient
from flask import Flask, render_template
import requests
import logging
from typing import Optional
import os


class FeatureFlagController:
    def __init__(self, app: Flask):
        self.app = app
        self.logger = logging.getLogger("feature-flag-controller")
        self.client: Optional[UnleashClient] = None
        
        unleash_url = os.getenv('UNLEASH_URL')
        unleash_instance_id = os.getenv('UNLEASH_INSTANCE_ID')
        unleash_app_name = os.getenv('UNLEASH_APP_NAME', 'central-command')
        
        if unleash_url and unleash_instance_id:
            try:
                self.client = UnleashClient(
                    url=unleash_url,
                    app_name=unleash_app_name,
                    instance_id=unleash_instance_id
                )
                self.client.initialize_client()
                self.logger.info("Unleash initialized: feature flags enabled (url=%s, app_name=%s)",
    unleash_url,
    unleash_app_name,)
            except Exception as e:
                self.logger.error('unleash-init-failed', f'failed to initialize: {e}',
                                error=str(e))
                self.client = None
        else:
            self.logger.info('unleash-disabled', 'no UNLEASH_URL/INSTANCE_ID - feature flags disabled')
    
    def is_enabled(self, flag_name: str, default: bool = True) -> bool:
        if self.client is None:
            return default
        
        try:
            enabled = self.client.is_enabled(flag_name)
            self.logger.debug('flag-checked', f'{flag_name}: {enabled}',
                            flag=flag_name, enabled=enabled)
            return enabled
        except Exception as e:
            self.logger.error('flag-check-failed', f'failed to check flag {flag_name}: {e}',
                            flag=flag_name, error=str(e))
            return default
        
    def shutdown(self):
        """Cleanup Unleash client"""
        if self.client:
            try:
                self.client.destroy()
            except Exception:
                pass