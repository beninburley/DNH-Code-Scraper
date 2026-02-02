"""
Parser for Amlegal (codelibrary.amlegal.com) municipal code platform.
Uses detection-only approach due to heavy JavaScript rendering.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class AmlegalParser:
    """Parser for Amlegal platform with JavaScript handling."""
    
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
        Detect ethics code presence in an Amlegal city.
        
        Args:
            city_info: Dict with 'city', 'state', 'url' keys
            
        Returns:
            Dict with detection info or None if not found
        """
        city_name = city_info.get('city', 'Unknown')
        state = city_info.get('state', 'Unknown')
        url = city_info.get('url', '')
        
        print(f"\n🔍 Checking {city_name} ({state})...")
        print(f"  Platform: Amlegal")
        print(f"  URL: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Load page and wait for JavaScript
                print("  ⏳ Loading page (Amlegal uses heavy JavaScript)...")
                page.goto(url, timeout=60000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(5000)  # Extra wait for JS rendering
                
                html = page.content()
                browser.close()
                
                soup = BeautifulSoup(html, 'lxml')
                page_text = soup.get_text()
                
                # Check if any ethics terms appear
                if self.search_for_ethics_sections(page_text):
                    # Try to find specific section titles
                    ethics_links = []
                    all_links = soup.find_all('a')
                    
                    for link in all_links:
                        link_text = link.get_text(strip=True)
                        if link_text and self.search_for_ethics_sections(link_text):
                            href = link.get('href', '')
                            ethics_links.append({
                                'title': link_text,
                                'url': href if href.startswith('http') else url
                            })
                    
                    if ethics_links:
                        print(f"  ✅ Found {len(ethics_links)} potential ethics section(s)")
                        for link in ethics_links[:3]:
                            print(f"     - {link['title'][:70]}")
                        
                        return {
                            'city': city_name,
                            'state': state,
                            'url': url,
                            'platform': 'Amlegal',
                            'ethics_sections': [{
                                'title': 'Ethics Code Detected in TOC',
                                'content': f"Amlegal platform detected ethics-related sections:\n\n" + 
                                          "\n".join([f"- {link['title']}" for link in ethics_links[:5]]) +
                                          "\n\nNote: Amlegal uses heavy JavaScript rendering. " +
                                          "Full content extraction requires manual review at: " + url,
                                'url': url
                            }],
                            'requires_manual_review': True
                        }
                    else:
                        print(f"  ⚠️  Ethics terms found but no specific sections identified")
                        return {
                            'city': city_name,
                            'state': state,
                            'url': url,
                            'platform': 'Amlegal',
                            'ethics_sections': [{
                                'title': 'Ethics Content Detected',
                                'content': f"Ethics-related content found in {city_name} code. " +
                                          "Manual review required at: " + url,
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
    parser = AmlegalParser()
    
    test_cities = [
        {
            'city': 'Salt Lake City',
            'state': 'Utah',
            'url': 'https://codelibrary.amlegal.com/codes/saltlakecityut/latest/saltlakecity_ut/0-0-0-1',
            'platform': 'Amlegal'
        },
        {
            'city': 'Logan',
            'state': 'Utah',
            'url': 'https://codelibrary.amlegal.com/codes/loganut/latest/logan_ut/0-0-0-1',
            'platform': 'Amlegal'
        }
    ]
    
    results = []
    for city_info in test_cities:
        result = parser.scrape_city(city_info)
        if result:
            results.append(result)
            print(f"\n{'='*80}")
            print(f"✅ {result['city']}: Detection successful")
    
    print(f"\n\n{'='*80}")
    print(f"SUMMARY: {len(results)}/{len(test_cities)} cities with ethics content detected")
