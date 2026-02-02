#!/usr/bin/env python3
"""
Business Lead Scraper - Command Line Interface

This CLI tool scrapes business leads using Selenium WebDriver.
It respects robots.txt, handles captchas gracefully, and exports to multiple formats.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import yaml
from colorama import init, Fore, Style

from selenium_scraper import SeleniumScraper
from exporter import DataExporter
from dedupe import Deduplicator
from config import Config
from utils import setup_logging, validate_location

# Initialize colorama for cross-platform colored output
init(autoreset=True)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Business Lead Scraper - Selenium-based lead generation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "coffee shop" --location "Lahore, Pakistan" --max 50
  %(prog)s --query "restaurants" --location "New York" --tile-mode --max 200
  %(prog)s --query "hotels" --location "Paris" --guest-mode --format csv json
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--query', '-q',
        required=True,
        help='Business type to search for (e.g., "coffee shop", "restaurant")'
    )
    
    parser.add_argument(
        '--location', '-l',
        required=True,
        help='Geographic location (e.g., "Lahore, Pakistan", "New York, USA")'
    )
    
    # Optional arguments
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=100,
        help='Maximum number of leads to collect (default: 100)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./data',
        help='Directory for output files (default: ./data)'
    )
    
    parser.add_argument(
        '--format', '-f',
        nargs='+',
        choices=['csv', 'json', 'sqlite', 'all'],
        default=['all'],
        help='Export formats (default: all)'
    )
    
    parser.add_argument(
        '--tile-mode',
        action='store_true',
        help='Enable geographic tiling for large areas'
    )
    
    parser.add_argument(
        '--tile-size',
        type=float,
        default=0.1,
        help='Size of each tile in degrees (default: 0.1)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.5,
        help='Delay between actions in seconds (default: 1.5)'
    )
    
    parser.add_argument(
        '--guest-mode',
        action='store_true',
        default=True,
        help='Launch Chrome in Guest mode (default: True)'
    )
    
    parser.add_argument(
        '--profile',
        type=str,
        default=None,
        help='Chrome profile name to use (e.g., "Profile 1")'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (not recommended for captcha handling)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Resume from a previous session file'
    )
    
    parser.add_argument(
        '--enrich-osm',
        action='store_true',
        help='Enable OpenStreetMap enrichment (optional)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    return parser.parse_args()


def print_banner():
    """Print application banner."""
    banner = f"""
{Fore.CYAN}{'='*70}
{Fore.CYAN}  ____            _                     _                    _
{Fore.CYAN} | __ ) _   _ ___(_)_ __   ___  ___ ___| |    ___  __ _  __| |___
{Fore.CYAN} |  _ \\| | | / __| | '_ \\ / _ \\/ __/ __| |   / _ \\/ _` |/ _` / __|
{Fore.CYAN} | |_) | |_| \\__ \\ | | | |  __/\\__ \\__ \\ |__|  __/ (_| | (_| \\__ \\
{Fore.CYAN} |____/ \\__,_|___/_|_| |_|\\___||___/___/_____\\___|\\__,_|\\__,_|___/
{Fore.CYAN}
{Fore.CYAN}  Selenium-Based Lead Generation Tool v1.0.0
{Fore.CYAN}{'='*70}
{Style.RESET_ALL}
"""
    print(banner)


def print_summary(leads, elapsed_time):
    """Print scraping summary."""
    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"{Fore.GREEN}  SCRAPING COMPLETE!")
    print(f"{Fore.GREEN}{'='*70}")
    print(f"{Fore.WHITE}  Total Leads Collected: {Fore.YELLOW}{len(leads)}")
    print(f"{Fore.WHITE}  Time Elapsed: {Fore.YELLOW}{elapsed_time:.2f} seconds")
    print(f"{Fore.WHITE}  Average Time per Lead: {Fore.YELLOW}{elapsed_time/len(leads):.2f} seconds" if leads else "")
    print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")


def main():
    """Main CLI entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Print banner
        print_banner()
        
        # Load configuration
        config = Config(args.config)
        
        # Override config with CLI arguments
        if args.verbose:
            config.logging['level'] = 'DEBUG'
        
        # Setup logging
        logger = setup_logging(config)
        
        # Validate inputs
        logger.info(f"Query: {args.query} | Location: {args.location}")
        
        if not validate_location(args.location):
            logger.warning("Location format may not be optimal. Consider using 'City, Country' format.")
        
        # Initialize scraper
        logger.info("Initializing Selenium scraper...")
        scraper = SeleniumScraper(
            config=config,
            headless=args.headless,
            guest_mode=args.guest_mode if not args.profile else False,
            profile=args.profile,
            delay=args.delay
        )
        
        # Start scraping
        start_time = datetime.now()
        logger.info(f"Starting scraping session at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        leads = scraper.scrape_google_maps(
            query=args.query,
            location=args.location,
            max_results=args.max,
            tile_mode=args.tile_mode,
            tile_size=args.tile_size
        )
        
        # Close scraper
        scraper.close()
        
        if not leads:
            logger.warning("No leads found. Try adjusting your query or location.")
            return 1
        
        # Deduplicate
        logger.info("Deduplicating results...")
        deduplicator = Deduplicator(config)
        unique_leads = deduplicator.deduplicate(leads)
        logger.info(f"✓ {len(unique_leads)} unique leads after deduplication")
        
        # Optional OSM enrichment
        if args.enrich_osm:
            logger.info("Enriching with OpenStreetMap data...")
            from overpass_enricher import OverpassEnricher
            enricher = OverpassEnricher(config)
            unique_leads = enricher.enrich(unique_leads)
        
        # Export results
        logger.info("Exporting results...")
        exporter = DataExporter(config, output_dir=args.output_dir)
        
        formats = args.format if 'all' not in args.format else ['csv', 'json', 'sqlite']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"leads_{timestamp}"
        
        exported_files = exporter.export(
            data=unique_leads,
            formats=formats,
            filename=base_filename
        )
        
        # Print summary
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print_summary(unique_leads, elapsed)
        
        # Print exported files
        print(f"{Fore.CYAN}Exported Files:{Style.RESET_ALL}")
        for file in exported_files:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {file}")
        
        logger.info("Scraping session completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Scraping interrupted by user{Style.RESET_ALL}")
        logger.info("Scraping interrupted by user")
        return 130
    
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
