"""
Configuration management for business lead scraper.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration loader and manager."""
    
    def __init__(self, config_file: str = 'config.yaml'):
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with defaults."""
        default_config = {
            'scraping': {
                'default_delay': 1.5,
                'delay_randomization': 0.5,
                'max_scroll_attempts': 10,
                'scroll_delay': 2.5,
                'request_timeout': 30,
                'retry_attempts': 3,
                'backoff_multiplier': 2,
                'max_leads_per_session': 500
            },
            'selenium': {
                'page_load_timeout': 60,
                'implicit_wait': 0,
                'window_size': '1920,1080',
                'chrome_options': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu'
                ],
                'user_agent': ''
            },
            'geographic': {
                'tile_mode': False,
                'tile_size': 0.1,
                'tile_overlap': 0.01,
                'max_tiles': 100
            },
            'export': {
                'output_dir': './data',
                'formats': ['csv', 'json', 'sqlite'],
                'csv_delimiter': ',',
                'csv_encoding': 'utf-8',
                'json_indent': 2,
                'sqlite_table_name': 'leads'
            },
            'deduplication': {
                'fuzzy_threshold': 0.85,
                'dedupe_fields': ['name', 'address', 'phone'],
                'prefer_place_id': True
            },
            'logging': {
                'level': 'INFO',
                'file': './logs/scraper.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'console': True
            },
            'robots': {
                'enabled': True,
                'user_agent': '*',
                'cache_enabled': True,
                'cache_duration': 3600
            },
            'enrichment': {
                'osm_enabled': False,
                'overpass_url': 'https://overpass-api.de/api/interpreter',
                'nominatim_url': 'https://nominatim.openstreetmap.org',
                'osm_delay': 1.0
            }
        }
        
        # Try to load from file
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        # Merge with defaults
                        default_config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    def __getattr__(self, name):
        """Allow attribute-style access to config sections."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._config.get(name, {})
    
    def get(self, key, default=None):
        """Get configuration value."""
        return self._config.get(key, default)
