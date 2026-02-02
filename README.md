# Business Lead Scraper - Selenium-Based Lead Generation Tool

⚠️ **IMPORTANT ETHICAL AND LEGAL NOTICE**

This project uses Selenium WebDriver to scrape publicly visible information from web pages. Before using this tool:

1. **Check Terms of Service**: Review the terms of service of any website you intend to scrape
2. **Respect robots.txt**: This tool checks and respects robots.txt files by default
3. **Local Laws**: Ensure compliance with local data protection and privacy laws (GDPR, CCPA, etc.)
4. **Rate Limiting**: Use reasonable delays to avoid overwhelming target servers
5. **Personal Data**: Be aware of data protection regulations when collecting business contact information

**This tool is for educational and research purposes. Users are solely responsible for ensuring their use complies with all applicable laws and terms of service.**

## Overview

A production-ready Python application that discovers business leads using Selenium WebDriver as the primary scraping engine. Includes both CLI and web UI interfaces, robust error handling, and ethical scraping practices.

### Key Features

- ✅ **Selenium-first approach**: Uses ChromeDriver for dynamic page interaction
- ✅ **Guest Mode & Profile Support**: Launch Chrome in Guest mode or with specific profiles
- ✅ **Google Maps Scraping**: Automated search and extraction from Google Maps
- ✅ **Geographic Tiling**: Split large areas into tiles for comprehensive coverage
- ✅ **Robust Selectors**: Explicit waits, retry logic, and fallback mechanisms
- ✅ **Captcha Detection**: Graceful handling with manual intervention support
- ✅ **robots.txt Compliance**: Automatic checking and enforcement
- ✅ **Multiple Export Formats**: CSV, JSON, and SQLite
- ✅ **Deduplication**: Intelligent fuzzy matching for duplicate removal
- ✅ **Flask Web UI**: User-friendly interface for non-technical users
- ✅ **Docker Support**: Containerized deployment option
- ✅ **100% Free**: No API keys, no paid services, lifetime-free operation

## Installation

### Prerequisites

- Python 3.9 or higher
- Chrome browser installed
- pip package manager

### Option 1: Local Installation

Clone or download the project
cd business-lead-scraper

Create virtual environment
python -m venv venv

Activate virtual environment
On Windows:
venv\Scripts\activate

On macOS/Linux:
source venv/bin/activate

Install dependencies
pip install -r requirements.txt

### Option 2: Docker Installation

Build the Docker image
docker build -t lead-scraper .

Run the container
docker run -it --rm -v $(pwd)/data:/app/data lead-scraper


## Quick Start

### CLI Usage

**Basic search:**

python cli.py --query "coffee shop" --location "Lahore, Pakistan" --max 50


**Advanced search with all options:**

python cli.py
--query "restaurants"
--location "New York, USA"
--max 200
--output-dir ./results
--format csv json sqlite
--tile-mode
--delay 2
--profile "Profile 1"


**Using Chrome Guest Mode (default):**

python cli.py --query "hotels" --location "Paris, France" --guest-mode


### Web UI Usage

Start the Flask server
python ui.py

Open browser to http://localhost:5000


## Chrome Profile Configuration

### Guest Mode (Default)

Guest mode launches Chrome without any saved data, extensions, or login information:

from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('--guest')


### Using a Named Profile

To use a specific Chrome profile (preserves logins, extensions, etc.):

**Find your Chrome profile path:**

- **Windows**: `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data`
- **macOS**: `~/Library/Application Support/Google/Chrome`
- **Linux**: `~/.config/google-chrome`

**List available profiles:**
Inside the User Data folder, you'll find directories like:
- `Default` (Profile 1)
- `Profile 1` (Profile 2)
- `Profile 2` (Profile 3)

**Use profile in CLI:**

python cli.py --query "shops" --location "London" --profile "Profile 1"


⚠️ **Note**: Chrome must be closed when using a specific profile, or you'll get a "profile in use" error.

## How It Works

### Selenium Scraping Flow

1. **Launch Chrome**: Opens visible Chrome window (Guest mode or specific profile)
2. **Navigate to Google Maps**: Goes to https://www.google.com/maps
3. **robots.txt Check**: Verifies scraping is allowed
4. **Search Query**: Types business type + location into search box
5. **Wait for Results**: Uses explicit waits for dynamic content to load
6. **Extract Cards**: Parses visible business cards from results panel
7. **Scroll & Paginate**: Scrolls left panel to load more results
8. **Detail Extraction**: Clicks each business for full details
9. **Deduplication**: Removes duplicates by place_id or fuzzy matching
10. **Export**: Saves to CSV, JSON, and SQLite

### Geographic Tiling

For large areas, the scraper divides the bounding box into smaller tiles:

+-------+-------+-------+
| T1 | T2 | T3 |
+-------+-------+-------+
| T4 | T5 | T6 |
+-------+-------+-------+
| T7 | T8 | T9 |


Each tile is searched independently to ensure comprehensive coverage.

## CLI Arguments

--query Business type to search for (required)
--location Geographic location (required)
--max Maximum number of leads to collect (default: 100)
--output-dir Directory for output files (default: ./data)
--format Export formats: csv, json, sqlite (default: all)
--tile-mode Enable geographic tiling for large areas
--tile-size Size of each tile in degrees (default: 0.1)
--delay Delay between actions in seconds (default: 1.5)
--guest-mode Launch Chrome in Guest mode (default: True)
--profile Chrome profile name to use (e.g., "Profile 1")
--headless Run in headless mode (not recommended)


## Configuration File

Create `config.yaml` to set default parameters:

scraping:
default_delay: 1
5 max_scroll_attempts
10 request_timeo
selenium:
page_load_timeout:
0 implicit_wai
export:
output_dir: "./dat
" f

deduplication:
fuzzy_threshold: 0.85
dedupe_fields: ["name", "address", "phone"]


## Handling Captchas and Blocks

### When a Captcha Appears

The scraper will:
1. Detect the captcha/block
2. Pause execution
3. Keep the Chrome window open
4. Print clear instructions:

⚠️ CAPTCHA DETECTED!

A captcha or verification page has been detected.
Please solve it manually in the open Chrome window.

Steps:

Switch to the Chrome window that just opened

Complete the captcha or verification

Wait for the page to load normally

Press ENTER in this terminal to continue...


### Resume After Manual Intervention

The scraper saves progress periodically, so if interrupted:


python cli.py --resume ./data/session_20251113_223045.json



## Safety & Rate Limiting

### Polite Scraping Defaults

- **Delay between actions**: 1.5-3 seconds (randomized)
- **Scroll delay**: 2-4 seconds
- **Retry backoff**: Exponential (1s, 2s, 4s, 8s...)
- **Max requests per session**: 500 (configurable)
- **User-Agent**: Real Chrome user agent
- **Concurrent limit**: 1 (no parallel requests)

### robots.txt Compliance

Before scraping any domain, the tool:
1. Fetches `/robots.txt`
2. Parses disallow rules
3. Checks if the target path is allowed
4. Skips and logs if disallowed

## Exported Data Fields

| Field | Description | Example |
|-------|-------------|---------|
| `place_id` | Google Maps unique ID | ChIJN1t_tDeuEmsRUsoyG83frY4 |
| `name` | Business name | The Coffee House |
| `address` | Full street address | 123 Main St, Lahore, Punjab 54000 |
| `phone` | Phone number | +92 42 1234567 |
| `website` | Business website URL | https://example.com |
| `category` | Business category/type | Coffee Shop |
| `rating` | Average rating | 4.5 |
| `reviews` | Number of reviews | 230 |
| `hours` | Opening hours | Mon-Fri: 9AM-9PM |
| `latitude` | Latitude coordinate | 31.5204 |
| `longitude` | Longitude coordinate | 74.3587 |
| `maps_url` | Google Maps URL | https://maps.google.com/?cid=... |
| `source_url` | Source page URL | https://www.google.com/maps/search/... |
| `timestamp` | Collection timestamp | 2025-11-13T22:30:45Z |
| `labels` | Additional labels | Delivery, Takeout, Dine-in |

## Testing

Run the test suite:

Run all tests
pytest tests/ -v

Run specific test module
pytest tests/test_dedupe.py -v

Run with coverage
pytest tests/ --cov=. --cov-report=html


## Example Output

### Sample CSV Output

name,address,phone,website,category,rating,reviews
The Coffee House,"123 Main St, Lahore",+92 42 1234567,https://example.com,Coffee Shop,4.5,230
Brew & Beans,"456 Park Ave, Lahore",+92 42 7654321,https://brewbeans.pk,Cafe,4.7,182



### Sample Run Log
[INFO] Starting business lead scraper
[INFO] Query: coffee shop | Location: Lahore, Pakistan
[INFO] Launching Chrome in Guest mode
[INFO] Checking robots.txt for google.com/maps
[INFO] ✓ Scraping allowed by robots.txt
[INFO] Navigating to Google Maps
[INFO] Entering search query: coffee shop Lahore, Pakistan
[INFO] Waiting for results to load...
[INFO] ✓ Found 120 results in left panel
[INFO] Extracting business cards (page 1/5)
[INFO] Scrolling for more results...
[INFO] ✓ Extracted 10 businesses
[INFO] Deduplicating results...
[INFO] ✓ 10 unique businesses found
[INFO] Exporting to CSV: ./data/leads_20251113_223045.csv
[INFO] Exporting to JSON: ./data/leads_20251113_223045.json
[INFO] Exporting to SQLite: ./data/leads_20251113_223045.db
[INFO] ✓ Scraping complete! 10 leads collected.



## Safer Alternatives

### OpenStreetMap / Overpass API

For structured POI data without scraping:

Enable OpenStreetMap enrichment
python cli.py --query "cafe" --location "Paris" --enrich-osm



**Tradeoffs:**
- ✅ **Pros**: Structured, legal, free, comprehensive
- ❌ **Cons**: May have less business detail (no reviews/ratings), data freshness varies

### Official APIs (Requires Keys)

For production use, consider official APIs:
- Google Places API (free tier: 0-100k requests/month)
- Bing Local Search API
- Foursquare Places API

## Troubleshooting

### Chrome fails to launch

**Error**: `WebDriverException: chrome not reachable`

**Solution**: Ensure Chrome is installed and chromedriver-manager can find it:
python -c "from selenium import webdriver; webdriver.Chrome()"



### Profile in use error

**Error**: `user data directory is already in use`

**Solution**: Close all Chrome instances before running with a specific profile.

### No results found

**Issue**: Search returns 0 results

**Solutions**:
- Check if the location is specific enough
- Try a different business type query
- Increase delay with `--delay 3`
- Run in visible mode to see what's happening

### Captcha appearing frequently

**Solutions**:
- Increase delays: `--delay 3`
- Use a real Chrome profile with browsing history
- Reduce max results: `--max 50`
- Run searches in smaller batches

## Docker Usage

### Build Image

docker build -t lead-scraper .



### Run CLI in Container

docker run -it --rm
-v $(pwd)/data:/app/data
lead-scraper
python cli.py --query "restaurants" --location "NYC" --max 50



### Run Web UI in Container

docker run -it --rm
-p 5000:5000
-v $(pwd)/data:/app/data
lead-scraper
python ui.py



## Project Structure

business-lead-scraper/
├── README.md
├── requirements.txt
├── Dockerfile
├── config.yaml
├── cli.py # CLI entry point
├── ui.py # Flask web UI
├── config.py # Configuration management
├── utils.py # Utility functions
├── selenium_scraper.py # Main Selenium scraper
├── overpass_enricher.py # Optional OSM enrichment
├── exporter.py # Export to CSV/JSON/SQLite
├── dedupe.py # Deduplication logic
├── robots_checker.py # robots.txt compliance
├── tests/
│ ├── init.py
│ ├── test_dedupe.py
│ ├── test_exporter.py
│ └── test_scraper.py
├── data/ # Output directory
│ ├── leads_.csv
│ ├── leads_.json
│ └── leads_*.db
└── logs/ # Log files
└── scraper.log



## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All tests pass
- New features include tests
- Documentation is updated

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is provided as-is for educational purposes. The authors are not responsible for misuse or any violations of terms of service, privacy laws, or other regulations. Always obtain proper authorization before scraping websites.

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Python**: 3.9+