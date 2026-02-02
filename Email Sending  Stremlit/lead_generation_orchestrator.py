"""
Lead Generation Orchestrator
Coordinates multiple scrapers and manages the lead generation process
"""

import asyncio
import threading
import time
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from tqdm import tqdm

from scrapers import GoogleMapsScraper
from lead_database_enhanced import LeadDatabase

logger = logging.getLogger(__name__)

class LeadGenerationOrchestrator:
    """Orchestrates lead generation from multiple sources"""
    
    def __init__(self, db_path: str = "leadai_pro.db"):
        try:
            self.db = LeadDatabase(db_path)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.db = None
        self.scrapers = {
            'google_maps': GoogleMapsScraper()
        }
        self.results = {}
        self.progress = {}
        self.is_running = False
    
    def generate_leads(self, 
                      city: str, 
                      country: str, 
                      niche: str, 
                      business_name: Optional[str] = None,
                      limit: int = 50,
                      sources: Optional[List[str]] = None,
                      progress_callback: Optional[callable] = None,
                      deduplicate: bool = True,
                      address: Optional[str] = None,
                      user_id: Optional[int] = None) -> Dict:
        """
        Generate leads from multiple sources
        
        Args:
            city: City to search in
            country: Country to search in
            niche: Industry/niche to search for
            business_name: Optional specific business name
            limit: Maximum number of leads to generate
            sources: List of sources to use (default: all)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with results summary
        """
        if sources is None:
            sources = list(self.scrapers.keys())
        # Map any human-readable names from UI to internal keys
        mapped_sources = []
        for s in sources:
            key = s
            s_lower = s.lower().strip()
            if s_lower in ["google maps", "google_maps", "google"]:
                key = 'google_maps'
            elif s_lower in ["yelp"]:
                key = 'yelp'
            elif s_lower in ["yellow pages", "yellowpages", "yellow_pages"]:
                key = 'yellowpages'
            elif s_lower in ["test", "test scraper", "test_scraper"]:
                key = 'test'
            # Skip unsupported sources like linkedin
            if key in self.scrapers and key not in mapped_sources:
                mapped_sources.append(key)
        sources = mapped_sources or list(self.scrapers.keys())
        
        self.is_running = True
        self.results = {}
        self.progress = {}
        
        # Calculate limit per source
        limit_per_source = max(1, limit // len(sources))
        
        try:
            logger.info(f"Starting lead generation for {niche} in {city}, {country}")
            
            # Run scrapers in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit tasks
                future_to_source = {}
                for source in sources:
                    if source in self.scrapers:
                        future = executor.submit(
                            self._run_scraper,
                            source,
                            city, country, niche, business_name, limit_per_source,
                            progress_callback
                        )
                        future_to_source[future] = source
                
                # Collect results
                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        result = future.result()
                        self.results[source] = result
                    except Exception as e:
                        logger.error(f"Error in {source} scraper: {e}")
                        self.results[source] = {
                            'leads': [],
                            'error': str(e),
                            'status': 'error'
                        }
            
            # Combine all results
            all_leads = []
            for source, result in self.results.items():
                if result.get('status') == 'success':
                    all_leads.extend(result.get('leads', []))
            
            # Deduplicate leads
            deduplicated_leads = self._deduplicate_leads(all_leads) if deduplicate else all_leads
            
            # Store in database
            if self.db:
                total_processed, duplicates_found, successfully_inserted = self.db.insert_leads(
                    [lead.to_dict() for lead in deduplicated_leads]
                )
            else:
                total_processed = len(deduplicated_leads)
                duplicates_found = 0
                successfully_inserted = 0
            
            # Prepare final results
            final_results = {
                'total_found': len(all_leads),
                'duplicates_removed': len(all_leads) - len(deduplicated_leads),
                'successfully_inserted': successfully_inserted,
                'inserted': successfully_inserted,
                'sources_used': sources,
                'leads_per_source': {source: len(result.get('leads', [])) for source, result in self.results.items()},
                'errors': {source: result.get('error') for source, result in self.results.items() if result.get('error')},
                'status': 'completed'
            }
            
            logger.info(f"Lead generation completed: {successfully_inserted} leads inserted")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in lead generation: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'total_found': 0,
                'duplicates_removed': 0,
                'successfully_inserted': 0
            }
        finally:
            self.is_running = False
    
    def _run_scraper(self, source: str, city: str, country: str, niche: str, 
                    business_name: Optional[str], limit: int, 
                    progress_callback: Optional[callable]) -> Dict:
        """Run individual scraper"""
        try:
            scraper = self.scrapers[source]
            
            # Update progress
            if progress_callback:
                progress_callback(f"Starting {source} scraper...")
            
            # Run scraper
            leads = scraper.search_leads(city, country, niche, business_name, limit)
            
            # Update progress
            if progress_callback:
                progress_callback(f"Completed {source} scraper: {len(leads)} leads found")
            
            return {
                'leads': leads,
                'status': 'success',
                'count': len(leads)
            }
            
        except Exception as e:
            logger.error(f"Error in {source} scraper: {e}")
            return {
                'leads': [],
                'status': 'error',
                'error': str(e),
                'count': 0
            }
    
    def _deduplicate_leads(self, leads: List) -> List:
        """Deduplicate leads based on multiple criteria"""
        if not leads:
            return []
        
        seen = set()
        deduplicated = []
        
        for lead in leads:
            # Create unique identifier based on multiple fields
            identifier_parts = []
            
            # Use name + address as primary identifier
            if lead.name and lead.address:
                identifier_parts.append(f"{lead.name.lower().strip()}|{lead.address.lower().strip()}")
            
            # Use email + phone as secondary identifier
            if lead.email and lead.phone:
                identifier_parts.append(f"{lead.email.lower().strip()}|{lead.phone.strip()}")
            
            # Use email only if available
            elif lead.email:
                identifier_parts.append(f"email|{lead.email.lower().strip()}")
            
            # Use phone only if available
            elif lead.phone:
                identifier_parts.append(f"phone|{lead.phone.strip()}")
            
            # Check if this lead is unique
            is_unique = True
            for identifier in identifier_parts:
                if identifier in seen:
                    is_unique = False
                    break
            
            if is_unique:
                # Add all identifiers to seen set
                for identifier in identifier_parts:
                    seen.add(identifier)
                deduplicated.append(lead)
        
        return deduplicated
    
    def get_available_sources(self) -> List[str]:
        """Get list of available scrapers"""
        # Return human-readable names for UI selection
        return [
            'Google Maps'
        ]
    
    def get_source_info(self) -> Dict[str, Dict]:
        """Get information about each scraper"""
        return {
            'google_maps': {
                'name': 'Google Maps',
                'description': 'Business listings from Google Maps with social media extraction',
                'rate_limit': '2.0s',
                'reliability': 'High'
            }
        }
    
    def get_lead_stats(self) -> Dict:
        """Get lead statistics from database"""
        if self.db:
            return self.db.get_lead_stats()
        return {}
    
    def export_leads(self, filters: Optional[Dict] = None, filename: Optional[str] = None) -> str:
        """Export leads to CSV"""
        if self.db:
            return self.db.export_to_csv(filters, filename)
        raise Exception("Database not available for export")
    
    def cleanup_duplicates(self) -> Tuple[int, int]:
        """Clean up existing duplicates in database"""
        if self.db:
            return self.db.cleanup_duplicates()
        return 0, 0
    
    def stop_generation(self):
        """Stop lead generation process"""
        self.is_running = False
        logger.info("Lead generation stopped by user")
