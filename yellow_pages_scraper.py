"""
Yellow Pages Scraper Module
Scrapes business data from Yellow Pages using Selenium
"""

import time
import random
import logging
from typing import List, Dict, Optional
from urllib.parse import quote_plus
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from utils import sleep_random


class YellowPagesScraper:
    """Selenium-based scraper for extracting business leads from Yellow Pages."""
    
    def __init__(self, config, headless=True, delay=2.0):
        """Initialize the Yellow Pages scraper."""
        self.config = config
        self.headless = headless
        self.delay = delay
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
        
        self._setup_driver()
    
    def _setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        self.logger.info("Setting up Chrome WebDriver for Yellow Pages...")
        
        options = Options()
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=en-US')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })
        
        # Additional stealth options
        options.add_argument('--disable-features=UserAgentClientHint')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-features=Translate')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.set_page_load_timeout(
                self.config.selenium['page_load_timeout']
            )
            
            self.wait = WebDriverWait(self.driver, 15)
            
            # Additional stealth scripts
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
            )
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
            )
            self.driver.execute_script(
                "const newProto = navigator.__proto__;\n"
                "delete newProto.webdriver;\n"
                "navigator.__proto__ = newProto;"
            )
            
            self.logger.info("✓ Chrome WebDriver initialized successfully for Yellow Pages")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def scrape_yellow_pages(
        self,
        query: str,
        location: str,
        max_results: int = 50
    ) -> List[Dict]:
        """Scrape business leads from Yellow Pages with enhanced extraction."""
        all_leads = []
        
        self.logger.info("Navigating to Yellow Pages...")
        self.driver.get('https://www.yellowpages.com/')
        sleep_random(3, 1)
        
        self.logger.info(f"Searching for: {query} in {location}")
        
        if not self._perform_search(query, location):
            self.logger.error("Search failed")
            return all_leads
        
        self.logger.info("Waiting for results to load...")
        sleep_random(4, 1)
        
        # Scroll to load more results
        self._scroll_for_more_results(max_results)
        
        leads = self._extract_results(max_results)
        all_leads.extend(leads)
        
        self.logger.info(f"✓ Extracted {len(leads)} businesses from Yellow Pages")
        
        return all_leads
    
    def _scroll_for_more_results(self, max_results: int):
        """Scroll the results to load more businesses on Yellow Pages."""
        try:
            self.logger.info("Scrolling to load more Yellow Pages results...")
            scroll_pause_time = 2.0
            scroll_attempts = min(max_results // 4, 12)  # Limit scroll attempts
            
            for i in range(scroll_attempts):
                # Scroll to bottom of page
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep_random(scroll_pause_time, 0.5)
                
                # Check if we have enough results
                current_results = len(self.driver.find_elements(By.CSS_SELECTOR, '.result'))
                self.logger.debug(f"Loaded {current_results} results after {i+1} scrolls")
                
                if current_results >= max_results:
                    break
            
            result_count = len(self.driver.find_elements(By.CSS_SELECTOR, '.result'))
            self.logger.info(f"Finished scrolling, loaded approximately {result_count} results")
            
        except Exception as e:
            self.logger.warning(f"Error during Yellow Pages scrolling: {e}")
    
    def _perform_search(self, query: str, location: str) -> bool:
        """Perform search on Yellow Pages."""
        try:
            # Find the search input fields
            search_box = None
            location_box = None
            
            # Try multiple selectors for search box
            search_selectors = [
                'input[name="query"]',
                'input[aria-label="Search for"]',
                'input#query',
                'input[data-impressed="1"]'
            ]
            
            for selector in search_selectors:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.debug(f"Found search box with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not search_box:
                self.logger.error("Search box not found with any selector")
                return False
            
            # Try multiple selectors for location box
            location_selectors = [
                'input[name="location"]',
                'input[aria-label="Where"]',
                'input#location',
                'input[data-placeholder="Enter a location"]'
            ]
            
            for selector in location_selectors:
                try:
                    location_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.debug(f"Found location box with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not location_box:
                self.logger.error("Location box not found with any selector")
                return False
            
            # Clear and fill the search boxes
            search_box.clear()
            sleep_random(0.5, 0.2)
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            location_box.clear()
            sleep_random(0.5, 0.2)
            for char in location:
                location_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            sleep_random(0.5, 0.2)
            search_box.send_keys(Keys.RETURN)
            
            self.logger.info("✓ Yellow Pages search submitted")
            return True
            
        except TimeoutException:
            self.logger.error("Search box not found")
            return False
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return False
    
    def _extract_results(self, max_results: int) -> List[Dict]:
        """Extract business information from search results."""
        leads = []
        processed_names = set()
        
        try:
            # Wait for results to load
            sleep_random(3, 0.5)
            
            # Find result containers
            result_containers = []
            container_selectors = [
                '.search-results .result',
                '.container .result',
                '.search-results li',
                '.result'
            ]
            
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        result_containers.extend(containers)
                        self.logger.debug(f"Found {len(containers)} result containers with {selector}")
                        break
                except:
                    continue
            
            if not result_containers:
                # Alternative: try general div containers
                try:
                    result_containers = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-track-component]')
                    if result_containers:
                        self.logger.debug(f"Found {len(result_containers)} alternative containers")
                except:
                    pass
            
            self.logger.info(f"Found {len(result_containers)} result containers")
            
            for idx, container in enumerate(result_containers):
                if len(leads) >= max_results:
                    break
                
                try:
                    # Extract business information from the container
                    business_data = self._extract_business_from_container(container)
                    
                    if business_data and business_data.get('name'):
                        name = business_data['name']
                        if name not in processed_names:
                            leads.append(business_data)
                            processed_names.add(name)
                            self.logger.info(f"✓ Extracted: {name}")
                            
                except Exception as e:
                    self.logger.debug(f"Error processing container {idx}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error in extraction: {e}", exc_info=True)
        
        return leads
    
    def _extract_business_from_container(self, container) -> Optional[Dict]:
        """Extract business details from a single container."""
        try:
            # Find the main link element which contains the business info
            link_selectors = [
                'a.business-name',
                '.business-name',
                'a[href*="/business/"]',
                'a[href*="/ypgseo"]'
            ]
            
            link_element = None
            for selector in link_selectors:
                try:
                    link_element = container.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not link_element:
                return None
            
            # Extract business name
            name = None
            try:
                name = link_element.text.strip() or link_element.get_attribute('title')
            except:
                pass
            
            if not name:
                return None
            
            # Extract other details
            details = {
                'name': name,
                'address': self._extract_address(container),
                'phone': self._extract_phone(container),
                'rating': self._extract_rating(container),
                'reviews': self._extract_review_count(container),
                'category': self._extract_category(container),
                'website': self._extract_website(container),
                'yellow_pages_url': link_element.get_attribute('href'),
                'source_url': self.driver.current_url,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'latitude': None,
                'longitude': None,
                'email': None,  # Yellow Pages doesn't typically show emails
                'labels': 'Yellow Pages'
            }
            
            # Visit the business page to get more details if possible
            original_window = self.driver.current_window_handle
            try:
                # Get the business URL
                business_url = link_element.get_attribute('href')
                if business_url and not business_url.startswith('http'):
                    business_url = 'https://www.yellowpages.com' + business_url
                
                if business_url:
                    # Open in new tab
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    
                    # Navigate to the business page
                    self.driver.get(business_url)
                    sleep_random(2, 0.5)
                    
                    # Extract additional details from the business page
                    details['address'] = details['address'] or self._extract_with_selectors(self.driver, [
                        '.address',
                        '[data-automation="address"]'
                    ])
                    
                    details['phone'] = details['phone'] or self._extract_with_selectors(self.driver, [
                        '.phone',
                        '[data-automation="phone"]'
                    ])
                    
                    details['website'] = details['website'] or self._extract_with_selectors(self.driver, [
                        '.website-link',
                        'a[href*="redirect"]'
                    ])
                
                # Close the new tab and switch back
                self.driver.close()
                self.driver.switch_to.window(original_window)
                
            except Exception as e:
                # If we can't get more details, continue with what we have
                self.driver.switch_to.window(original_window)
                self.logger.debug(f"Could not get extra details: {e}")
            
            return details
            
        except Exception as e:
            self.logger.debug(f"Error extracting business from container: {e}")
            return None
    
    def _extract_address(self, container):
        """Extract address from container."""
        try:
            address_selectors = [
                '.adr',
                '.street-address',
                '.address',
                '[data-automation="address"]'
            ]
            
            for selector in address_selectors:
                try:
                    address_elem = container.find_element(By.CSS_SELECTOR, selector)
                    address = address_elem.text.strip()
                    if address:
                        return address
                except:
                    continue
        except:
            pass
        return None
    
    def _extract_phone(self, container):
        """Extract phone from container."""
        try:
            phone_selectors = [
                '.phone',
                '[data-automation="phone"]',
                '.tel'
            ]
            
            for selector in phone_selectors:
                try:
                    phone_elem = container.find_element(By.CSS_SELECTOR, selector)
                    phone = phone_elem.text.strip()
                    if phone and phone.startswith('('):
                        return phone
                except:
                    continue
        except:
            pass
        return None
    
    def _extract_rating(self, container):
        """Extract rating from container."""
        try:
            rating_selectors = [
                '.rating',
                '.star',
                '[data-automation*="rating"]'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = container.find_element(By.CSS_SELECTOR, selector)
                    aria_label = rating_elem.get_attribute('aria-label')
                    if aria_label and 'star' in aria_label.lower():
                        # Extract rating number
                        rating_match = re.search(r'(\d+\.?\d*)', aria_label)
                        if rating_match:
                            return float(rating_match.group(1))
                except:
                    continue
        except:
            pass
        return None
    
    def _extract_review_count(self, container):
        """Extract review count from container."""
        try:
            review_selectors = [
                '.count',
                '[data-automation*="review"]',
                'span:contains("review")'
            ]
            
            for selector in review_selectors:
                try:
                    review_elem = container.find_element(By.CSS_SELECTOR, selector)
                    text = review_elem.text.strip()
                    if 'review' in text.lower():
                        # Extract number
                        count_match = re.search(r'(\d+)', text)
                        if count_match:
                            return int(count_match.group(1))
                except:
                    continue
        except:
            pass
        return None
    
    def _extract_category(self, container):
        """Extract business category from container."""
        try:
            category_selectors = [
                '.categories',
                '.categories a',
                '[data-automation="categories"]'
            ]
            
            for selector in category_selectors:
                try:
                    category_elem = container.find_element(By.CSS_SELECTOR, selector)
                    category = category_elem.text.strip()
                    if category and len(category) < 100:  # Filter out overly long text
                        return category
                except:
                    continue
        except:
            pass
        return None
    
    def _extract_website(self, container):
        """Extract website from container."""
        try:
            website_selectors = [
                '.website-link',
                'a[href*="redirect"]',
                '[data-automation="website"]'
            ]
            
            for selector in website_selectors:
                try:
                    website_elem = container.find_element(By.CSS_SELECTOR, selector)
                    website = website_elem.get_attribute('href')
                    if website:
                        return website
                except:
                    continue
        except:
            pass
        return None
    
    def _extract_with_selectors(self, driver_instance, selectors):
        """Extract text using multiple selectors."""
        for selector in selectors:
            try:
                sub_element = driver_instance.find_element(By.CSS_SELECTOR, selector)
                text = sub_element.text.strip()
                if text:
                    return text
            except:
                continue
        return None
    
    def close(self):
        """Close browser."""
        if self.driver:
            self.logger.info("Closing browser...")
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")