"""
Base scraper class for all lead generation scrapers
Provides common functionality for retries, rate limiting, and data validation
"""

import time
import random
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LeadData:
    """Standardized lead data structure with social media fields"""
    name: str
    address: str
    city: str
    country: str
    niche: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    # Social media fields
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    tiktok: Optional[str] = None
    source: str = ""
    scraped_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'niche': self.niche,
            'phone': self.phone or '',
            'email': self.email or '',
            'website': self.website or '',
            'facebook': self.facebook or '',
            'twitter': self.twitter or '',
            'linkedin': self.linkedin or '',
            'instagram': self.instagram or '',
            'youtube': self.youtube or '',
            'tiktok': self.tiktok or '',
            'source': self.source,
            'scraped_at': self.scraped_at or ''
        }

class BaseScraper(ABC):
    """Base class for all lead scrapers"""
    
    def __init__(self, name: str, rate_limit_delay: float = 1.0):
        self.name = name
        self.rate_limit_delay = rate_limit_delay
        
        # Try to use fake-useragent, fallback to static UAs
        try:
            from fake_useragent import UserAgent
            self.ua = UserAgent()
            self._random_ua = None
        except Exception:
            self.ua = None
            self._random_ua = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16 Safari/605.1.15",
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            ]
        
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with headers and retry strategy"""
        ua_value = self.ua.random if self.ua else self._random_ua[0]
        self.session.headers.update({
            'User-Agent': ua_value,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _get_random_delay(self) -> float:
        """Get random delay between requests to avoid detection"""
        base_delay = self.rate_limit_delay
        return base_delay + random.uniform(0, base_delay * 0.5)
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        if self.ua:
            self.session.headers['User-Agent'] = self.ua.random
        elif self._random_ua:
            import random
            self.session.headers['User-Agent'] = random.choice(self._random_ua)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def _make_request(self, url: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        try:
            # Add random delay
            time.sleep(self._get_random_delay())
            
            # Rotate user agent occasionally
            if random.random() < 0.3:
                self._rotate_user_agent()
            
            logger.info(f"Making request to {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=30, **kwargs)
            logger.info(f"Response status: {response.status_code}, content length: {len(response.content)}")
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {self.name}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        if not text:
            return None
        
        import re
        # Common phone number patterns
        phone_patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        if not text:
            return None
        
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def _extract_social_links(self, text: str, website_url: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Extract social media links from text and website"""
        social_links = {
            'facebook': None,
            'twitter': None,
            'linkedin': None,
            'instagram': None,
            'youtube': None,
            'tiktok': None
        }
        
        if not text:
            return social_links
        
        import re
        text_lower = text.lower()
        
        # Facebook patterns
        fb_patterns = [
            r'facebook\.com/[^"\s\'\)]+',
            r'fb\.com/[^"\s\'\)]+',
            r'fb\.me/[^"\s\'\)]+'
        ]
        
        for pattern in fb_patterns:
            match = re.search(pattern, text_lower)
            if match:
                social_links['facebook'] = 'https://' + match.group(0)
                break
        
        # Twitter/X patterns
        twitter_patterns = [
            r'twitter\.com/[^"\s\'\)]+',
            r'x\.com/[^"\s\'\)]+'
        ]
        
        for pattern in twitter_patterns:
            match = re.search(pattern, text_lower)
            if match:
                social_links['twitter'] = 'https://' + match.group(0)
                break
        
        # LinkedIn patterns
        linkedin_patterns = [
            r'linkedin\.com/[^"\s\'\)]+',
            r'linkedin\.com/in/[^"\s\'\)]+'
        ]
        
        for pattern in linkedin_patterns:
            match = re.search(pattern, text_lower)
            if match:
                social_links['linkedin'] = 'https://' + match.group(0)
                break
        
        # Instagram patterns
        ig_patterns = [
            r'instagram\.com/[^"\s\'\)]+',
            r'instagr\.am/[^"\s\'\)]+'
        ]
        
        for pattern in ig_patterns:
            match = re.search(pattern, text_lower)
            if match:
                social_links['instagram'] = 'https://' + match.group(0)
                break
        
        # YouTube patterns
        yt_patterns = [
            r'youtube\.com/[^"\s\'\)]+',
            r'youtu\.be/[^"\s\'\)]+'
        ]
        
        for pattern in yt_patterns:
            match = re.search(pattern, text_lower)
            if match:
                social_links['youtube'] = 'https://' + match.group(0)
                break
        
        # TikTok patterns
        tiktok_patterns = [
            r'tiktok\.com/[^"\s\'\)]+',
            r'@tiktok\.com/[^"\s\'\)]+'
        ]
        
        for pattern in tiktok_patterns:
            match = re.search(pattern, text_lower)
            if match:
                social_links['tiktok'] = 'https://' + match.group(0)
                break
        
        # Also check for common social media references in text
        social_keywords = {
            'facebook': ['facebook', 'fb.com'],
            'twitter': ['twitter', 'x.com', '@twitter'],
            'linkedin': ['linkedin', 'linkedin.com/in'],
            'instagram': ['instagram', 'instagr.am', '@instagram'],
            'youtube': ['youtube', 'youtu.be', '@youtube'],
            'tiktok': ['tiktok', '@tiktok']
        }
        
        for platform, keywords in social_keywords.items():
            if social_links[platform] is None:
                for keyword in keywords:
                    if keyword in text_lower:
                        # Try to find handle/username after @ or in URL
                        handle_pattern = r'[@/]' + re.escape(keyword.split('.')[-1] if '.' in keyword else keyword) + r'/([^\s"\']+)'
                        match = re.search(handle_pattern, text, re.IGNORECASE)
                        if match:
                            username = match.group(1).strip('/')
                            if username and len(username) > 2:
                                base_url = {
                                    'facebook': 'https://facebook.com/',
                                    'twitter': 'https://twitter.com/',
                                    'linkedin': 'https://linkedin.com/in/',
                                    'instagram': 'https://instagram.com/',
                                    'youtube': 'https://youtube.com/@',
                                    'tiktok': 'https://tiktok.com/@'
                                }
                                social_links[platform] = base_url[platform] + username
                                break
        
        return social_links
    
    def _validate_lead(self, lead: LeadData) -> bool:
        """Validate lead data before returning"""
        return (
            lead.name and len(lead.name.strip()) > 2 and
            lead.address and len(lead.address.strip()) > 5 and
            lead.city and len(lead.city.strip()) > 1 and
            lead.country and len(lead.country.strip()) > 1 and
            lead.niche and len(lead.niche.strip()) > 2
        )
    
    @abstractmethod
    def search_leads(self, 
                    city: str, 
                    country: str, 
                    niche: str, 
                    business_name: Optional[str] = None,
                    limit: int = 50) -> List[LeadData]:
        """
        Search for leads based on criteria
        
        Args:
            city: City to search in
            country: Country to search in  
            niche: Industry/niche to search for
            business_name: Optional specific business name
            limit: Maximum number of leads to return
            
        Returns:
            List of LeadData objects
        """
        pass
    
    def __str__(self):
        return f"{self.name} Scraper"