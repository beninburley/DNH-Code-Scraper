"""
Collector for ecode360 municipalities from General Code library.
Scrapes the list of municipalities by state from generalcode.com/library.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import re


class Ecode360Collector:
    """Collects ecode360 city links from General Code library."""
    
    def __init__(self):
        self.base_url = "https://www.generalcode.com/library/"
        self.source_library_url = "https://www.generalcode.com/source-library/"
    
    def collect_state_cities(self, state_code: str) -> List[Dict]:
        """
        Collect all cities for a given state from General Code library.
        
        Args:
            state_code: Two-letter state code (e.g., 'NY', 'CA')
            
        Returns:
            List of dicts with 'city', 'state', 'url', 'code' keys
        """
        print(f"\n🗺️  Collecting {state_code} municipalities from General Code library...")
        
        cities = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            try:
                # Navigate directly to the source-library iframe with state parameter
                # The library page uses an iframe that loads from /source-library/
                url = f"{self.source_library_url}?state={state_code}"
                print(f"  📍 Loading {url}")
                page.goto(url, timeout=60000)
                
                # Wait for JavaScript to render
                page.wait_for_load_state('networkidle')
                time.sleep(3)  # Extra wait for dynamic content
                
                # Get page content after state is selected
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')
                
                # Debug: save HTML to file
                with open(f"debug_{state_code}_library.html", 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"  🐛 Saved page HTML to debug_{state_code}_library.html")
                
                # Look for municipality links
                # General Code library typically shows links in a list format
                # Links to ecode360 typically have pattern: ecode360.com/[CODE]
                
                links = soup.find_all('a', href=re.compile(r'ecode360\.com/[A-Z]{2}\d+'))
                
                if not links:
                    # Try alternative selector - look for any links containing ecode360
                    links = soup.find_all('a', href=re.compile(r'ecode360\.com/\w+'))
                
                print(f"  📊 Found {len(links)} potential municipality links")
                
                # Debug: also look for any links at all
                all_links = soup.find_all('a', href=True)
                ecode_links = [l for l in all_links if 'ecode360' in l.get('href', '')]
                print(f"  🐛 Found {len(ecode_links)} links containing 'ecode360'")
                
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Extract code from URL (e.g., MA1379 from ecode360.com/MA1379)
                    match = re.search(r'ecode360\.com/([A-Z]{2}\d+)', href)
                    if match:
                        code = match.group(1)
                        
                        # Clean city name
                        city_name = self._clean_city_name(text)
                        
                        # Build full URL if needed
                        if not href.startswith('http'):
                            href = f"https://ecode360.com/{code}"
                        
                        cities.append({
                            'city': city_name,
                            'state': state_code,
                            'url': href,
                            'code': code
                        })
                
                # Filter out counties - only keep cities, towns, villages, etc.
                original_count = len(cities)
                cities = [c for c in cities if not self._is_county(c['city'])]
                filtered_count = original_count - len(cities)
                
                print(f"  ✅ Collected {len(cities)} municipalities for {state_code}")
                if filtered_count > 0:
                    print(f"  🚫 Filtered out {filtered_count} counties")
                
            except Exception as e:
                print(f"  ❌ Error collecting {state_code} municipalities: {e}")
            
            finally:
                browser.close()
        
        return cities
    
    def _is_county(self, name: str) -> bool:
        """Check if municipality name is a county."""
        name_lower = name.lower()
        # Check if it explicitly says "county" but not "county of"
        if 'county' in name_lower:
            # Allow "County of X" format (some municipalities use this)
            if name_lower.startswith('county of'):
                return False
            # Filter out "X County" format
            if name_lower.endswith('county') or ' county' in name_lower:
                return True
        return False
    
    def _clean_city_name(self, text: str) -> str:
        """Clean up city name from link text."""
        # Remove common suffixes
        text = re.sub(r'\s*-\s*Code.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*,\s*[A-Z]{2}.*', '', text)  # Remove ", NY" etc.
        text = text.strip()
        return text
    
    def save_cities(self, cities: List[Dict], filename: str = "ecode360_cities.json"):
        """Save collected cities to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cities, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(cities)} cities to {filename}")
    
    def load_cities(self, filename: str = "ecode360_cities.json") -> List[Dict]:
        """Load cities from JSON file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                cities = json.load(f)
            print(f"📂 Loaded {len(cities)} cities from {filename}")
            return cities
        except FileNotFoundError:
            print(f"⚠️  File {filename} not found")
            return []


if __name__ == "__main__":
    # Test the collector
    collector = Ecode360Collector()
    ny_cities = collector.collect_state_cities('NY')
    
    if ny_cities:
        collector.save_cities(ny_cities)
        print(f"\n📋 Sample cities:")
        for city in ny_cities[:5]:
            print(f"  - {city['city']}: {city['url']}")
