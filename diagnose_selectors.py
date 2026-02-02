#!/usr/bin/env python3
"""
Diagnostic script to check Google Maps page structure
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def diagnose_google_maps():
    """Check what elements are available on Google Maps"""
    
    # Setup Chrome
    options = Options()
    options.add_argument('--guest')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print("Navigating to Google Maps...")
        driver.get('https://www.google.com/maps')
        time.sleep(5)
        
        print("Page title:", driver.title)
        print("Current URL:", driver.current_url)
        
        # Check for various search input selectors
        selectors_to_check = [
            '#searchboxinput',
            'input[id*="search"]',
            'input[placeholder*="Search"]',
            'input[placeholder*="search"]',
            'input[type="text"]',
            'input[name="q"]',
            '#searchbox-form input',
            '.searchbox input',
            '[data-attr*="search"] input',
            'input[aria-label*="Search"]',
            'input[aria-label*="search"]',
            'input',
        ]
        
        print("\n=== Checking Search Input Selectors ===")
        found_any = False
        for selector in selectors_to_check:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✓ Found {len(elements)} elements with: {selector}")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        print(f"  Element {i+1}: placeholder='{elem.get_attribute('placeholder')}', id='{elem.get_attribute('id')}', class='{elem.get_attribute('class')}'")
                    found_any = True
                else:
                    print(f"✗ No elements found with: {selector}")
            except Exception as e:
                print(f"✗ Error with {selector}: {e}")
        
        # Check all input elements
        print("\n=== All Input Elements ===")
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"Found {len(inputs)} total input elements:")
        for i, inp in enumerate(inputs[:10]):  # Show first 10
            print(f"  Input {i+1}: type='{inp.get_attribute('type')}', placeholder='{inp.get_attribute('placeholder')}', id='{inp.get_attribute('id')}', class='{inp.get_attribute('class')}'")
        
        # Check for any search-related elements
        print("\n=== Search-Related Elements ===")
        search_selectors = [
            '[class*="search"]',
            '[id*="search"]',
            '[aria-label*="search"]',
            '[data-testid*="search"]',
        ]
        
        for selector in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✓ Found {len(elements)} elements with: {selector}")
                    for i, elem in enumerate(elements[:3]):
                        print(f"  Element {i+1}: tag={elem.tag_name}, text='{elem.text[:50]}'")
            except Exception as e:
                print(f"✗ Error with {selector}: {e}")
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to close browser...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    diagnose_google_maps()
