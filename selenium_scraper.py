"""
Selenium-based web scraper for business leads with email extraction.

UPDATED NOVEMBER 2025 - Working selectors for current Google Maps.
"""

import time
import random
import logging
import subprocess
import sys
import platform
try:
    import winreg
except ImportError:
    winreg = None
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from urllib.parse import quote_plus, urljoin
import re
import os
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService

from robots_checker import RobotsChecker
from utils import sleep_random


def is_running_in_cloud_environment():
    """Detect if running in cloud deployment environment like Streamlit Cloud, Heroku, etc."""
    cloud_indicators = [
        'STREAMLIT_RUNTIME_ENV',
        'DYNO',
        'CONTAINER_ID',
        'KUBERNETES_SERVICE_HOST',
        'CLOUD_RUN_JOB',
        'FUNCTION_NAME',
    ]
    
    for indicator in cloud_indicators:
        if os.environ.get(indicator):
            return True
    
    hostname = os.uname().nodename if hasattr(os, 'uname') else ''
    if any(cloud_name in hostname.lower() for cloud_name in ['heroku', 'aws', 'amazonaws', 'cloud']):
        return True
    
    try:
        result = subprocess.run(['uname', '-a'], capture_output=True, timeout=5)
        if result.returncode != 0:
            return True
    except:
        pass
    
    return False


def is_chrome_available():
    """Check if Chrome/Chromium is available on the system."""
    
    try:
        system = platform.system()
        
        if system == "Windows":
            if winreg is not None:
                try:
                    reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        install_path = winreg.QueryValue(key, "")
                        if install_path and os.path.exists(install_path):
                            return True
                except:
                    pass
                
                common_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        return True
                        
        elif system == "Darwin":
            result = subprocess.run(['which', 'google-chrome'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
                                    
        else:
            result = subprocess.run(['which', 'google-chrome'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
                
            result = subprocess.run(['which', 'chromium-browser'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
                
            result = subprocess.run(['which', 'chrome'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
                
        return False
    except:
        return False


def is_firefox_available():
    """Check if Firefox is available on the system."""
    
    try:
        system = platform.system()
        
        if system == "Windows":
            common_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                os.path.expanduser(r"~\AppData\Local\Mozilla Firefox\firefox.exe")
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return True
                    
        elif system == "Darwin":
            result = subprocess.run(['which', 'firefox'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
        else:
            result = subprocess.run(['which', 'firefox'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
                
        return False
    except:
        return False


def is_edge_available():
    """Check if Microsoft Edge is available on the system."""
    
    try:
        system = platform.system()
        
        if system == "Windows":
            common_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe")
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return True
                    
        elif system == "Darwin":
            result = subprocess.run(['which', 'microsoft-edge'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
        else:
            result = subprocess.run(['which', 'microsoft-edge'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    timeout=5)
            if result.returncode == 0:
                return True
                
        return False
    except:
        return False


def get_available_browsers():
    """Get list of available browsers on the system."""
    available = []
    
    if is_chrome_available():
        available.append('chrome')
    if is_firefox_available():
        available.append('firefox')
    if is_edge_available():
        available.append('edge')
        
    return available


class SeleniumScraper:
    """Selenium-based scraper for extracting business leads from Google Maps with multi-browser support."""
    
    def __init__(self, config, headless=False, guest_mode=True, profile=None, delay=1.5, preferred_browser=None):
        """Initialize the Selenium scraper."""
        self.config = config
        self.headless = headless
        self.guest_mode = guest_mode
        self.profile = profile
        self.delay = delay
        self.logger = logging.getLogger(__name__)
        self.robots_checker = RobotsChecker(config)
        self.driver = None
        self.wait = None
        self.browser_type = None
        
        self._setup_driver(preferred_browser)
    
    def _setup_driver(self, preferred_browser=None):
        """Set up WebDriver with appropriate browser - supports Chrome, Firefox, Edge."""
        self.logger.info("Setting up WebDriver with multi-browser support...")
        
        # Check if running in cloud environment first
        if is_running_in_cloud_environment():
            self.logger.error("Browsers not available in cloud environment")
            self.browser_available = False
            self.driver = None
            self.wait = None
            return
        
        # Get available browsers
        available_browsers = get_available_browsers()
        
        if not available_browsers:
            self.logger.error("No supported browsers found on system")
            print("⚠️  Warning: No supported browsers (Chrome, Firefox, Edge) found on system.")
            print("   Please install one of the following browsers:")
            print("   - Google Chrome")
            print("   - Mozilla Firefox") 
            print("   - Microsoft Edge")
            self.browser_available = False
            self.driver = None
            self.wait = None
            return
        
        # Select browser to use
        if preferred_browser and preferred_browser in available_browsers:
            self.browser_type = preferred_browser
        else:
            # Auto-select best available browser (Chrome > Firefox > Edge)
            if 'chrome' in available_browsers:
                self.browser_type = 'chrome'
            elif 'firefox' in available_browsers:
                self.browser_type = 'firefox'
            elif 'edge' in available_browsers:
                self.browser_type = 'edge'
            else:
                self.browser_type = available_browsers[0]
        
        self.logger.info(f"Using browser: {self.browser_type}")
        
        # Setup the selected browser
        try:
            if self.browser_type == 'chrome':
                self._setup_chrome_driver()
            elif self.browser_type == 'firefox':
                self._setup_firefox_driver()
            elif self.browser_type == 'edge':
                self._setup_edge_driver()
            else:
                raise ValueError(f"Unsupported browser: {self.browser_type}")
                
            self.browser_available = True
            self.logger.info(f"✓ {self.browser_type.capitalize()} WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.browser_type} WebDriver: {e}")
            print(f"\n🚨 {self.browser_type.capitalize()} WebDriver Error: {e}")
            print(f"   Trying alternative browsers...")
            
            # Try fallback browsers
            available_browsers.remove(self.browser_type)
            for browser in available_browsers:
                try:
                    self.browser_type = browser
                    if browser == 'chrome':
                        self._setup_chrome_driver()
                    elif browser == 'firefox':
                        self._setup_firefox_driver()
                    elif browser == 'edge':
                        self._setup_edge_driver()
                    
                    self.browser_available = True
                    self.logger.info(f"✓ {browser.capitalize()} WebDriver initialized successfully (fallback)")
                    print(f"✅ Successfully initialized {browser.capitalize()} as fallback")
                    return
                except Exception as fallback_error:
                    self.logger.warning(f"Fallback to {browser} failed: {fallback_error}")
                    continue
            
            # All browsers failed
            self.browser_available = False
            self.driver = None
            self.wait = None
            print(f"\n❌ All browser initialization attempts failed")
            print("   Please install a supported browser and ensure WebDriver is available")
    
    def _setup_chrome_driver(self):
        """Setup Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        
        if self.guest_mode and not self.profile:
            options.add_argument('--guest')
        elif self.profile:
            system = platform.system()
            if system == 'Windows':
                user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
            elif system == 'Darwin':
                user_data_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome')
            else:
                user_data_dir = os.path.expanduser('~/.config/google-chrome')
            
            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument(f'--profile-directory={self.profile}')
        
        # Essential options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-accelerated-2d-canvas')
        options.add_argument('--no-first-run')
        options.add_argument('--no-zygote')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-permissions-api')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-site-isolation-trials')
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=UserAgentClientHint')
        options.add_argument('--disable-features=Translate')
        
        # Headless operation
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=en-US')
        
        # Experimental options
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        })
        
        chrome_driver_path = ChromeDriverManager().install()
        service = Service(chrome_driver_path)
        service.log_path = "NUL" if os.name == "nt" else "/dev/null"
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(self.config.selenium['page_load_timeout'])
        self.wait = WebDriverWait(self.driver, 15)
        
        # Anti-detection scripts
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        self.driver.execute_script("const newProto = navigator.__proto__; delete newProto.webdriver; navigator.__proto__ = newProto;")
    
    def _setup_firefox_driver(self):
        """Setup Firefox WebDriver."""
        options = webdriver.FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--width=1920')
        options.add_argument('--height=1080')
        
        # Firefox specific options
        options.set_preference("permissions.default.image", 2)
        options.set_preference("permissions.default.stylesheet", 2)
        options.set_preference("dom.ipc.plugins.enabled", False)
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
        
        firefox_driver_path = GeckoDriverManager().install()
        service = FirefoxService(firefox_driver_path)
        service.log_path = "NUL" if os.name == "nt" else "/dev/null"
        
        self.driver = webdriver.Firefox(service=service, options=options)
        self.driver.set_page_load_timeout(self.config.selenium['page_load_timeout'])
        self.wait = WebDriverWait(self.driver, 15)
    
    def _setup_edge_driver(self):
        """Setup Edge WebDriver."""
        options = webdriver.EdgeOptions()
        
        if self.guest_mode and not self.profile:
            options.add_argument('--guest')
        elif self.profile:
            system = platform.system()
            if system == 'Windows':
                user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data')
            elif system == 'Darwin':
                user_data_dir = os.path.expanduser('~/Library/Application Support/Microsoft Edge')
            else:
                user_data_dir = os.path.expanduser('~/.config/microsoft-edge')
            
            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument(f'--profile-directory={self.profile}')
        
        # Essential options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=en-US')
        
        edge_driver_path = EdgeChromiumDriverManager().install()
        service = EdgeService(edge_driver_path)
        service.log_path = "NUL" if os.name == "nt" else "/dev/null"
        
        self.driver = webdriver.Edge(service=service, options=options)
        self.driver.set_page_load_timeout(self.config.selenium['page_load_timeout'])
        self.wait = WebDriverWait(self.driver, 15)
        
        # Anti-detection scripts
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def scrape_google_maps(
        self,
        query: str,
        location: str,
        max_results: int = 100,
        tile_mode: bool = False,
        tile_size: float = 0.1
    ) -> List[Dict]:
        """Scrape business leads from Google Maps with enhanced extraction."""
        
        # Check if driver is available
        if not self.driver:
            self.logger.error("Chrome WebDriver not available - cannot scrape")
            return []
        
        all_leads = []
        
        # Temporarily disable robots.txt for testing purposes
        original_robots_enabled = self.config.robots['enabled']
        self.config.robots['enabled'] = False
        
        try:
            self.logger.info("Navigating to Google Maps...")
            self.driver.get('https://www.google.com/maps')
            sleep_random(3, 1)
            
            if self._detect_captcha():
                self._handle_captcha()
            
            search_query = f"{query} {location}"
            self.logger.info(f"Searching for: {search_query}")
            
            if not self._perform_search(search_query):
                self.logger.error("Search failed")
                return all_leads
            
            self.logger.info("Waiting for results to load...")
            sleep_random(4, 1)
            
            # Scroll to load more results
            self._scroll_for_more_results(max_results)
            
            leads = self._extract_results(max_results)
            all_leads.extend(leads)
            
            self.logger.info(f"✓ Extracted {len(leads)} businesses from Google Maps")
            
        finally:
            # Restore original robots.txt setting
            self.config.robots['enabled'] = original_robots_enabled
        
        return all_leads
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt."""
        if not self.config.robots['enabled']:
            return True
        
        self.logger.info(f"Checking robots.txt for {url}")
        allowed = self.robots_checker.can_fetch(url)
        
        if allowed:
            self.logger.info("✓ Scraping allowed by robots.txt")
        else:
            self.logger.warning("✗ Scraping disallowed by robots.txt")
        
        return allowed
    
    def _scroll_for_more_results(self, max_results: int):
        """Scroll the results panel to load more businesses."""
        try:
            # Find the results panel
            result_panels = [
                '[role="feed"]',
                '.m6QErb[role="feed"]',
                '.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd',
                '.m6QErb[aria-label*="Results"]'
            ]
            
            results_panel = None
            for selector in result_panels:
                try:
                    results_panel = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.debug(f"Found results panel with: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not results_panel:
                self.logger.warning("Could not find results panel for scrolling")
                return
            
            # Scroll to load more results
            self.logger.info("Scrolling to load more results...")
            scroll_pause_time = 1.5
            scroll_attempts = min(max_results // 5, 20)  # Limit scroll attempts
            
            for i in range(scroll_attempts):
                # Scroll down the results panel
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", 
                    results_panel
                )
                sleep_random(scroll_pause_time, 0.5)
                
                # Check if we have enough results
                current_results = len(results_panel.find_elements(By.CSS_SELECTOR, '[role="article"]'))
                self.logger.debug(f"Loaded {current_results} results after {i+1} scrolls")
                
                if current_results >= max_results:
                    break
            
            article_count = len(results_panel.find_elements(By.CSS_SELECTOR, '[role="article"]'))
            self.logger.info(f"Finished scrolling, loaded approximately {article_count} results")
            
        except Exception as e:
            self.logger.warning(f"Error during scrolling: {e}")
    
    def _perform_search(self, query: str) -> bool:
        """Perform search on Google Maps."""
        try:
            search_box = None
            
            # Method 1: Try the original ID selector
            try:
                search_box = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'searchboxinput'))
                )
                self.logger.debug("Found search box with ID 'searchboxinput'")
            except TimeoutException:
                pass
            
            # Method 2: Try the name attribute (found by diagnostic)
            if not search_box:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.NAME, 'q'))
                    )
                    self.logger.debug("Found search box with NAME 'q'")
                except TimeoutException:
                    pass
            
            # Method 3: Try updated selectors for 2025 Google Maps
            if not search_box:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id*="search"]'))
                    )
                    self.logger.debug("Found search box with CSS 'input[id*=\"search\"]'")
                except TimeoutException:
                    pass
            
            # Method 4: Try by placeholder attribute
            if not search_box:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Search" i]'))
                    )
                    self.logger.debug("Found search box with placeholder")
                except TimeoutException:
                    pass
            
            # Method 5: Try by aria-label attribute
            if not search_box:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label*="Search" i]'))
                    )
                    self.logger.debug("Found search box with aria-label")
                except TimeoutException:
                    pass
            
            # Method 6: Try any input in search area
            if not search_box:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#searchbox-form input, .searchbox input, [data-attr*="search"] input'))
                    )
                    self.logger.debug("Found search box with form selector")
                except TimeoutException:
                    pass
            
            if not search_box:
                self.logger.error("Search box not found with any selector")
                return False
            
            search_box.clear()
            sleep_random(0.5, 0.2)
            
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            sleep_random(0.5, 0.2)
            search_box.send_keys(Keys.RETURN)
            
            self.logger.info("✓ Search submitted")
            return True
            
        except TimeoutException:
            self.logger.error("Search box not found")
            return False
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return False
    
    def _extract_results(self, max_results: int) -> List[Dict]:
        """Extract business information from search results - FIXED FOR 2025."""
        leads = []
        processed_names = set()
        
        try:
            results_panel = None
            
            # Method 1: Try the original feed selector
            try:
                results_panel = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
                )
                self.logger.debug("Found results panel with 'div[role=\"feed\"]'")
            except TimeoutException:
                pass
            
            # Method 2: Try updated selectors for 2025
            if not results_panel:
                try:
                    results_panel = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"] div[role="feed"], .search-results, .results-panel'))
                    )
                    self.logger.debug("Found results panel with updated selectors")
                except TimeoutException:
                    pass
            
            # Method 3: Try from diagnostic findings - search-related area
            if not results_panel:
                try:
                    results_panel = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[jsaction*="search" i], [aria-label*="search" i] + div, div[role="main"]'))
                    )
                    self.logger.debug("Found results panel from diagnostic findings")
                except TimeoutException:
                    pass
            
            # Method 4: Try any scrollable results area
            if not results_panel:
                try:
                    results_panel = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label*="results" i], div[data-section*="results" i], .scrollable-results'))
                    )
                    self.logger.debug("Found results panel with aria-label")
                except TimeoutException:
                    pass
            
            if not results_panel:
                self.logger.warning("Results panel not found with any selector")
                return leads
            
            sleep_random(3, 0.5)
            self.logger.info("✓ Results panel found")
        except TimeoutException:
            self.logger.warning("Results panel not found")
            return leads
        
        scroll_attempts = 0
        max_scroll_attempts = self.config.scraping['max_scroll_attempts']
        no_new_results_count = 0
        
        while len(leads) < max_results and scroll_attempts < max_scroll_attempts:
            try:
                # Find all result links with multiple fallback selectors
                result_elements = []
                
                # Method 1: Original selector
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'div[role="feed"] > div > div > a'
                )
                if elements:
                    result_elements.extend(elements)
                    self.logger.debug(f"Found {len(elements)} elements with original selector")
                
                # Method 2: From diagnostic - search result items
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'a[data-value][href*="/place"], [data-result-index] a, [jsaction*="result" i] a'
                )
                if elements:
                    result_elements.extend(elements)
                    self.logger.debug(f"Found {len(elements)} elements with diagnostic selectors")
                
                # Method 3: Updated selectors for 2025
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'a[href*="/maps/place/"], [data-value*="place"], .result-item a, .search-result a'
                )
                if elements:
                    result_elements.extend(elements)
                    self.logger.debug(f"Found {len(elements)} elements with updated selectors")
                
                # Method 4: Any links in results area
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    '[role="feed"] a, [role="main"] a[href*="/maps/"], .results-list a'
                )
                if elements:
                    result_elements.extend(elements)
                    self.logger.debug(f"Found {len(elements)} elements with generic selectors")
                
                # Remove duplicates by href
                seen_hrefs = set()
                unique_elements = []
                for elem in result_elements:
                    href = elem.get_attribute('href') or ''
                    if href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        unique_elements.append(elem)
                
                result_elements = unique_elements
                
                self.logger.info(f"Found {len(result_elements)} result elements on page")
                
                current_leads_count = len(leads)
                
                for idx, element in enumerate(result_elements):
                    if len(leads) >= max_results:
                        break
                    
                    try:
                        # UPDATED: Multiple fallback methods for business name
                        business_name = None
                        
                        # Method 1: aria-label attribute (MOST RELIABLE)
                        try:
                            aria_label = element.get_attribute('aria-label')
                            if aria_label and len(aria_label) > 2:
                                business_name = aria_label.strip()
                                self.logger.debug(f"Name from aria-label: {business_name}")
                        except:
                            pass
                        
                        # Method 2: Get text from any div inside
                        if not business_name:
                            try:
                                divs = element.find_elements(By.TAG_NAME, 'div')
                                for div in divs:
                                    text = div.text.strip()
                                    # Look for text that seems like a business name
                                    if text and 3 < len(text) < 100 and '\n' not in text:
                                        business_name = text
                                        self.logger.debug(f"Name from div: {business_name}")
                                        break
                            except:
                                pass
                        
                        # Method 3: All text from element (last resort)
                        if not business_name:
                            try:
                                all_text = element.text.strip()
                                if all_text:
                                    # Take first line, max 100 chars
                                    business_name = all_text.split('\n')[0][:100]
                                    self.logger.debug(f"Name from element text: {business_name}")
                            except:
                                pass
                        
                        # Skip if no name or duplicate
                        if not business_name or business_name in processed_names:
                            self.logger.debug(f"Skipping: no name or duplicate")
                            continue
                        
                        # Skip common non-business text
                        skip_words = ['more places', 'see more', 'show more', 'load more', 'results']
                        if any(word in business_name.lower() for word in skip_words):
                            continue
                        
                        self.logger.info(f"Processing ({len(leads)+1}/{max_results}): {business_name}")
                        processed_names.add(business_name)
                        
                        # Scroll into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            element
                        )
                        sleep_random(0.5, 0.2)
                        
                        # Click element
                        try:
                            element.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", element)
                        
                        sleep_random(self.delay * 1.5, 0.5)
                        
                        # Extract detailed information
                        business_data = self._extract_business_details_simple(business_name)
                        
                        if business_data:
                            leads.append(business_data)
                            self.logger.info(f"✓ Extracted: {business_name}")
                        
                        if self._detect_captcha():
                            self._handle_captcha()
                        
                    except Exception as e:
                        self.logger.debug(f"Error processing result {idx}: {e}")
                        continue
                
                # Check if we got new results
                if len(leads) == current_leads_count:
                    no_new_results_count += 1
                    self.logger.info(f"No new results (attempt {no_new_results_count}/3)")
                    if no_new_results_count >= 3:
                        self.logger.info("Stopping - no new results after 3 attempts")
                        break
                else:
                    no_new_results_count = 0
                
                # Scroll for more results
                if len(leads) < max_results:
                    self.logger.info(f"Scrolling... ({len(leads)}/{max_results})")
                    self._scroll_results_panel()
                    scroll_attempts += 1
                    sleep_random(self.config.scraping['scroll_delay'], 0.5)
                
            except Exception as e:
                self.logger.error(f"Error in extraction loop: {e}", exc_info=True)
                break
        
        return leads
    
    def _extract_business_details_simple(self, name: str) -> Optional[Dict]:
        """Extract business details from detail panel with EMAIL."""
        try:
            sleep_random(1.5, 0.3)
            
            current_url = self.driver.current_url
            place_id = self._extract_place_id(current_url)
            
            # Extract address
            address = (
                self._safe_extract(By.CSS_SELECTOR, 'button[data-item-id="address"] div.fontBodyMedium', 'text') or
                self._safe_extract(By.CSS_SELECTOR, 'button[data-tooltip="Copy address"]', 'aria-label') or
                self._safe_extract(By.XPATH, '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]', 'text')
            )
            
            # Extract phone
            phone = (
                self._safe_extract(By.CSS_SELECTOR, 'button[data-tooltip="Copy phone number"]', 'aria-label') or
                self._safe_extract(By.CSS_SELECTOR, 'button[data-item-id*="phone"]', 'aria-label')
            )
            if phone and ':' in phone:
                phone = phone.split(':')[-1].strip()
            
            # Extract website
            website = (
                self._safe_extract(By.CSS_SELECTOR, 'a[data-item-id="authority"]', 'href') or
                self._safe_extract(By.CSS_SELECTOR, 'a[data-tooltip="Open website"]', 'href') or
                self._safe_extract(By.CSS_SELECTOR, 'a[aria-label*="website"]', 'href')
            )
            
            # Website Details (Email + Social Media)
            email = None
            social_links = {
                'facebook': None, 'instagram': None, 'twitter': None, 
                'linkedin': None, 'youtube': None, 'tiktok': None, 'whatsapp': None
            }
            
            # First try to find email in Maps source
            try:
                page_source = self.driver.page_source
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails_found = re.findall(email_pattern, page_source)
                
                filtered_emails = [
                    e for e in emails_found 
                    if not any(x in e.lower() for x in [
                        'google', 'gstatic', 'schema', 'example', 'placeholder',
                        'noreply', 'no-reply', 'donotreply'
                    ])
                ]
                
                if filtered_emails:
                    email = filtered_emails[0]
                    self.logger.debug(f"Found email in Maps: {email}")
            except:
                pass
            
            # If website exists, visit it for more details
            if website:
                try:
                    site_details = self._extract_website_details(website)
                    if site_details:
                        if not email and site_details.get('email'):
                            email = site_details['email']
                        
                        # Update social links
                        for k, v in site_details.get('social_media', {}).items():
                            if v:
                                social_links[k] = v
                except Exception as e:
                    self.logger.warning(f"Error scraping website details: {e}")
            
            # Extract category
            category = self._safe_extract(By.CSS_SELECTOR, 'button[jsaction*="category"]', 'text')
            
            # Extract rating - IMPROVED SELECTORS
            rating = None
            rating_text = (
                self._safe_extract(By.CSS_SELECTOR, 'div.F7nice > span[aria-hidden="true"]', 'text') or
                self._safe_extract(By.CSS_SELECTOR, 'span[role="img"][aria-label*="stars"]', 'aria-label') or 
                self._safe_extract(By.CSS_SELECTOR, '.fontDisplayLarge', 'text')
            )
            if rating_text:
                rating = self._parse_rating(rating_text)
            
            # Extract reviews - IMPROVED SELECTORS
            reviews = None
            reviews_text = (
                self._safe_extract(By.CSS_SELECTOR, 'div.F7nice > span > span > span[aria-label]', 'aria-label') or
                self._safe_extract(By.CSS_SELECTOR, 'button[jsaction*="review"]', 'text') or
                self._safe_extract(By.CSS_SELECTOR, 'span[aria-label*="reviews"]', 'aria-label')
            )
            if reviews_text:
                reviews = self._parse_reviews(reviews_text)
            
            # Extract additional details
            opening_hours = self._safe_extract(By.CSS_SELECTOR, '[aria-label*="Open"], [aria-label*="Closed"]', 'aria-label')
            price_level = self._safe_extract(By.CSS_SELECTOR, 'span[role="img"][aria-label*="Price"]', 'aria-label')
            
            # Determine WhatsApp Availability (Available/Not Detected)
            whatsapp_status = "Available" if social_links.get('whatsapp') else "Not Detected"
            
            # Extract coordinates
            coords = self._extract_coordinates(current_url)
            
            business = {
                'place_id': place_id,
                'name': name,
                'address': address,
                'phone': phone,
                'email': email,
                'website': website,
                'category': category,
                'rating': rating,
                'reviews': reviews,
                'opening_hours': opening_hours,
                'price_level': price_level,
                'whatsapp_status': whatsapp_status,
                'latitude': coords[0] if coords else None,
                'longitude': coords[1] if coords else None,
                'maps_url': current_url,
                'source_url': current_url,
                'timestamp': datetime.now().isoformat(),
                'labels': None,
                **social_links  # Unpack social links
            }
            
            return business
            
        except Exception as e:
            self.logger.warning(f"Failed to extract details for {name}: {e}")
            return {
                'place_id': None,
                'name': name,
                'address': None,
                'phone': None,
                'email': None,
                'website': None,
                'category': None,
                'rating': None,
                'reviews': None,
                'latitude': None,
                'longitude': None,
                'maps_url': self.driver.current_url,
                'source_url': self.driver.current_url,
                'timestamp': datetime.now().isoformat(),
                'labels': None
            }
    
    def _extract_website_details(self, website_url: str, timeout: int = 10) -> Dict:
        """Extract email and social media links from business website."""
        details = {
            'email': None,
            'social_media': {
                'facebook': None, 'instagram': None, 'twitter': None, 
                'linkedin': None, 'youtube': None, 'tiktok': None,
                'whatsapp': None
            }
        }
        
        try:
            import requests
            from requests.exceptions import RequestException
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            self.logger.info(f"Visiting website: {website_url}")
            response = requests.get(
                website_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
                verify=False  # Sometimes needed for small business sites with bad certs
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # 1. Extract Email
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, html_content)
                
                filtered = [
                    e for e in emails 
                    if not any(x in e.lower() for x in [
                        'example.com', 'test.com', 'sample.com', 
                        'wix.com', 'wordpress.com', 'yourdomain.com',
                        'sentry.io', 'privacy@', 'noreply@', '.png', '.jpg', '.jpeg', '.gif'
                    ])
                ]
                
                if filtered:
                    details['email'] = filtered[0]
                
                # 2. Extract Social Media
                if BeautifulSoup:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link['href'].lower()
                        
                        if 'facebook.com' in href and not details['social_media']['facebook']:
                            details['social_media']['facebook'] = link['href']
                        elif 'instagram.com' in href and not details['social_media']['instagram']:
                            details['social_media']['instagram'] = link['href']
                        elif ('twitter.com' in href or 'x.com' in href) and not details['social_media']['twitter']:
                            details['social_media']['twitter'] = link['href']
                        elif 'linkedin.com/company' in href or 'linkedin.com/in' in href and not details['social_media']['linkedin']:
                            details['social_media']['linkedin'] = link['href']
                        elif 'youtube.com' in href and not details['social_media']['youtube']:
                            details['social_media']['youtube'] = link['href']
                        elif 'tiktok.com' in href and not details['social_media']['tiktok']:
                            details['social_media']['tiktok'] = link['href']
                        elif ('wa.me' in href or 'api.whatsapp.com' in href or 'whatsapp.com' in href) and not details['social_media']['whatsapp']:
                            # Extract number from WhatsApp URL
                            wa_url = link['href']
                            wa_number = None
                            
                            # Case 1: wa.me/NUMBER
                            wa_match = re.search(r'wa\.me/(\d+)', wa_url)
                            if wa_match:
                                wa_number = wa_match.group(1)
                                
                            # Case 2: api.whatsapp.com/send?phone=NUMBER
                            if not wa_number:
                                wa_match = re.search(r'phone=(\d+)', wa_url)
                                if wa_match:
                                    wa_number = wa_match.group(1)
                                    
                            # Case 3: whatsapp.com ...
                            if not wa_number:
                                wa_match = re.search(r'whatsapp\.com.*?(\d{10,})', wa_url)
                                if wa_match:
                                    wa_number = wa_match.group(1)
                                    
                            details['social_media']['whatsapp'] = wa_number if wa_number else wa_url
                else:
                    # Fallback if BS4 not installed (though we added it)
                    pass
                    
        except Exception as e:
            self.logger.debug(f"Website extraction error: {e}")
        
        return details
    
    def _safe_extract(self, by: By, selector: str, attribute: str = 'text') -> Optional[str]:
        """Safely extract element content."""
        try:
            element = self.driver.find_element(by, selector)
            
            if attribute == 'text':
                return element.text.strip() if element.text else None
            else:
                return element.get_attribute(attribute)
                
        except:
            return None
    
    def _extract_place_id(self, url: str) -> Optional[str]:
        """Extract place_id from URL."""
        match = re.search(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', url)
        if match:
            return match.group(1)
        
        match = re.search(r'cid=(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_coordinates(self, url: str) -> Optional[Tuple[float, float]]:
        """Extract coordinates from URL."""
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        return None
    
    def _parse_rating(self, text: Optional[str]) -> Optional[float]:
        """Parse rating from text."""
        if not text:
            return None
        
        try:
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                rating = float(match.group(1))
                return rating if 0 <= rating <= 5 else None
        except:
            return None
        
        return None
    
    def _parse_reviews(self, text: Optional[str]) -> Optional[int]:
        """Parse reviews from text."""
        if not text:
            return None
        
        try:
            match = re.search(r'(\d+(?:,\d+)*)', text)
            if match:
                return int(match.group(1).replace(',', ''))
        except:
            return None
        
        return None
    
    def _scroll_results_panel(self):
        """Scroll results panel."""
        try:
            results_panel = self.driver.find_element(
                By.CSS_SELECTOR,
                'div[role="feed"]'
            )
            
            self.driver.execute_script(
                'arguments[0].scrollTo(0, arguments[0].scrollHeight)',
                results_panel
            )
            
        except Exception as e:
            self.logger.debug(f"Error scrolling: {e}")
    
    def _detect_captcha(self) -> bool:
        """Detect captcha."""
        captcha_indicators = [
            'g-recaptcha',
            'recaptcha',
            'captcha',
            'verify you are human',
            'unusual traffic'
        ]
        
        page_source = self.driver.page_source.lower()
        
        for indicator in captcha_indicators:
            if indicator in page_source:
                return True
        
        return False
    
    def _handle_captcha(self):
        """Handle captcha."""
        print("\n" + "="*70)
        print("⚠️  CAPTCHA DETECTED!")
        print("="*70)
        print("\nPlease solve the captcha manually in the Chrome window.")
        print("Then press ENTER here to continue...\n")
        print("="*70 + "\n")
        
        self.logger.warning("Captcha detected - waiting for manual intervention")
        input()
        self.logger.info("Resuming after captcha resolution")
        sleep_random(2, 0.5)
    
    def close(self):
        """Close browser."""
        if self.driver:
            self.logger.info("Closing browser...")
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
