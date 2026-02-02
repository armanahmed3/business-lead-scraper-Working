# 🔍 Lead Generation System

## Overview

The Lead Generation system is a comprehensive scraping solution that automatically finds and collects business leads from multiple free public sources. It's designed to be production-ready, robust, and scalable.

## ✨ Features

### 🌐 Multiple Data Sources
- **Google Maps**: Business listings with contact info and addresses
- **Yelp**: Business reviews and detailed information
- **Yellow Pages**: Traditional business directory listings
- **LinkedIn**: Company pages via Bing search (public only)

### 🔧 Advanced Features
- **Smart Deduplication**: Removes duplicates based on name+address or email+phone
- **Rate Limiting**: Respects website rate limits to avoid blocking
- **Error Handling**: Robust retry mechanisms and graceful error handling
- **Progress Tracking**: Real-time progress updates during scraping
- **CSV Export**: Export leads in marketing-ready CSV format
- **Database Storage**: SQLite database with advanced indexing
- **User Agent Rotation**: Prevents detection and blocking

### 🎯 Lead Data Captured
- Business Name
- Address
- City & Country
- Industry/Niche
- Phone Number
- Email Address
- Website
- Source Platform
- Scraping Timestamp

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the System
```bash
python test_scrapers.py
```

### 3. Run the Application
```bash
streamlit run deploy_app.py
```

### 4. Navigate to Lead Generation
- Open the app in your browser
- Go to "Lead Generation" page
- Fill in search criteria
- Select data sources
- Click "Generate Leads"

## 📁 File Structure

```
scrapers/
├── __init__.py                 # Package initialization
├── base_scraper.py            # Base scraper class
├── google_maps_scraper.py     # Google Maps scraper
├── yelp_scraper.py           # Yelp scraper
├── yellowpages_scraper.py    # Yellow Pages scraper
└── linkedin_scraper.py       # LinkedIn scraper

lead_database_enhanced.py      # Enhanced database module
lead_generation_orchestrator.py # Main orchestrator
test_scrapers.py              # Test script
deploy_app.py                 # Updated main app with UI
```

## 🔧 Configuration

### Database Settings
The system uses SQLite by default. Database file: `leadai_pro.db`

### Rate Limiting
Each scraper has configurable rate limits:
- Google Maps: 2.0s delay
- Yelp: 1.5s delay  
- Yellow Pages: 1.2s delay
- LinkedIn: 2.5s delay

### User Agents
The system automatically rotates user agents to avoid detection.

## 📊 Usage Examples

### Basic Lead Generation
```python
from lead_generation_orchestrator import LeadGenerationOrchestrator

orchestrator = LeadGenerationOrchestrator()

results = orchestrator.generate_leads(
    city="New York",
    country="United States",
    niche="restaurants",
    limit=50,
    sources=['google_maps', 'yelp']
)

print(f"Found {results['total_found']} leads")
print(f"Inserted {results['successfully_inserted']} leads")
```

### Export to CSV
```python
# Export all leads
csv_path = orchestrator.export_leads()

# Export with filters
csv_path = orchestrator.export_leads(
    filters={'city': 'New York', 'niche': 'restaurants'}
)
```

### Database Operations
```python
# Get lead statistics
stats = orchestrator.get_lead_stats()

# Get leads with filters
leads = orchestrator.db.get_leads(
    filters={'city': 'New York'},
    limit=100
)

# Cleanup duplicates
duplicates_found, duplicates_removed = orchestrator.cleanup_duplicates()
```

## 🛡️ Best Practices

### Rate Limiting
- Always respect website rate limits
- Use delays between requests
- Rotate user agents regularly

### Error Handling
- Implement retry mechanisms
- Log errors for debugging
- Gracefully handle failures

### Data Quality
- Validate lead data before storing
- Remove duplicates across sources
- Clean and normalize data

### Legal Compliance
- Only scrape public data
- Respect robots.txt files
- Don't overload servers

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **No Leads Found**
   - Check internet connection
   - Verify search criteria
   - Try different sources

3. **Rate Limiting**
   - Increase delays between requests
   - Use fewer concurrent scrapers

4. **Database Errors**
   - Check file permissions
   - Ensure SQLite is available

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

### Optimization Tips
- Use appropriate limits per source
- Enable deduplication
- Clean up old data regularly
- Monitor database size

### Scaling
- Run scrapers in parallel
- Use multiple user agents
- Implement caching
- Consider distributed scraping

## 🔒 Security

### Data Protection
- Store data securely
- Encrypt sensitive information
- Regular backups
- Access controls

### Compliance
- GDPR compliance for EU data
- CCPA compliance for California
- Respect privacy policies
- Data retention policies

## 🚀 Future Enhancements

### Planned Features
- More data sources
- AI-powered lead scoring
- Advanced filtering
- API integration
- Real-time monitoring

### Custom Scrapers
The modular design makes it easy to add new scrapers:

```python
from scrapers.base_scraper import BaseScraper, LeadData

class CustomScraper(BaseScraper):
    def __init__(self):
        super().__init__("Custom Source", rate_limit_delay=1.0)
    
    def search_leads(self, city, country, niche, business_name=None, limit=50):
        # Implement your scraping logic
        leads = []
        # ... scraping code ...
        return leads
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test script
3. Check logs for errors
4. Review the code documentation

## 📄 License

This lead generation system is part of the LeadAI Pro platform. Please ensure compliance with all applicable laws and website terms of service when using this system.
