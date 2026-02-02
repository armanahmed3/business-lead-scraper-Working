"""
Google Maps scraper for business leads
Uses Google Maps search results to extract business information including social media
"""

import re
import json
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging
from .base_scraper import BaseScraper, LeadData

class GoogleMapsScraper(BaseScraper):
    """Scraper for Google Maps business listings with social media extraction"""
    
    def __init__(self):
        super().__init__("Google Maps", rate_limit_delay=2.0)
        self.base_url = "https://www.google.com/maps/search"
        self._logger = logging.getLogger(__name__)
    
    def search_leads(self, 
                    city: str, 
                    country: str, 
                    niche: str, 
                    business_name: Optional[str] = None,
                    limit: int = 50) -> List[LeadData]:
        """Search for leads on Google Maps with social media extraction"""
        leads = []
        
        try:
            # Construct search query
            query_parts = [niche]
            if business_name:
                query_parts.append(business_name)
            query_parts.extend([city, country])
            
            search_query = " ".join(query_parts)
            
            # Search parameters
            params = {
                'q': search_query,
                'hl': 'en',
                'gl': country.lower()
            }
            
            self._logger.info(f"Searching Google Maps for: {search_query}")
            
            # Make request
            response = self._make_request(self.base_url, params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract leads from search results
            # Google Maps search results are typically in script tags with JSON data
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string and 'window.APP_INITIALIZATION_STATE' in script.string:
                    # Extract JSON data from script
                    try:
                        # Look for the data structure containing business information
                        json_match = re.search(r'window\.APP_INITIALIZATION_STATE=(\[.*?\]);', script.string)
                        if json_match:
                            data = json.loads(json_match.group(1))
                            
                            # Parse the business data
                            businesses = self._parse_google_maps_data(data, niche, city, country)
                            leads.extend(businesses)
                            
                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        self._logger.warning(f"Error parsing Google Maps data: {e}")
                        continue
            
            # If no structured data found, try parsing HTML directly
            if not leads:
                leads = self._parse_google_maps_html(soup, niche, city, country)
            
            # Limit results
            leads = leads[:limit]
            
            self._logger.info(f"Found {len(leads)} leads from Google Maps")
            return leads
            
        except Exception as e:
            self._logger.error(f"Error scraping Google Maps: {e}")
            return []

    def _parse_google_maps_data(self, data: List, niche: str, city: str, country: str) -> List[LeadData]:
        """Parse Google Maps JSON data"""
        leads = []
        
        try:
            # The data structure is complex, look for business information
            # This is a simplified approach - real implementation would need more detailed parsing
            for item in data:
                if isinstance(item, list) and len(item) > 6:
                    # Look for business name and details
                    business_data = item[6] if len(item) > 6 else None
                    if business_data and isinstance(business_data, str):
                        # Try to extract business information from the string data
                        lead = self._extract_lead_from_text(business_data, niche, city, country)
                        if lead and self._validate_lead(lead):
                            leads.append(lead)
                            
        except Exception as e:
            self._logger.warning(f"Error parsing Google Maps JSON data: {e}")
            
        return leads

    def _parse_google_maps_html(self, soup: BeautifulSoup, niche: str, city: str, country: str) -> List[LeadData]:
        """Parse Google Maps HTML directly"""
        leads = []
        
        try:
            # Look for business listings in various HTML structures
            # Google Maps uses dynamic loading, so we might only get limited data
            business_elements = soup.find_all(['div', 'a'], class_=lambda x: x and 'search' in x.lower())
            
            for element in business_elements:
                # Extract text content
                text_content = element.get_text()
                if text_content and len(text_content.strip()) > 10:
                    lead = self._extract_lead_from_text(text_content, niche, city, country)
                    if lead and self._validate_lead(lead):
                        leads.append(lead)
                        
        except Exception as e:
            self._logger.warning(f"Error parsing Google Maps HTML: {e}")
            
        return leads

    def _extract_lead_from_text(self, text: str, niche: str, city: str, country: str) -> Optional[LeadData]:
        """Extract lead information from text content including social media"""
        try:
            # Clean the text
            clean_text = self._clean_text(text)
            
            # Extract basic information using regex patterns
            # Extract business name (assuming it's at the beginning or prominent)
            name_pattern = r'^([A-Z][a-zA-Z0-9\s&\-\.]{3,50})'
            name_match = re.search(name_pattern, clean_text)
            name = name_match.group(1).strip() if name_match else ""
            
            # Extract phone number
            phone = self._extract_phone(clean_text)
            
            # Extract email
            email = self._extract_email(clean_text)
            
            # Extract website (look for URLs)
            website_pattern = r'https?://[^\s"\'>]+'
            website_match = re.search(website_pattern, clean_text)
            website = website_match.group(0) if website_match else None
            
            # Extract address (look for address patterns)
            address_pattern = r'(\d+\s+[A-Za-z0-9\s\.,\-]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Sq|Square|Pkwy|Parkway)[\s\.,A-Za-z0-9]*)'
            address_match = re.search(address_pattern, clean_text, re.IGNORECASE)
            address = address_match.group(1).strip() if address_match else ""
            
            # Extract social media links
            social_links = self._extract_social_links(clean_text, website)
            
            if name and address:
                return LeadData(
                    name=name,
                    address=address,
                    city=city,
                    country=country,
                    niche=niche,
                    phone=phone,
                    email=email,
                    website=website,
                    facebook=social_links['facebook'],
                    twitter=social_links['twitter'],
                    linkedin=social_links['linkedin'],
                    instagram=social_links['instagram'],
                    youtube=social_links['youtube'],
                    tiktok=social_links['tiktok'],
                    source=self.name
                )
                
        except Exception as e:
            self._logger.warning(f"Error extracting lead from text: {e}")
            
        return None