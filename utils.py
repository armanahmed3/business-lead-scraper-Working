"""
Utility functions for the business lead scraper.
"""

import time
import random
import logging
import re
from pathlib import Path
from typing import Optional


def sleep_random(base_delay: float, randomization: float = 0.5):
    """
    Sleep for a random duration based on base delay.
    
    Args:
        base_delay: Base delay in seconds
        randomization: Randomization range (+/-)
    """
    delay = base_delay + random.uniform(-randomization, randomization)
    delay = max(0.1, delay)  # Ensure minimum delay
    time.sleep(delay)


def setup_logging(config):
    """
    Set up logging configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        Logger instance
    """
    # Create logs directory
    log_file = Path(config.logging['file'])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, config.logging['level'].upper(), logging.INFO)
    log_format = config.logging['format']
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() if config.logging['console'] else logging.NullHandler()
        ]
    )
    
    return logging.getLogger('business_scraper')


def validate_location(location: str) -> bool:
    """
    Validate location string format.
    
    Args:
        location: Location string
        
    Returns:
        True if format looks valid
    """
    # Basic validation - should have at least city name
    if not location or len(location.strip()) < 2:
        return False
    
    # Preferred format: "City, Country" or "City, State, Country"
    if ',' in location:
        return True
    
    # Single word locations are acceptable but not ideal
    return True


def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison.
    
    Args:
        url: URL string
        
    Returns:
        Normalized URL
    """
    # Remove trailing slashes, convert to lowercase
    url = url.strip().lower()
    if url.endswith('/'):
        url = url[:-1]
    return url


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain name or None
    """
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return match.group(1) if match else None


def format_timestamp(timestamp: str) -> str:
    """
    Format ISO timestamp for display.
    
    Args:
        timestamp: ISO format timestamp
        
    Returns:
        Formatted timestamp string
    """
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp
