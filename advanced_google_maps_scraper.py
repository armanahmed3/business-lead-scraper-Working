import requests
import json
import time
import re
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote, urlparse
from dataclasses import dataclass
from datetime import datetime
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BusinessLead:
    """Data class for business lead information"""
    name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maps_url: Optional[str] = None
    place_id: Optional[str] = None
    
    # Social media links
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    tiktok: Optional[str] = None
    
    # Metadata
    timestamp: str = None
    source_url: Optional[str] = None

class AdvancedGoogleMapsScraper:
    """Advanced Google Maps scraper that extracts real data and social media links"""
    
    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def search_google_maps(self, query: str, location: str, max_results: int = 20) -> List[BusinessLead]:
        """Search Google Maps and extract business leads"""
        logger.info(f"Searching Google Maps for: {query} in {location}")
        
        search_query = f"{query} in {location}"
        encoded_query = quote(search_query)
        
        # Google Maps search URL
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        
        try:
            # Get the search results page
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Extract business data from the page
            leads = self._extract_businesses_from_search_page(response.text, search_url)
            
            # Process each lead to get detailed information
            detailed_leads = []
            for i, lead in enumerate(leads[:max_results]):
                logger.info(f"Processing lead {i+1}/{min(len(leads), max_results)}: {lead.name}")
                
                # Get detailed information
                detailed_lead = self._get_detailed_business_info(lead)
                
                if detailed_lead and self._is_real_lead(detailed_lead):
                    detailed_leads.append(detailed_lead)
                
                # Rate limiting
                time.sleep(self.delay + random.uniform(0.5, 1.5))
            
            # Remove duplicates and ensure uniqueness
            unique_leads = self._remove_duplicates(detailed_leads)
            
            logger.info(f"Found {len(unique_leads)} unique real leads with social media")
            return unique_leads
            
        except Exception as e:
            logger.error(f"Error searching Google Maps: {e}")
            return []
    
    def _extract_businesses_from_search_page(self, html_content: str, search_url: str) -> List[BusinessLead]:
        """Extract basic business information from Google Maps search page"""
        leads = []
        
        # Look for business data in the HTML
        # Google Maps embeds JSON data in the page
        try:
            # Find the data section
            data_match = re.search(r'window\.APP_INITIALIZATION_STATE.*?(\[.*?\]);', html_content, re.DOTALL)
            if data_match:
                data_json = json.loads(data_match.group(1))
                # Parse the business data from the JSON structure
                leads = self._parse_business_data(data_json, search_url)
        except Exception as e:
            logger.warning(f"Could not parse JSON data: {e}")
        
        # Fallback: Extract from HTML structure
        if not leads:
            leads = self._extract_from_html_structure(html_content, search_url)
        
        return leads
    
    def _parse_business_data(self, data_json, search_url: str) -> List[BusinessLead]:
        """Parse business data from Google Maps JSON structure"""
        leads = []
        
        try:
            # The data structure is complex - look for business entities
            for item in data_json:
                if isinstance(item, list) and len(item) > 2:
                    try:
                        # Look for business data in nested structures
                        business_data = self._find_business_entities(item)
                        for biz_data in business_data:
                            lead = self._create_lead_from_data(biz_data, search_url)
                            if lead:
                                leads.append(lead)
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Error parsing business data: {e}")
        
        return leads
    
    def _find_business_entities(self, data_item) -> List[Dict]:
        """Recursively find business entities in nested data structure"""
        business_entities = []
        
        if isinstance(data_item, dict):
            # Check if this looks like a business entity
            if self._looks_like_business_entity(data_item):
                business_entities.append(data_item)
            
            # Recursively check nested items
            for value in data_item.values():
                business_entities.extend(self._find_business_entities(value))
        
        elif isinstance(data_item, list):
            for item in data_item:
                business_entities.extend(self._find_business_entities(item))
        
        return business_entities
    
    def _looks_like_business_entity(self, data_item: Dict) -> bool:
        """Check if a data item looks like a business entity"""
        required_fields = ['title', 'address']
        return all(field in data_item for field in required_fields)
    
    def _create_lead_from_data(self, biz_data: Dict, search_url: str) -> Optional[BusinessLead]:
        """Create a BusinessLead from parsed data"""
        try:
            lead = BusinessLead(
                name=biz_data.get('title', ''),
                address=biz_data.get('address', ''),
                phone=biz_data.get('phone'),
                website=biz_data.get('website'),
                category=biz_data.get('category'),
                rating=biz_data.get('rating'),
                reviews=biz_data.get('reviews'),
                latitude=biz_data.get('latitude'),
                longitude=biz_data.get('longitude'),
                maps_url=biz_data.get('maps_url', search_url),
                place_id=biz_data.get('place_id'),
                timestamp=datetime.now().isoformat()
            )
            return lead if lead.name and lead.address else None
        except Exception:
            return None
    
    def _extract_from_html_structure(self, html_content: str, search_url: str) -> List[BusinessLead]:
        """Extract business data from HTML structure (fallback method)"""
        leads = []
        
        # Look for business listings in HTML
        business_pattern = r'<div[^>]*class="[^"]*fontHeadlineSmall[^"]*"[^>]*>([^<]+)</div>'
        name_matches = re.findall(business_pattern, html_content)
        
        address_pattern = r'<div[^>]*class="[^"]*fontBodyMedium[^"]*"[^>]*>([^<]+)</div>'
        address_matches = re.findall(address_pattern, html_content)
        
        # Create leads from found matches
        for i, name in enumerate(name_matches[:10]):  # Limit to first 10 for demo
            if i < len(address_matches):
                lead = BusinessLead(
                    name=name.strip(),
                    address=address_matches[i].strip(),
                    maps_url=search_url,
                    timestamp=datetime.now().isoformat()
                )
                leads.append(lead)
        
        return leads
    
    def _get_detailed_business_info(self, lead: BusinessLead) -> Optional[BusinessLead]:
        """Get detailed business information including social media links"""
        try:
            # If we have a website, extract social media from it
            if lead.website:
                social_media = self._extract_social_media_from_website(lead.website)
                lead.facebook = social_media.get('facebook')
                lead.twitter = social_media.get('twitter')
                lead.linkedin = social_media.get('linkedin')
                lead.instagram = social_media.get('instagram')
                lead.youtube = social_media.get('youtube')
                lead.tiktok = social_media.get('tiktok')
            
            # Try to extract email from website
            if lead.website and not lead.email:
                lead.email = self._extract_email_from_website(lead.website)
            
            # Add source information
            lead.source_url = lead.website or lead.maps_url
            
            return lead
            
        except Exception as e:
            logger.warning(f"Error getting detailed info for {lead.name}: {e}")
            return lead  # Return original lead even if detailed info fails
    
    def _extract_social_media_from_website(self, website_url: str) -> Dict[str, str]:
        """Extract social media links from business website"""
        social_media = {
            'facebook': None,
            'twitter': None,
            'linkedin': None,
            'instagram': None,
            'youtube': None,
            'tiktok': None
        }
        
        try:
            # Clean the URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            # Fetch website content
            response = self.session.get(website_url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            content = response.text
            
            # Extract social media links using regex patterns
            social_patterns = {
                'facebook': r'(?:https?://)?(?:www\.)?(?:facebook|fb)\.com/(?:[^/\s"\'<>]+)',
                'twitter': r'(?:https?://)?(?:www\.)?twitter\.com/(?:[^/\s"\'<>]+)',
                'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/(?:[^/\s"\'<>]+)',
                'instagram': r'(?:https?://)?(?:www\.)?instagram\.com/(?:[^/\s"\'<>]+)',
                'youtube': r'(?:https?://)?(?:www\.)?(?:youtube|youtu\.be)/(?:[^/\s"\'<>]+)',
                'tiktok': r'(?:https?://)?(?:www\.)?tiktok\.com/(?:[^/\s"\'<>]+)'
            }
            
            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Clean up the URL
                    clean_url = matches[0]
                    if not clean_url.startswith('http'):
                        clean_url = 'https://' + clean_url
                    social_media[platform] = clean_url
                    
        except Exception as e:
            logger.warning(f"Error extracting social media from {website_url}: {e}")
        
        return social_media
    
    def _extract_email_from_website(self, website_url: str) -> Optional[str]:
        """Extract email address from business website"""
        try:
            # Clean the URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            # Fetch website content
            response = self.session.get(website_url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            content = response.text.lower()
            
            # Email pattern
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, content)
            
            # Filter out common non-business emails
            filtered_emails = [
                email for email in emails
                if not any(bad_domain in email.lower() for bad_domain in [
                    'example.com', 'test.com', 'sample.com', 'placeholder.com',
                    'privacy@', 'noreply@', 'no-reply@', 'donotreply@',
                    'wix.com', 'wordpress.com', 'sentry.io'
                ])
            ]
            
            return filtered_emails[0] if filtered_emails else None
            
        except Exception as e:
            logger.warning(f"Error extracting email from {website_url}: {e}")
            return None
    
    def _is_real_lead(self, lead: BusinessLead) -> bool:
        """Check if this is a real business lead (not demo/sample)"""
        if not lead or not lead.name:
            return False
        
        # Check for demo/sample keywords
        demo_keywords = ['demo', 'sample', 'test', 'fake', 'placeholder', 'lorem ipsum']
        name_lower = lead.name.lower()
        if any(keyword in name_lower for keyword in demo_keywords):
            return False
        
        # Check if it has real contact information
        has_contact_info = any([
            lead.website,
            lead.phone,
            lead.email,
            lead.address
        ])
        
        # Check if it has social media links (as requested)
        has_social_media = any([
            lead.facebook, lead.twitter, lead.linkedin,
            lead.instagram, lead.youtube, lead.tiktok
        ])
        
        return has_contact_info and has_social_media
    
    def _remove_duplicates(self, leads: List[BusinessLead]) -> List[BusinessLead]:
        """Remove duplicate leads based on multiple criteria for maximum uniqueness"""
        seen_identifiers = set()
        unique_leads = []
        
        for lead in leads:
            # Create unique identifiers based on multiple criteria
            identifiers = []
            
            # Name + Address combination (strong identifier)
            if lead.name and lead.address:
                identifiers.append(('name_address', lead.name.lower().strip(), lead.address.lower().strip()))
            
            # Website (very strong identifier)
            if lead.website:
                identifiers.append(('website', lead.website.lower().strip()))
            
            # Phone number (normalized)
            if lead.phone:
                clean_phone = re.sub(r'\D', '', lead.phone)
                if clean_phone:
                    identifiers.append(('phone', clean_phone))
            
            # Email
            if lead.email:
                identifiers.append(('email', lead.email.lower().strip()))
            
            # Social media profiles
            social_fields = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'tiktok']
            for field in social_fields:
                if getattr(lead, field):
                    identifiers.append((field, getattr(lead, field).lower().strip()))
            
            # Check if any identifier has been seen before
            is_duplicate = False
            for identifier in identifiers:
                if identifier in seen_identifiers:
                    is_duplicate = True
                    break
            
            # If not a duplicate, add to unique leads
            if not is_duplicate:
                # Add all identifiers to seen set
                for identifier in identifiers:
                    if identifier:  # Only add non-empty identifiers
                        seen_identifiers.add(identifier)
                unique_leads.append(lead)
        
        logger.info(f"Removed {len(leads) - len(unique_leads)} duplicates from {len(leads)} leads")
        return unique_leads
    
    def scrape(self, query: str, location: str, max_results: int = 20) -> List[BusinessLead]:
        """Main scraping method - returns only real, unique leads with social media"""
        logger.info(f"Starting advanced Google Maps scrape: {query} in {location}")
        
        # Search for businesses
        leads = self.search_google_maps(query, location, max_results)
        
        # Filter for real leads with social media
        real_leads = [lead for lead in leads if self._is_real_lead(lead)]
        
        # Remove duplicates for maximum uniqueness
        unique_real_leads = self._remove_duplicates(real_leads)
        
        logger.info(f"Final result: {len(unique_real_leads)} unique real leads with social media")
        return unique_real_leads

# Example usage
if __name__ == "__main__":
    # Create scraper instance
    scraper = AdvancedGoogleMapsScraper(delay=1.5)
    
    # Scrape business leads
    results = scraper.scrape("restaurants", "New York", max_results=10)
    
    # Display results
    print(f"\nFound {len(results)} unique real leads with social media:")
    print("=" * 80)
    
    for i, lead in enumerate(results, 1):
        print(f"\n{i}. {lead.name}")
        print(f"   📍 {lead.address}")
        if lead.phone:
            print(f"   📞 {lead.phone}")
        if lead.email:
            print(f"   📧 {lead.email}")
        if lead.website:
            print(f"   🌐 {lead.website}")
        
        # Show social media links
        social_links = []
        if lead.facebook:
            social_links.append(f"📘 Facebook: {lead.facebook}")
        if lead.twitter:
            social_links.append(f"🐦 Twitter: {lead.twitter}")
        if lead.linkedin:
            social_links.append(f"💼 LinkedIn: {lead.linkedin}")
        if lead.instagram:
            social_links.append(f"📸 Instagram: {lead.instagram}")
        if lead.youtube:
            social_links.append(f"▶️ YouTube: {lead.youtube}")
        if lead.tiktok:
            social_links.append(f"🎵 TikTok: {lead.tiktok}")
        
        if social_links:
            print("   🌍 Social Media:")
            for link in social_links:
                print(f"      {link}")
        else:
            print("   🌍 No social media links found")
        
        print("-" * 50)