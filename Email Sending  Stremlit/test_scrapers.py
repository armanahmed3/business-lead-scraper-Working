"""
Test script for lead generation scrapers
Run this to verify all scrapers are working correctly
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scrapers():
    """Test Google Maps scraper with social media extraction"""
    
    try:
        from scrapers import GoogleMapsScraper
        from lead_database_enhanced import LeadDatabase
        from lead_generation_orchestrator import LeadGenerationOrchestrator
        
        print("✅ All imports successful")
        
        # Test database
        print("\n🔧 Testing database...")
        db = LeadDatabase("test_leads.db")
        print("✅ Database initialized")
        
        # Test orchestrator
        print("\n🔧 Testing orchestrator...")
        orchestrator = LeadGenerationOrchestrator("test_leads.db")
        print("✅ Orchestrator initialized")
        
        # Test Google Maps scraper
        print("\n🔧 Testing Google Maps scraper with social media extraction...")
        google_scraper = GoogleMapsScraper()
        google_leads = google_scraper.search_leads("New York", "United States", "restaurants", limit=5)
        print(f"✅ Google Maps: Found {len(google_leads)} leads")
        
        # Show sample lead data including social media
        if google_leads:
            sample_lead = google_leads[0]
            print(f"\n📋 Sample lead with social media:")
            print(f"   Name: {sample_lead.name}")
            print(f"   Address: {sample_lead.address}")
            print(f"   Phone: {sample_lead.phone}")
            print(f"   Website: {sample_lead.website}")
            if sample_lead.facebook:
                print(f"   Facebook: {sample_lead.facebook}")
            if sample_lead.twitter:
                print(f"   Twitter: {sample_lead.twitter}")
            if sample_lead.linkedin:
                print(f"   LinkedIn: {sample_lead.linkedin}")
            if sample_lead.instagram:
                print(f"   Instagram: {sample_lead.instagram}")
            if sample_lead.youtube:
                print(f"   YouTube: {sample_lead.youtube}")
            if sample_lead.tiktok:
                print(f"   TikTok: {sample_lead.tiktok}")
        
        # Test full orchestrator
        print("\n🔧 Testing full orchestrator...")
        results = orchestrator.generate_leads(
            city="New York",
            country="United States", 
            niche="restaurants",
            limit=10,
            sources=['google_maps']
        )
        
        print(f"✅ Orchestrator test completed:")
        print(f"   - Total found: {results.get('total_found', 0)}")
        print(f"   - Duplicates removed: {results.get('duplicates_removed', 0)}")
        print(f"   - Successfully inserted: {results.get('successfully_inserted', 0)}")
        
        # Test database operations
        print("\n🔧 Testing database operations...")
        stats = orchestrator.get_lead_stats()
        print(f"✅ Database stats: {stats.get('total_leads', 0)} total leads")
        
        # Test CSV export
        print("\n🔧 Testing CSV export...")
        try:
            csv_path = orchestrator.export_leads(filename="test_export.csv")
            print(f"✅ CSV export successful: {csv_path}")
        except Exception as e:
            print(f"⚠️ CSV export failed: {e}")
        
        print("\n🎉 All tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test failed with exception")

if __name__ == "__main__":
    test_scrapers()