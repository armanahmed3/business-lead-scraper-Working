"""
robots.txt checker module.

This module handles fetching and parsing robots.txt files to ensure
compliant scraping behavior.
"""

import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from typing import Optional
import time


class RobotsChecker:
    """
    Check and enforce robots.txt rules.
    
    This class:
    - Fetches robots.txt from target domains
    - Parses disallow rules
    - Caches robots.txt files
    - Determines if scraping is allowed for specific paths
    """
    
    def __init__(self, config):
        """
        Initialize the robots.txt checker.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = config.robots.get('cache_duration', 3600)
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """
        Check if fetching the URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            user_agent: User agent string (default: '*')
            
        Returns:
            True if fetching is allowed, False otherwise
        """
        if not self.config.robots.get('enabled', True):
            return True
        
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(domain, '/robots.txt')
        
        # Check cache
        if robots_url in self.cache:
            parser, timestamp = self.cache[robots_url]
            if time.time() - timestamp < self.cache_duration:
                return parser.can_fetch(user_agent, url)
        
        # Fetch and parse robots.txt
        parser = self._fetch_robots(robots_url)
        
        if parser:
            self.cache[robots_url] = (parser, time.time())
            return parser.can_fetch(user_agent, url)
        
        # If robots.txt not found, allow by default
        return True
    
    def _fetch_robots(self, robots_url: str) -> Optional[RobotFileParser]:
        """
        Fetch and parse robots.txt file.
        
        Args:
            robots_url: URL of robots.txt file
            
        Returns:
            RobotFileParser object or None if fetch fails
        """
        try:
            self.logger.debug(f"Fetching robots.txt from {robots_url}")
            
            response = requests.get(
                robots_url,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (compatible)'}
            )
            
            if response.status_code == 200:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
                self.logger.debug(f"✓ Successfully parsed robots.txt")
                return parser
            
            elif response.status_code == 404:
                self.logger.debug("robots.txt not found (404) - allowing by default")
                return None
            
            else:
                self.logger.warning(f"robots.txt returned status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch robots.txt: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing robots.txt: {e}")
            return None
