"""
Parser for Code Publishing (codepublishing.com) municipal code platform.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class CodePublishingParser:
    """Parser for Code Publishing platform."""
    
    ETHICS_TERMS = [
        'ethic', 'conflict of interest', 'financial disclosure',
        'code of conduct', 'prohibited interest'
    ]
    
    def search_for_ethics_sections(self, text):
        """Check if text contains ethics-related terms."""
        text_lower = text.lower()
        return any(term in text_lower for term in self.ETHICS_TERMS)
    
    def scrape_city(self, city_info):
        """
        Detect ethics code presence in a Code Publishing city.
        
        Args:
            city_info: Dict with 'city', 'state', 'url' keys
            
        Returns:
            Dict with detection info or None if not found
        """
        city_name = city_info.get('city', 'Unknown')
        state = city_info.get('state', 'Unknown')
        url = city_info.get('url', '')
        
        print(f"\n🔍 Checking {city_name} ({state})...")
        print(f"  Platform: Code Publishing")
        print(f"  URL: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                print("  ⏳ Loading page...")
                page.goto(url, timeout=60000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)
                
                html = page.content()
                browser.close()
                
                soup = BeautifulSoup(html, 'lxml')
                page_text = soup.get_text()
                
                # Check for ethics content
                if self.search_for_ethics_sections(page_text):
                    print(f"  ✅ Ethics content detected")
                    return {
                        'city': city_name,
                        'state': state,
                        'url': url,
                        'platform': 'Code Publishing',
                        'ethics_sections': [{
                            'title': 'Ethics Content Detected',
                            'content': f"Ethics-related content found in {city_name} code. " +
                                      "Code Publishing platform requires manual review at: " + url,
                            'url': url
                        }],
                        'requires_manual_review': True
                    }
                else:
                    print(f"  ℹ️  No ethics content detected")
                    return None
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return None


if __name__ == '__main__':
    parser = CodePublishingParser()
    
    test_city = {
        'city': 'Eagle Mountain',
        'state': 'Utah',
        'url': 'http://www.codepublishing.com/ut/eaglemountain/',
        'platform': 'Code Publishing'
    }
    
    result = parser.scrape_city(test_city)
    if result:
        print(f"\n{'='*80}")
        print(f"✅ {result['city']}: Detection successful")
