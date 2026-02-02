"""
Parser for General Code (municipal.codes) municipal code platform.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

class GeneralCodeParser:
    """Parser for municipal.codes platform."""
    
    ETHICS_TERMS = [
        'ethic', 'conflict of interest', 'financial disclosure',
        'code of conduct', 'public officer', 'prohibited interest'
    ]
    
    def __init__(self):
        self.browser = None
        self.page = None
    
    def search_for_ethics_sections(self, text):
        """Check if text contains ethics-related terms."""
        text_lower = text.lower()
        return any(term in text_lower for term in self.ETHICS_TERMS)
    
    def scrape_city(self, city_info):
        """
        Scrape ethics code from a General Code city.
        
        Args:
            city_info: Dict with 'city', 'state', 'url' keys
            
        Returns:
            Dict with ethics sections or None if not found
        """
        city_name = city_info.get('city', 'Unknown')
        state = city_info.get('state', 'Unknown')
        url = city_info.get('url', '')
        
        print(f"\n🔍 Scraping {city_name} City Code ({state})...")
        print(f"  Platform: General Code")
        print(f"  URL: {url}")
        
        try:
            with sync_playwright() as p:
                self.browser = p.chromium.launch(headless=True)
                self.page = self.browser.new_page(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Step 1: Load homepage to find chapters
                print("  🔍 Loading homepage...")
                self.page.goto(url, timeout=60000)
                self.page.wait_for_load_state('networkidle')
                self.page.wait_for_timeout(2000)
                
                html = self.page.content()
                soup = BeautifulSoup(html, 'lxml')
                
                # Find all chapter links
                chapter_links = soup.find_all('a', class_='homepage-product-list-item')
                
                # Check chapters that might contain ethics (Government, Personnel, etc.)
                potential_chapters = []
                for link in chapter_links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    # Check if it's Code chapter (not GenPlan, Tables, etc.)
                    if href and '/Code/' in href and not any(x in href for x in ['/Tables', '/CFS', '/SSDFS']):
                        # Prioritize government/personnel/administration chapters
                        priority_keywords = ['government', 'personnel', 'administration', 'general', 'board', 'commission', 'public officer']
                        is_priority = any(keyword in text.lower() for keyword in priority_keywords)
                        
                        if is_priority:
                            potential_chapters.insert(0, {
                                'title': text,
                                'url': href if href.startswith('http') else f"{url.rstrip('/')}{href}"
                            })
                        else:
                            potential_chapters.append({
                                'title': text,
                                'url': href if href.startswith('http') else f"{url.rstrip('/')}{href}"
                            })
                
                # If we have too many chapters, limit to priority ones for efficiency
                if len(potential_chapters) > 15:
                    print(f"  📋 Found {len(potential_chapters)} chapters - checking priority chapters first")
                    potential_chapters = potential_chapters[:10]
                else:
                    print(f"  📋 Found {len(potential_chapters)} chapters to check")
                
                # Check each chapter for ethics content
                ethics_chapters = []
                for chapter in potential_chapters:
                    chapter_url = chapter['url']
                    print(f"    🔍 Checking: {chapter['title']}")
                    
                    self.page.goto(chapter_url, timeout=60000)
                    self.page.wait_for_load_state('networkidle')
                    self.page.wait_for_timeout(1000)
                    
                    chapter_html = self.page.content()
                    chapter_text = BeautifulSoup(chapter_html, 'lxml').get_text()
                    
                    if self.search_for_ethics_sections(chapter_text):
                        ethics_chapters.append(chapter)
                        print(f"      ✅ Found ethics content in {chapter['title']}")
                
                if not ethics_chapters:
                    print(f"  ℹ️  No ethics chapters found in {city_name} City Code ({state})")
                    self.browser.close()
                    return None
                
                # Step 2: Scrape each ethics chapter
                print(f"  🔍 Scraping {len(ethics_chapters)} chapter(s)...")
                ethics_sections = []
                
                for chapter in ethics_chapters:
                    chapter_url = chapter['url']
                    print(f"    📖 Loading chapter: {chapter['title']}")
                    
                    self.page.goto(chapter_url, timeout=60000)
                    self.page.wait_for_load_state('networkidle')
                    self.page.wait_for_timeout(2000)
                    
                    chapter_html = self.page.content()
                    chapter_soup = BeautifulSoup(chapter_html, 'lxml')
                    
                    # Find ethics-related sections within the chapter
                    section_links = chapter_soup.find_all('a', href=True)
                    for sec_link in section_links:
                        sec_text = sec_link.get_text(strip=True)
                        if sec_text and self.search_for_ethics_sections(sec_text):
                            sec_href = sec_link.get('href', '')
                            if sec_href and not sec_href.startswith('#'):
                                # Build proper URL
                                if sec_href.startswith('http'):
                                    section_url = sec_href
                                elif sec_href.startswith('/'):
                                    # Absolute path from root
                                    base_domain = '/'.join(url.split('/')[:3])  # https://provo.municipal.codes
                                    section_url = f"{base_domain}{sec_href}"
                                else:
                                    # Relative path - section numbers like "2.70"
                                    # URL pattern is /Code/2.70 not /Code/2/2.70
                                    base_domain = '/'.join(url.split('/')[:3])
                                    section_url = f"{base_domain}/Code/{sec_href}"
                                
                                print(f"      ✅ Found ethics section: {sec_text}")
                                
                                # Load the specific section
                                self.page.goto(section_url, timeout=60000)
                                self.page.wait_for_load_state('networkidle')
                                self.page.wait_for_timeout(2000)
                                
                                section_html = self.page.content()
                                section_soup = BeautifulSoup(section_html, 'lxml')
                                
                                # Extract main content
                                main_content = section_soup.find('div', id='main-column')
                                if main_content:
                                    content_text = main_content.get_text(separator='\n', strip=True)
                                    
                                    ethics_sections.append({
                                        'title': sec_text,
                                        'content': content_text,
                                        'url': section_url
                                    })
                                    
                                    print(f"        📝 Extracted {len(content_text)} characters")
                
                self.browser.close()
                
                if not ethics_sections:
                    print(f"  ⚠️  No ethics sections found")
                    return None
                
                print(f"  ✅ Found {len(ethics_sections)} ethics section(s)")
                
                return {
                    'city': city_name,
                    'state': state,
                    'url': url,
                    'platform': 'General Code',
                    'ethics_sections': ethics_sections
                }
                
        except Exception as e:
            print(f"  ❌ Error scraping {city_name}: {str(e)}")
            if self.browser:
                self.browser.close()
            return None


if __name__ == '__main__':
    # Test with Provo (known to have ethics code)
    parser = GeneralCodeParser()
    
    test_cities = [
        {
            'city': 'Provo',
            'state': 'Utah',
            'url': 'https://provo.municipal.codes/',
            'platform': 'General Code'
        }
    ]
    
    for city_info in test_cities:
        result = parser.scrape_city(city_info)
        
        if result:
            print(f"\n{'='*80}")
            print(f"✅ Success: {result['city']}, {result['state']}")
            print(f"{'='*80}")
            for section in result['ethics_sections']:
                print(f"\n📄 {section['title']}")
                print(f"🔗 {section['url']}")
                content_preview = section['content'][:500]
                print(f"📝 {content_preview}...")
                print(f"   Total: {len(section['content'])} characters")
        else:
            print(f"\n⚠️  No ethics sections found")
