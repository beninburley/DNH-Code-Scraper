"""
Parser for ecode360.com municipal code platform.
Scrapes codes of ethics/conduct from ecode360 sites.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional


class Ecode360Parser:
    """Parser for ecode360.com platform."""
    
    # Enhanced ethics terms including aspirational language
    ETHICS_TERMS = [
        'ethic', 'code of conduct', 'code of ethic', 'conflict of interest',
        'financial disclosure', 'public officer', 'prohibited interest',
        'standards of conduct', 'professional conduct'
    ]
    
    ASPIRATIONAL_TERMS = [
        'strive', 'shall endeavor', 'aspire', 'seek to', 'best interest',
        'shall pursue', 'commit to'
    ]
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.cloudflare_blocked = False
    
    def search_for_ethics_terms(self, text: str) -> bool:
        """Check if text contains ethics-related terms."""
        text_lower = text.lower()
        return any(term in text_lower for term in self.ETHICS_TERMS)
    
    def contains_aspirational_language(self, text: str) -> bool:
        """Check if text contains aspirational language."""
        text_lower = text.lower()
        return any(term in text_lower for term in self.ASPIRATIONAL_TERMS)
    
    def scrape_city(self, city_info: Dict) -> Optional[Dict]:
        """
        Scrape ethics code from an ecode360 city.
        
        Args:
            city_info: Dict with 'city', 'state', 'url', 'code' keys
            
        Returns:
            Dict with 'city', 'state', 'url', 'ethics_sections' or None if not found
        """
        city_name = city_info.get('city', 'Unknown')
        state = city_info.get('state', 'Unknown')
        url = city_info.get('url', '')
        code = city_info.get('code', '')
        
        print(f"\n🔍 Scraping {city_name}, {state}...")
        print(f"  Platform: ecode360")
        print(f"  URL: {url}")
        
        try:
            with sync_playwright() as p:
                # Launch with more realistic browser settings to avoid detection
                self.browser = p.chromium.launch(
                    headless=False,  # Run in headed mode to avoid detection
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                self.page = context.new_page()
                
                # Step 1: Load homepage to find table of contents
                print("  🔍 Loading homepage...")
                self.page.goto(url, timeout=60000)
                self.page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                html = self.page.content()
                soup = BeautifulSoup(html, 'lxml')
                
                # Debug: save HTML
                with open(f"debug_malta_home.html", 'w', encoding='utf-8') as f:
                    f.write(html)
                
                # Find all chapter/section links in the table of contents
                # ecode360 uses class="titleLink" for chapter links
                all_links = soup.find_all('a', class_='titleLink')
                
                print(f"  📋 Found {len(all_links)} chapters")
                
                # Filter for ethics-related sections
                ethics_sections = []
                for link in all_links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    # Only check titled sections (chapters), not subsections yet
                    # Look for chapter-level links that contain "ethics" or "code of"
                    if self.search_for_ethics_terms(text):
                        print(f"    ✅ Found potential ethics section: {text}")
                        
                        # Build full URL - ecode360 uses numeric IDs
                        if href.startswith('http'):
                            section_url = href
                        elif href.startswith('/'):
                            section_url = f"https://ecode360.com{href}"
                        else:
                            # Just a numeric ID like "8555611"
                            section_url = f"https://ecode360.com/{href}"
                        
                        # Scrape this section and all its subsections
                        section_data = self._scrape_section(section_url, text)
                        if section_data:
                            ethics_sections.append(section_data)
                
                if ethics_sections:
                    print(f"  ✅ Found {len(ethics_sections)} ethics section(s)")
                    return {
                        'city': city_name,
                        'state': state,
                        'url': url,
                        'code': code,
                        'ethics_sections': ethics_sections
                    }
                else:
                    print(f"  ⚠️  No ethics sections found")
                    return None
                
        except Exception as e:
            print(f"  ❌ Error scraping {city_name}: {e}")
            return None
    
    def _scrape_section(self, url: str, title: str) -> Optional[Dict]:
        """
        Scrape a specific section and all its content.
        
        Args:
            url: URL of the section
            title: Title of the section
            
        Returns:
            Dict with 'title', 'url', 'content', 'has_aspirational_language'
        """
        try:
            print(f"      🔍 Scraping section: {title}")
            self.page.goto(url, timeout=60000)
            self.page.wait_for_load_state('networkidle')
            
            # Wait for content to load - ecode360 is heavily JavaScript-based
            try:
                # Wait for main content area to appear
                self.page.wait_for_selector('div[id="page-content"]', timeout=10000)
                time.sleep(2)  # Additional wait for dynamic content
            except:
                print(f"        ⚠️  Timeout waiting for content")
            
            html = self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Debug: save section HTML
            with open(f"debug_section_{url.split('/')[-1]}.html", 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"        🐛 Saved section HTML")
            
            # Extract the main content
            # ecode360 typically has the content in specific containers
            content_elements = []
            
            # Look for the main content area - ecode360 structure
            # The actual content is usually in specific divs
            main_content = soup.find('div', id='page-content') or soup.body
            
            if main_content:
                # Extract text from paragraphs, divs with specific classes, etc.
                # ecode360 uses contentText class for main paragraphs
                for elem in main_content.find_all(['p', 'div'], class_=lambda x: x and ('contentText' in str(x) or 'section' in str(x).lower()) if x else False):
                    text = elem.get_text(separator='\n', strip=True)
                    if text and len(text) > 20:  # Filter out empty/tiny elements
                        content_elements.append({'type': 'paragraph', 'text': text})
                
                # Also get headings
                for elem in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5:
                        content_elements.append({'type': 'heading', 'level': elem.name, 'text': text})
                
                # If still nothing, get all paragraphs
                if not content_elements:
                    for elem in main_content.find_all('p'):
                        text = elem.get_text(separator='\n', strip=True)
                        if text and len(text) > 20:
                            content_elements.append({'type': 'paragraph', 'text': text})
                
                # Last resort: get all text
                if not content_elements:
                    full_text = main_content.get_text(separator='\n\n', strip=True)
                    if full_text:
                        # Split into paragraphs
                        paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip() and len(p.strip()) > 20]
                        content_elements = [{'type': 'paragraph', 'text': p} for p in paragraphs[:100]]  # Limit to avoid huge dumps
            
            if content_elements:
                # Combine all text to check for aspirational language
                full_text = '\n'.join([elem['text'] for elem in content_elements])
                has_aspirational = self.contains_aspirational_language(full_text)
                
                print(f"        📝 Extracted {len(content_elements)} content elements")
                if has_aspirational:
                    print(f"        ⭐ Contains aspirational language!")
                
                return {
                    'title': title,
                    'url': url,
                    'content': content_elements,
                    'has_aspirational_language': has_aspirational,
                    'full_text': full_text  # For PDF generation
                }
            else:
                print(f"        ⚠️  No content extracted")
                return None
                
        except Exception as e:
            print(f"        ❌ Error scraping section: {e}")
            return None


if __name__ == "__main__":
    # Test the parser with Malta, NY
    parser = Ecode360Parser()
    test_city = {
        'city': 'Town of Malta',
        'state': 'NY',
        'url': 'https://ecode360.com/MA1379',
        'code': 'MA1379'
    }
    
    result = parser.scrape_city(test_city)
    if result:
        print(f"\n✅ Successfully scraped {result['city']}")
        print(f"Found {len(result['ethics_sections'])} ethics section(s)")
        for section in result['ethics_sections']:
            print(f"\n  Section: {section['title']}")
            print(f"  URL: {section['url']}")
            print(f"  Has aspirational language: {section['has_aspirational_language']}")
            print(f"  Content elements: {len(section['content'])}")
