"""
Lead Generation Scrapers Package
Modular scraping system for Google Maps with social media extraction
"""

from .base_scraper import BaseScraper
from .google_maps_scraper import GoogleMapsScraper

__all__ = [
    'BaseScraper',
    'GoogleMapsScraper'
]